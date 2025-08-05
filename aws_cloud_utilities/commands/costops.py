"""AWS Cost optimization and analysis commands."""

import logging
import json
import os
import csv
import statistics
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import (
    print_output,
    save_to_file,
    get_timestamp,
    get_detailed_timestamp,
    ensure_directory,
    parallel_execute,
)
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()

# AWS Pricing API constants
PRICING_API_BASE = "https://pricing.us-east-1.amazonaws.com"
HTTP_TIMEOUT = 30

# EBS volume types for optimization analysis
EBS_VOLUME_TYPES = {
    "gp2": {"name": "General Purpose SSD (gp2)", "optimizable": True, "target": "gp3"},
    "gp3": {"name": "General Purpose SSD (gp3)", "optimizable": False, "target": None},
    "io1": {"name": "Provisioned IOPS SSD (io1)", "optimizable": True, "target": "io2"},
    "io2": {"name": "Provisioned IOPS SSD (io2)", "optimizable": False, "target": None},
    "st1": {"name": "Throughput Optimized HDD", "optimizable": False, "target": None},
    "sc1": {"name": "Cold HDD", "optimizable": False, "target": None},
    "standard": {"name": "Magnetic", "optimizable": True, "target": "gp3"},
}


@click.group(name="costops")
def costops_group():
    """AWS cost optimization and analysis commands."""
    pass


@costops_group.command(name="pricing")
@click.option("--service", help="Specific AWS service to get pricing for (e.g., AmazonEC2, AmazonS3)")
@click.option("--output-dir", help="Output directory for pricing data (default: ./aws_pricing_<timestamp>)")
@click.option("--list-services", is_flag=True, help="List all available AWS services for pricing")
@click.option(
    "--format",
    type=click.Choice(["json", "summary"]),
    default="summary",
    help="Output format: json (raw data) or summary (processed)",
)
@click.pass_context
def pricing(
    ctx: click.Context, service: Optional[str], output_dir: Optional[str], list_services: bool, format: str
) -> None:
    """Get AWS pricing information for services."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        if list_services:
            console.print("[blue]Listing available AWS services for pricing[/blue]")
            services_data = _get_available_pricing_services()

            print_output(
                services_data,
                output_format=config.aws_output_format,
                title=f"Available AWS Services for Pricing ({len(services_data)} found)",
            )
            return

        # Generate output directory if not provided
        if not output_dir:
            timestamp = get_timestamp()
            output_dir = f"aws_pricing_{timestamp}"

        output_path = Path(output_dir)
        ensure_directory(output_path)

        if service:
            console.print(f"[blue]Getting pricing data for service: {service}[/blue]")
            console.print(f"[dim]Output directory: {output_path}[/dim]")
            console.print(f"[dim]Format: {format}[/dim]")

            # Get pricing for specific service
            pricing_results = _get_service_pricing(service, output_path, format, config.workers)

        else:
            console.print("[blue]Getting pricing data for all AWS services[/blue]")
            console.print(f"[dim]Output directory: {output_path}[/dim]")
            console.print(f"[dim]Format: {format}[/dim]")
            console.print(
                "[yellow]⚠️  This will download pricing data for all services (may take several minutes)[/yellow]"
            )

            if not click.confirm("Continue with downloading all service pricing data?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

            # Get pricing for all services
            pricing_results = _get_all_services_pricing(output_path, format, config.workers)

        # Display results
        _display_pricing_results(config, pricing_results)

        console.print(f"\n[green]✅ Pricing data collection completed![/green]")
        console.print(f"[dim]Data saved to: {output_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting pricing data:[/red] {e}")
        raise click.Abort()


@costops_group.command(name="cost-analysis")
@click.option("--months", type=int, default=3, help="Number of months to analyze (default: 3)")
@click.option("--service", help="Specific AWS service to analyze (e.g., Amazon Elastic Compute Cloud - Compute)")
@click.option(
    "--group-by",
    type=click.Choice(["service", "usage_type", "region", "account"]),
    default="service",
    help="Group costs by dimension (default: service)",
)
@click.option("--output-file", help="Output file for cost analysis (supports .json, .yaml, .csv)")
@click.pass_context
def cost_analysis(
    ctx: click.Context, months: int, service: Optional[str], group_by: str, output_file: Optional[str]
) -> None:
    """Analyze AWS costs using Cost Explorer."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        console.print(f"[blue]Analyzing AWS costs for the last {months} months[/blue]")
        if service:
            console.print(f"[dim]Service filter: {service}[/dim]")
        console.print(f"[dim]Grouped by: {group_by}[/dim]")

        # Get Cost Explorer client
        ce_client = aws_auth.get_client("ce", region_name="us-east-1")

        # Execute cost analysis
        cost_results = _analyze_costs(ce_client, months, service, group_by)

        # Display results
        _display_cost_analysis(config, cost_results, months, service, group_by)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(cost_results, output_path, file_format)
            console.print(f"[green]Cost analysis saved to:[/green] {output_path}")

        console.print(f"\n[green]✅ Cost analysis completed![/green]")

    except Exception as e:
        console.print(f"[red]Error analyzing costs:[/red] {e}")
        raise click.Abort()


@costops_group.command(name="ebs-optimization")
@click.option("--region", help="AWS region to analyze (default: current region)")
@click.option("--all-regions", is_flag=True, help="Analyze EBS volumes across all regions")
@click.option(
    "--volume-type",
    type=click.Choice(list(EBS_VOLUME_TYPES.keys())),
    help="Filter by specific volume type (default: analyze all types)",
)
@click.option(
    "--show-recommendations", is_flag=True, default=True, help="Show optimization recommendations (default: enabled)"
)
@click.option("--include-cost-estimates", is_flag=True, help="Include cost savings estimates (requires pricing data)")
@click.option("--output-file", help="Output file for EBS analysis (supports .json, .yaml, .csv)")
@click.pass_context
def ebs_optimization(
    ctx: click.Context,
    region: Optional[str],
    all_regions: bool,
    volume_type: Optional[str],
    show_recommendations: bool,
    include_cost_estimates: bool,
    output_file: Optional[str],
) -> None:
    """Analyze EBS volumes for cost optimization opportunities."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Determine regions to analyze
        if all_regions:
            target_regions = aws_auth.get_available_regions("ec2")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]

        console.print(f"[blue]Analyzing EBS volumes for optimization across {len(target_regions)} regions[/blue]")
        if volume_type:
            console.print(f"[dim]Volume type filter: {volume_type} ({EBS_VOLUME_TYPES[volume_type]['name']})[/dim]")
        if include_cost_estimates:
            console.print("[dim]Including cost savings estimates[/dim]")

        # Execute EBS analysis
        ebs_results = _analyze_ebs_volumes(
            aws_auth, target_regions, volume_type, show_recommendations, include_cost_estimates, config.workers
        )

        # Display results
        _display_ebs_analysis(config, ebs_results, show_recommendations)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(ebs_results, output_path, file_format)
            console.print(f"[green]EBS analysis saved to:[/green] {output_path}")

        console.print(f"\n[green]✅ EBS optimization analysis completed![/green]")

    except Exception as e:
        console.print(f"[red]Error analyzing EBS volumes:[/red] {e}")
        raise click.Abort()


@costops_group.command(name="usage-metrics")
@click.argument("service_name")
@click.option("--months", type=int, default=3, help="Number of months to analyze (default: 3)")
@click.option(
    "--metric-type",
    type=click.Choice(["cost", "usage", "both"]),
    default="both",
    help="Type of metrics to retrieve (default: both)",
)
@click.option(
    "--group-by",
    type=click.Choice(["usage_type", "region", "instance_type", "operation"]),
    default="usage_type",
    help="Group metrics by dimension (default: usage_type)",
)
@click.option("--output-file", help="Output file for usage metrics (supports .json, .yaml, .csv)")
@click.pass_context
def usage_metrics(
    ctx: click.Context, service_name: str, months: int, metric_type: str, group_by: str, output_file: Optional[str]
) -> None:
    """Get detailed usage metrics for a specific AWS service."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        console.print(f"[blue]Getting usage metrics for service: {service_name}[/blue]")
        console.print(f"[dim]Time period: Last {months} months[/dim]")
        console.print(f"[dim]Metric type: {metric_type}[/dim]")
        console.print(f"[dim]Grouped by: {group_by}[/dim]")

        # Get Cost Explorer client
        ce_client = aws_auth.get_client("ce", region_name="us-east-1")

        # Execute usage metrics analysis
        metrics_results = _get_usage_metrics(ce_client, service_name, months, metric_type, group_by)

        # Display results
        _display_usage_metrics(config, metrics_results, service_name, months, metric_type)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(metrics_results, output_path, file_format)
            console.print(f"[green]Usage metrics saved to:[/green] {output_path}")

        console.print(f"\n[green]✅ Usage metrics analysis completed![/green]")

    except Exception as e:
        console.print(f"[red]Error getting usage metrics:[/red] {e}")
        raise click.Abort()


@costops_group.command(name="spot-pricing")
@click.option("--region", help="Specific AWS region to collect spot pricing for")
@click.option("--all-regions", is_flag=True, help="Collect spot pricing data from all regions")
@click.option("--time-range", type=int, default=24, help="Time range in hours for spot pricing data (default: 24)")
@click.option("--instance-types", help="Comma-separated list of instance types to include (e.g., m5.large,c5.xlarge)")
@click.option("--product-description", default="Linux/UNIX", help="Product description filter (default: Linux/UNIX)")
@click.option("--output-dir", help="Output directory for spot pricing data (default: ./spot_pricing_<timestamp>)")
@click.option("--output-file", help="Output file for consolidated spot pricing analysis (supports .json, .yaml, .csv)")
@click.pass_context
def spot_pricing(
    ctx: click.Context,
    region: Optional[str],
    all_regions: bool,
    time_range: int,
    instance_types: Optional[str],
    product_description: str,
    output_dir: Optional[str],
    output_file: Optional[str],
) -> None:
    """Collect and analyze EC2 spot pricing data across regions."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Determine regions to collect from
        if all_regions:
            target_regions = aws_auth.get_available_regions("ec2")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]

        # Parse instance types filter
        instance_types_filter = None
        if instance_types:
            instance_types_filter = [it.strip() for it in instance_types.split(",")]

        # Generate output directory if not provided
        if not output_dir:
            timestamp = get_timestamp()
            output_dir = f"spot_pricing_{timestamp}"

        output_path = Path(output_dir)
        ensure_directory(output_path)

        console.print(f"[blue]Collecting spot pricing data from {len(target_regions)} regions[/blue]")
        console.print(f"[dim]Time range: Last {time_range} hours[/dim]")
        console.print(f"[dim]Product description: {product_description}[/dim]")
        console.print(f"[dim]Output directory: {output_path}[/dim]")
        if instance_types_filter:
            console.print(f"[dim]Instance types filter: {', '.join(instance_types_filter)}[/dim]")

        # Collect spot pricing data
        spot_results = _collect_spot_pricing(
            aws_auth, target_regions, time_range, instance_types_filter, product_description, output_path, config.workers
        )

        # Display results summary
        _display_spot_pricing_results(config, spot_results)

        # Generate analysis if requested
        if output_file:
            console.print(f"[blue]Generating spot pricing analysis...[/blue]")
            analysis_results = _analyze_spot_pricing_data(output_path)
            
            # Save analysis to file
            analysis_output_path = Path(output_file)
            file_format = analysis_output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = analysis_output_path.stem
            new_filename = f"{stem}_{timestamp}{analysis_output_path.suffix}"
            analysis_output_path = analysis_output_path.parent / new_filename

            save_to_file(analysis_results, analysis_output_path, file_format)
            console.print(f"[green]Spot pricing analysis saved to:[/green] {analysis_output_path}")

        console.print(f"\n[green]✅ Spot pricing data collection completed![/green]")
        console.print(f"[dim]Data saved to: {output_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error collecting spot pricing data:[/red] {e}")
        raise click.Abort()


@costops_group.command(name="spot-analysis")
@click.argument("data_directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--top-n", type=int, default=10, help="Number of top cheapest instances to show (default: 10)")
@click.option("--estimate-period", type=int, default=30, help="Period in days for cost estimation (default: 30)")
@click.option("--instance-type-filter", help="Filter results by instance type pattern (e.g., 'm5', 'c5.large')")
@click.option("--region-filter", help="Filter results by region")
@click.option("--output-file", help="Output file for analysis results (supports .json, .yaml, .csv)")
@click.pass_context
def spot_analysis(
    ctx: click.Context,
    data_directory: str,
    top_n: int,
    estimate_period: int,
    instance_type_filter: Optional[str],
    region_filter: Optional[str],
    output_file: Optional[str],
) -> None:
    """Analyze previously collected spot pricing data to find cheapest options."""
    config: Config = ctx.obj["config"]

    try:
        data_path = Path(data_directory)
        
        console.print(f"[blue]Analyzing spot pricing data from: {data_path}[/blue]")
        console.print(f"[dim]Showing top {top_n} cheapest instances[/dim]")
        console.print(f"[dim]Cost estimation period: {estimate_period} days[/dim]")
        
        if instance_type_filter:
            console.print(f"[dim]Instance type filter: {instance_type_filter}[/dim]")
        if region_filter:
            console.print(f"[dim]Region filter: {region_filter}[/dim]")

        # Analyze the spot pricing data
        analysis_results = _analyze_spot_pricing_data(
            data_path, top_n, estimate_period, instance_type_filter, region_filter
        )

        # Display analysis results
        _display_spot_analysis_results(config, analysis_results, top_n, estimate_period)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(analysis_results, output_path, file_format)
            console.print(f"[green]Spot pricing analysis saved to:[/green] {output_path}")

        console.print(f"\n[green]✅ Spot pricing analysis completed![/green]")

    except Exception as e:
        console.print(f"[red]Error analyzing spot pricing data:[/red] {e}")
        raise click.Abort()


def _get_available_pricing_services() -> List[Dict[str, Any]]:
    """Get list of available AWS services for pricing."""

    try:
        # Get the main pricing index
        response = requests.get(f"{PRICING_API_BASE}/offers/v1.0/aws/index.json", timeout=HTTP_TIMEOUT)
        response.raise_for_status()

        pricing_index = response.json()
        services_data = []

        for service_code, service_info in pricing_index.get("offers", {}).items():
            services_data.append(
                {
                    "Service Code": service_code,
                    "Service Name": service_info.get("offerName", ""),
                    "Current Version": (
                        service_info.get("currentVersionUrl", "").split("/")[-1]
                        if service_info.get("currentVersionUrl")
                        else ""
                    ),
                    "Version Index URL": service_info.get("versionIndexUrl", ""),
                }
            )

        # Sort by service name
        services_data.sort(key=lambda x: x["Service Name"])

        return services_data

    except Exception as e:
        logger.error(f"Error getting available pricing services: {e}")
        raise


def _get_service_pricing(service_code: str, output_path: Path, format: str, max_workers: int) -> Dict[str, Any]:
    """Get pricing data for a specific service."""

    result = {
        "service_code": service_code,
        "format": format,
        "output_path": str(output_path),
        "files_created": 0,
        "data_size": 0,
        "errors": [],
    }

    try:
        console.print(f"[dim]Fetching pricing index for {service_code}...[/dim]")

        # Get service pricing index
        index_url = f"{PRICING_API_BASE}/offers/v1.0/aws/index.json"
        index_response = requests.get(index_url, timeout=HTTP_TIMEOUT)
        index_response.raise_for_status()

        pricing_index = index_response.json()

        if service_code not in pricing_index.get("offers", {}):
            raise ValueError(f"Service '{service_code}' not found in pricing index")

        service_info = pricing_index["offers"][service_code]

        # Get version index
        version_index_url = f"{PRICING_API_BASE}{service_info['versionIndexUrl']}"
        version_response = requests.get(version_index_url, timeout=HTTP_TIMEOUT)
        version_response.raise_for_status()

        version_data = version_response.json()

        # Save version index
        version_file = output_path / f"pricing_{service_code}_versions.json"
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=2)

        result["files_created"] += 1
        result["data_size"] += version_file.stat().st_size

        # Get current pricing data
        current_version = list(version_data["versions"].keys())[0]
        pricing_url = f"{PRICING_API_BASE}{version_data['versions'][current_version]['offerVersionUrl']}"

        console.print(f"[dim]Downloading current pricing data for {service_code}...[/dim]")
        pricing_response = requests.get(pricing_url, timeout=HTTP_TIMEOUT)
        pricing_response.raise_for_status()

        pricing_data = pricing_response.json()

        if format == "json":
            # Save raw JSON data
            pricing_file = output_path / f"pricing_{service_code}_{current_version}.json"
            with open(pricing_file, "w", encoding="utf-8") as f:
                json.dump(pricing_data, f, indent=2)
        else:
            # Process and save summary
            summary_data = _process_pricing_summary(service_code, pricing_data)
            pricing_file = output_path / f"pricing_{service_code}_summary.json"
            with open(pricing_file, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2)

        result["files_created"] += 1
        result["data_size"] += pricing_file.stat().st_size

    except Exception as e:
        error_msg = f"Error getting pricing for {service_code}: {str(e)}"
        result["errors"].append(error_msg)
        logger.error(error_msg)

    return result


def _get_all_services_pricing(output_path: Path, format: str, max_workers: int) -> Dict[str, Any]:
    """Get pricing data for all AWS services."""

    result = {
        "format": format,
        "output_path": str(output_path),
        "total_services": 0,
        "services_processed": 0,
        "files_created": 0,
        "total_data_size": 0,
        "errors": [],
    }

    try:
        # Get list of available services
        services_data = _get_available_pricing_services()
        result["total_services"] = len(services_data)

        def process_service(service_info: Dict[str, Any]) -> Dict[str, Any]:
            """Process pricing for a single service."""
            service_code = service_info["Service Code"]
            return _get_service_pricing(service_code, output_path, format, 1)

        # Process services in parallel
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            task = progress.add_task("Processing services...", total=len(services_data))

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_service, service) for service in services_data]

                for future in futures:
                    service_result = future.result()

                    if not service_result["errors"]:
                        result["services_processed"] += 1

                    result["files_created"] += service_result["files_created"]
                    result["total_data_size"] += service_result["data_size"]
                    result["errors"].extend(service_result["errors"])

                    progress.advance(task)

    except Exception as e:
        result["errors"].append(f"Error processing all services pricing: {str(e)}")

    return result


def _process_pricing_summary(service_code: str, pricing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process raw pricing data into a summary format."""

    summary = {
        "service_code": service_code,
        "service_name": pricing_data.get("formatVersion", ""),
        "publication_date": pricing_data.get("publicationDate", ""),
        "version": pricing_data.get("version", ""),
        "total_products": len(pricing_data.get("products", {})),
        "total_terms": len(pricing_data.get("terms", {})),
        "regions": set(),
        "product_families": set(),
        "usage_types": set(),
    }

    # Analyze products
    for product_id, product in pricing_data.get("products", {}).items():
        attributes = product.get("attributes", {})

        if "location" in attributes:
            summary["regions"].add(attributes["location"])

        if "productFamily" in attributes:
            summary["product_families"].add(attributes["productFamily"])

        if "usagetype" in attributes:
            summary["usage_types"].add(attributes["usagetype"])

    # Convert sets to sorted lists
    summary["regions"] = sorted(list(summary["regions"]))
    summary["product_families"] = sorted(list(summary["product_families"]))
    summary["usage_types"] = sorted(list(summary["usage_types"]))


def _get_date_ranges(months: int) -> List[Tuple[str, str]]:
    """Get date ranges for the last N months."""

    today = datetime.today()
    date_ranges = []

    for i in range(months):
        # Calculate the first and last day of each month
        first_day = (today - relativedelta(months=i + 1)).replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)
        date_ranges.append((first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")))

    return date_ranges[::-1]  # Reverse to have chronological order


def _analyze_costs(ce_client, months: int, service_filter: Optional[str], group_by: str) -> Dict[str, Any]:
    """Analyze costs using Cost Explorer."""

    result = {
        "months": months,
        "service_filter": service_filter,
        "group_by": group_by,
        "date_ranges": [],
        "total_cost": 0.0,
        "cost_by_period": [],
        "cost_breakdown": {},
        "errors": [],
    }

    try:
        date_ranges = _get_date_ranges(months)
        result["date_ranges"] = date_ranges

        # Map group_by to Cost Explorer dimension
        dimension_map = {
            "service": "SERVICE",
            "usage_type": "USAGE_TYPE",
            "region": "REGION",
            "account": "LINKED_ACCOUNT",
        }

        dimension = dimension_map.get(group_by, "SERVICE")

        for start_date, end_date in date_ranges:
            try:
                # Build request parameters
                request_params = {
                    "TimePeriod": {"Start": start_date, "End": end_date},
                    "Granularity": "MONTHLY",
                    "Metrics": ["UnblendedCost"],
                    "GroupBy": [{"Type": "DIMENSION", "Key": dimension}],
                }

                # Add service filter if specified
                if service_filter:
                    request_params["Filter"] = {"Dimensions": {"Key": "SERVICE", "Values": [service_filter]}}

                response = ce_client.get_cost_and_usage(**request_params)

                period_data = {"start_date": start_date, "end_date": end_date, "total_cost": 0.0, "breakdown": {}}

                if response.get("ResultsByTime"):
                    results = response["ResultsByTime"][0]["Groups"]

                    for group in results:
                        key = group["Keys"][0]
                        cost = float(group["Metrics"]["UnblendedCost"]["Amount"])

                        period_data["breakdown"][key] = cost
                        period_data["total_cost"] += cost

                        # Add to overall breakdown
                        if key not in result["cost_breakdown"]:
                            result["cost_breakdown"][key] = 0.0
                        result["cost_breakdown"][key] += cost

                result["cost_by_period"].append(period_data)
                result["total_cost"] += period_data["total_cost"]

            except Exception as e:
                error_msg = f"Error getting costs for period {start_date} to {end_date}: {str(e)}"
                result["errors"].append(error_msg)
                logger.debug(error_msg)

    except Exception as e:
        result["errors"].append(f"Error analyzing costs: {str(e)}")

    return result


def _get_usage_metrics(ce_client, service_name: str, months: int, metric_type: str, group_by: str) -> Dict[str, Any]:
    """Get usage metrics for a specific service."""

    result = {
        "service_name": service_name,
        "months": months,
        "metric_type": metric_type,
        "group_by": group_by,
        "total_cost": 0.0,
        "cost_breakdown": {},
        "usage_breakdown": {},
        "errors": [],
    }

    try:
        date_ranges = _get_date_ranges(months)

        # Map group_by to Cost Explorer dimension
        dimension_map = {
            "usage_type": "USAGE_TYPE",
            "region": "REGION",
            "instance_type": "INSTANCE_TYPE",
            "operation": "OPERATION",
        }

        dimension = dimension_map.get(group_by, "USAGE_TYPE")

        for start_date, end_date in date_ranges:
            try:
                # Get cost data if requested
                if metric_type in ["cost", "both"]:
                    cost_response = ce_client.get_cost_and_usage(
                        TimePeriod={"Start": start_date, "End": end_date},
                        Granularity="MONTHLY",
                        Metrics=["UnblendedCost"],
                        Filter={"Dimensions": {"Key": "SERVICE", "Values": [service_name]}},
                        GroupBy=[{"Type": "DIMENSION", "Key": dimension}],
                    )

                    if cost_response.get("ResultsByTime"):
                        for group in cost_response["ResultsByTime"][0]["Groups"]:
                            key = group["Keys"][0]
                            cost = float(group["Metrics"]["UnblendedCost"]["Amount"])

                            if key not in result["cost_breakdown"]:
                                result["cost_breakdown"][key] = 0.0
                            result["cost_breakdown"][key] += cost
                            result["total_cost"] += cost

                # Get usage data if requested
                if metric_type in ["usage", "both"]:
                    usage_response = ce_client.get_cost_and_usage(
                        TimePeriod={"Start": start_date, "End": end_date},
                        Granularity="MONTHLY",
                        Metrics=["UsageQuantity"],
                        Filter={"Dimensions": {"Key": "SERVICE", "Values": [service_name]}},
                        GroupBy=[{"Type": "DIMENSION", "Key": dimension}],
                    )

                    if usage_response.get("ResultsByTime"):
                        for group in usage_response["ResultsByTime"][0]["Groups"]:
                            key = group["Keys"][0]
                            quantity = float(group["Metrics"]["UsageQuantity"]["Amount"])

                            if key not in result["usage_breakdown"]:
                                result["usage_breakdown"][key] = 0.0
                            result["usage_breakdown"][key] += quantity

            except Exception as e:
                error_msg = f"Error getting metrics for period {start_date} to {end_date}: {str(e)}"
                result["errors"].append(error_msg)
                logger.debug(error_msg)

    except Exception as e:
        result["errors"].append(f"Error getting usage metrics: {str(e)}")

    return result


def _analyze_ebs_volumes(
    aws_auth: AWSAuth,
    regions: List[str],
    volume_type_filter: Optional[str],
    show_recommendations: bool,
    include_cost_estimates: bool,
    max_workers: int,
) -> Dict[str, Any]:
    """Analyze EBS volumes across regions for optimization opportunities."""

    result = {
        "regions_analyzed": len(regions),
        "volume_type_filter": volume_type_filter,
        "total_volumes": 0,
        "optimizable_volumes": 0,
        "potential_savings": 0.0,
        "volumes_by_type": {},
        "volumes_by_region": {},
        "optimization_opportunities": [],
        "errors": [],
    }

    def analyze_region(region: str) -> Tuple[str, Dict[str, Any]]:
        """Analyze EBS volumes in a single region."""
        region_result = {"region": region, "volumes": [], "volume_count": 0, "optimizable_count": 0, "errors": []}

        try:
            ec2_client = aws_auth.get_client("ec2", region_name=region)

            # Build filters
            filters = []
            if volume_type_filter:
                filters.append({"Name": "volume-type", "Values": [volume_type_filter]})

            # Get volumes
            paginator = ec2_client.get_paginator("describe_volumes")

            for page in paginator.paginate(Filters=filters):
                for volume in page.get("Volumes", []):
                    volume_info = _process_ebs_volume(ec2_client, volume, show_recommendations)
                    region_result["volumes"].append(volume_info)
                    region_result["volume_count"] += 1

                    if volume_info.get("optimizable", False):
                        region_result["optimizable_count"] += 1

        except Exception as e:
            error_msg = f"Error analyzing region {region}: {str(e)}"
            region_result["errors"].append(error_msg)
            logger.debug(error_msg)

        return region, region_result

    # Process regions in parallel
    region_results = parallel_execute(
        analyze_region, regions, max_workers=max_workers, show_progress=True, description="Analyzing EBS volumes"
    )

    # Compile results
    for region, region_data in region_results:
        result["volumes_by_region"][region] = region_data
        result["total_volumes"] += region_data["volume_count"]
        result["optimizable_volumes"] += region_data["optimizable_count"]
        result["errors"].extend(region_data["errors"])

        # Aggregate by volume type
        for volume in region_data["volumes"]:
            vol_type = volume["volume_type"]
            if vol_type not in result["volumes_by_type"]:
                result["volumes_by_type"][vol_type] = {"count": 0, "optimizable": 0, "total_size": 0}

            result["volumes_by_type"][vol_type]["count"] += 1
            result["volumes_by_type"][vol_type]["total_size"] += volume["size"]

            if volume.get("optimizable", False):
                result["volumes_by_type"][vol_type]["optimizable"] += 1

                # Add to optimization opportunities
                result["optimization_opportunities"].append(
                    {
                        "volume_id": volume["volume_id"],
                        "region": region,
                        "current_type": vol_type,
                        "recommended_type": volume.get("recommended_type"),
                        "size": volume["size"],
                        "instance_id": volume.get("instance_id"),
                        "tags": volume.get("tags", {}),
                        "estimated_savings": volume.get("estimated_savings", 0.0),
                    }
                )

    return result


def _process_ebs_volume(ec2_client, volume: Dict[str, Any], show_recommendations: bool) -> Dict[str, Any]:
    """Process a single EBS volume for optimization analysis."""

    volume_info = {
        "volume_id": volume["VolumeId"],
        "volume_type": volume["VolumeType"],
        "size": volume["Size"],
        "state": volume["State"],
        "created": volume["CreateTime"].strftime("%Y-%m-%d %H:%M:%S") if volume.get("CreateTime") else "",
        "optimizable": False,
        "recommended_type": None,
        "tags": {},
        "instance_id": None,
        "instance_tags": {},
    }

    # Process tags
    if "Tags" in volume:
        for tag in volume["Tags"]:
            volume_info["tags"][tag["Key"]] = tag["Value"]

    # Process attachments
    if "Attachments" in volume and volume["Attachments"]:
        attachment = volume["Attachments"][0]
        instance_id = attachment["InstanceId"]
        volume_info["instance_id"] = instance_id

        # Get instance tags if possible
        try:
            instance_response = ec2_client.describe_instances(InstanceIds=[instance_id])
            if instance_response["Reservations"]:
                instance = instance_response["Reservations"][0]["Instances"][0]
                if "Tags" in instance:
                    for tag in instance["Tags"]:
                        volume_info["instance_tags"][tag["Key"]] = tag["Value"]
        except Exception as e:
            logger.debug(f"Error getting instance tags for {instance_id}: {e}")

    # Check optimization opportunities
    if show_recommendations:
        vol_type = volume["VolumeType"]
        if vol_type in EBS_VOLUME_TYPES and EBS_VOLUME_TYPES[vol_type]["optimizable"]:
            volume_info["optimizable"] = True
            volume_info["recommended_type"] = EBS_VOLUME_TYPES[vol_type]["target"]


def _display_pricing_results(config: Config, results: Dict[str, Any]) -> None:
    """Display pricing data collection results."""

    if "total_services" in results:
        # All services results
        summary_display = {
            "Format": results["format"],
            "Output Path": results["output_path"],
            "Total Services": results["total_services"],
            "Services Processed": results["services_processed"],
            "Files Created": results["files_created"],
            "Total Data Size": _human_readable_size(results["total_data_size"]),
            "Errors": len(results["errors"]),
        }
        title = "AWS Pricing Data Collection Results (All Services)"
    else:
        # Single service results
        summary_display = {
            "Service Code": results["service_code"],
            "Format": results["format"],
            "Output Path": results["output_path"],
            "Files Created": results["files_created"],
            "Data Size": _human_readable_size(results["data_size"]),
            "Errors": len(results["errors"]),
        }
        title = "AWS Pricing Data Collection Results"

    print_output(summary_display, output_format=config.aws_output_format, title=title)

    # Show errors if any
    if results["errors"]:
        console.print("\n[red]Errors encountered:[/red]")
        for error in results["errors"][:5]:  # Show first 5 errors
            console.print(f"  • {error}")
        if len(results["errors"]) > 5:
            console.print(f"  ... and {len(results['errors']) - 5} more errors")


def _display_cost_analysis(
    config: Config, results: Dict[str, Any], months: int, service_filter: Optional[str], group_by: str
) -> None:
    """Display cost analysis results."""

    # Summary
    summary_display = {
        "Analysis Period": f"Last {months} months",
        "Service Filter": service_filter or "All services",
        "Grouped By": group_by.replace("_", " ").title(),
        "Total Cost": f"${results['total_cost']:.2f}",
        "Number of Periods": len(results["cost_by_period"]),
        "Breakdown Items": len(results["cost_breakdown"]),
        "Errors": len(results["errors"]),
    }

    print_output(summary_display, output_format=config.aws_output_format, title="Cost Analysis Summary")

    # Cost breakdown (top 10)
    if results["cost_breakdown"]:
        breakdown_data = []
        sorted_breakdown = sorted(results["cost_breakdown"].items(), key=lambda x: x[1], reverse=True)

        for item, cost in sorted_breakdown[:10]:
            breakdown_data.append(
                {
                    group_by.replace("_", " ").title(): item,
                    "Total Cost": f"${cost:.2f}",
                    "Percentage": (
                        f"{(cost / results['total_cost'] * 100):.1f}%" if results["total_cost"] > 0 else "0.0%"
                    ),
                }
            )

        print_output(
            breakdown_data,
            output_format=config.aws_output_format,
            title=f"Top 10 Cost Breakdown by {group_by.replace('_', ' ').title()}",
        )

    # Show errors if any
    if results["errors"]:
        console.print("\n[red]Errors encountered:[/red]")
        for error in results["errors"][:3]:
            console.print(f"  • {error}")
        if len(results["errors"]) > 3:
            console.print(f"  ... and {len(results['errors']) - 3} more errors")


def _display_usage_metrics(
    config: Config, results: Dict[str, Any], service_name: str, months: int, metric_type: str
) -> None:
    """Display usage metrics results."""

    # Summary
    summary_display = {
        "Service Name": service_name,
        "Analysis Period": f"Last {months} months",
        "Metric Type": metric_type.title(),
        "Total Cost": f"${results['total_cost']:.2f}" if results["total_cost"] > 0 else "N/A",
        "Cost Breakdown Items": len(results["cost_breakdown"]),
        "Usage Breakdown Items": len(results["usage_breakdown"]),
        "Errors": len(results["errors"]),
    }

    print_output(summary_display, output_format=config.aws_output_format, title="Usage Metrics Summary")

    # Cost breakdown (top 10)
    if results["cost_breakdown"] and metric_type in ["cost", "both"]:
        cost_data = []
        sorted_costs = sorted(results["cost_breakdown"].items(), key=lambda x: x[1], reverse=True)

        for usage_type, cost in sorted_costs[:10]:
            cost_data.append({"Usage Type": usage_type, "Total Cost": f"${cost:.2f}"})

        print_output(cost_data, output_format=config.aws_output_format, title="Top 10 Cost Breakdown by Usage Type")

    # Usage breakdown (top 10)
    if results["usage_breakdown"] and metric_type in ["usage", "both"]:
        usage_data = []
        sorted_usage = sorted(results["usage_breakdown"].items(), key=lambda x: x[1], reverse=True)

        for usage_type, quantity in sorted_usage[:10]:
            usage_data.append({"Usage Type": usage_type, "Total Quantity": f"{quantity:,.0f}"})

        print_output(usage_data, output_format=config.aws_output_format, title="Top 10 Usage Breakdown by Usage Type")

    # Show errors if any
    if results["errors"]:
        console.print("\n[red]Errors encountered:[/red]")
        for error in results["errors"][:3]:
            console.print(f"  • {error}")
        if len(results["errors"]) > 3:
            console.print(f"  ... and {len(results['errors']) - 3} more errors")


def _display_ebs_analysis(config: Config, results: Dict[str, Any], show_recommendations: bool) -> None:
    """Display EBS optimization analysis results."""

    # Summary
    summary_display = {
        "Regions Analyzed": results["regions_analyzed"],
        "Total Volumes": results["total_volumes"],
        "Optimizable Volumes": results["optimizable_volumes"],
        "Optimization Rate": f"{(results['optimizable_volumes'] / max(results['total_volumes'], 1) * 100):.1f}%",
        "Volume Type Filter": results["volume_type_filter"] or "All types",
        "Errors": len(results["errors"]),
    }

    print_output(summary_display, output_format=config.aws_output_format, title="EBS Optimization Analysis Summary")

    # Volume breakdown by type
    if results["volumes_by_type"]:
        type_data = []
        for vol_type, data in results["volumes_by_type"].items():
            type_info = EBS_VOLUME_TYPES.get(vol_type, {"name": vol_type})
            type_data.append(
                {
                    "Volume Type": f"{vol_type} ({type_info['name']})",
                    "Total Count": data["count"],
                    "Optimizable": data["optimizable"],
                    "Total Size (GB)": f"{data['total_size']:,}",
                    "Optimization Rate": f"{(data['optimizable'] / max(data['count'], 1) * 100):.1f}%",
                }
            )

        # Sort by count descending
        type_data.sort(key=lambda x: int(x["Total Count"]), reverse=True)

        print_output(type_data, output_format=config.aws_output_format, title="Volume Breakdown by Type")

    # Optimization opportunities (top 20)
    if show_recommendations and results["optimization_opportunities"]:
        opp_data = []
        for opp in results["optimization_opportunities"][:20]:
            opp_data.append(
                {
                    "Volume ID": opp["volume_id"],
                    "Region": opp["region"],
                    "Current Type": opp["current_type"],
                    "Recommended": opp["recommended_type"],
                    "Size (GB)": opp["size"],
                    "Instance ID": opp.get("instance_id", "Unattached"),
                    "Name Tag": opp.get("tags", {}).get("Name", ""),
                }
            )

        print_output(
            opp_data,
            output_format=config.aws_output_format,
            title=f"Top 20 Optimization Opportunities (of {len(results['optimization_opportunities'])} total)",
        )

    # Show errors if any
    if results["errors"]:
        console.print("\n[red]Errors encountered:[/red]")
        for error in results["errors"][:5]:
            console.print(f"  • {error}")
        if len(results["errors"]) > 5:
            console.print(f"  ... and {len(results['errors']) - 5} more errors")


def _human_readable_size(num_bytes: int) -> str:
    """Convert bytes to human readable format."""
    if not isinstance(num_bytes, (int, float)):
        return str(num_bytes)

    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"


def _collect_spot_pricing(
    aws_auth: AWSAuth,
    regions: List[str],
    time_range: int,
    instance_types_filter: Optional[List[str]],
    product_description: str,
    output_path: Path,
    max_workers: int,
) -> Dict[str, Any]:
    """Collect spot pricing data from multiple regions."""
    
    result = {
        "regions_processed": 0,
        "total_records": 0,
        "files_created": 0,
        "time_range_hours": time_range,
        "product_description": product_description,
        "instance_types_filter": instance_types_filter,
        "regions": {},
        "errors": [],
    }

    def collect_region_pricing(region: str) -> Tuple[str, Dict[str, Any]]:
        """Collect spot pricing for a single region."""
        region_result = {"region": region, "records": 0, "file_path": None, "errors": []}

        try:
            ec2_client = aws_auth.get_client("ec2", region_name=region)

            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_range)

            # Build request parameters
            request_params = {
                "StartTime": start_time,
                "EndTime": end_time,
                "ProductDescriptions": [product_description],
            }

            # Add instance types filter if specified
            if instance_types_filter:
                request_params["InstanceTypes"] = instance_types_filter

            # Create output file for this region
            output_filename = output_path / f"spot_prices_{region}.csv"
            
            with open(output_filename, mode="w", newline="", encoding="utf-8") as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(["Region", "InstanceType", "AvailabilityZone", "SpotPrice", "Timestamp"])

                # Paginate through results
                paginator = ec2_client.get_paginator("describe_spot_price_history")
                
                for page in paginator.paginate(**request_params):
                    for item in page.get("SpotPriceHistory", []):
                        csv_writer.writerow([
                            region,
                            item["InstanceType"],
                            item["AvailabilityZone"],
                            item["SpotPrice"],
                            item["Timestamp"].isoformat(),
                        ])
                        region_result["records"] += 1

            region_result["file_path"] = str(output_filename)

        except Exception as e:
            error_msg = f"Error collecting spot pricing for region {region}: {str(e)}"
            region_result["errors"].append(error_msg)
            logger.debug(error_msg)

        return region, region_result

    # Process regions in parallel
    region_results = parallel_execute(
        collect_region_pricing,
        regions,
        max_workers=max_workers,
        show_progress=True,
        description="Collecting spot pricing data",
    )

    # Compile results
    for region, region_data in region_results:
        result["regions"][region] = region_data
        result["total_records"] += region_data["records"]
        result["errors"].extend(region_data["errors"])
        
        if region_data["file_path"]:
            result["files_created"] += 1
        
        if not region_data["errors"]:
            result["regions_processed"] += 1

    return result


def _analyze_spot_pricing_data(
    data_path: Path,
    top_n: int = 10,
    estimate_period: int = 30,
    instance_type_filter: Optional[str] = None,
    region_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze spot pricing data to find cheapest options."""
    
    result = {
        "data_path": str(data_path),
        "files_processed": 0,
        "total_records": 0,
        "filters": {
            "instance_type": instance_type_filter,
            "region": region_filter,
        },
        "top_n": top_n,
        "estimate_period_days": estimate_period,
        "cheapest_instances": [],
        "price_statistics": {},
        "errors": [],
    }

    try:
        # Find all CSV files in the data directory
        csv_files = list(data_path.glob("spot_prices_*.csv"))
        
        if not csv_files:
            result["errors"].append("No spot pricing CSV files found in the specified directory")
            return result

        # Structure: {(region, instance_type, az): [list of spot prices]}
        price_map = {}

        for csv_file in csv_files:
            try:
                result["files_processed"] += 1
                
                with open(csv_file, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        region = row["Region"]
                        instance_type = row["InstanceType"]
                        az = row["AvailabilityZone"]
                        spot_price = float(row["SpotPrice"])
                        
                        # Apply filters
                        if region_filter and region_filter not in region:
                            continue
                        if instance_type_filter and instance_type_filter not in instance_type:
                            continue
                        
                        key = (region, instance_type, az)
                        if key not in price_map:
                            price_map[key] = []
                        price_map[key].append(spot_price)
                        result["total_records"] += 1

            except Exception as e:
                error_msg = f"Error processing file {csv_file}: {str(e)}"
                result["errors"].append(error_msg)
                logger.debug(error_msg)

        # Compute statistics for each key
        avg_prices = {}
        for key, prices in price_map.items():
            if prices:  # Ensure we have data
                stats = {
                    "average": statistics.mean(prices),
                    "median": statistics.median(prices),
                    "min": min(prices),
                    "max": max(prices),
                    "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0.0,
                    "sample_count": len(prices),
                }
                avg_prices[key] = stats["average"]
                result["price_statistics"][f"{key[0]}_{key[1]}_{key[2]}"] = stats

        # Sort by average spot price (ascending) and get top N cheapest
        sorted_prices = sorted(avg_prices.items(), key=lambda x: x[1])

        # Calculate cost estimates
        hours_in_period = estimate_period * 24
        
        for (region, instance_type, az), avg_price in sorted_prices[:top_n]:
            estimated_cost = avg_price * hours_in_period
            stats = result["price_statistics"].get(f"{region}_{instance_type}_{az}", {})
            
            result["cheapest_instances"].append({
                "rank": len(result["cheapest_instances"]) + 1,
                "region": region,
                "instance_type": instance_type,
                "availability_zone": az,
                "average_price_per_hour": avg_price,
                "estimated_cost_period": estimated_cost,
                "min_price": stats.get("min", 0.0),
                "max_price": stats.get("max", 0.0),
                "median_price": stats.get("median", 0.0),
                "price_std_dev": stats.get("std_dev", 0.0),
                "sample_count": stats.get("sample_count", 0),
            })

    except Exception as e:
        result["errors"].append(f"Error analyzing spot pricing data: {str(e)}")

    return result


def _display_spot_pricing_results(config: Config, results: Dict[str, Any]) -> None:
    """Display spot pricing data collection results."""
    
    # Summary
    summary_display = {
        "Regions Processed": f"{results['regions_processed']}/{len(results['regions'])}",
        "Total Records Collected": f"{results['total_records']:,}",
        "Files Created": results["files_created"],
        "Time Range": f"{results['time_range_hours']} hours",
        "Product Description": results["product_description"],
        "Instance Types Filter": ", ".join(results["instance_types_filter"]) if results["instance_types_filter"] else "All types",
        "Errors": len(results["errors"]),
    }

    print_output(summary_display, output_format=config.aws_output_format, title="Spot Pricing Data Collection Summary")

    # Per-region breakdown
    if results["regions"]:
        region_data = []
        for region, region_info in results["regions"].items():
            region_data.append({
                "Region": region,
                "Records Collected": f"{region_info['records']:,}",
                "Status": "✓ Success" if not region_info["errors"] else "✗ Error",
                "File Created": "Yes" if region_info["file_path"] else "No",
            })

        # Sort by records collected (descending)
        region_data.sort(key=lambda x: int(x["Records Collected"].replace(",", "")), reverse=True)

        print_output(region_data, output_format=config.aws_output_format, title="Per-Region Collection Results")

    # Show errors if any
    if results["errors"]:
        console.print("\n[red]Errors encountered:[/red]")
        for error in results["errors"][:5]:
            console.print(f"  • {error}")
        if len(results["errors"]) > 5:
            console.print(f"  ... and {len(results['errors']) - 5} more errors")


def _display_spot_analysis_results(config: Config, results: Dict[str, Any], top_n: int, estimate_period: int) -> None:
    """Display spot pricing analysis results."""
    
    # Summary
    summary_display = {
        "Data Directory": results["data_path"],
        "Files Processed": results["files_processed"],
        "Total Records Analyzed": f"{results['total_records']:,}",
        "Instance Type Filter": results["filters"]["instance_type"] or "None",
        "Region Filter": results["filters"]["region"] or "None",
        "Cost Estimation Period": f"{estimate_period} days ({estimate_period * 24} hours)",
        "Top Instances Shown": top_n,
        "Errors": len(results["errors"]),
    }

    print_output(summary_display, output_format=config.aws_output_format, title="Spot Pricing Analysis Summary")

    # Top cheapest instances
    if results["cheapest_instances"]:
        cheapest_data = []
        for instance in results["cheapest_instances"]:
            cheapest_data.append({
                "Rank": instance["rank"],
                "Region": instance["region"],
                "Instance Type": instance["instance_type"],
                "Availability Zone": instance["availability_zone"],
                "Avg Price/Hour": f"${instance['average_price_per_hour']:.6f}",
                f"{estimate_period}d Estimate": f"${instance['estimated_cost_period']:.2f}",
                "Min Price": f"${instance['min_price']:.6f}",
                "Max Price": f"${instance['max_price']:.6f}",
                "Samples": instance["sample_count"],
            })

        print_output(
            cheapest_data,
            output_format=config.aws_output_format,
            title=f"Top {top_n} Cheapest Spot Instance Options",
        )

    # Show errors if any
    if results["errors"]:
        console.print("\n[red]Errors encountered:[/red]")
        for error in results["errors"][:5]:
            console.print(f"  • {error}")
        if len(results["errors"]) > 5:
            console.print(f"  ... and {len(results['errors']) - 5} more errors")
