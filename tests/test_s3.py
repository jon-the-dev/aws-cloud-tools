"""Tests for S3 bucket-details command enhancements (issue #185)."""

import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from aws_cloud_utilities.commands.s3 import _get_all_bucket_details, s3_group
from aws_cloud_utilities.core.auth import AWSAuth
from aws_cloud_utilities.core.config import Config

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config():
    """Minimal Config mock."""
    cfg = Mock(spec=Config)
    cfg.workers = 2
    cfg.aws_output_format = "table"
    return cfg


@pytest.fixture
def mock_aws_auth():
    """AWSAuth mock wired to return a pre-configured S3 client mock."""
    auth = Mock(spec=AWSAuth)
    return auth


@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def cli_ctx(mock_config, mock_aws_auth):
    """Click context obj dict mirroring the real CLI."""
    return {"config": mock_config, "aws_auth": mock_aws_auth}


# ---------------------------------------------------------------------------
# Helper: _get_all_bucket_details
# ---------------------------------------------------------------------------


class TestGetAllBucketDetails:
    """Unit tests for the _get_all_bucket_details helper."""

    def test_returns_one_entry_per_bucket(self, mock_config, mock_aws_auth):
        """All-buckets mode produces one result dict per bucket returned by list_buckets."""
        s3_client = Mock()
        s3_client.list_buckets.return_value = {
            "Buckets": [{"Name": "alpha"}, {"Name": "beta"}]
        }
        mock_aws_auth.get_client.return_value = s3_client

        bucket_detail_returns = [
            {"Bucket Name": "alpha", "Region": "us-east-1"},
            {"Bucket Name": "beta", "Region": "eu-west-1"},
        ]

        with patch(
            "aws_cloud_utilities.commands.s3._get_bucket_details",
            side_effect=bucket_detail_returns,
        ):
            results = _get_all_bucket_details(
                mock_aws_auth,
                mock_config,
                False,
                False,
                False,
                False,
                False,
            )

        assert len(results) == 2
        names = {r["Bucket Name"] for r in results}
        assert names == {"alpha", "beta"}

    def test_returns_empty_list_when_no_buckets(self, mock_config, mock_aws_auth):
        """Returns [] when the account has no buckets."""
        s3_client = Mock()
        s3_client.list_buckets.return_value = {"Buckets": []}
        mock_aws_auth.get_client.return_value = s3_client

        results = _get_all_bucket_details(
            mock_aws_auth,
            mock_config,
            False,
            False,
            False,
            False,
            False,
        )

        assert results == []

    def test_captures_per_bucket_error_gracefully(self, mock_config, mock_aws_auth):
        """A failure on one bucket does not abort; that bucket gets an Error key."""
        s3_client = Mock()
        s3_client.list_buckets.return_value = {
            "Buckets": [{"Name": "good"}, {"Name": "bad"}]
        }
        mock_aws_auth.get_client.return_value = s3_client

        def side_effect(auth, name, region, *args, **kwargs):
            if name == "bad":
                raise RuntimeError("AccessDenied")
            return {"Bucket Name": name, "Region": "us-east-1"}

        with patch(
            "aws_cloud_utilities.commands.s3._get_bucket_details",
            side_effect=side_effect,
        ):
            results = _get_all_bucket_details(
                mock_aws_auth,
                mock_config,
                False,
                False,
                False,
                False,
                False,
            )

        assert len(results) == 2
        bad = next(r for r in results if r["Bucket Name"] == "bad")
        assert "Error" in bad


# ---------------------------------------------------------------------------
# CLI command validation paths (via CliRunner)
# ---------------------------------------------------------------------------


class TestBucketDetailsCommand:
    """Validate bucket-details CLI argument/flag behaviour."""

    def test_error_when_neither_name_nor_all_buckets(self, runner, cli_ctx):
        """Supplying neither BUCKET_NAME nor --all-buckets should abort with an error."""
        result = runner.invoke(
            s3_group,
            ["bucket-details"],
            obj=cli_ctx,
        )
        assert result.exit_code != 0 or "Error" in result.output

    def test_error_when_both_name_and_all_buckets(self, runner, cli_ctx):
        """Supplying both BUCKET_NAME and --all-buckets should abort with an error."""
        result = runner.invoke(
            s3_group,
            ["bucket-details", "my-bucket", "--all-buckets"],
            obj=cli_ctx,
        )
        assert result.exit_code != 0 or "Error" in result.output

    def test_single_bucket_calls_get_bucket_details(self, runner, cli_ctx):
        """Single-bucket path calls _get_bucket_details exactly once with the bucket name."""
        detail = {"Bucket Name": "my-bucket", "Region": "us-east-1"}
        with (
            patch(
                "aws_cloud_utilities.commands.s3._get_bucket_details",
                return_value=detail,
            ) as mock_gbd,
            patch("aws_cloud_utilities.commands.s3.print_output"),
        ):
            runner.invoke(
                s3_group,
                ["bucket-details", "my-bucket"],
                obj=cli_ctx,
            )

        mock_gbd.assert_called_once()
        assert mock_gbd.call_args[0][1] == "my-bucket"

    def test_all_buckets_calls_get_all_bucket_details(self, runner, cli_ctx):
        """--all-buckets path delegates to _get_all_bucket_details, not the single-bucket helper."""
        all_results = [
            {"Bucket Name": "alpha", "Region": "us-east-1"},
            {"Bucket Name": "beta", "Region": "eu-west-1"},
        ]
        with (
            patch(
                "aws_cloud_utilities.commands.s3._get_all_bucket_details",
                return_value=all_results,
            ) as mock_gabd,
            patch("aws_cloud_utilities.commands.s3.print_output"),
        ):
            result = runner.invoke(
                s3_group,
                ["bucket-details", "--all-buckets"],
                obj=cli_ctx,
            )

        mock_gabd.assert_called_once()
        assert result.exit_code == 0
