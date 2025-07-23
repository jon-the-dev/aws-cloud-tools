"""AWS CloudWatch Logs management and processing commands."""

import logging
import json
import gzip
import re
import os
import shutil
import tempfile
from datetime import datetime, timedelta
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

# Log type constants for aggregator
LOG_TYPE_CLOUDTRAIL = "cloudtrail"
LOG_TYPE_CLOUDFRONT = "cloudfront"
LOG_TYPE_ELB = "elb"
LOG_TYPE_ALB = "alb"
LOG_TYPE_ROUTE53 = "route53"

# Log file patterns for detection
LOG_PATTERNS = {
    LOG_TYPE_CLOUDTRAIL: r".*cloudtrail.*\.json(\.gz)?$",
    LOG_TYPE_CLOUDFRONT: r".*cloudfront.*\.(log|json)(\.gz)?$",
    LOG_TYPE_ELB: r".*elasticloadbalancing.*\.log(\.gz)?$",
    LOG_TYPE_ALB: r".*app/.*\.log(\.gz)?$|.*net/.*\.log(\.gz)?$",
    LOG_TYPE_ROUTE53: r".*route53.*\.log(\.gz)?$",
}


@click.group(name="logs")
def logs_group():
    """AWS CloudWatch Logs management and processing commands."""
    pass


@logs_group.command(name="list-groups")
@click.option("--region", help="AWS region to list log groups from (default: current region)")
@click.option("--all-regions", is_flag=True, help="List log groups from all available regions")
@click.option("--include-size", is_flag=True, help="Include storage size information for each log group")
@click.option("--output-file", help="Output file for log groups list (supports .json, .yaml, .csv)")
@click.pass_context
def list_groups(
    ctx: click.Context, region: Optional[str], all_regions: bool, include_size: bool, output_file: Optional[str]
) -> None:
    """List CloudWatch log groups with details."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Determine regions to scan
        if all_regions:
            target_regions = aws_auth.get_available_regions("logs")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]

        console.print(f"[blue]Listing CloudWatch log groups across {len(target_regions)} regions[/blue]")

        # Get log groups data
        log_groups_data = _get_all_log_groups(aws_auth, target_regions, include_size)

        if log_groups_data:
            print_output(
                log_groups_data,
                output_format=config.aws_output_format,
                title=f"CloudWatch Log Groups ({len(log_groups_data)} found)",
            )

            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                file_format = output_path.suffix.lstrip(".") or "json"

                # Add timestamp to filename
                timestamp = get_timestamp()
                stem = output_path.stem
                new_filename = f"{stem}_{timestamp}{output_path.suffix}"
                output_path = output_path.parent / new_filename

                save_to_file(log_groups_data, output_path, file_format)
                console.print(f"[green]Log groups list saved to:[/green] {output_path}")
        else:
            console.print("[yellow]No CloudWatch log groups found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing log groups:[/red] {e}")
        raise click.Abort()


@logs_group.command(name="download")
@click.argument("log_group")
@click.option("--days", type=int, default=7, help="Number of days to look back for logs (default: 7)")
@click.option("--region", help="AWS region where the log group is located (default: current region)")
@click.option("--output-dir", help="Output directory for downloaded logs (default: ./logs_<timestamp>)")
@click.option("--all-groups", is_flag=True, help="Download logs from all log groups (use 'ALL' as log_group argument)")
@click.pass_context
def download(
    ctx: click.Context, log_group: str, days: int, region: Optional[str], output_dir: Optional[str], all_groups: bool
) -> None:
    """Download CloudWatch logs for a specific log group or all groups."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"

        # Generate output directory if not provided
        if not output_dir:
            timestamp = get_timestamp()
            output_dir = f"logs_{timestamp}"

        output_path = Path(output_dir)
        ensure_directory(output_path)

        # Handle ALL groups case
        if log_group.upper() == "ALL" or all_groups:
            console.print(f"[blue]Downloading logs from all log groups in region {target_region}[/blue]")
            console.print(f"[dim]Looking back {days} days[/dim]")
            console.print(f"[dim]Output directory: {output_path}[/dim]")

            # Get all log groups
            logs_client = aws_auth.get_client("logs", region_name=target_region)
            log_groups = _get_log_groups_list(logs_client)

            if not log_groups:
                console.print("[yellow]No log groups found[/yellow]")
                return

            # Download from all groups
            download_results = _download_multiple_log_groups(
                aws_auth, target_region, log_groups, days, output_path, config.workers
            )

        else:
            console.print(f"[blue]Downloading logs from log group: {log_group}[/blue]")
            console.print(f"[dim]Region: {target_region}, Days: {days}[/dim]")
            console.print(f"[dim]Output directory: {output_path}[/dim]")

            # Download from single group
            download_results = _download_single_log_group(aws_auth, target_region, log_group, days, output_path)

        # Display results
        _display_download_results(config, download_results)

        console.print(f"\n[green]✅ Log download completed![/green]")
        console.print(f"[dim]Logs saved to: {output_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error downloading logs:[/red] {e}")
        raise click.Abort()


@logs_group.command(name="set-retention")
@click.argument("log_group")
@click.argument("retention", type=int, default=30)
@click.option("--region", help="AWS region where the log group is located (default: current region)")
@click.option("--if-never", is_flag=True, help="Only set retention if current retention is 'Never'")
@click.option("--dry-run", is_flag=True, help="Show what would be changed without making changes")
@click.pass_context
def set_retention(
    ctx: click.Context, log_group: str, retention: int, region: Optional[str], if_never: bool, dry_run: bool
) -> None:
    """Set retention policy for a CloudWatch log group."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"

        console.print(f"[blue]Setting retention for log group: {log_group}[/blue]")
        console.print(f"[dim]Region: {target_region}, Retention: {retention} days[/dim]")
        if if_never:
            console.print("[dim]Only updating groups with 'Never' retention[/dim]")
        if dry_run:
            console.print("[yellow]DRY RUN MODE: No changes will be made[/yellow]")

        # Get logs client
        logs_client = aws_auth.get_client("logs", region_name=target_region)

        # Check current retention
        try:
            response = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
            log_groups = response.get("logGroups", [])

            # Find exact match
            target_group = None
            for group in log_groups:
                if group["logGroupName"] == log_group:
                    target_group = group
                    break

            if not target_group:
                console.print(f"[red]Log group '{log_group}' not found[/red]")
                raise click.Abort()

            current_retention = target_group.get("retentionInDays")

            # Display current status
            current_display = "Never" if current_retention is None else f"{current_retention} days"
            console.print(f"[dim]Current retention: {current_display}[/dim]")

            # Check if we should skip based on --if-never flag
            if if_never and current_retention is not None:
                console.print(f"[yellow]Skipping: Current retention is not 'Never' ({current_retention} days)[/yellow]")
                return

            # Check if retention is already set to the target value
            if current_retention == retention:
                console.print(f"[yellow]Retention already set to {retention} days[/yellow]")
                return

            if dry_run:
                console.print(f"[yellow][DRY RUN] Would set retention to {retention} days[/yellow]")
                return

            # Set retention
            logs_client.put_retention_policy(logGroupName=log_group, retentionInDays=retention)

            console.print(f"[green]✅ Retention set to {retention} days[/green]")

        except logs_client.exceptions.ResourceNotFoundException:
            console.print(f"[red]Log group '{log_group}' not found[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error setting retention:[/red] {e}")
        raise click.Abort()


@logs_group.command(name="delete-group")
@click.argument("log_group")
@click.option("--region", help="AWS region where the log group is located (default: current region)")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_group(ctx: click.Context, log_group: str, region: Optional[str], confirm: bool) -> None:
    """Delete a CloudWatch log group."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"

        # Show log group details
        console.print(f"[yellow]Log group to delete:[/yellow]")
        console.print(f"  Name: {log_group}")
        console.print(f"  Region: {target_region}")

        # Confirmation
        if not confirm:
            if not click.confirm(f"\nAre you sure you want to delete log group '{log_group}'?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Get logs client
        logs_client = aws_auth.get_client("logs", region_name=target_region)

        # Delete log group
        try:
            logs_client.delete_log_group(logGroupName=log_group)
            console.print(f"[green]✅ Log group '{log_group}' deleted successfully[/green]")

        except logs_client.exceptions.ResourceNotFoundException:
            console.print(f"[red]Log group '{log_group}' not found[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error deleting log group:[/red] {e}")
        raise click.Abort()


@logs_group.command(name="combine")
@click.argument("log_folder")
@click.option("--output-file", help="Output file for combined logs (default: combined_logs_<timestamp>.log)")
@click.option("--sort-lines", is_flag=True, default=True, help="Sort log lines chronologically (default: enabled)")
@click.pass_context
def combine(ctx: click.Context, log_folder: str, output_file: Optional[str], sort_lines: bool) -> None:
    """Combine multiple log files into a single sorted file."""
    config: Config = ctx.obj["config"]

    try:
        folder_path = Path(log_folder).resolve()

        if not folder_path.is_dir():
            console.print(f"[red]Provided path '{folder_path}' is not a directory[/red]")
            raise click.Abort()

        # Generate output filename if not provided
        if not output_file:
            timestamp = get_timestamp()
            output_file = f"combined_logs_{timestamp}.log"

        console.print(f"[blue]Combining log files from: {folder_path}[/blue]")
        console.print(f"[dim]Output file: {output_file}[/dim]")
        console.print(f"[dim]Sort lines: {'Yes' if sort_lines else 'No'}[/dim]")

        # Execute combine operation
        combine_results = _combine_log_files(folder_path, output_file, sort_lines)

        # Display results
        results_display = {
            "Input Directory": str(folder_path),
            "Output File": output_file,
            "Files Processed": combine_results["files_processed"],
            "Total Lines": combine_results["total_lines"],
            "Lines Sorted": "Yes" if sort_lines else "No",
            "Output Size": _human_readable_size(combine_results["output_size"]),
            "Processing Time": f"{combine_results['processing_time']:.2f} seconds",
        }

        print_output(results_display, output_format=config.aws_output_format, title="Log Combine Results")

        console.print(f"\n[green]✅ Log files combined successfully![/green]")
        console.print(f"[dim]Combined log saved to: {output_file}[/dim]")

    except Exception as e:
        console.print(f"[red]Error combining log files:[/red] {e}")
        raise click.Abort()


@logs_group.command(name="aggregate")
@click.argument("input_directory")
@click.option("--output-dir", help="Output directory for aggregated files (default: ./aggregated_logs)")
@click.option("--target-size", type=int, default=250, help="Target size for aggregated files in MB (default: 250)")
@click.option(
    "--log-type",
    type=click.Choice(["cloudtrail", "cloudfront", "elb", "alb", "route53", "all"]),
    help="Log type to process (auto-detect if not specified)",
)
@click.option("--prefix", default="aggregated", help="Prefix for output files (default: aggregated)")
@click.option("--keep-structure", is_flag=True, help="Keep original directory structure in output")
@click.option("--no-compression", is_flag=True, help="Disable compression of output files")
@click.option("--delete-source", is_flag=True, help="Delete source files after successful processing")
@click.pass_context
def aggregate(
    ctx: click.Context,
    input_directory: str,
    output_dir: Optional[str],
    target_size: int,
    log_type: Optional[str],
    prefix: str,
    keep_structure: bool,
    no_compression: bool,
    delete_source: bool,
) -> None:
    """Aggregate AWS log files into larger files for efficient processing."""
    config: Config = ctx.obj["config"]

    try:
        input_path = Path(input_directory).resolve()

        if not input_path.is_dir():
            console.print(f"[red]Input directory '{input_path}' does not exist or is not a directory[/red]")
            raise click.Abort()

        # Generate output directory if not provided
        if not output_dir:
            output_dir = "./aggregated_logs"

        output_path = Path(output_dir).resolve()

        console.print(f"[blue]Aggregating AWS log files[/blue]")
        console.print(f"[dim]Input directory: {input_path}[/dim]")
        console.print(f"[dim]Output directory: {output_path}[/dim]")
        console.print(f"[dim]Target size: {target_size} MB[/dim]")
        console.print(f"[dim]Log type: {log_type or 'auto-detect'}[/dim]")
        console.print(f"[dim]Compression: {'Disabled' if no_compression else 'Enabled'}[/dim]")
        if delete_source:
            console.print("[yellow]⚠️  Source files will be deleted after processing[/yellow]")

        # Confirmation for delete operation
        if delete_source:
            if not click.confirm("Are you sure you want to delete source files after processing?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Execute aggregation
        aggregation_results = _aggregate_log_files(
            input_path, output_path, target_size, log_type, prefix, keep_structure, not no_compression, delete_source
        )

        # Display results
        _display_aggregation_results(config, aggregation_results)

        console.print(f"\n[green]✅ Log aggregation completed![/green]")
        console.print(f"[dim]Aggregated files saved to: {output_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error aggregating log files:[/red] {e}")
        raise click.Abort()


def _get_all_log_groups(aws_auth: AWSAuth, regions: List[str], include_size: bool) -> List[Dict[str, Any]]:
    """Get all CloudWatch log groups across regions."""

    def get_region_log_groups(region: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Get log groups for a single region."""
        region_groups = []

        try:
            logs_client = aws_auth.get_client("logs", region_name=region)
            paginator = logs_client.get_paginator("describe_log_groups")

            for page in paginator.paginate():
                for group in page.get("logGroups", []):
                    group_data = {
                        "Log Group Name": group.get("logGroupName", ""),
                        "Region": region,
                        "Creation Time": group.get("creationTime", 0),
                        "Retention": group.get("retentionInDays", "Never"),
                        "Stored Bytes": group.get("storedBytes", 0),
                        "ARN": group.get("arn", ""),
                    }

                    # Format creation time
                    if group_data["Creation Time"]:
                        creation_dt = datetime.fromtimestamp(group_data["Creation Time"] / 1000)
                        group_data["Created"] = creation_dt.strftime("%Y-%m-%d %H:%M")
                    else:
                        group_data["Created"] = "Unknown"

                    # Format retention
                    if isinstance(group_data["Retention"], int):
                        group_data["Retention"] = f"{group_data['Retention']} days"

                    # Format size if requested
                    if include_size:
                        group_data["Storage Size"] = _human_readable_size(group_data["Stored Bytes"])

                    # Remove raw values
                    del group_data["Creation Time"]
                    if not include_size:
                        del group_data["Stored Bytes"]

                    region_groups.append(group_data)

        except Exception as e:
            logger.warning(f"Error getting log groups in region {region}: {e}")

        return region, region_groups

    # Get log groups in parallel
    region_results = parallel_execute(
        get_region_log_groups, regions, max_workers=4, show_progress=True, description="Scanning log groups"
    )

    # Combine results
    all_groups = []
    for region, groups in region_results:
        all_groups.extend(groups)

    return all_groups


def _get_log_groups_list(logs_client) -> List[str]:
    """Get list of log group names."""
    log_groups = []

    try:
        paginator = logs_client.get_paginator("describe_log_groups")

        for page in paginator.paginate():
            for group in page.get("logGroups", []):
                log_groups.append(group["logGroupName"])

    except Exception as e:
        logger.error(f"Error getting log groups list: {e}")
        raise

    return log_groups


def _download_single_log_group(
    aws_auth: AWSAuth, region: str, log_group: str, days: int, output_path: Path
) -> Dict[str, Any]:
    """Download logs from a single log group."""

    logs_client = aws_auth.get_client("logs", region_name=region)

    # Calculate time range
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)

    result = {
        "log_group": log_group,
        "region": region,
        "days": days,
        "streams_processed": 0,
        "events_downloaded": 0,
        "files_created": 0,
        "total_size": 0,
        "errors": [],
    }

    try:
        # Get log streams
        paginator = logs_client.get_paginator("describe_log_streams")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:

            task = progress.add_task(f"Processing {log_group}...", total=None)

            for page in paginator.paginate(logGroupName=log_group, orderBy="LastEventTime", descending=True):
                for stream in page.get("logStreams", []):
                    stream_name = stream["logStreamName"]

                    # Skip streams with no events in our time range
                    if stream.get("lastEventTime", 0) < start_timestamp:
                        continue

                    progress.update(task, description=f"Processing stream: {stream_name[:50]}...")

                    # Download events from this stream
                    stream_result = _download_log_stream(
                        logs_client, log_group, stream_name, start_timestamp, end_timestamp, output_path
                    )

                    result["streams_processed"] += 1
                    result["events_downloaded"] += stream_result["events"]
                    result["total_size"] += stream_result["size"]

                    if stream_result["file_created"]:
                        result["files_created"] += 1

    except Exception as e:
        error_msg = f"Error downloading from {log_group}: {str(e)}"
        result["errors"].append(error_msg)
        logger.error(error_msg)

    return result


def _download_multiple_log_groups(
    aws_auth: AWSAuth, region: str, log_groups: List[str], days: int, output_path: Path, max_workers: int
) -> Dict[str, Any]:
    """Download logs from multiple log groups in parallel."""

    def download_group(log_group: str) -> Dict[str, Any]:
        """Download logs from a single group."""
        return _download_single_log_group(aws_auth, region, log_group, days, output_path)

    # Process groups in parallel
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        task = progress.add_task("Downloading from log groups...", total=len(log_groups))

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_group, group) for group in log_groups]

            for future in futures:
                result = future.result()
                results.append(result)
                progress.advance(task)

    # Compile summary
    summary = {
        "total_groups": len(log_groups),
        "groups_processed": len([r for r in results if not r["errors"]]),
        "total_streams": sum(r["streams_processed"] for r in results),
        "total_events": sum(r["events_downloaded"] for r in results),
        "total_files": sum(r["files_created"] for r in results),
        "total_size": sum(r["total_size"] for r in results),
        "errors": [error for r in results for error in r["errors"]],
        "results": results,
    }

    return summary


def _download_log_stream(
    logs_client, log_group: str, stream_name: str, start_time: int, end_time: int, output_path: Path
) -> Dict[str, Any]:
    """Download events from a single log stream."""

    result = {"stream": stream_name, "events": 0, "size": 0, "file_created": False}

    try:
        # Sanitize filename
        safe_group_name = re.sub(r"[^\w\-_.]", "_", log_group)
        safe_stream_name = re.sub(r"[^\w\-_.]", "_", stream_name)

        output_file = output_path / f"{safe_group_name}_{safe_stream_name}.log"

        # Get log events
        paginator = logs_client.get_paginator("get_log_events")

        events = []
        for page in paginator.paginate(
            logGroupName=log_group, logStreamName=stream_name, startTime=start_time, endTime=end_time
        ):
            events.extend(page.get("events", []))

        if events:
            # Write events to file
            with open(output_file, "w", encoding="utf-8") as f:
                for event in events:
                    timestamp = datetime.fromtimestamp(event["timestamp"] / 1000)
                    f.write(f"{timestamp.isoformat()} {event['message']}\n")

            result["events"] = len(events)
            result["size"] = output_file.stat().st_size
            result["file_created"] = True

    except Exception as e:
        logger.debug(f"Error downloading stream {stream_name}: {e}")

    return result


def _combine_log_files(folder_path: Path, output_file: str, sort_lines: bool) -> Dict[str, Any]:
    """Combine multiple log files into a single file."""

    start_time = datetime.now()

    # Find all log files
    files = [p for p in folder_path.iterdir() if p.is_file()]

    combined_lines = []
    files_processed = 0

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                combined_lines.extend(lines)
                files_processed += 1
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")

    # Sort lines if requested
    if sort_lines:
        combined_lines.sort()

    # Write combined file
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(combined_lines)

    # Get output file size
    output_size = Path(output_file).stat().st_size
    processing_time = (datetime.now() - start_time).total_seconds()

    return {
        "files_processed": files_processed,
        "total_lines": len(combined_lines),
        "output_size": output_size,
        "processing_time": processing_time,
    }


def _human_readable_size(num_bytes: int) -> str:
    """Convert bytes to human readable format."""
    if not isinstance(num_bytes, (int, float)):
        return str(num_bytes)

    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"


def _display_download_results(config: Config, results: Dict[str, Any]) -> None:
    """Display download results."""

    if "total_groups" in results:
        # Multiple groups results
        summary_display = {
            "Total Log Groups": results["total_groups"],
            "Groups Processed": results["groups_processed"],
            "Total Streams": results["total_streams"],
            "Total Events": results["total_events"],
            "Files Created": results["total_files"],
            "Total Size": _human_readable_size(results["total_size"]),
            "Errors": len(results["errors"]),
        }
    else:
        # Single group results
        summary_display = {
            "Log Group": results["log_group"],
            "Region": results["region"],
            "Days": results["days"],
            "Streams Processed": results["streams_processed"],
            "Events Downloaded": results["events_downloaded"],
            "Files Created": results["files_created"],
            "Total Size": _human_readable_size(results["total_size"]),
            "Errors": len(results["errors"]),
        }

    print_output(summary_display, output_format=config.aws_output_format, title="Log Download Results")

    # Show errors if any
    if results.get("errors"):
        console.print("\n[red]Errors encountered:[/red]")
        for error in results["errors"][:5]:  # Show first 5 errors
            console.print(f"  • {error}")
        if len(results["errors"]) > 5:
            console.print(f"  ... and {len(results['errors']) - 5} more errors")


def _aggregate_log_files(
    input_path: Path,
    output_path: Path,
    target_size_mb: int,
    log_type: Optional[str],
    prefix: str,
    keep_structure: bool,
    compress: bool,
    delete_source: bool,
) -> Dict[str, Any]:
    """Aggregate log files into larger files."""

    start_time = datetime.now()

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Find log files
    log_files = _find_log_files(input_path, log_type)

    result = {
        "input_directory": str(input_path),
        "output_directory": str(output_path),
        "target_size_mb": target_size_mb,
        "log_type": log_type or "auto-detect",
        "files_found": sum(len(files) for files in log_files.values()),
        "files_processed": 0,
        "output_files_created": 0,
        "total_input_size": 0,
        "total_output_size": 0,
        "deleted_files": 0,
        "processing_time": 0,
        "errors": [],
    }

    try:
        target_size_bytes = target_size_mb * 1024 * 1024

        for detected_log_type, files in log_files.items():
            if not files:
                continue

            console.print(f"[dim]Processing {len(files)} {detected_log_type} files...[/dim]")

            # Aggregate files of this type
            type_result = _aggregate_files_by_type(
                files, output_path, detected_log_type, target_size_bytes, prefix, compress, delete_source
            )

            result["files_processed"] += type_result["processed"]
            result["output_files_created"] += type_result["output_files"]
            result["total_input_size"] += type_result["input_size"]
            result["total_output_size"] += type_result["output_size"]
            result["deleted_files"] += type_result["deleted"]
            result["errors"].extend(type_result["errors"])

    except Exception as e:
        result["errors"].append(f"Aggregation error: {str(e)}")

    result["processing_time"] = (datetime.now() - start_time).total_seconds()

    return result


def _find_log_files(input_path: Path, log_type: Optional[str]) -> Dict[str, List[Path]]:
    """Find and categorize log files."""

    log_files = {log_type: [] for log_type in LOG_PATTERNS.keys()}

    # Walk through directory
    for file_path in input_path.rglob("*"):
        if not file_path.is_file():
            continue

        # Detect log type
        detected_type = _detect_log_type(file_path, log_type)
        if detected_type:
            log_files[detected_type].append(file_path)

    return log_files


def _detect_log_type(file_path: Path, specified_type: Optional[str]) -> Optional[str]:
    """Detect log type from file path and content."""

    # If type is specified, use it
    if specified_type and specified_type != "all":
        return specified_type

    file_name = str(file_path)

    # Check filename patterns
    for log_type, pattern in LOG_PATTERNS.items():
        if re.match(pattern, file_name, re.IGNORECASE):
            return log_type

    # Try content detection for ambiguous files
    try:
        content_sample = _read_file_sample(file_path, 5)

        # JSON structure detection
        if content_sample.strip().startswith("{"):
            try:
                json_data = json.loads(content_sample)
                if "Records" in json_data and "eventVersion" in json_data.get("Records", [{}])[0]:
                    return LOG_TYPE_CLOUDTRAIL
                elif "Records" in json_data:
                    return LOG_TYPE_CLOUDFRONT
            except json.JSONDecodeError:
                pass

        # CloudFront TSV format
        if "#Version:" in content_sample and "#Fields:" in content_sample:
            return LOG_TYPE_CLOUDFRONT

        # ELB/ALB detection
        if "#Version:" in content_sample and "elasticloadbalancing" in file_name:
            if "app/" in content_sample or "net/" in content_sample:
                return LOG_TYPE_ALB
            return LOG_TYPE_ELB

        # Route 53 detection
        if "#Version:" in content_sample and "route53" in file_name:
            return LOG_TYPE_ROUTE53

    except Exception:
        pass

    return None


def _read_file_sample(file_path: Path, num_lines: int = 5) -> str:
    """Read first few lines of a file, handling gzip."""

    try:
        if str(file_path).endswith(".gz"):
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                return "".join([f.readline() for _ in range(num_lines)])
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return "".join([f.readline() for _ in range(num_lines)])
    except Exception:
        return ""


def _aggregate_files_by_type(
    files: List[Path],
    output_path: Path,
    log_type: str,
    target_size_bytes: int,
    prefix: str,
    compress: bool,
    delete_source: bool,
) -> Dict[str, Any]:
    """Aggregate files of a specific type."""

    result = {"processed": 0, "output_files": 0, "input_size": 0, "output_size": 0, "deleted": 0, "errors": []}

    current_batch = []
    current_size = 0
    batch_number = 1

    for file_path in files:
        try:
            file_size = file_path.stat().st_size
            result["input_size"] += file_size

            # Check if adding this file would exceed target size
            if current_size + file_size > target_size_bytes and current_batch:
                # Write current batch
                _write_aggregated_file(current_batch, output_path, log_type, prefix, batch_number, compress)
                result["output_files"] += 1
                batch_number += 1

                # Start new batch
                current_batch = [file_path]
                current_size = file_size
            else:
                current_batch.append(file_path)
                current_size += file_size

            result["processed"] += 1

        except Exception as e:
            result["errors"].append(f"Error processing {file_path}: {str(e)}")

    # Write final batch if any files remain
    if current_batch:
        _write_aggregated_file(current_batch, output_path, log_type, prefix, batch_number, compress)
        result["output_files"] += 1

    # Delete source files if requested
    if delete_source:
        for file_path in files:
            try:
                file_path.unlink()
                result["deleted"] += 1
            except Exception as e:
                result["errors"].append(f"Error deleting {file_path}: {str(e)}")

    # Calculate output size
    for output_file in output_path.glob(f"{prefix}_{log_type}_*.log*"):
        result["output_size"] += output_file.stat().st_size

    return result


def _write_aggregated_file(
    files: List[Path], output_path: Path, log_type: str, prefix: str, batch_number: int, compress: bool
) -> None:
    """Write aggregated file from a batch of input files."""

    timestamp = get_timestamp()
    output_filename = f"{prefix}_{log_type}_{batch_number}_{timestamp}.log"

    if compress:
        output_filename += ".gz"
        output_file = output_path / output_filename

        with gzip.open(output_file, "wt", encoding="utf-8") as out_f:
            for file_path in files:
                _copy_file_content(file_path, out_f)
    else:
        output_file = output_path / output_filename

        with open(output_file, "w", encoding="utf-8") as out_f:
            for file_path in files:
                _copy_file_content(file_path, out_f)


def _copy_file_content(file_path: Path, output_file) -> None:
    """Copy content from input file to output file."""

    try:
        if str(file_path).endswith(".gz"):
            with gzip.open(file_path, "rt", encoding="utf-8") as in_f:
                shutil.copyfileobj(in_f, output_file)
        else:
            with open(file_path, "r", encoding="utf-8") as in_f:
                shutil.copyfileobj(in_f, output_file)

        # Add newline between files
        output_file.write("\n")

    except Exception as e:
        logger.warning(f"Error copying content from {file_path}: {e}")


def _display_aggregation_results(config: Config, results: Dict[str, Any]) -> None:
    """Display aggregation results."""

    summary_display = {
        "Input Directory": results["input_directory"],
        "Output Directory": results["output_directory"],
        "Log Type": results["log_type"],
        "Target Size (MB)": results["target_size_mb"],
        "Files Found": results["files_found"],
        "Files Processed": results["files_processed"],
        "Output Files Created": results["output_files_created"],
        "Input Size": _human_readable_size(results["total_input_size"]),
        "Output Size": _human_readable_size(results["total_output_size"]),
        "Compression Ratio": f"{(results['total_output_size'] / max(results['total_input_size'], 1)) * 100:.1f}%",
        "Files Deleted": results["deleted_files"],
        "Processing Time": f"{results['processing_time']:.2f} seconds",
        "Errors": len(results["errors"]),
    }

    print_output(summary_display, output_format=config.aws_output_format, title="Log Aggregation Results")

    # Show errors if any
    if results["errors"]:
        console.print("\n[red]Errors encountered:[/red]")
        for error in results["errors"][:5]:  # Show first 5 errors
            console.print(f"  • {error}")
        if len(results["errors"]) > 5:
            console.print(f"  ... and {len(results['errors']) - 5} more errors")
