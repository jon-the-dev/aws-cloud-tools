"""Regression tests for runtime bugs found by running the CLI against a live account.

Each test here corresponds to a filed issue and fails against the pre-fix code:

- #297 waf: commands used @click.pass_obj and config.region
- #298 security: _collect_security_metrics never returned its result
- #299 iam: --max-items was passed as a page size, not a pagination cap
- #300 s3: NoSuchLifecycleConfiguration is no longer on the S3 exception factory
"""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from click.testing import CliRunner

from aws_cloud_utilities.commands import iam as iam_cmd
from aws_cloud_utilities.commands import s3 as s3_cmd
from aws_cloud_utilities.commands import security as security_cmd
from aws_cloud_utilities.commands import waf as waf_cmd

# --------------------------------------------------------------------------- #
# #298 security metrics
# --------------------------------------------------------------------------- #


def test_collect_security_metrics_returns_metrics_keyed_by_region():
    """It must return the assembled dict; returning None made the caller do len(None)."""
    summary = {"metrics": {}, "errors": []}

    with patch.object(
        security_cmd,
        "parallel_execute",
        return_value=[("us-east-1", {"WAF": {"web_acls": 0}})],
    ):
        result = security_cmd._collect_security_metrics(
            Mock(), ["us-east-1"], ["waf"], 24, summary
        )

    assert result is not None, "_collect_security_metrics returned None"
    assert result == {"us-east-1": {"WAF": {"web_acls": 0}}}
    assert summary["metrics"] == result


def test_collect_security_metrics_result_supports_len():
    """The caller does len(all_metrics); guard the exact failure that was seen."""
    summary = {"metrics": {}, "errors": []}

    with patch.object(
        security_cmd,
        "parallel_execute",
        return_value=[("us-east-1", {}), ("us-west-2", {})],
    ):
        result = security_cmd._collect_security_metrics(
            Mock(), ["us-east-1", "us-west-2"], ["waf"], 24, summary
        )

    assert len(result) == 2


# --------------------------------------------------------------------------- #
# #299 iam list-roles --max-items
# --------------------------------------------------------------------------- #


def _run_list_roles(max_items, pages):
    """Invoke `iam list-roles` with a paginator that yields `pages`."""
    paginator = Mock()
    paginator.paginate.return_value = pages
    iam_client = Mock()
    iam_client.get_paginator.return_value = paginator

    aws_auth = Mock()
    aws_auth.get_client.return_value = iam_client

    runner = CliRunner()
    result = runner.invoke(
        iam_cmd.list_roles,
        ["--max-items", str(max_items)],
        obj={"config": Mock(aws_output_format="table"), "aws_auth": aws_auth},
    )
    return result, paginator


def test_list_roles_passes_max_items_through_pagination_config():
    """MaxItems as a service parameter only caps page size; the paginator walks every page."""
    result, paginator = _run_list_roles(5, [{"Roles": []}])

    assert result.exit_code == 0, result.output
    kwargs = paginator.paginate.call_args.kwargs

    assert "PaginationConfig" in kwargs, "MaxItems must go through PaginationConfig"
    assert kwargs["PaginationConfig"]["MaxItems"] == 5
    assert "MaxItems" not in kwargs, "MaxItems must not be sent as a service parameter"


def test_list_roles_path_prefix_still_a_service_parameter():
    """PathPrefix is a real API parameter and must not move into PaginationConfig."""
    paginator = Mock()
    paginator.paginate.return_value = [{"Roles": []}]
    iam_client = Mock()
    iam_client.get_paginator.return_value = paginator
    aws_auth = Mock()
    aws_auth.get_client.return_value = iam_client

    CliRunner().invoke(
        iam_cmd.list_roles,
        ["--path-prefix", "/service-role/"],
        obj={"config": Mock(aws_output_format="table"), "aws_auth": aws_auth},
    )

    kwargs = paginator.paginate.call_args.kwargs
    assert kwargs["PathPrefix"] == "/service-role/"
    assert "MaxItems" in kwargs["PaginationConfig"]


# --------------------------------------------------------------------------- #
# #300 s3 bucket-details lifecycle
# --------------------------------------------------------------------------- #


def _s3_client_without_lifecycle_exception():
    """An S3 client whose exception factory lacks NoSuchLifecycleConfiguration.

    This mirrors botocore >= 1.43, where referencing that attribute inside an
    `except` clause raises AttributeError while handling the original error.
    """

    class Exceptions:
        NoSuchBucket = ClientError

        def __getattr__(self, name):
            raise AttributeError(
                f"object has no attribute {name}. Valid exceptions are: NoSuchBucket"
            )

    client = Mock()
    client.exceptions = Exceptions()
    return client


def _bucket_details_with_lifecycle_error(error_code):
    """Run _get_bucket_details against a client that fails the lifecycle call."""
    client = _s3_client_without_lifecycle_exception()
    client.get_bucket_lifecycle_configuration.side_effect = ClientError(
        {"Error": {"Code": error_code, "Message": error_code}},
        "GetBucketLifecycleConfiguration",
    )
    # Everything else the function touches returns benign empty data.
    client.get_bucket_location.return_value = {"LocationConstraint": None}
    client.list_objects_v2.return_value = {}
    client.get_bucket_versioning.return_value = {}
    client.get_bucket_encryption.return_value = {}
    client.get_bucket_tagging.return_value = {}

    aws_auth = Mock()
    aws_auth.get_client.return_value = client

    return s3_cmd._get_bucket_details(
        aws_auth,
        "my-bucket",
        "us-east-1",
        include_policies=False,
        include_lifecycle=True,
        include_cors=False,
        include_website=False,
        include_logging=False,
    )


def test_lifecycle_absent_is_reported_as_none_not_an_error():
    """A bucket with no lifecycle config is the normal case and must not crash."""
    details = _bucket_details_with_lifecycle_error("NoSuchLifecycleConfiguration")
    assert details["Lifecycle Rules"] == "None"


def test_lifecycle_other_client_error_is_reported_as_error():
    """A genuine failure (e.g. AccessDenied) must not be silently reported as 'None'."""
    details = _bucket_details_with_lifecycle_error("AccessDenied")
    assert details["Lifecycle Rules"] == "Error"


# --------------------------------------------------------------------------- #
# #297 waf context handling
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "command,args",
    [
        (waf_cmd.list_web_acls, []),
        (waf_cmd.get_waf_stats, ["--web-acl", "acl"]),
        (waf_cmd.troubleshoot_waf, ["--web-acl", "acl"]),
    ],
)
def test_waf_commands_read_config_from_ctx_obj(command, args):
    """ctx.obj is a dict; @click.pass_obj handed it in where a Config was expected."""
    config = Mock()
    config.aws_region = "us-east-1"
    config.aws_output_format = "table"

    with patch.object(waf_cmd, "WAFAnalyzer") as analyzer_cls:
        analyzer_cls.return_value.list_web_acls.return_value = []
        analyzer_cls.return_value.get_web_acl_stats.return_value = {}
        result = CliRunner().invoke(
            command, args, obj={"config": config, "aws_auth": Mock()}
        )

    assert "has no attribute" not in result.output, result.output
    analyzer_cls.assert_called_once()
    # The analyzer must be constructed with the region from config.aws_region.
    assert analyzer_cls.call_args.args[1] == "us-east-1"


def test_waf_list_exits_non_zero_on_failure():
    """The failure path used to print an error and still exit 0."""
    config = Mock(aws_region="us-east-1", aws_output_format="table")

    with patch.object(waf_cmd, "WAFAnalyzer") as analyzer_cls:
        analyzer_cls.return_value.list_web_acls.side_effect = RuntimeError("boom")
        result = CliRunner().invoke(
            waf_cmd.list_web_acls, [], obj={"config": config, "aws_auth": Mock()}
        )

    assert result.exit_code != 0, "waf list must not report success when it failed"


def test_waf_commands_do_not_use_pass_obj():
    """Every other module uses @click.pass_context; pass_obj is what broke this group."""
    source = (waf_cmd.__file__ or "").replace(".pyc", ".py")
    with open(source) as handle:
        assert "pass_obj" not in handle.read()
