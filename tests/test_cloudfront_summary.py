"""Regression tests for CloudFront DistributionSummary handling.

Covers #303 and #304. Three call sites read ``DistributionConfig`` off the
results of ``list_distributions``, which returns DistributionSummary objects
that have no such key -- their fields are flattened to the top level, and there
is no logging block at all.

The fixtures below mirror the real DistributionSummary shape. A fixture that
invents a ``DistributionConfig`` wrapper would pass against the broken code and
prove nothing.
"""

from datetime import datetime
from unittest.mock import Mock

from aws_cloud_utilities.commands import cloudfront as cf


def distribution_summary(
    dist_id="E1234567890ABC",
    enabled=True,
    aliases=("example.com",),
    comment="test distribution",
):
    """A DistributionSummary as list_distributions actually returns it.

    Note there is no DistributionConfig wrapper and no Logging block. Both
    omissions are the point of these tests.
    """
    return {
        "Id": dist_id,
        "ARN": f"arn:aws:cloudfront::123456789012:distribution/{dist_id}",
        "DomainName": f"{dist_id.lower()}.cloudfront.net",
        "Status": "Deployed",
        "Enabled": enabled,
        "Comment": comment,
        "PriceClass": "PriceClass_All",
        "HttpVersion": "http2",
        "IsIPV6Enabled": True,
        "Staging": False,
        "LastModifiedTime": datetime(2026, 8, 5, 12, 0),
        "Aliases": {"Quantity": len(aliases), "Items": list(aliases)},
        "Origins": {"Quantity": 0, "Items": []},
        "WebACLId": "",
    }


def paginated_client(summaries):
    """A CloudFront client whose paginator yields the given summaries."""
    paginator = Mock()
    paginator.paginate.return_value = [
        {"DistributionList": {"Quantity": len(summaries), "Items": summaries}}
    ]
    client = Mock()
    client.get_paginator.return_value = paginator
    return client


def with_logging(client, enabled, bucket="", prefix=""):
    """Make get_distribution_config report a given logging state."""
    client.get_distribution_config.return_value = {
        "ETag": "ETAG",
        "DistributionConfig": {
            "Logging": {
                "Enabled": enabled,
                "Bucket": bucket,
                "Prefix": prefix,
                "IncludeCookies": False,
            }
        },
    }
    return client


# --------------------------------------------------------------------------- #
# #304 list-distributions
# --------------------------------------------------------------------------- #


def test_list_distributions_reads_fields_from_summary():
    """The whole command raised KeyError: 'DistributionConfig' before this."""
    client = paginated_client([distribution_summary()])

    rows = cf._get_all_distributions(
        client, include_disabled=False, show_logging_status=False
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["Distribution ID"] == "E1234567890ABC"
    assert row["State"] == "Enabled"
    assert row["Price Class"] == "PriceClass_All"
    assert row["Comment"] == "test distribution"
    assert row["Aliases"] == "example.com"
    assert row["Last Modified"] == "2026-08-05 12:00"


def test_disabled_distributions_filtered_unless_requested():
    """Enabled lives on the summary; reading it from the wrong place hid this."""
    summaries = [
        distribution_summary("EENABLED0000", enabled=True),
        distribution_summary("EDISABLED000", enabled=False),
    ]

    without = cf._get_all_distributions(
        paginated_client(summaries), include_disabled=False, show_logging_status=False
    )
    with_disabled = cf._get_all_distributions(
        paginated_client(summaries), include_disabled=True, show_logging_status=False
    )

    assert [r["Distribution ID"] for r in without] == ["EENABLED0000"]
    assert len(with_disabled) == 2


def test_long_comment_is_truncated():
    """The truncation branch called len() on a value that used to be unreachable."""
    client = paginated_client([distribution_summary(comment="x" * 80)])

    row = cf._get_all_distributions(client, False, False)[0]

    assert row["Comment"] == "x" * 50 + "..."


def test_show_logging_status_fetches_real_state():
    """A summary has no Logging block, so this needs a per-distribution call."""
    client = with_logging(
        paginated_client([distribution_summary()]), enabled=True, bucket="my-logs"
    )

    row = cf._get_all_distributions(client, False, show_logging_status=True)[0]

    assert row["Logging"] == "Enabled"
    assert row["Log Bucket"] == "my-logs"
    client.get_distribution_config.assert_called_once_with(Id="E1234567890ABC")


def test_logging_status_not_fetched_when_not_requested():
    """Don't pay for N extra API calls unless --show-logging-status was passed."""
    client = paginated_client([distribution_summary()])

    cf._get_all_distributions(client, False, show_logging_status=False)

    client.get_distribution_config.assert_not_called()


# --------------------------------------------------------------------------- #
# #304 invalidate by domain name
# --------------------------------------------------------------------------- #


def test_find_distribution_resolves_an_alias():
    """The KeyError was swallowed, so an alias silently resolved to 'not found'."""
    client = paginated_client(
        [distribution_summary("EOTHER000000", aliases=("other.example.com",))]
        + [distribution_summary("ETARGET00000", aliases=("cdn.example.com",))]
    )
    client.exceptions.NoSuchDistribution = type("NoSuchDistribution", (Exception,), {})
    client.get_distribution.side_effect = client.exceptions.NoSuchDistribution()

    assert cf._get_distribution_id(client, "cdn.example.com") == "ETARGET00000"


def test_find_distribution_resolves_a_cloudfront_domain():
    client = paginated_client([distribution_summary("EDOMAIN00000")])
    client.exceptions.NoSuchDistribution = type("NoSuchDistribution", (Exception,), {})
    client.get_distribution.side_effect = client.exceptions.NoSuchDistribution()

    found = cf._get_distribution_id(client, "edomain00000.cloudfront.net")

    assert found == "EDOMAIN00000"


def test_find_distribution_returns_none_for_unknown_target():
    client = paginated_client([distribution_summary(aliases=("known.example.com",))])
    client.exceptions.NoSuchDistribution = type("NoSuchDistribution", (Exception,), {})
    client.get_distribution.side_effect = client.exceptions.NoSuchDistribution()

    assert cf._get_distribution_id(client, "unknown.example.com") is None


# --------------------------------------------------------------------------- #
# #303 update-logging
# --------------------------------------------------------------------------- #


def _update_one(client, summary, log_bucket="new-logs", dry_run=True):
    aws_auth = Mock()
    aws_auth.get_client.return_value = Mock()
    return cf._update_single_distribution(
        aws_auth,
        client,
        summary,
        "us-east-1",
        log_bucket,
        "cf-logs",
        setup_alarms=False,
        remove_alarms=False,
        sns_topic_arn=None,
        dry_run=dry_run,
    )


def test_already_configured_distribution_is_not_flagged_for_update(monkeypatch):
    """This is the bug: every distribution was reported as needing logging."""
    monkeypatch.setattr(cf, "_get_cloudformation_stack", lambda *a, **k: None)
    client = with_logging(Mock(), enabled=True, bucket="new-logs", prefix="example-com")

    result = _update_one(client, distribution_summary())

    assert result["logging_enabled"] is True
    assert result["current_bucket"] == "new-logs"
    assert result["would_update"] is False


def test_unconfigured_distribution_is_flagged_for_update(monkeypatch):
    monkeypatch.setattr(cf, "_get_cloudformation_stack", lambda *a, **k: None)
    client = with_logging(Mock(), enabled=False)

    result = _update_one(client, distribution_summary())

    assert result["logging_enabled"] is False
    assert result["would_update"] is True


def test_distribution_logging_to_a_different_bucket_is_flagged(monkeypatch):
    monkeypatch.setattr(cf, "_get_cloudformation_stack", lambda *a, **k: None)
    client = with_logging(Mock(), enabled=True, bucket="some-other-bucket")

    result = _update_one(client, distribution_summary())

    assert result["would_update"] is True


def test_aliases_are_read_from_the_summary(monkeypatch):
    """Aliases resolved to [] before, so every distribution got the same prefix."""
    monkeypatch.setattr(cf, "_get_cloudformation_stack", lambda *a, **k: None)
    client = with_logging(Mock(), enabled=False)

    result = _update_one(client, distribution_summary(aliases=("cdn.example.com",)))

    assert result["aliases"] == ["cdn.example.com"]


def test_real_run_derives_log_prefix_from_the_first_alias(monkeypatch):
    """With aliases always empty, every distribution logged under the flat default."""
    monkeypatch.setattr(cf, "_get_cloudformation_stack", lambda *a, **k: None)
    captured = {}

    def fake_enable(aws_auth, dist_id, bucket, prefix):
        captured["prefix"] = prefix

    monkeypatch.setattr(cf, "_enable_distribution_logging", fake_enable)
    client = with_logging(Mock(), enabled=False)

    _update_one(
        client, distribution_summary(aliases=("cdn.example.com",)), dry_run=False
    )

    assert captured["prefix"] == "cdn-example-com"


# --------------------------------------------------------------------------- #
# helper
# --------------------------------------------------------------------------- #


def test_logging_helper_returns_empty_dict_on_error():
    """A failed lookup must not take down the whole listing."""
    client = Mock()
    client.get_distribution_config.side_effect = RuntimeError("denied")

    assert cf._get_distribution_logging(client, "E123") == {}


def test_logging_helper_skips_the_call_for_an_empty_id():
    client = Mock()

    assert cf._get_distribution_logging(client, "") == {}
    client.get_distribution_config.assert_not_called()
