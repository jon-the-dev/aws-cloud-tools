"""Route 53 domain and hosted zone migration between AWS accounts.

Transferring a registered domain between AWS accounts does not move its hosted
zone. The registrar keeps pointing at the old zone, so DNS keeps working, but
the zone is orphaned in the source account. These commands do the full move:

    backup            snapshot every zone and registered domain in source
    transfer          offer the domain from source, accept it in destination
    migrate-zone      recreate the zone in destination, copy records, repoint
                      the registrar at the new name servers
    cleanup           delete the old source zone once the registrar points at
                      the destination zone
    migration-status  show where each domain stands and which step is next
"""

import copy
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import click
from rich.console import Console

from ..core.auth import AWSAuth
from ..core.config import Config
from ..core.utils import print_output

console = Console()

MAX_BATCH_ELEMENTS = 1000
MAX_BATCH_CHARS = 32000
POLL_SECONDS = 15
MAX_POLLS = 120
MAX_RETRIES = 10
DOMAINS_REGION = "us-east-1"
SOURCE_BOUND_FIELDS = ("HealthCheckId", "TrafficPolicyInstanceId", "CidrRoutingConfig")


class Accounts:
    """Route 53 and Route 53 Domains clients for the source and destination."""

    def __init__(self, source_profile: str, dest_profile: str):
        self.source_profile = source_profile
        self.dest_profile = dest_profile
        self._src = AWSAuth(
            profile_name=source_profile,
            region_name=DOMAINS_REGION,
            max_retries=MAX_RETRIES,
        )
        self._dst = AWSAuth(
            profile_name=dest_profile,
            region_name=DOMAINS_REGION,
            max_retries=MAX_RETRIES,
        )
        if self._src.get_account_id() == self._dst.get_account_id():
            raise click.ClickException(
                f"--source-profile {source_profile} and --dest-profile {dest_profile} "
                "resolve to the same AWS account; nothing to migrate"
            )
        self.route53_src = self._src.get_client("route53")
        self.domains_src = self._src.get_client("route53domains")
        self.route53_dst = self._dst.get_client("route53")
        self.domains_dst = self._dst.get_client("route53domains")

    def dest_account_id(self) -> str:
        return self._dst.get_account_id()


def normalize_ns(name: str) -> str:
    return name.lower().rstrip(".")


def normalize_domain(domain: str) -> str:
    name = domain.strip().lower().rstrip(".")
    if not name or "/" in name or name.startswith(".") or ".." in name:
        raise click.ClickException(f"{domain!r} is not a valid domain name")
    return name


def zone_id_of(zone: Dict[str, Any]) -> str:
    """Strip the ``/hostedzone/`` prefix from a hosted zone Id."""
    return str(zone["Id"]).split("/")[-1]


def is_apex_ns_or_soa(record: Dict[str, Any], apex: str) -> bool:
    """True for the zone's own NS and SOA records, which Route 53 manages."""
    return record["Name"] == apex and record["Type"] in ("NS", "SOA")


def find_zone(route53: Any, domain: str) -> Optional[Dict[str, Any]]:
    """Return the public hosted zone whose name exactly matches ``domain``."""
    name = normalize_domain(domain) + "."
    zones = route53.list_hosted_zones_by_name(DNSName=name, MaxItems="5")["HostedZones"]
    for zone in zones:
        if zone["Name"] == name and not zone["Config"].get("PrivateZone"):
            return dict(zone)
    return None


def list_records(route53: Any, zone_id: str) -> List[Dict[str, Any]]:
    paginator = route53.get_paginator("list_resource_record_sets")
    records: List[Dict[str, Any]] = []
    for page in paginator.paginate(HostedZoneId=zone_id):
        records.extend(page["ResourceRecordSets"])
    return records


def registered_domains(domains: Any) -> Set[str]:
    paginator = domains.get_paginator("list_domains")
    return {d["DomainName"] for page in paginator.paginate() for d in page["Domains"]}


def wait_for_operation(domains: Any, operation_id: str, label: str) -> None:
    """Poll a Route 53 Domains operation until it succeeds, fails, or times out."""
    for _ in range(MAX_POLLS):
        detail = domains.get_operation_detail(OperationId=operation_id)
        status = detail["Status"]
        console.print(f"  [dim]{label}: {status}[/dim]")
        if status == "SUCCESSFUL":
            return
        if status in ("ERROR", "FAILED"):
            message = detail.get("Message", "no message from Route 53")
            raise click.ClickException(f"{label} failed: {message}")
        time.sleep(POLL_SECONDS)
    raise click.ClickException(
        f"{label}: operation {operation_id} still {status} after "
        f"{MAX_POLLS * POLL_SECONDS // 60} minutes; check it in the Route 53 console"
    )


def next_step(registered_in: str, zone_in_src: bool, zone_in_dst: bool) -> str:
    """Return the next migration command for a domain given where things live."""
    if registered_in == "source":
        return "transfer"
    if not zone_in_dst:
        return "migrate-zone"
    if zone_in_src:
        return "cleanup"
    return "done"


def zone_location(zone_in_src: bool, zone_in_dst: bool) -> str:
    return {
        (True, True): "both",
        (True, False): "source",
        (False, True): "dest",
        (False, False): "none",
    }[(zone_in_src, zone_in_dst)]


def rewrite_record(
    record: Dict[str, Any], src_zone_id: str, dst_zone_id: str
) -> Dict[str, Any]:
    """Repoint an alias whose target is the source zone itself at the new zone."""
    record = copy.deepcopy(record)
    alias = record.get("AliasTarget")
    if alias and alias["HostedZoneId"] == src_zone_id:
        alias["HostedZoneId"] = dst_zone_id
    return record


def records_to_copy(
    records: List[Dict[str, Any]], src_zone_id: str, dst_zone_id: str
) -> List[Dict[str, Any]]:
    """Everything except the apex NS and SOA, with self-referencing aliases rewritten.

    Raises if a record references a health check, traffic policy, or CIDR
    collection, since those belong to the source account and cannot be copied.
    """
    apex = next((r["Name"] for r in records if r["Type"] == "SOA"), None)
    if apex is None:
        raise click.ClickException("source zone has no SOA record; refusing to copy")
    bound = [
        f"{r['Name']} {r['Type']} ({', '.join(f for f in SOURCE_BOUND_FIELDS if f in r)})"
        for r in records
        if any(f in r for f in SOURCE_BOUND_FIELDS)
    ]
    if bound:
        raise click.ClickException(
            "these records reference resources in the source account and must be "
            "recreated by hand in the destination first: " + "; ".join(bound)
        )
    return [
        rewrite_record(r, src_zone_id, dst_zone_id)
        for r in records
        if not is_apex_ns_or_soa(r, apex)
    ]


def change_weight(action: str, record: Dict[str, Any]) -> Tuple[int, int]:
    """Cost of one change against the Route 53 ChangeBatch limits.

    Route 53 caps a batch at 1000 ResourceRecord elements and 32000 characters
    of record values, and an UPSERT counts twice against both.
    """
    values = [rr["Value"] for rr in record.get("ResourceRecords", [])]
    factor = 2 if action == "UPSERT" else 1
    return max(len(values), 1) * factor, sum(len(v) for v in values) * factor


def change_in_batches(
    route53: Any, zone_id: str, action: str, records: List[Dict[str, Any]]
) -> None:
    """Apply one action to every record, splitting to stay under the batch limits."""
    changes: List[Dict[str, Any]] = []
    elements = chars = 0
    for record in records:
        weight_elements, weight_chars = change_weight(action, record)
        over_limit = (
            elements + weight_elements > MAX_BATCH_ELEMENTS
            or chars + weight_chars > MAX_BATCH_CHARS
        )
        if changes and over_limit:
            route53.change_resource_record_sets(
                HostedZoneId=zone_id, ChangeBatch={"Changes": changes}
            )
            changes, elements, chars = [], 0, 0
        changes.append({"Action": action, "ResourceRecordSet": record})
        elements += weight_elements
        chars += weight_chars
    if changes:
        route53.change_resource_record_sets(
            HostedZoneId=zone_id, ChangeBatch={"Changes": changes}
        )


def default_backup_root(config: Config) -> Path:
    return config.get_data_dir() / "route53"


def write_private(path: Path, text: str) -> None:
    """Write a file readable only by the owner, replacing any existing one."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    if hasattr(os, "fchmod"):
        os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(text)


def record_key(record: Dict[str, Any]) -> Tuple[str, str, Optional[str]]:
    return (record["Name"].lower(), record["Type"], record.get("SetIdentifier"))


ROUTING_FIELDS = (
    "TTL",
    "Weight",
    "Region",
    "Failover",
    "GeoLocation",
    "GeoProximityLocation",
    "MultiValueAnswer",
)


def record_payload(record: Dict[str, Any]) -> Tuple[Any, ...]:
    values = sorted(rr["Value"] for rr in record.get("ResourceRecords", []))
    routing = tuple(json.dumps(record.get(f), sort_keys=True) for f in ROUTING_FIELDS)
    return (tuple(values), record.get("AliasTarget")) + routing


def missing_in_destination(
    src_records: List[Dict[str, Any]],
    dst_records: List[Dict[str, Any]],
    src_zone_id: str,
    dst_zone_id: str,
) -> List[str]:
    """Source records the destination does not serve identically."""
    dst_by_key = {record_key(r): record_payload(r) for r in dst_records}
    missing = []
    for record in src_records:
        expected = record_payload(rewrite_record(record, src_zone_id, dst_zone_id))
        if dst_by_key.get(record_key(record)) != expected:
            missing.append(f"{record['Name']} {record['Type']}")
    return missing


def save_transfer_state(root: Path, domain: str, state: Dict[str, Any]) -> Path:
    """Persist the transfer password so a failed accept can be retried."""
    path = root / "transfers" / f"{domain}.json"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    write_private(path, json.dumps(state, indent=2))
    return path


def accept_retry_hint(domain: str, dest_profile: str, state_path: Path) -> str:
    return (
        f"the one-time password is kept in {state_path} (valid 3 days); retry with:\n"
        f"  aws route53domains accept-domain-transfer-from-another-aws-account "
        f"--region {DOMAINS_REGION} --profile {dest_profile} "
        f"--domain-name {domain} --password <password>"
    )


def profile_options(func: Callable[..., None]) -> Callable[..., None]:
    func = click.option(
        "--dest-profile",
        required=True,
        help="AWS profile of the account domains move into",
    )(func)
    func = click.option(
        "--source-profile",
        required=True,
        help="AWS profile of the account domains move out of",
    )(func)
    return func


@click.group(name="route53")
def route53_group() -> None:
    """Migrate Route 53 registered domains and hosted zones between accounts.

    Run in order: backup, transfer, migrate-zone, then cleanup a couple of days
    later. migration-status shows where each domain stands and what to run next.
    """
    pass


@route53_group.command(name="migration-status")
@profile_options
@click.pass_context
def migration_status(
    ctx: click.Context, source_profile: str, dest_profile: str
) -> None:
    """Show each domain's registered account, zone location, and next step."""
    config: Config = ctx.obj["config"]
    accounts = Accounts(source_profile, dest_profile)

    in_src = registered_domains(accounts.domains_src)
    in_dst = registered_domains(accounts.domains_dst)
    rows = []
    for domain in sorted(in_src | in_dst):
        registered_in = "source" if domain in in_src else "dest"
        zone_in_src = find_zone(accounts.route53_src, domain) is not None
        zone_in_dst = find_zone(accounts.route53_dst, domain) is not None
        rows.append(
            {
                "Domain": domain,
                "Registered": registered_in,
                "Zone": zone_location(zone_in_src, zone_in_dst),
                "Next": next_step(registered_in, zone_in_src, zone_in_dst),
            }
        )

    print_output(
        rows, output_format=config.aws_output_format, title="Route 53 Migration Status"
    )
    if config.aws_output_format == "table":
        console.print(
            f"[dim]{len(in_src)} registered in {source_profile}, "
            f"{len(in_dst)} in {dest_profile}[/dim]"
        )


@route53_group.command(name="backup")
@click.option(
    "--source-profile",
    required=True,
    help="AWS profile of the account to snapshot",
)
@click.option(
    "--output-dir",
    help="Directory to write the snapshot into (default: <data-dir>/route53/<timestamp>)",
)
@click.pass_context
def backup(ctx: click.Context, source_profile: str, output_dir: Optional[str]) -> None:
    """Snapshot every hosted zone and registered domain in the source account."""
    config: Config = ctx.obj["config"]
    auth = AWSAuth(
        profile_name=source_profile, region_name=DOMAINS_REGION, max_retries=MAX_RETRIES
    )
    route53, domains = auth.get_client("route53"), auth.get_client("route53domains")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(output_dir) if output_dir else default_backup_root(config) / stamp
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(out, 0o700)

    zones = [
        z
        for page in route53.get_paginator("list_hosted_zones").paginate()
        for z in page["HostedZones"]
    ]
    for zone in zones:
        zone_id = zone_id_of(zone)
        detail = route53.get_hosted_zone(Id=zone_id)
        payload = {
            "zone": zone,
            "delegation_set": detail.get("DelegationSet"),
            "vpcs": detail.get("VPCs", []),
            "records": list_records(route53, zone_id),
        }
        path = out / f"{zone['Name'].rstrip('.')}.{zone_id}.json"
        write_private(path, json.dumps(payload, indent=2, default=str))
        console.print(
            f"  {zone['Name']:<30} {len(payload['records']):>4} records -> {path.name}"
        )

    details = []
    for name in sorted(registered_domains(domains)):
        detail = domains.get_domain_detail(DomainName=name)
        detail.pop("ResponseMetadata", None)
        details.append(detail)
    write_private(
        out / "registered-domains.json", json.dumps(details, indent=2, default=str)
    )
    console.print(
        f"[green]Backed up {len(zones)} zones and {len(details)} registered domains "
        f"to {out}[/green]"
    )


@route53_group.command(name="transfer")
@profile_options
@click.option(
    "--state-dir",
    help="Where to keep the one-time transfer password until accept succeeds "
    "(default: <data-dir>/route53)",
)
@click.argument("domains", nargs=-1, required=True)
@click.pass_context
def transfer(
    ctx: click.Context,
    source_profile: str,
    dest_profile: str,
    state_dir: Optional[str],
    domains: Tuple[str, ...],
) -> None:
    """Move domain registration from the source account to the destination."""
    config: Config = ctx.obj["config"]
    accounts = Accounts(source_profile, dest_profile)
    root = Path(state_dir) if state_dir else default_backup_root(config)
    dest_account = accounts.dest_account_id()

    for domain in map(normalize_domain, domains):
        console.print(f"[blue]== {domain}: transfer to {dest_account}[/blue]")
        offer = accounts.domains_src.transfer_domain_to_another_aws_account(
            DomainName=domain, AccountId=dest_account
        )
        state_path = save_transfer_state(
            root,
            domain,
            {
                "operation_id": offer["OperationId"],
                "password": offer["Password"],
                "dest_account": dest_account,
            },
        )
        console.print(f"  transfer offered; password saved to {state_path}")
        try:
            accept = (
                accounts.domains_dst.accept_domain_transfer_from_another_aws_account(
                    DomainName=domain, Password=offer["Password"]
                )
            )
            wait_for_operation(accounts.domains_dst, accept["OperationId"], "accept")
        except Exception as exc:
            hint = accept_retry_hint(domain, dest_profile, state_path)
            raise click.ClickException(f"{domain}: accept failed: {exc}\n{hint}")
        state_path.unlink()
        console.print(f"[green]  {domain} is now registered in {dest_account}[/green]")


def _ensure_destination_zone(
    accounts: Accounts, domain: str, src_zone: Dict[str, Any]
) -> str:
    dst_zone = find_zone(accounts.route53_dst, domain)
    if dst_zone:
        console.print(f"  destination zone already exists: {zone_id_of(dst_zone)}")
        return zone_id_of(dst_zone)
    created = accounts.route53_dst.create_hosted_zone(
        Name=src_zone["Name"],
        CallerReference=f"migrate-{domain}-{int(time.time())}",
        HostedZoneConfig={"Comment": f"migrated from {zone_id_of(src_zone)}"},
    )["HostedZone"]
    console.print(f"  created destination zone {zone_id_of(created)}")
    return zone_id_of(created)


def _migrate_one_zone(accounts: Accounts, domain: str) -> None:
    src_zone = find_zone(accounts.route53_src, domain)
    if not src_zone:
        raise click.ClickException(
            f"no public hosted zone for {domain} in {accounts.source_profile}"
        )
    if domain not in registered_domains(accounts.domains_dst):
        raise click.ClickException(
            f"{domain} is not registered in {accounts.dest_profile}; "
            f"run `transfer {domain}` first"
        )
    src_zone_id = zone_id_of(src_zone)
    records = list_records(accounts.route53_src, src_zone_id)
    dst_zone_id = _ensure_destination_zone(accounts, domain, src_zone)

    to_copy = records_to_copy(records, src_zone_id, dst_zone_id)
    change_in_batches(accounts.route53_dst, dst_zone_id, "UPSERT", to_copy)
    dst_count = len(list_records(accounts.route53_dst, dst_zone_id))
    console.print(
        f"  copied {len(to_copy)} records; destination has {dst_count}, source had {len(records)}"
    )
    if dst_count != len(records):
        raise click.ClickException(
            f"{domain}: record count mismatch; inspect before repointing name servers"
        )

    delegation = accounts.route53_dst.get_hosted_zone(Id=dst_zone_id)["DelegationSet"]
    name_servers = delegation["NameServers"]
    op = accounts.domains_dst.update_domain_nameservers(
        DomainName=domain, Nameservers=[{"Name": ns} for ns in name_servers]
    )
    wait_for_operation(accounts.domains_dst, op["OperationId"], "update name servers")
    console.print(f"[green]  registrar now points at: {' '.join(name_servers)}[/green]")
    console.print(f"  verify: dig +short NS {domain} @{name_servers[0]}")


@route53_group.command(name="migrate-zone")
@profile_options
@click.argument("domains", nargs=-1, required=True)
def migrate_zone(
    source_profile: str, dest_profile: str, domains: Tuple[str, ...]
) -> None:
    """Recreate the hosted zone in the destination and repoint the registrar.

    Requires the domain to already be registered in the destination account.
    Copies every record except the apex NS and SOA, checks the counts match,
    then updates the registrar's name servers. Both zones answer identically
    while the change propagates.
    """
    accounts = Accounts(source_profile, dest_profile)
    for domain in map(normalize_domain, domains):
        console.print(f"[blue]== {domain}: migrate hosted zone[/blue]")
        _migrate_one_zone(accounts, domain)


def _check_cleanup_safe(
    accounts: Accounts, domain: str
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Return the source zone and its deletable records if cleanup is safe.

    Safe means: a public zone exists in both accounts, the domain is registered
    in the destination, the registrar points at the destination zone's name
    servers, and the destination serves every non-apex source record.
    """
    src_zone = find_zone(accounts.route53_src, domain)
    dst_zone = find_zone(accounts.route53_dst, domain)
    if not src_zone or not dst_zone:
        raise click.ClickException(
            f"{domain}: need a zone in both accounts before deleting the source one"
        )
    if zone_id_of(src_zone) == zone_id_of(dst_zone):
        raise click.ClickException(
            f"{domain}: source and destination are the same zone; not deleting"
        )
    if domain not in registered_domains(accounts.domains_dst):
        raise click.ClickException(
            f"{domain} is not registered in {accounts.dest_profile}; "
            f"run `transfer {domain}` first"
        )
    detail = accounts.domains_dst.get_domain_detail(DomainName=domain)
    registrar_ns = {normalize_ns(ns["Name"]) for ns in detail["Nameservers"]}
    src_zone_id, dst_zone_id = zone_id_of(src_zone), zone_id_of(dst_zone)
    delegation = accounts.route53_dst.get_hosted_zone(Id=dst_zone_id)["DelegationSet"]
    if registrar_ns != {normalize_ns(ns) for ns in delegation["NameServers"]}:
        raise click.ClickException(
            f"{domain}: registrar name servers do not match the destination zone; not deleting"
        )
    leftovers = [
        r
        for r in list_records(accounts.route53_src, src_zone_id)
        if not is_apex_ns_or_soa(r, src_zone["Name"])
    ]
    missing = missing_in_destination(
        leftovers,
        list_records(accounts.route53_dst, dst_zone_id),
        src_zone_id,
        dst_zone_id,
    )
    if missing:
        raise click.ClickException(
            f"{domain}: destination zone is missing or differs on "
            f"{len(missing)} source records; re-run `migrate-zone {domain}` first: "
            + ", ".join(missing)
        )
    return src_zone, leftovers


@route53_group.command(name="cleanup")
@profile_options
@click.option("--confirm", is_flag=True, help="Skip the confirmation prompt")
@click.argument("domains", nargs=-1, required=True)
def cleanup(
    source_profile: str, dest_profile: str, confirm: bool, domains: Tuple[str, ...]
) -> None:
    """Delete the old source zone once the registrar points at the destination.

    Refuses unless a zone exists in both accounts and the registrar already
    points at the destination zone's name servers. Wait at least two days
    after migrate-zone so TLD name server caches have expired.
    """
    accounts = Accounts(source_profile, dest_profile)
    for domain in map(normalize_domain, domains):
        src_zone, leftovers = _check_cleanup_safe(accounts, domain)
        src_zone_id = zone_id_of(src_zone)
        if not confirm:
            console.print(
                f"[red]This will permanently delete zone {src_zone_id} ({domain}) "
                f"and its {len(leftovers)} records from {source_profile}.[/red]"
            )
            if not click.confirm(f"Delete the source zone for {domain}?"):
                console.print("[yellow]Skipped[/yellow]")
                continue
        if leftovers:
            change_in_batches(accounts.route53_src, src_zone_id, "DELETE", leftovers)
        accounts.route53_src.delete_hosted_zone(Id=src_zone_id)
        console.print(
            f"[green]== {domain}: deleted source zone {src_zone_id} "
            f"({len(leftovers)} records)[/green]"
        )
