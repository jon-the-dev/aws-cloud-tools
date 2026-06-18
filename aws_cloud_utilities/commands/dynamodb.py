"""DynamoDB cost and capacity analysis commands."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console

from aws_cloud_utilities.core.auth import AWSAuth
from aws_cloud_utilities.core.config import Config
from aws_cloud_utilities.core.utils import (
    format_bytes,
    get_timestamp,
    print_output,
    save_to_file,
)

logger = logging.getLogger(__name__)
console = Console()

# Provisioned cost formula: (RCU + WCU) * $0.0072/hour * 24h * 30d (us-west-2 pricing)
_COST_PER_RCU_WCU_HOUR = 0.0072
_HOURS_PER_MONTH = 24 * 30


def _compute_provisioned_cost(rcu: int, wcu: int) -> float:
    """Compute estimated monthly cost for a provisioned-throughput table.

    Args:
        rcu: Read capacity units
        wcu: Write capacity units

    Returns:
        Estimated monthly cost in USD
    """
    return (rcu + wcu) * _COST_PER_RCU_WCU_HOUR * _HOURS_PER_MONTH


def _describe_table(
    client: Any, table_name: str, region: str
) -> Optional[Dict[str, Any]]:
    """Describe a single DynamoDB table and return a normalised record.

    Args:
        client: Boto3 DynamoDB client
        table_name: Table name
        region: AWS region the table lives in

    Returns:
        Dictionary with table metrics, or None on error
    """
    try:
        resp = client.describe_table(TableName=table_name)
        tbl = resp["Table"]

        billing_summary = tbl.get("BillingModeSummary", {})
        billing_mode = billing_summary.get("BillingMode", "PROVISIONED")

        throughput = tbl.get("ProvisionedThroughput", {})
        rcu = int(throughput.get("ReadCapacityUnits", 0))
        wcu = int(throughput.get("WriteCapacityUnits", 0))

        if billing_mode == "PAY_PER_REQUEST":
            estimated_cost: Optional[float] = None
        else:
            estimated_cost = _compute_provisioned_cost(rcu, wcu)

        item_count = int(tbl.get("ItemCount", 0))
        size_bytes = int(tbl.get("TableSizeBytes", 0))
        created = tbl.get("CreationDateTime")

        return {
            "name": table_name,
            "region": region,
            "billing_mode": billing_mode,
            "rcu": rcu,
            "wcu": wcu,
            "item_count": item_count,
            "size_bytes": size_bytes,
            "size_human": format_bytes(size_bytes),
            "estimated_monthly_cost": estimated_cost,
            "created": str(created) if created else "unknown",
        }
    except Exception as exc:
        logger.warning("Failed to describe table %s in %s: %s", table_name, region, exc)
        return None


def _list_tables_in_region(client: Any) -> List[str]:
    """Paginate list_tables and return all table names.

    Args:
        client: Boto3 DynamoDB client

    Returns:
        List of table names
    """
    table_names: List[str] = []
    kwargs: Dict[str, Any] = {}
    while True:
        resp = client.list_tables(**kwargs)
        table_names.extend(resp.get("TableNames", []))
        last = resp.get("LastEvaluatedTableName")
        if not last:
            break
        kwargs["ExclusiveStartTableName"] = last
    return table_names


def _collect_region(
    aws_auth: AWSAuth, region: str, workers: int
) -> List[Dict[str, Any]]:
    """List and describe all DynamoDB tables in one region.

    Args:
        aws_auth: AWS authentication object
        region: AWS region name
        workers: Thread-pool size for parallel describe_table calls

    Returns:
        List of table records
    """
    try:
        client = aws_auth.get_client("dynamodb", region_name=region)
        table_names = _list_tables_in_region(client)
    except Exception as exc:
        logger.warning("Could not scan DynamoDB in %s: %s", region, exc)
        return []

    if not table_names:
        return []

    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_describe_table, client, name, region): name
            for name in table_names
        }
        for future in as_completed(futures):
            record = future.result()
            if record is not None:
                results.append(record)

    return results


def _build_summary(tables: List[Dict[str, Any]], top_n: int) -> Dict[str, Any]:
    """Build summary statistics from a list of table records.

    Args:
        tables: List of table records from _collect_region
        top_n: How many top-expensive tables to include

    Returns:
        Summary dictionary
    """
    provisioned = [t for t in tables if t["billing_mode"] != "PAY_PER_REQUEST"]
    on_demand = [t for t in tables if t["billing_mode"] == "PAY_PER_REQUEST"]

    total_rcu = sum(t["rcu"] for t in provisioned)
    total_wcu = sum(t["wcu"] for t in provisioned)
    total_cost = sum(t["estimated_monthly_cost"] or 0.0 for t in provisioned)

    sorted_by_cost = sorted(
        provisioned, key=lambda t: t["estimated_monthly_cost"] or 0.0, reverse=True
    )
    top_tables = sorted_by_cost[:top_n]

    empty_but_expensive = [
        t
        for t in provisioned
        if t["item_count"] == 0 and (t["estimated_monthly_cost"] or 0.0) > 1.0
    ]

    prefix_totals: Dict[str, float] = {}
    for t in provisioned:
        prefix = t["name"].split("-")[0]
        prefix_totals[prefix] = prefix_totals.get(prefix, 0.0) + (
            t["estimated_monthly_cost"] or 0.0
        )

    return {
        "total_tables": len(tables),
        "provisioned_tables": len(provisioned),
        "on_demand_tables": len(on_demand),
        "total_provisioned_rcu": total_rcu,
        "total_provisioned_wcu": total_wcu,
        "total_estimated_monthly_cost_usd": round(total_cost, 4),
        "top_expensive_tables": [
            {
                "name": t["name"],
                "region": t["region"],
                "rcu": t["rcu"],
                "wcu": t["wcu"],
                "estimated_monthly_cost_usd": round(
                    t["estimated_monthly_cost"] or 0.0, 4
                ),
            }
            for t in top_tables
        ],
        "empty_but_expensive_tables": [
            {
                "name": t["name"],
                "region": t["region"],
                "estimated_monthly_cost_usd": round(
                    t["estimated_monthly_cost"] or 0.0, 4
                ),
            }
            for t in empty_but_expensive
        ],
        "cost_by_project_prefix": {
            k: round(v, 4) for k, v in sorted(prefix_totals.items())
        },
    }


@click.group(name="dynamodb")
def dynamodb_group() -> None:
    """DynamoDB cost and capacity analysis commands."""
    pass


@dynamodb_group.command(name="cost-analysis")
@click.option(
    "--region", default=None, help="Single region to scan (default: all regions)."
)
@click.option(
    "--all-regions",
    "all_regions",
    is_flag=True,
    default=False,
    help="Scan all regions (default behavior).",
)
@click.option(
    "--top",
    default=10,
    show_default=True,
    type=int,
    help="Number of top-expensive tables to show.",
)
@click.option(
    "--output-file", default=None, help="Save results to file (.json/.yaml/.csv)."
)
@click.pass_context
def cost_analysis(
    ctx: click.Context,
    region: Optional[str],
    all_regions: bool,
    top: int,
    output_file: Optional[str],
) -> None:
    """Analyse DynamoDB tables for capacity usage and estimated monthly cost.

    Scans provisioned-throughput tables and computes estimated monthly cost
    using the formula: (RCU + WCU) * $0.0072 * 24 * 30 (us-west-2 pricing).
    PAY_PER_REQUEST tables are listed but excluded from cost totals.

    Examples:

        aws-cloud-utilities dynamodb cost-analysis

        aws-cloud-utilities dynamodb cost-analysis --region us-east-1

        aws-cloud-utilities dynamodb cost-analysis --top 5 --output-file report.json
    """
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    if region:
        regions = [region]
    else:
        regions = aws_auth.get_available_regions("dynamodb")

    console.print(f"[blue]Scanning DynamoDB in {len(regions)} region(s)...[/blue]")

    all_tables: List[Dict[str, Any]] = []
    for r in regions:
        tables = _collect_region(aws_auth, r, config.workers)
        all_tables.extend(tables)

    if not all_tables:
        console.print("[yellow]No DynamoDB tables found.[/yellow]")
        return

    # Sort by cost desc for display (on-demand tables have None cost, sort them last)
    display_tables = sorted(
        all_tables,
        key=lambda t: (
            t["estimated_monthly_cost"]
            if t["estimated_monthly_cost"] is not None
            else -1
        ),
        reverse=True,
    )

    table_rows = [
        {
            "Name": t["name"],
            "Region": t["region"],
            "Billing": t["billing_mode"],
            "RCU": t["rcu"],
            "WCU": t["wcu"],
            "Items": t["item_count"],
            "Size": t["size_human"],
            "Est. Monthly Cost": (
                f"${t['estimated_monthly_cost']:.2f}"
                if t["estimated_monthly_cost"] is not None
                else "On-Demand"
            ),
        }
        for t in display_tables
    ]

    print_output(
        table_rows, output_format=config.aws_output_format, title="DynamoDB Tables"
    )

    summary = _build_summary(all_tables, top)
    print_output(
        summary, output_format=config.aws_output_format, title="DynamoDB Cost Summary"
    )

    if output_file:
        output_path = Path(output_file)
        file_format = output_path.suffix.lstrip(".") or "json"
        timestamp = get_timestamp()
        stem = output_path.stem
        output_path = output_path.parent / f"{stem}_{timestamp}{output_path.suffix}"
        payload = {"tables": display_tables, "summary": summary}
        save_to_file(payload, output_path, file_format)
        console.print(f"[green]Results saved to:[/green] {output_path}")
