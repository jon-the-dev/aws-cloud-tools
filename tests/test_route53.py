"""Tests for the Route 53 cross-account migration commands."""

import json
import stat
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from aws_cloud_utilities.cli import main
from aws_cloud_utilities.commands import route53
from aws_cloud_utilities.commands.route53 import (
    _check_cleanup_safe,
    _migrate_one_zone,
    change_in_batches,
    find_zone,
    next_step,
    records_to_copy,
    rewrite_record,
    route53_group,
    save_transfer_state,
    wait_for_operation,
    zone_id_of,
    zone_location,
)
from aws_cloud_utilities.core.config import Config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SRC_ZONE_ID = "ZSRC"
DST_ZONE_ID = "ZDST"


def _zone(name: str, zone_id: str = SRC_ZONE_ID, private: bool = False) -> dict:
    return {
        "Id": f"/hostedzone/{zone_id}",
        "Name": name,
        "Config": {"PrivateZone": private},
    }


def _record(name: str, rtype: str = "A", **extra) -> dict:
    return {"Name": name, "Type": rtype, **extra}


def _zone_records(domain: str = "example.com.") -> list:
    return [
        _record(domain, "NS"),
        _record(domain, "SOA"),
        _record(f"www.{domain}", "A"),
        _record(f"sub.{domain}", "NS"),
    ]


def _route53_client(zones=None, records=None, delegation=None) -> MagicMock:
    """Mock route53 client whose zone lookup and record paginator are canned."""
    client = MagicMock()
    client.list_hosted_zones_by_name.return_value = {"HostedZones": zones or []}
    client.get_paginator.return_value.paginate.return_value = [
        {"ResourceRecordSets": records or []}
    ]
    if delegation is not None:
        client.get_hosted_zone.return_value = {
            "DelegationSet": {"NameServers": delegation}
        }
    return client


def _domains_client(registered=(), nameservers=None) -> MagicMock:
    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value = [
        {"Domains": [{"DomainName": d} for d in registered]}
    ]
    if nameservers is not None:
        client.get_domain_detail.return_value = {
            "Nameservers": [{"Name": ns} for ns in nameservers]
        }
    client.update_domain_nameservers.return_value = {"OperationId": "op-1"}
    return client


def _accounts(**clients) -> SimpleNamespace:
    defaults = {
        "route53_src": _route53_client(),
        "route53_dst": _route53_client(),
        "domains_src": _domains_client(),
        "domains_dst": _domains_client(),
    }
    defaults.update(clients)
    return SimpleNamespace(source_profile="src", dest_profile="dst", **defaults)


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------


class TestNextStep:
    def test_registered_in_source_means_transfer(self):
        for in_src in (True, False):
            for in_dst in (True, False):
                assert next_step("source", in_src, in_dst) == "transfer"

    def test_registered_in_dest_without_dest_zone_means_migrate_zone(self):
        assert next_step("dest", True, False) == "migrate-zone"
        assert next_step("dest", False, False) == "migrate-zone"

    def test_registered_in_dest_with_zones_in_both_means_cleanup(self):
        assert next_step("dest", True, True) == "cleanup"

    def test_registered_in_dest_with_zone_only_in_dest_means_done(self):
        assert next_step("dest", False, True) == "done"


class TestZoneLocation:
    @pytest.mark.parametrize(
        "in_src,in_dst,expected",
        [
            (True, True, "both"),
            (True, False, "source"),
            (False, True, "dest"),
            (False, False, "none"),
        ],
    )
    def test_all_combinations(self, in_src, in_dst, expected):
        assert zone_location(in_src, in_dst) == expected


class TestZoneIdOf:
    def test_strips_hostedzone_prefix(self):
        assert zone_id_of({"Id": "/hostedzone/Z123ABC"}) == "Z123ABC"

    def test_bare_id_is_unchanged(self):
        assert zone_id_of({"Id": "Z123ABC"}) == "Z123ABC"


class TestFindZone:
    def test_returns_exact_match_and_ignores_subdomain_zone(self):
        client = _route53_client(
            zones=[_zone("sub.example.com.", "ZSUB"), _zone("example.com.", "ZAPEX")]
        )

        zone = find_zone(client, "example.com")

        assert zone is not None
        assert zone_id_of(zone) == "ZAPEX"

    def test_returns_none_when_only_subdomain_zone_present(self):
        client = _route53_client(zones=[_zone("sub.example.com.")])
        assert find_zone(client, "example.com") is None

    def test_skips_private_zone(self):
        client = _route53_client(zones=[_zone("example.com.", private=True)])
        assert find_zone(client, "example.com") is None

    def test_picks_public_zone_when_private_zone_shares_name(self):
        client = _route53_client(
            zones=[
                _zone("example.com.", "ZPRIV", private=True),
                _zone("example.com.", "ZPUB"),
            ]
        )
        assert zone_id_of(find_zone(client, "example.com")) == "ZPUB"

    def test_returns_none_when_no_zones(self):
        assert find_zone(_route53_client(), "example.com") is None

    @pytest.mark.parametrize("domain", ["example.com", "example.com."])
    def test_trailing_dot_is_normalised_in_query_and_match(self, domain):
        client = _route53_client(zones=[_zone("example.com.")])

        assert find_zone(client, domain) is not None
        assert client.list_hosted_zones_by_name.call_args.kwargs["DNSName"] == (
            "example.com."
        )


class TestRewriteRecord:
    def test_alias_to_source_zone_is_repointed_to_dest(self):
        record = _record(
            "lb.example.com.",
            AliasTarget={"HostedZoneId": SRC_ZONE_ID, "DNSName": "x.example.com."},
        )

        result = rewrite_record(record, SRC_ZONE_ID, DST_ZONE_ID)

        assert result["AliasTarget"]["HostedZoneId"] == DST_ZONE_ID
        assert result["AliasTarget"]["DNSName"] == "x.example.com."

    def test_alias_to_other_zone_is_left_alone(self):
        cloudfront_zone = "Z2FDTNDATAQYW2"
        record = _record(
            "cdn.example.com.",
            AliasTarget={"HostedZoneId": cloudfront_zone, "DNSName": "d.cloudfront.net."},
        )

        result = rewrite_record(record, SRC_ZONE_ID, DST_ZONE_ID)

        assert result["AliasTarget"]["HostedZoneId"] == cloudfront_zone

    def test_non_alias_record_is_untouched(self):
        record = _record("www.example.com.", ResourceRecords=[{"Value": "1.2.3.4"}])
        expected = json.loads(json.dumps(record))

        assert rewrite_record(record, SRC_ZONE_ID, DST_ZONE_ID) == expected


class TestRecordsToCopy:
    def test_drops_apex_ns_and_soa_but_keeps_subdomain_delegation(self):
        records = _zone_records()

        copied = records_to_copy(records, SRC_ZONE_ID, DST_ZONE_ID)

        assert [(r["Name"], r["Type"]) for r in copied] == [
            ("www.example.com.", "A"),
            ("sub.example.com.", "NS"),
        ]

    def test_keeps_other_record_types_at_apex(self):
        records = _zone_records() + [_record("example.com.", "MX"), _record("example.com.", "A")]

        copied = records_to_copy(records, SRC_ZONE_ID, DST_ZONE_ID)

        assert ("example.com.", "MX") in [(r["Name"], r["Type"]) for r in copied]
        assert ("example.com.", "A") in [(r["Name"], r["Type"]) for r in copied]

    def test_applies_alias_rewrite(self):
        records = _zone_records() + [
            _record(
                "self.example.com.",
                AliasTarget={"HostedZoneId": SRC_ZONE_ID, "DNSName": "www.example.com."},
            )
        ]

        copied = records_to_copy(records, SRC_ZONE_ID, DST_ZONE_ID)

        alias = next(r for r in copied if r["Name"] == "self.example.com.")
        assert alias["AliasTarget"]["HostedZoneId"] == DST_ZONE_ID

    def test_zone_without_soa_raises(self):
        with pytest.raises(click.ClickException, match="no SOA"):
            records_to_copy([_record("www.example.com.")], SRC_ZONE_ID, DST_ZONE_ID)

    @pytest.mark.parametrize(
        "field, value",
        [
            ("HealthCheckId", "abc-123"),
            ("TrafficPolicyInstanceId", "tp-1"),
            ("CidrRoutingConfig", {"CollectionId": "c1", "LocationName": "l1"}),
        ],
    )
    def test_source_bound_record_raises_naming_the_record(self, field, value):
        records = _zone_records() + [_record("hc.example.com.", "A", **{field: value})]

        with pytest.raises(click.ClickException) as exc:
            records_to_copy(records, SRC_ZONE_ID, DST_ZONE_ID)

        assert "hc.example.com. A" in str(exc.value)
        assert field in str(exc.value)


class TestChangeInBatches:
    def test_1200_records_split_500_500_200_with_action(self):
        client = MagicMock()
        records = [_record(f"r{i}.example.com.") for i in range(1200)]

        change_in_batches(client, DST_ZONE_ID, "UPSERT", records)

        calls = client.change_resource_record_sets.call_args_list
        sizes = [len(c.kwargs["ChangeBatch"]["Changes"]) for c in calls]
        assert sizes == [500, 500, 200]
        for c in calls:
            assert c.kwargs["HostedZoneId"] == DST_ZONE_ID
            assert {ch["Action"] for ch in c.kwargs["ChangeBatch"]["Changes"]} == {"UPSERT"}

    def test_delete_counts_single_against_the_element_limit(self):
        client = MagicMock()
        records = [_record(f"r{i}.example.com.") for i in range(1001)]

        change_in_batches(client, DST_ZONE_ID, "DELETE", records)

        first, second = client.change_resource_record_sets.call_args_list
        assert len(first.kwargs["ChangeBatch"]["Changes"]) == 1000
        assert first.kwargs["ChangeBatch"]["Changes"][0] == {
            "Action": "DELETE",
            "ResourceRecordSet": records[0],
        }
        assert second.kwargs["ChangeBatch"]["Changes"] == [
            {"Action": "DELETE", "ResourceRecordSet": records[1000]}
        ]

    def test_multi_value_records_weigh_by_value_count(self):
        client = MagicMock()
        values = [{"Value": f"10.0.0.{i}"} for i in range(10)]
        records = [
            _record(f"r{i}.example.com.", ResourceRecords=values) for i in range(51)
        ]

        change_in_batches(client, DST_ZONE_ID, "UPSERT", records)

        sizes = [
            len(c.kwargs["ChangeBatch"]["Changes"])
            for c in client.change_resource_record_sets.call_args_list
        ]
        assert sizes == [50, 1]

    def test_long_values_split_on_the_character_limit(self):
        client = MagicMock()
        txt = [{"Value": "x" * 2000}]
        records = [
            _record(f"dkim{i}.example.com.", "TXT", ResourceRecords=txt)
            for i in range(9)
        ]

        change_in_batches(client, DST_ZONE_ID, "UPSERT", records)

        sizes = [
            len(c.kwargs["ChangeBatch"]["Changes"])
            for c in client.change_resource_record_sets.call_args_list
        ]
        assert sizes == [8, 1]

    def test_exactly_one_full_batch_makes_one_call(self):
        client = MagicMock()
        records = [_record(f"r{i}.example.com.") for i in range(500)]

        change_in_batches(client, DST_ZONE_ID, "UPSERT", records)

        assert client.change_resource_record_sets.call_count == 1

    def test_zero_records_make_no_call(self):
        client = MagicMock()

        change_in_batches(client, DST_ZONE_ID, "UPSERT", [])

        client.change_resource_record_sets.assert_not_called()


class TestNormalizeDomain:
    @pytest.mark.parametrize(
        "raw", ["Example.COM", "example.com.", " example.com ", "EXAMPLE.com."]
    )
    def test_strips_case_whitespace_and_trailing_dot(self, raw):
        assert route53.normalize_domain(raw) == "example.com"


class TestWaitForOperation:
    def test_times_out_with_a_clear_error(self):
        domains = MagicMock()
        domains.get_operation_detail.return_value = {"Status": "IN_PROGRESS"}

        with patch.object(route53.time, "sleep"), pytest.raises(
            click.ClickException, match="still IN_PROGRESS"
        ):
            wait_for_operation(domains, "op-1", "accept")

        assert domains.get_operation_detail.call_count == route53.MAX_POLLS

    def test_returns_on_successful(self):
        domains = MagicMock()
        domains.get_operation_detail.return_value = {"Status": "SUCCESSFUL"}

        with patch.object(route53.time, "sleep") as sleep:
            wait_for_operation(domains, "op-1", "accept")

        sleep.assert_not_called()
        domains.get_operation_detail.assert_called_once_with(OperationId="op-1")

    @pytest.mark.parametrize("status", ["ERROR", "FAILED"])
    def test_raises_with_label_and_message_on_failure(self, status):
        domains = MagicMock()
        domains.get_operation_detail.return_value = {
            "Status": status,
            "Message": "registry said no",
        }

        with pytest.raises(click.ClickException) as exc:
            wait_for_operation(domains, "op-1", "accept")

        assert "accept" in exc.value.message
        assert "registry said no" in exc.value.message

    def test_failure_without_message_still_raises_with_label(self):
        domains = MagicMock()
        domains.get_operation_detail.return_value = {"Status": "FAILED"}

        with pytest.raises(click.ClickException) as exc:
            wait_for_operation(domains, "op-1", "update name servers")

        assert "update name servers" in exc.value.message

    def test_polls_through_in_progress_until_successful(self):
        domains = MagicMock()
        domains.get_operation_detail.side_effect = [
            {"Status": "IN_PROGRESS"},
            {"Status": "IN_PROGRESS"},
            {"Status": "SUCCESSFUL"},
        ]

        with patch.object(route53.time, "sleep") as sleep:
            wait_for_operation(domains, "op-1", "accept")

        assert domains.get_operation_detail.call_count == 3
        assert sleep.call_count == 2
        sleep.assert_called_with(route53.POLL_SECONDS)


class TestSaveTransferState:
    def test_writes_json_with_owner_only_permissions(self, tmp_path):
        state = {"operation_id": "op-1", "password": "s3cret", "dest_account": "123"}

        path = save_transfer_state(tmp_path, "example.com", state)

        assert path == tmp_path / "transfers" / "example.com.json"
        assert json.loads(path.read_text()) == state
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700

    def test_overwrite_keeps_restrictive_mode(self, tmp_path):
        save_transfer_state(tmp_path, "example.com", {"password": "old"})

        path = save_transfer_state(tmp_path, "example.com", {"password": "new"})

        assert json.loads(path.read_text()) == {"password": "new"}
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


# ---------------------------------------------------------------------------
# Safety checks and zone migration
# ---------------------------------------------------------------------------

NS_DST = ["ns-1.awsdns-01.org", "ns-2.awsdns-02.com"]


class TestCheckCleanupSafe:
    def test_raises_when_source_zone_missing(self):
        accounts = _accounts(route53_dst=_route53_client(zones=[_zone("example.com.", DST_ZONE_ID)]))

        with pytest.raises(click.ClickException, match="both accounts"):
            _check_cleanup_safe(accounts, "example.com")

    def test_raises_when_dest_zone_missing(self):
        accounts = _accounts(route53_src=_route53_client(zones=[_zone("example.com.")]))

        with pytest.raises(click.ClickException, match="both accounts"):
            _check_cleanup_safe(accounts, "example.com")

    def test_raises_when_registrar_ns_differ_from_dest_delegation(self):
        accounts = _accounts(
            route53_src=_route53_client(zones=[_zone("example.com.")]),
            route53_dst=_route53_client(
                zones=[_zone("example.com.", DST_ZONE_ID)], delegation=NS_DST
            ),
            domains_dst=_domains_client(
                registered=["example.com"],
                nameservers=["ns-9.awsdns-09.net"] + NS_DST[:1],
            ),
        )

        with pytest.raises(click.ClickException, match="do not match"):
            _check_cleanup_safe(accounts, "example.com")

    def test_raises_when_registrar_ns_are_still_the_source_ones(self):
        accounts = _accounts(
            route53_src=_route53_client(zones=[_zone("example.com.")]),
            route53_dst=_route53_client(
                zones=[_zone("example.com.", DST_ZONE_ID)], delegation=NS_DST
            ),
            domains_dst=_domains_client(
                registered=["example.com"],
                nameservers=["ns-7.awsdns-07.co.uk", "ns-8.awsdns-08.org"],
            ),
        )

        with pytest.raises(click.ClickException):
            _check_cleanup_safe(accounts, "example.com")

    def test_raises_when_domain_not_registered_in_dest(self):
        accounts = _accounts(
            route53_src=_route53_client(zones=[_zone("example.com.")]),
            route53_dst=_route53_client(
                zones=[_zone("example.com.", DST_ZONE_ID)], delegation=NS_DST
            ),
            domains_dst=_domains_client(nameservers=NS_DST),
        )

        with pytest.raises(click.ClickException, match="not registered"):
            _check_cleanup_safe(accounts, "example.com")

        accounts.domains_dst.get_domain_detail.assert_not_called()

    def test_raises_when_destination_lacks_a_source_record(self):
        src_records = _zone_records() + [
            _record("mail.example.com.", "MX", ResourceRecords=[{"Value": "10 mx"}])
        ]
        dst_records = _zone_records()
        accounts = _accounts(
            route53_src=_route53_client(
                zones=[_zone("example.com.", SRC_ZONE_ID)], records=src_records
            ),
            route53_dst=_route53_client(
                zones=[_zone("example.com.", DST_ZONE_ID)],
                records=dst_records,
                delegation=NS_DST,
            ),
            domains_dst=_domains_client(registered=["example.com"], nameservers=NS_DST),
        )

        with pytest.raises(click.ClickException) as exc:
            _check_cleanup_safe(accounts, "example.com")

        assert "mail.example.com. MX" in str(exc.value)
        assert "www.example.com. A" not in str(exc.value)

    def test_raises_when_destination_record_values_differ(self):
        src_records = _zone_records() + [
            _record("api.example.com.", "A", ResourceRecords=[{"Value": "10.0.0.1"}])
        ]
        dst_records = _zone_records() + [
            _record("api.example.com.", "A", ResourceRecords=[{"Value": "10.0.0.2"}])
        ]
        accounts = _accounts(
            route53_src=_route53_client(
                zones=[_zone("example.com.", SRC_ZONE_ID)], records=src_records
            ),
            route53_dst=_route53_client(
                zones=[_zone("example.com.", DST_ZONE_ID)],
                records=dst_records,
                delegation=NS_DST,
            ),
            domains_dst=_domains_client(registered=["example.com"], nameservers=NS_DST),
        )

        with pytest.raises(click.ClickException, match="api.example.com. A"):
            _check_cleanup_safe(accounts, "example.com")

    def test_rewritten_alias_in_destination_counts_as_present(self):
        src_records = _zone_records() + [
            _record(
                "self.example.com.",
                "A",
                AliasTarget={"HostedZoneId": SRC_ZONE_ID, "DNSName": "example.com."},
            )
        ]
        dst_records = _zone_records() + [
            _record(
                "self.example.com.",
                "A",
                AliasTarget={"HostedZoneId": DST_ZONE_ID, "DNSName": "example.com."},
            )
        ]
        accounts = _accounts(
            route53_src=_route53_client(
                zones=[_zone("example.com.", SRC_ZONE_ID)], records=src_records
            ),
            route53_dst=_route53_client(
                zones=[_zone("example.com.", DST_ZONE_ID)],
                records=dst_records,
                delegation=NS_DST,
            ),
            domains_dst=_domains_client(registered=["example.com"], nameservers=NS_DST),
        )

        zone, leftovers = _check_cleanup_safe(accounts, "example.com")

        assert zone_id_of(zone) == SRC_ZONE_ID
        assert [r["Name"] for r in leftovers] == [
            "www.example.com.",
            "sub.example.com.",
            "self.example.com.",
        ]

    def test_returns_source_zone_when_everything_matches(self):
        accounts = _accounts(
            route53_src=_route53_client(zones=[_zone("example.com.", SRC_ZONE_ID)]),
            route53_dst=_route53_client(
                zones=[_zone("example.com.", DST_ZONE_ID)], delegation=NS_DST
            ),
            domains_dst=_domains_client(
                registered=["example.com"], nameservers=list(reversed(NS_DST))
            ),
        )

        zone, leftovers = _check_cleanup_safe(accounts, "example.com")

        assert zone_id_of(zone) == SRC_ZONE_ID
        assert leftovers == []
        accounts.route53_dst.get_hosted_zone.assert_called_once_with(Id=DST_ZONE_ID)

    def test_name_server_case_and_trailing_dot_do_not_block_cleanup(self):
        registrar = [ns.upper() + "." for ns in NS_DST]
        accounts = _accounts(
            route53_src=_route53_client(zones=[_zone("example.com.", SRC_ZONE_ID)]),
            route53_dst=_route53_client(
                zones=[_zone("example.com.", DST_ZONE_ID)], delegation=NS_DST
            ),
            domains_dst=_domains_client(registered=["example.com"], nameservers=registrar),
        )

        zone, _ = _check_cleanup_safe(accounts, "example.com")

        assert zone_id_of(zone) == SRC_ZONE_ID


def _migration_accounts(dst_zones=None, dst_record_count=None) -> SimpleNamespace:
    """Accounts where example.com. has a source zone and is registered in dest."""
    src_records = _zone_records()
    dst = _route53_client(
        zones=dst_zones or [],
        records=[None] * (len(src_records) if dst_record_count is None else dst_record_count),
        delegation=NS_DST,
    )
    dst.create_hosted_zone.return_value = {"HostedZone": _zone("example.com.", DST_ZONE_ID)}
    return _accounts(
        route53_src=_route53_client(zones=[_zone("example.com.")], records=src_records),
        route53_dst=dst,
        domains_dst=_domains_client(registered=["example.com"]),
    )


@pytest.fixture
def no_waiting():
    with patch.object(route53, "wait_for_operation") as wait, patch.object(
        route53.time, "sleep"
    ):
        yield wait


class TestMigrateOneZone:
    def test_raises_when_no_source_zone(self, no_waiting):
        accounts = _accounts(domains_dst=_domains_client(registered=["example.com"]))

        with pytest.raises(click.ClickException, match="no public hosted zone"):
            _migrate_one_zone(accounts, "example.com")

        accounts.domains_dst.update_domain_nameservers.assert_not_called()

    def test_raises_when_domain_not_registered_in_dest(self, no_waiting):
        accounts = _migration_accounts()
        accounts.domains_dst = _domains_client(registered=["other.com"])

        with pytest.raises(click.ClickException, match="not registered in dst"):
            _migrate_one_zone(accounts, "example.com")

        accounts.route53_dst.create_hosted_zone.assert_not_called()
        accounts.domains_dst.update_domain_nameservers.assert_not_called()

    def test_creates_dest_zone_when_absent(self, no_waiting):
        accounts = _migration_accounts()

        _migrate_one_zone(accounts, "example.com")

        accounts.route53_dst.create_hosted_zone.assert_called_once()
        assert accounts.route53_dst.create_hosted_zone.call_args.kwargs["Name"] == "example.com."
        upsert = accounts.route53_dst.change_resource_record_sets.call_args.kwargs
        assert upsert["HostedZoneId"] == DST_ZONE_ID

    def test_reuses_dest_zone_when_present(self, no_waiting):
        accounts = _migration_accounts(dst_zones=[_zone("example.com.", "ZEXISTING")])

        _migrate_one_zone(accounts, "example.com")

        accounts.route53_dst.create_hosted_zone.assert_not_called()
        upsert = accounts.route53_dst.change_resource_record_sets.call_args.kwargs
        assert upsert["HostedZoneId"] == "ZEXISTING"

    def test_copies_records_without_apex_ns_and_soa(self, no_waiting):
        accounts = _migration_accounts()

        _migrate_one_zone(accounts, "example.com")

        changes = accounts.route53_dst.change_resource_record_sets.call_args.kwargs[
            "ChangeBatch"
        ]["Changes"]
        assert {c["Action"] for c in changes} == {"UPSERT"}
        assert [(c["ResourceRecordSet"]["Name"], c["ResourceRecordSet"]["Type"]) for c in changes] == [
            ("www.example.com.", "A"),
            ("sub.example.com.", "NS"),
        ]

    def test_record_count_mismatch_raises_before_registrar_is_touched(self, no_waiting):
        accounts = _migration_accounts(dst_record_count=3)

        with pytest.raises(click.ClickException, match="record count mismatch"):
            _migrate_one_zone(accounts, "example.com")

        accounts.domains_dst.update_domain_nameservers.assert_not_called()
        no_waiting.assert_not_called()

    def test_success_points_registrar_at_dest_delegation_set(self, no_waiting):
        accounts = _migration_accounts()

        _migrate_one_zone(accounts, "example.com")

        accounts.domains_dst.update_domain_nameservers.assert_called_once_with(
            DomainName="example.com", Nameservers=[{"Name": ns} for ns in NS_DST]
        )
        no_waiting.assert_called_once_with(
            accounts.domains_dst, "op-1", "update name servers"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

SUBCOMMANDS = ["backup", "transfer", "migrate-zone", "cleanup", "migration-status"]


class TestCliHelp:
    def test_group_help_lists_all_subcommands(self):
        result = CliRunner().invoke(main, ["route53", "--help"])

        assert result.exit_code == 0
        for name in SUBCOMMANDS:
            assert name in result.output

    @pytest.mark.parametrize("command", [c for c in SUBCOMMANDS if c != "backup"])
    def test_subcommand_help_mentions_both_profile_options(self, command):
        result = CliRunner().invoke(main, ["route53", command, "--help"])

        assert result.exit_code == 0
        assert "--source-profile" in result.output
        assert "--dest-profile" in result.output

    def test_backup_help_only_needs_the_source_profile(self):
        result = CliRunner().invoke(main, ["route53", "backup", "--help"])

        assert result.exit_code == 0
        assert "--source-profile" in result.output
        assert "--dest-profile" not in result.output

    def test_migrate_zone_without_domain_fails(self):
        result = CliRunner().invoke(
            main,
            ["route53", "migrate-zone", "--source-profile", "a", "--dest-profile", "b"],
        )

        assert result.exit_code != 0
        assert "DOMAINS" in result.output or "Missing argument" in result.output

    def test_missing_profile_options_fail(self):
        result = CliRunner().invoke(main, ["route53", "cleanup", "example.com"])

        assert result.exit_code != 0


class TestCleanupCommand:
    OPTIONS = ["--source-profile", "src", "--dest-profile", "dst"]

    def _invoke(self, args, input_text=None, leftover_count=3):
        zone = _zone("example.com.", SRC_ZONE_ID)
        leftovers = [_record(f"r{i}.example.com.") for i in range(leftover_count)]
        accounts = MagicMock()
        accounts.route53_src = _route53_client()
        with patch.object(route53, "Accounts", return_value=accounts), patch.object(
            route53, "_check_cleanup_safe", return_value=(zone, leftovers)
        ):
            result = CliRunner().invoke(
                route53_group,
                ["cleanup", *self.OPTIONS, *args],
                input=input_text,
                obj={"config": Config(aws_output_format="table")},
            )
        return result, accounts

    def test_declining_prompt_deletes_nothing(self):
        result, accounts = self._invoke(["example.com"], input_text="n\n")

        assert result.exit_code == 0
        accounts.route53_src.delete_hosted_zone.assert_not_called()
        accounts.route53_src.change_resource_record_sets.assert_not_called()

    def test_accepting_prompt_deletes_zone(self):
        result, accounts = self._invoke(["example.com"], input_text="y\n")

        assert result.exit_code == 0
        accounts.route53_src.delete_hosted_zone.assert_called_once_with(Id=SRC_ZONE_ID)

    def test_confirm_deletes_records_in_batches_then_zone(self):
        result, accounts = self._invoke(["--confirm", "example.com"], leftover_count=1001)

        assert result.exit_code == 0
        calls = accounts.route53_src.change_resource_record_sets.call_args_list
        sizes = [len(c.kwargs["ChangeBatch"]["Changes"]) for c in calls]
        assert sizes == [1000, 1]
        deleted = [
            ch["ResourceRecordSet"]["Name"]
            for c in calls
            for ch in c.kwargs["ChangeBatch"]["Changes"]
        ]
        assert "example.com." not in deleted
        assert {ch["Action"] for c in calls for ch in c.kwargs["ChangeBatch"]["Changes"]} == {"DELETE"}
        accounts.route53_src.delete_hosted_zone.assert_called_once_with(Id=SRC_ZONE_ID)

    def test_confirm_with_only_apex_records_skips_record_deletion(self):
        result, accounts = self._invoke(["--confirm", "example.com"], leftover_count=0)

        assert result.exit_code == 0
        accounts.route53_src.change_resource_record_sets.assert_not_called()
        accounts.route53_src.delete_hosted_zone.assert_called_once_with(Id=SRC_ZONE_ID)

    def test_unsafe_zone_aborts_without_deleting(self):
        accounts = MagicMock()
        with patch.object(route53, "Accounts", return_value=accounts), patch.object(
            route53, "_check_cleanup_safe", side_effect=click.ClickException("unsafe")
        ):
            result = CliRunner().invoke(
                route53_group,
                ["cleanup", *self.OPTIONS, "--confirm", "example.com"],
                obj={"config": Config(aws_output_format="table")},
            )

        assert result.exit_code != 0
        assert "unsafe" in result.output
        accounts.route53_src.delete_hosted_zone.assert_not_called()


class TestBackupCommand:
    def _invoke(self, tmp_path, zones, records=(), zone_detail=None):
        auth = MagicMock()
        r53 = MagicMock()
        r53.get_paginator.side_effect = lambda name: MagicMock(
            paginate=MagicMock(
                return_value=[{"HostedZones": zones}]
                if name == "list_hosted_zones"
                else [{"ResourceRecordSets": list(records)}]
            )
        )
        r53.get_hosted_zone.return_value = zone_detail or {
            "DelegationSet": {"NameServers": NS_DST}
        }
        domains = _domains_client(registered=["example.com"])
        domains.get_domain_detail.return_value = {
            "DomainName": "example.com",
            "ResponseMetadata": {"RequestId": "x"},
        }
        auth.get_client.side_effect = lambda svc: r53 if svc == "route53" else domains
        out = tmp_path / "snap"
        with patch.object(route53, "AWSAuth", return_value=auth):
            result = CliRunner().invoke(
                route53_group,
                ["backup", "--source-profile", "src", "--output-dir", str(out)],
                obj={"config": Config(aws_output_format="table")},
            )
        return result, out

    def test_same_name_zones_get_distinct_files_with_private_modes(self, tmp_path):
        zones = [
            _zone("example.com.", "ZPUBLIC"),
            _zone("example.com.", "ZPRIVATE", private=True),
        ]

        result, out = self._invoke(tmp_path, zones)

        assert result.exit_code == 0, result.output
        names = sorted(p.name for p in out.iterdir())
        assert names == [
            "example.com.ZPRIVATE.json",
            "example.com.ZPUBLIC.json",
            "registered-domains.json",
        ]
        assert stat.S_IMODE(out.stat().st_mode) == 0o700
        for path in out.iterdir():
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
        detail = json.loads((out / "registered-domains.json").read_text())
        assert detail == [{"DomainName": "example.com"}]

    def test_private_zone_without_delegation_set_is_still_written(self, tmp_path):
        zones = [_zone("internal.", "ZPRIV", private=True)]

        result, out = self._invoke(
            tmp_path, zones, zone_detail={"VPCs": [{"VPCId": "vpc-1"}]}
        )

        assert result.exit_code == 0, result.output
        payload = json.loads((out / "internal.ZPRIV.json").read_text())
        assert payload["delegation_set"] is None
        assert payload["vpcs"] == [{"VPCId": "vpc-1"}]
