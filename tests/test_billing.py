"""Tests for the billing CUR setup command and CURManager provisioning."""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from click.testing import CliRunner

from aws_cloud_utilities.cli import main
from aws_cloud_utilities.commands.billing import CURManager
from aws_cloud_utilities.core.exceptions import AWSError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manager(region="us-east-1"):
    """Build a CURManager with fully mocked AWS clients.

    Patches ``__init__`` so no real STS/CUR/S3 calls happen; wires up mock
    ``cur_client``/``s3_client`` and a mock ``aws_auth`` whose ``get_client``
    returns a region-scoped S3 client.
    """
    manager = CURManager.__new__(CURManager)
    manager.logger = MagicMock()
    manager.account_id = "123456789012"
    manager.cur_client = MagicMock()
    manager.s3_client = MagicMock()

    region_s3 = MagicMock()
    aws_auth = MagicMock()
    aws_auth.region_name = region
    aws_auth.get_client.return_value = region_s3
    manager.aws_auth = aws_auth
    return manager


def _not_found_error():
    return ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket")


# ---------------------------------------------------------------------------
# bucket_exists / report_exists
# ---------------------------------------------------------------------------


class TestBucketExists:
    def test_returns_true_when_head_succeeds(self):
        mgr = _make_manager()
        client = MagicMock()
        assert mgr.bucket_exists("b", client) is True
        client.head_bucket.assert_called_once_with(Bucket="b")

    def test_returns_false_when_not_found(self):
        mgr = _make_manager()
        client = MagicMock()
        client.head_bucket.side_effect = _not_found_error()
        assert mgr.bucket_exists("b", client) is False

    def test_raises_when_owned_by_another_account(self):
        mgr = _make_manager()
        client = MagicMock()
        client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}}, "HeadBucket"
        )
        with pytest.raises(AWSError, match="not owned by this account"):
            mgr.bucket_exists("b", client)


class TestReportExists:
    def test_true_when_details_found(self):
        mgr = _make_manager()
        mgr.get_cur_details = MagicMock(return_value={"ReportName": "r"})
        assert mgr.report_exists("r") is True

    def test_false_when_details_none(self):
        mgr = _make_manager()
        mgr.get_cur_details = MagicMock(return_value=None)
        assert mgr.report_exists("r") is False


# ---------------------------------------------------------------------------
# create_cur_bucket - region handling
# ---------------------------------------------------------------------------


class TestCreateCurBucket:
    def test_us_east_1_omits_location_constraint(self):
        mgr = _make_manager()
        client = MagicMock()
        mgr.create_cur_bucket("b", "us-east-1", client)
        client.create_bucket.assert_called_once_with(Bucket="b")

    def test_other_region_sets_location_constraint(self):
        mgr = _make_manager()
        client = MagicMock()
        mgr.create_cur_bucket("b", "us-west-2", client)
        client.create_bucket.assert_called_once_with(
            Bucket="b",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )

    def test_already_owned_is_swallowed(self):
        mgr = _make_manager()
        client = MagicMock()
        client.create_bucket.side_effect = ClientError(
            {"Error": {"Code": "BucketAlreadyOwnedByYou", "Message": "x"}},
            "CreateBucket",
        )
        # Should not raise
        mgr.create_cur_bucket("b", "us-east-1", client)


# ---------------------------------------------------------------------------
# apply_bucket_security / apply_lifecycle_policy
# ---------------------------------------------------------------------------


class TestApplyBucketSecurity:
    def test_blocks_all_public_access_and_encrypts(self):
        mgr = _make_manager()
        client = MagicMock()
        mgr.apply_bucket_security("b", enable_versioning=False, s3_client=client)

        pab = client.put_public_access_block.call_args.kwargs[
            "PublicAccessBlockConfiguration"
        ]
        assert pab == {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        }
        enc = client.put_bucket_encryption.call_args.kwargs[
            "ServerSideEncryptionConfiguration"
        ]
        assert (
            enc["Rules"][0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
            == "AES256"
        )
        client.put_bucket_versioning.assert_not_called()

    def test_versioning_enabled_when_requested(self):
        mgr = _make_manager()
        client = MagicMock()
        mgr.apply_bucket_security("b", enable_versioning=True, s3_client=client)
        client.put_bucket_versioning.assert_called_once_with(
            Bucket="b", VersioningConfiguration={"Status": "Enabled"}
        )


class TestApplyLifecyclePolicy:
    def test_lifecycle_rules_match_reference(self):
        mgr = _make_manager()
        client = MagicMock()
        mgr.apply_lifecycle_policy("b", "cur", 365, client)

        cfg = client.put_bucket_lifecycle_configuration.call_args.kwargs[
            "LifecycleConfiguration"
        ]
        rules = {r["ID"]: r for r in cfg["Rules"]}

        expire = rules["delete-old-cur-data"]
        assert expire["Filter"] == {"Prefix": "cur/"}
        assert expire["Expiration"] == {"Days": 365}
        assert expire["NoncurrentVersionExpiration"] == {"NoncurrentDays": 30}

        multipart = rules["abort-incomplete-multipart-uploads"]
        assert multipart["AbortIncompleteMultipartUpload"] == {"DaysAfterInitiation": 7}


# ---------------------------------------------------------------------------
# create_report_definition - mirrors reference Terraform
# ---------------------------------------------------------------------------


class TestCreateReportDefinition:
    def test_report_definition_params(self):
        mgr = _make_manager()
        mgr.create_report_definition("r", "b", "cur", "HOURLY", "us-east-1")

        rd = mgr.cur_client.put_report_definition.call_args.kwargs["ReportDefinition"]
        assert rd["Format"] == "Parquet"
        assert rd["Compression"] == "Parquet"
        assert rd["AdditionalSchemaElements"] == ["RESOURCES"]
        assert rd["RefreshClosedReports"] is True
        assert rd["ReportVersioning"] == "OVERWRITE_REPORT"
        assert rd["TimeUnit"] == "HOURLY"
        assert rd["S3Region"] == "us-east-1"
        # setup uses a lean definition (no Redshift/QuickSight artifacts)
        assert "AdditionalArtifacts" not in rd

    def test_daily_time_unit_passthrough(self):
        mgr = _make_manager()
        mgr.create_report_definition("r", "b", "cur", "DAILY", "us-west-2")
        rd = mgr.cur_client.put_report_definition.call_args.kwargs["ReportDefinition"]
        assert rd["TimeUnit"] == "DAILY"

    def test_duplicate_report_raises(self):
        mgr = _make_manager()
        mgr.cur_client.put_report_definition.side_effect = Exception(
            "DuplicateReportNameException: exists"
        )
        with pytest.raises(AWSError, match="already exists"):
            mgr.create_report_definition("r", "b", "cur", "HOURLY", "us-east-1")


# ---------------------------------------------------------------------------
# _create_bucket_policy - principal + SourceArn condition
# ---------------------------------------------------------------------------


class TestBucketPolicy:
    def test_policy_grants_billing_service_with_source_conditions(self):
        mgr = _make_manager()
        client = MagicMock()
        mgr._create_bucket_policy("b", "cur", client)

        policy = json.loads(client.put_bucket_policy.call_args.kwargs["Policy"])
        statements = policy["Statement"]
        # Both statements target the billing service principal.
        for stmt in statements:
            assert stmt["Principal"] == {"Service": "billingreports.amazonaws.com"}
            cond = stmt["Condition"]["StringEquals"]
            assert (
                cond["aws:SourceArn"]
                == "arn:aws:cur:us-east-1:123456789012:definition/*"
            )
            assert cond["aws:SourceAccount"] == "123456789012"

        # One statement allows PutObject on the prefixed objects.
        put_stmt = [s for s in statements if s["Action"] == "s3:PutObject"][0]
        assert put_stmt["Resource"] == "arn:aws:s3:::b/cur/*"


# ---------------------------------------------------------------------------
# setup_cur - orchestration, idempotency, dry-run
# ---------------------------------------------------------------------------


class TestSetupCur:
    def test_dry_run_makes_no_mutating_calls(self):
        mgr = _make_manager()
        mgr.bucket_exists = MagicMock(return_value=False)
        mgr.report_exists = MagicMock(return_value=False)
        mgr.create_cur_bucket = MagicMock()
        mgr.apply_bucket_security = MagicMock()
        mgr.apply_lifecycle_policy = MagicMock()
        mgr._create_bucket_policy = MagicMock()
        mgr.create_report_definition = MagicMock()

        summary = mgr.setup_cur(
            report_name="r",
            bucket="b",
            prefix="cur",
            time_unit="HOURLY",
            retention_days=365,
            dry_run=True,
        )

        assert summary["dry_run"] is True
        assert summary["region"] == "us-east-1"
        assert any("create" == s["action"] for s in summary["steps"])
        mgr.create_cur_bucket.assert_not_called()
        mgr.apply_bucket_security.assert_not_called()
        mgr.apply_lifecycle_policy.assert_not_called()
        mgr._create_bucket_policy.assert_not_called()
        mgr.create_report_definition.assert_not_called()

    def test_full_provision_creates_everything(self):
        mgr = _make_manager()
        mgr.bucket_exists = MagicMock(return_value=False)
        mgr.report_exists = MagicMock(return_value=False)
        mgr.create_cur_bucket = MagicMock()
        mgr.apply_bucket_security = MagicMock()
        mgr.apply_lifecycle_policy = MagicMock()
        mgr._create_bucket_policy = MagicMock()
        mgr.create_report_definition = MagicMock()

        mgr.setup_cur(
            report_name="r",
            bucket="b",
            prefix="cur",
            time_unit="HOURLY",
            retention_days=365,
        )

        mgr.create_cur_bucket.assert_called_once()
        mgr.apply_bucket_security.assert_called_once()
        mgr.apply_lifecycle_policy.assert_called_once()
        mgr._create_bucket_policy.assert_called_once()
        mgr.create_report_definition.assert_called_once()

    def test_existing_bucket_is_not_recreated_but_config_reapplied(self):
        mgr = _make_manager()
        mgr.bucket_exists = MagicMock(return_value=True)
        mgr.report_exists = MagicMock(return_value=False)
        mgr.create_cur_bucket = MagicMock()
        mgr.apply_bucket_security = MagicMock()
        mgr.apply_lifecycle_policy = MagicMock()
        mgr._create_bucket_policy = MagicMock()
        mgr.create_report_definition = MagicMock()

        summary = mgr.setup_cur(
            report_name="r",
            bucket="b",
            prefix="cur",
            time_unit="HOURLY",
            retention_days=365,
        )

        mgr.create_cur_bucket.assert_not_called()
        mgr.apply_bucket_security.assert_called_once()
        mgr.create_report_definition.assert_called_once()
        assert summary["steps"][0]["action"] == "already exists"

    def test_existing_report_is_skipped(self):
        mgr = _make_manager()
        mgr.bucket_exists = MagicMock(return_value=True)
        mgr.report_exists = MagicMock(return_value=True)
        mgr.apply_bucket_security = MagicMock()
        mgr.apply_lifecycle_policy = MagicMock()
        mgr._create_bucket_policy = MagicMock()
        mgr.create_report_definition = MagicMock()

        summary = mgr.setup_cur(
            report_name="r",
            bucket="b",
            prefix="cur",
            time_unit="HOURLY",
            retention_days=365,
        )

        mgr.create_report_definition.assert_not_called()
        assert "skipped" in summary["steps"][-1]["action"]

    def test_region_resolution_prefers_explicit_arg(self):
        mgr = _make_manager(region="eu-west-1")
        mgr.bucket_exists = MagicMock(return_value=True)
        mgr.report_exists = MagicMock(return_value=True)
        mgr.apply_bucket_security = MagicMock()
        mgr.apply_lifecycle_policy = MagicMock()
        mgr._create_bucket_policy = MagicMock()

        summary = mgr.setup_cur(
            report_name="r",
            bucket="b",
            prefix="cur",
            time_unit="HOURLY",
            retention_days=365,
            region="ap-south-1",
        )

        assert summary["region"] == "ap-south-1"
        mgr.aws_auth.get_client.assert_called_once_with("s3", region_name="ap-south-1")


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


class TestCurSetupCommand:
    def test_help_lists_options(self):
        runner = CliRunner()
        result = runner.invoke(main, ["billing", "cur-setup", "--help"])
        assert result.exit_code == 0
        assert "--bucket" in result.output
        assert "--dry-run" in result.output
        assert "--time-unit" in result.output

    def test_bucket_is_required(self):
        runner = CliRunner()
        result = runner.invoke(main, ["billing", "cur-setup"])
        assert result.exit_code != 0
        assert "bucket" in result.output.lower()

    @patch("aws_cloud_utilities.commands.billing.CURManager")
    def test_dry_run_invokes_setup_and_prints_plan(self, mock_manager_cls):
        mock_manager = MagicMock()
        mock_manager.setup_cur.return_value = {
            "region": "us-east-1",
            "dry_run": True,
            "steps": [{"resource": "S3 bucket s3://b", "action": "create"}],
        }
        mock_manager_cls.return_value = mock_manager

        runner = CliRunner()
        with (
            patch("aws_cloud_utilities.cli.AWSAuth"),
            patch("aws_cloud_utilities.cli.Config"),
        ):
            result = runner.invoke(
                main,
                ["billing", "cur-setup", "--bucket", "b", "--dry-run"],
            )

        assert result.exit_code == 0
        assert mock_manager.setup_cur.call_args.kwargs["dry_run"] is True
        assert "no resources were created" in result.output.lower()
