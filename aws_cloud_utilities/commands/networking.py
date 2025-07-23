"""AWS networking and IP management commands."""

import logging
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import click
from rich.console import Console

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import print_output, save_to_file, get_timestamp, ensure_directory
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="networking")
def networking_group():
    """AWS networking and IP management commands."""
    pass


@networking_group.command(name="ip-ranges")
@click.option("--output-file", help="Output file for AWS IP ranges (supports .json, .yaml, .csv)")
@click.option("--filter-service", help="Filter IP ranges by AWS service (e.g., EC2, S3, CLOUDFRONT)")
@click.option("--filter-region", help="Filter IP ranges by AWS region (e.g., us-east-1, eu-west-1)")
@click.option("--ipv6", is_flag=True, help="Include IPv6 ranges in addition to IPv4")
@click.option("--show-summary", is_flag=True, help="Show summary statistics of IP ranges")
@click.pass_context
def ip_ranges(
    ctx: click.Context,
    output_file: Optional[str],
    filter_service: Optional[str],
    filter_region: Optional[str],
    ipv6: bool,
    show_summary: bool,
) -> None:
    """Download and analyze AWS IP ranges."""
    config: Config = ctx.obj["config"]

    try:
        console.print("[blue]Downloading AWS IP ranges...[/blue]")

        # Download IP ranges from AWS
        ip_data = _download_aws_ip_ranges()

        if not ip_data:
            console.print("[red]Failed to download AWS IP ranges[/red]")
            raise click.Abort()

        console.print(f"[green]✓[/green] Downloaded IP ranges (sync token: {ip_data.get('syncToken', 'unknown')})")

        # Filter data if requested
        filtered_data = _filter_ip_ranges(ip_data, filter_service, filter_region, ipv6)

        # Display summary if requested
        if show_summary:
            _display_ip_ranges_summary(config, filtered_data, filter_service, filter_region)

        # Format for display
        display_data = _format_ip_ranges_for_display(filtered_data, ipv6)

        if display_data:
            print_output(display_data, output_format=config.aws_output_format, title="AWS IP Ranges")
        else:
            console.print("[yellow]No IP ranges match the specified filters[/yellow]")

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            # Save the full filtered data (not just display format)
            save_to_file(filtered_data, output_path, file_format)
            console.print(f"[green]IP ranges saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error downloading AWS IP ranges:[/red] {e}")
        raise click.Abort()


@networking_group.command(name="ip-summary")
@click.option("--service", help="Show summary for specific service only")
@click.option("--region", help="Show summary for specific region only")
@click.pass_context
def ip_summary(ctx: click.Context, service: Optional[str], region: Optional[str]) -> None:
    """Show summary statistics of AWS IP ranges."""
    config: Config = ctx.obj["config"]

    try:
        console.print("[blue]Downloading AWS IP ranges for analysis...[/blue]")

        # Download IP ranges from AWS
        ip_data = _download_aws_ip_ranges()

        if not ip_data:
            console.print("[red]Failed to download AWS IP ranges[/red]")
            raise click.Abort()

        # Generate comprehensive summary
        summary_data = _generate_ip_ranges_summary(ip_data, service, region)

        # Display summary
        print_output(summary_data["overview"], output_format=config.aws_output_format, title="AWS IP Ranges Overview")

        if summary_data["by_service"]:
            print_output(
                summary_data["by_service"], output_format=config.aws_output_format, title="IP Ranges by Service"
            )

        if summary_data["by_region"]:
            print_output(summary_data["by_region"], output_format=config.aws_output_format, title="IP Ranges by Region")

    except Exception as e:
        console.print(f"[red]Error analyzing AWS IP ranges:[/red] {e}")
        raise click.Abort()


def _download_aws_ip_ranges() -> Optional[Dict[str, Any]]:
    """Download AWS IP ranges from the official endpoint."""
    try:
        response = requests.get("https://ip-ranges.amazonaws.com/ip-ranges.json", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error downloading AWS IP ranges: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing AWS IP ranges JSON: {e}")
        return None


def _filter_ip_ranges(
    ip_data: Dict[str, Any], filter_service: Optional[str], filter_region: Optional[str], include_ipv6: bool
) -> Dict[str, Any]:
    """Filter IP ranges based on service, region, and IP version."""
    filtered_data = {
        "syncToken": ip_data.get("syncToken"),
        "createDate": ip_data.get("createDate"),
        "prefixes": [],
        "ipv6_prefixes": [],
    }

    # Filter IPv4 prefixes
    for prefix in ip_data.get("prefixes", []):
        include = True

        if filter_service and prefix.get("service", "").upper() != filter_service.upper():
            include = False

        if filter_region and prefix.get("region") != filter_region:
            include = False

        if include:
            filtered_data["prefixes"].append(prefix)

    # Filter IPv6 prefixes if requested
    if include_ipv6:
        for prefix in ip_data.get("ipv6_prefixes", []):
            include = True

            if filter_service and prefix.get("service", "").upper() != filter_service.upper():
                include = False

            if filter_region and prefix.get("region") != filter_region:
                include = False

            if include:
                filtered_data["ipv6_prefixes"].append(prefix)

    return filtered_data


def _format_ip_ranges_for_display(ip_data: Dict[str, Any], include_ipv6: bool) -> List[Dict[str, str]]:
    """Format IP ranges data for display."""
    display_data = []

    # Add IPv4 ranges
    for prefix in ip_data.get("prefixes", []):
        display_data.append(
            {
                "IP Prefix": prefix.get("ip_prefix", ""),
                "Region": prefix.get("region", ""),
                "Service": prefix.get("service", ""),
                "Network Border Group": prefix.get("network_border_group", ""),
                "IP Version": "IPv4",
            }
        )

    # Add IPv6 ranges if requested
    if include_ipv6:
        for prefix in ip_data.get("ipv6_prefixes", []):
            display_data.append(
                {
                    "IP Prefix": prefix.get("ipv6_prefix", ""),
                    "Region": prefix.get("region", ""),
                    "Service": prefix.get("service", ""),
                    "Network Border Group": prefix.get("network_border_group", ""),
                    "IP Version": "IPv6",
                }
            )

    return display_data


def _display_ip_ranges_summary(
    config: Config, ip_data: Dict[str, Any], filter_service: Optional[str], filter_region: Optional[str]
) -> None:
    """Display summary of IP ranges."""
    ipv4_count = len(ip_data.get("prefixes", []))
    ipv6_count = len(ip_data.get("ipv6_prefixes", []))

    summary = {
        "Sync Token": ip_data.get("syncToken", "unknown"),
        "Create Date": ip_data.get("createDate", "unknown"),
        "IPv4 Prefixes": ipv4_count,
        "IPv6 Prefixes": ipv6_count,
        "Total Prefixes": ipv4_count + ipv6_count,
        "Service Filter": filter_service or "None",
        "Region Filter": filter_region or "None",
    }

    print_output(summary, output_format=config.aws_output_format, title="AWS IP Ranges Summary")


def _generate_ip_ranges_summary(
    ip_data: Dict[str, Any], service_filter: Optional[str], region_filter: Optional[str]
) -> Dict[str, Any]:
    """Generate comprehensive summary of IP ranges."""

    # Count by service
    service_counts = {}
    region_counts = {}

    # Process IPv4 prefixes
    for prefix in ip_data.get("prefixes", []):
        service = prefix.get("service", "UNKNOWN")
        region = prefix.get("region", "UNKNOWN")

        if not service_filter or service.upper() == service_filter.upper():
            if not region_filter or region == region_filter:
                service_counts[service] = service_counts.get(service, 0) + 1
                region_counts[region] = region_counts.get(region, 0) + 1

    # Process IPv6 prefixes
    for prefix in ip_data.get("ipv6_prefixes", []):
        service = prefix.get("service", "UNKNOWN")
        region = prefix.get("region", "UNKNOWN")

        if not service_filter or service.upper() == service_filter.upper():
            if not region_filter or region == region_filter:
                service_counts[service] = service_counts.get(service, 0) + 1
                region_counts[region] = region_counts.get(region, 0) + 1

    # Format for display
    overview = {
        "Sync Token": ip_data.get("syncToken", "unknown"),
        "Create Date": ip_data.get("createDate", "unknown"),
        "Total IPv4 Prefixes": len(ip_data.get("prefixes", [])),
        "Total IPv6 Prefixes": len(ip_data.get("ipv6_prefixes", [])),
        "Unique Services": len(service_counts),
        "Unique Regions": len(region_counts),
    }

    by_service = [
        {"Service": service, "IP Ranges": count}
        for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    by_region = [
        {"Region": region, "IP Ranges": count}
        for region, count in sorted(region_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    return {"overview": overview, "by_service": by_service, "by_region": by_region}
