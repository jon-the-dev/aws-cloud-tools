"""AWS CloudFront distribution management and monitoring commands."""

import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
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


@click.group(name="cloudfront")
def cloudfront_group():
    """AWS CloudFront distribution management and monitoring commands."""
    pass


@cloudfront_group.command(name="update-logging")
@click.option("--log-bucket", help="S3 bucket for CloudFront logs (required for logging configuration)")
@click.option(
    "--log-prefix", default="cf-logs", help="Default log prefix when no alternate domain names found (default: cf-logs)"
)
@click.option("--setup-alarms", is_flag=True, help="Setup CloudWatch alarms for CloudFront distributions")
@click.option("--remove-alarms", is_flag=True, help="Remove CloudWatch alarms for CloudFront distributions")
@click.option("--sns-topic", help="SNS topic name for alarm notifications (required for alarm setup)")
@click.option("--region", help="AWS region for SNS topic and CloudWatch alarms (default: current region)")
@click.option("--dry-run", is_flag=True, help="Show what would be changed without making changes")
@click.option("--output-file", help="Output file for results (supports .json, .yaml, .csv)")
@click.pass_context
def update_logging(
    ctx: click.Context,
    log_bucket: Optional[str],
    log_prefix: str,
    setup_alarms: bool,
    remove_alarms: bool,
    sns_topic: Optional[str],
    region: Optional[str],
    dry_run: bool,
    output_file: Optional[str],
) -> None:
    """Update CloudFront distributions to enable logging and optionally setup alarms."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"

        # Validate mutually exclusive options
        if setup_alarms and remove_alarms:
            console.print("[red]Error: --setup-alarms and --remove-alarms cannot be used together[/red]")
            raise click.Abort()

        # Validate required parameters
        if not log_bucket and not setup_alarms and not remove_alarms:
            console.print(
                "[yellow]⚠️  Warning: No --log-bucket specified. Logging configuration will be skipped.[/yellow]"
            )
            console.print("[dim]Use --log-bucket to enable CloudFront logging configuration[/dim]")

        if setup_alarms and not sns_topic:
            console.print(
                "[yellow]⚠️  Warning: No --sns-topic specified. Alarms will be created without notification actions.[/yellow]"
            )
            console.print("[dim]Use --sns-topic to enable alarm notifications[/dim]")

        console.print(f"[blue]Processing CloudFront distributions[/blue]")
        if log_bucket:
            console.print(f"[dim]Target log bucket: {log_bucket}[/dim]")
        if setup_alarms:
            console.print(
                f"[dim]Setting up CloudWatch alarms{' with SNS topic: ' + sns_topic if sns_topic else ' (no notifications)'}[/dim]"
            )
        elif remove_alarms:
            console.print(f"[dim]Removing CloudWatch alarms[/dim]")
        if dry_run:
            console.print(f"[yellow]DRY RUN MODE: No changes will be made[/yellow]")

        # Get CloudFront client
        cf_client = aws_auth.get_client("cloudfront")

        # Get SNS topic ARN if needed
        sns_topic_arn = None
        if setup_alarms and sns_topic:
            sns_topic_arn = _get_sns_topic_arn(aws_auth, sns_topic, target_region)
            if sns_topic_arn:
                console.print(f"[green]Found SNS topic ARN:[/green] {sns_topic_arn}")
            else:
                console.print(f"[yellow]⚠️  SNS topic '{sns_topic}' not found in region {target_region}[/yellow]")
                console.print("[dim]Alarms will be created without notification actions[/dim]")

        # Execute the update process
        update_results = _update_cloudfront_distributions(
            aws_auth,
            cf_client,
            target_region,
            log_bucket,
            log_prefix,
            setup_alarms,
            remove_alarms,
            sns_topic_arn,
            dry_run,
            config.workers,
        )

        # Display results
        _display_update_results(config, update_results, dry_run)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(update_results, output_path, file_format)
            console.print(f"[green]Update results saved to:[/green] {output_path}")

        console.print(f"\n[green]✅ CloudFront distribution processing completed![/green]")

    except Exception as e:
        console.print(f"[red]Error processing CloudFront distributions:[/red] {e}")
        raise click.Abort()


@cloudfront_group.command(name="list-distributions")
@click.option("--include-disabled", is_flag=True, help="Include disabled distributions in the list")
@click.option("--show-logging-status", is_flag=True, help="Show logging configuration status for each distribution")
@click.option("--output-file", help="Output file for distributions list (supports .json, .yaml, .csv)")
@click.pass_context
def list_distributions(
    ctx: click.Context, include_disabled: bool, show_logging_status: bool, output_file: Optional[str]
) -> None:
    """List CloudFront distributions with their configuration details."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        console.print("[blue]Listing CloudFront distributions[/blue]")

        # Get CloudFront client
        cf_client = aws_auth.get_client("cloudfront")

        # Get all distributions
        distributions_data = _get_all_distributions(cf_client, include_disabled, show_logging_status)

        if distributions_data:
            print_output(
                distributions_data,
                output_format=config.aws_output_format,
                title=f"CloudFront Distributions ({len(distributions_data)} found)",
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

                save_to_file(distributions_data, output_path, file_format)
                console.print(f"[green]Distributions list saved to:[/green] {output_path}")
        else:
            console.print("[yellow]No CloudFront distributions found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing CloudFront distributions:[/red] {e}")
        raise click.Abort()


@cloudfront_group.command(name="distribution-details")
@click.argument("distribution_id")
@click.option("--show-config", is_flag=True, help="Show detailed distribution configuration")
@click.option("--output-file", help="Output file for distribution details (supports .json, .yaml)")
@click.pass_context
def distribution_details(
    ctx: click.Context, distribution_id: str, show_config: bool, output_file: Optional[str]
) -> None:
    """Get detailed information about a specific CloudFront distribution."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        console.print(f"[blue]Getting details for CloudFront distribution: {distribution_id}[/blue]")

        # Get CloudFront client
        cf_client = aws_auth.get_client("cloudfront")

        # Get distribution details
        try:
            response = cf_client.get_distribution(Id=distribution_id)
            distribution = response["Distribution"]

        except cf_client.exceptions.NoSuchDistribution:
            console.print(f"[red]Distribution '{distribution_id}' not found[/red]")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]Error retrieving distribution details:[/red] {e}")
            raise click.Abort()

        # Format basic information
        dist_config = distribution["DistributionConfig"]

        basic_info = {
            "Distribution ID": distribution.get("Id", ""),
            "Domain Name": distribution.get("DomainName", ""),
            "Status": distribution.get("Status", ""),
            "State": "Enabled" if dist_config.get("Enabled", False) else "Disabled",
            "Price Class": dist_config.get("PriceClass", ""),
            "HTTP Version": dist_config.get("HttpVersion", ""),
            "IPv6 Enabled": "Yes" if dist_config.get("IsIPV6Enabled", False) else "No",
            "Default Root Object": dist_config.get("DefaultRootObject", "Not set"),
            "Comment": dist_config.get("Comment", ""),
            "Last Modified": (
                distribution.get("LastModifiedTime", "").strftime("%Y-%m-%d %H:%M:%S")
                if distribution.get("LastModifiedTime")
                else ""
            ),
        }

        # Add aliases if present
        aliases = dist_config.get("Aliases", {}).get("Items", [])
        if aliases:
            basic_info["Aliases"] = ", ".join(aliases)

        # Add logging information
        logging_config = dist_config.get("Logging", {})
        basic_info["Logging Enabled"] = "Yes" if logging_config.get("Enabled", False) else "No"
        if logging_config.get("Enabled", False):
            basic_info["Log Bucket"] = logging_config.get("Bucket", "")
            basic_info["Log Prefix"] = logging_config.get("Prefix", "")

        print_output(
            basic_info,
            output_format=config.aws_output_format,
            title=f"CloudFront Distribution Details: {distribution_id}",
        )

        # Show detailed config if requested
        if show_config:
            console.print("\n[bold]Detailed Distribution Configuration:[/bold]")
            console.print_json(json.dumps(dist_config, indent=2, default=str))

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            # Include full distribution data in saved file
            save_data = {
                "basic_info": basic_info,
                "full_distribution": distribution if show_config else None,
                "retrieved_at": datetime.now().isoformat(),
            }

            save_to_file(save_data, output_path, file_format)
            console.print(f"[green]Distribution details saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error getting distribution details:[/red] {e}")
        raise click.Abort()


@cloudfront_group.command(name="invalidate")
@click.argument("target", required=True)
@click.option("--paths", multiple=True, help="Paths to invalidate (default: /*)")
@click.option("--output-file", help="Output file for invalidation details (supports .json, .yaml)")
@click.pass_context
def invalidate(
    ctx: click.Context, 
    target: str, 
    paths: Tuple[str, ...], 
    output_file: Optional[str]
) -> None:
    """Invalidate CloudFront distribution cache by domain name or distribution ID.
    
    TARGET can be either:
    - A domain name (e.g., example.com)
    - A distribution ID (e.g., E1234567890123)
    """
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Default to /* if no paths specified
        invalidation_paths = list(paths) if paths else ["/*"]
        
        console.print(f"[blue]Processing CloudFront invalidation for: {target}[/blue]")
        console.print(f"[dim]Paths to invalidate: {', '.join(invalidation_paths)}[/dim]")

        # Get CloudFront client
        cf_client = aws_auth.get_client("cloudfront")

        # Determine if target is a distribution ID or domain name
        distribution_id = _get_distribution_id(cf_client, target)
        
        if not distribution_id:
            console.print(f"[red]No CloudFront distribution found for: {target}[/red]")
            raise click.Abort()

        console.print(f"[green]Found distribution ID:[/green] {distribution_id}")

        # Create invalidation
        invalidation_result = _create_invalidation(cf_client, distribution_id, invalidation_paths)
        
        # Display results
        result_data = {
            "Target": target,
            "Distribution ID": distribution_id,
            "Invalidation ID": invalidation_result["Invalidation"]["Id"],
            "Status": invalidation_result["Invalidation"]["Status"],
            "Paths": invalidation_paths,
            "Caller Reference": invalidation_result["Invalidation"]["InvalidationBatch"]["CallerReference"],
            "Created At": invalidation_result["Invalidation"]["CreateTime"].strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        print_output(
            result_data,
            output_format=config.aws_output_format,
            title=f"CloudFront Invalidation Created"
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

            # Include full invalidation data
            save_data = {
                "invalidation_summary": result_data,
                "full_response": invalidation_result,
                "created_at": datetime.now().isoformat(),
            }

            save_to_file(save_data, output_path, file_format)
            console.print(f"[green]Invalidation details saved to:[/green] {output_path}")

        console.print(f"\n[green]✅ CloudFront invalidation created successfully![/green]")
        console.print(f"[dim]Note: Invalidations typically take 10-15 minutes to complete[/dim]")

    except Exception as e:
        console.print(f"[red]Error creating CloudFront invalidation:[/red] {e}")
        raise click.Abort()


def _get_distribution_id(cf_client, target: str) -> Optional[str]:
    """Get distribution ID from target (domain name or distribution ID)."""
    try:
        # Check if target is already a distribution ID (starts with E and is alphanumeric)
        if target.startswith("E") and len(target) > 10 and target.replace("E", "").isalnum():
            # Verify the distribution exists
            try:
                cf_client.get_distribution(Id=target)
                return target
            except cf_client.exceptions.NoSuchDistribution:
                return None
        
        # Target is a domain name, search for it in distributions
        paginator = cf_client.get_paginator("list_distributions")
        
        for page in paginator.paginate():
            if "Items" not in page["DistributionList"]:
                continue
                
            for distribution in page["DistributionList"]["Items"]:
                # Check aliases
                aliases = distribution["DistributionConfig"].get("Aliases", {}).get("Items", [])
                if target in aliases:
                    return distribution["Id"]
                
                # Check CloudFront domain name
                if distribution.get("DomainName") == target:
                    return distribution["Id"]
        
        return None
        
    except Exception as e:
        logger.debug(f"Error finding distribution for target {target}: {e}")
        return None


def _create_invalidation(cf_client, distribution_id: str, paths: List[str]) -> Dict[str, Any]:
    """Create an invalidation for the specified distribution and paths."""
    try:
        # Generate unique caller reference using timestamp
        caller_reference = f"invalidate_{int(time.time() * 1000)}"
        
        response = cf_client.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                "Paths": {
                    "Quantity": len(paths),
                    "Items": paths
                },
                "CallerReference": caller_reference
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating invalidation for distribution {distribution_id}: {e}")
        raise


def _get_sns_topic_arn(aws_auth: AWSAuth, topic_name: str, region: str) -> Optional[str]:
    """Get the ARN for an SNS topic by name."""
    try:
        sns_client = aws_auth.get_client("sns", region_name=region)
        paginator = sns_client.get_paginator("list_topics")

        for page in paginator.paginate():
            for topic in page["Topics"]:
                if topic["TopicArn"].endswith(f":{topic_name}"):
                    return topic["TopicArn"]

        return None
    except Exception as e:
        logger.debug(f"Error getting SNS topic ARN for {topic_name} in {region}: {e}")
        return None


def _get_all_distributions(cf_client, include_disabled: bool, show_logging_status: bool) -> List[Dict[str, Any]]:
    """Get all CloudFront distributions with their details."""
    distributions_data = []

    try:
        paginator = cf_client.get_paginator("list_distributions")

        for page in paginator.paginate():
            if "Items" not in page["DistributionList"]:
                continue

            for dist in page["DistributionList"]["Items"]:
                dist_config = dist["DistributionConfig"]

                # Skip disabled distributions unless requested
                if not include_disabled and not dist_config.get("Enabled", False):
                    continue

                dist_data = {
                    "Distribution ID": dist.get("Id", ""),
                    "Domain Name": dist.get("DomainName", ""),
                    "Status": dist.get("Status", ""),
                    "State": "Enabled" if dist_config.get("Enabled", False) else "Disabled",
                    "Price Class": dist_config.get("PriceClass", ""),
                    "Comment": (
                        dist_config.get("Comment", "")[:50] + "..."
                        if len(dist_config.get("Comment", "")) > 50
                        else dist_config.get("Comment", "")
                    ),
                    "Last Modified": (
                        dist.get("LastModifiedTime", "").strftime("%Y-%m-%d %H:%M")
                        if dist.get("LastModifiedTime")
                        else ""
                    ),
                }

                # Add aliases if present
                aliases = dist_config.get("Aliases", {}).get("Items", [])
                if aliases:
                    dist_data["Aliases"] = ", ".join(aliases[:3]) + ("..." if len(aliases) > 3 else "")

                # Add logging status if requested
                if show_logging_status:
                    logging_config = dist_config.get("Logging", {})
                    dist_data["Logging"] = "Enabled" if logging_config.get("Enabled", False) else "Disabled"
                    if logging_config.get("Enabled", False):
                        dist_data["Log Bucket"] = logging_config.get("Bucket", "")

                distributions_data.append(dist_data)

    except Exception as e:
        logger.error(f"Error listing distributions: {e}")
        raise

    return distributions_data


def _update_cloudfront_distributions(
    aws_auth: AWSAuth,
    cf_client,
    region: str,
    log_bucket: Optional[str],
    log_prefix: str,
    setup_alarms: bool,
    remove_alarms: bool,
    sns_topic_arn: Optional[str],
    dry_run: bool,
    max_workers: int,
) -> Dict[str, Any]:
    """Update CloudFront distributions with logging and alarm configuration."""

    # Get all distributions
    paginator = cf_client.get_paginator("list_distributions")
    distributions = []

    for page in paginator.paginate():
        if "Items" in page["DistributionList"]:
            distributions.extend(page["DistributionList"]["Items"])

    console.print(f"[dim]Found {len(distributions)} CloudFront distributions[/dim]")

    # Process distributions in parallel
    def process_distribution(dist: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single distribution."""
        return _update_single_distribution(
            aws_auth, dist, region, log_bucket, log_prefix, setup_alarms, remove_alarms, sns_topic_arn, dry_run
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        task = progress.add_task("Processing distributions...", total=len(distributions))

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_distribution, dist) for dist in distributions]

            for future in futures:
                result = future.result()
                results.append(result)
                progress.advance(task)

    # Compile summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_distributions": len(distributions),
        "updated_count": sum(1 for r in results if r.get("updated", False)),
        "would_update_count": sum(1 for r in results if r.get("would_update", False)),
        "error_count": sum(1 for r in results if r.get("error")),
        "cf_managed_count": sum(1 for r in results if r.get("stack_name")),
        "alarms_created": sum(len(r.get("alarms_result", {}).get("alarms_created", [])) for r in results),
        "alarms_removed": sum(len(r.get("alarms_result", {}).get("alarms_removed", [])) for r in results),
        "alarm_errors": sum(len(r.get("alarms_result", {}).get("errors", [])) for r in results),
        "results": results,
    }

    return summary


def _update_single_distribution(
    aws_auth: AWSAuth,
    distribution: Dict[str, Any],
    region: str,
    log_bucket: Optional[str],
    log_prefix: str,
    setup_alarms: bool,
    remove_alarms: bool,
    sns_topic_arn: Optional[str],
    dry_run: bool,
) -> Dict[str, Any]:
    """Update a single CloudFront distribution."""

    dist_id = distribution.get("Id", "")
    dist_config = distribution.get("DistributionConfig", {})

    result = {
        "id": dist_id,
        "domain": distribution.get("DomainName", ""),
        "updated": False,
        "would_update": False,
        "error": None,
        "stack_name": None,
        "logging_enabled": False,
        "current_bucket": "",
        "log_prefix": "",
        "aliases": [],
    }

    try:
        # Get aliases
        aliases = dist_config.get("Aliases", {}).get("Items", [])
        result["aliases"] = aliases

        # Check if managed by CloudFormation
        result["stack_name"] = _get_cloudformation_stack(aws_auth, dist_id)

        # Check current logging configuration
        logging_config = dist_config.get("Logging", {})
        result["logging_enabled"] = logging_config.get("Enabled", False)
        result["current_bucket"] = logging_config.get("Bucket", "")
        result["log_prefix"] = logging_config.get("Prefix", "")

        # Update logging if needed and log_bucket is provided
        if log_bucket:
            needs_update = not result["logging_enabled"] or not result["current_bucket"].startswith(log_bucket)

            if needs_update:
                if dry_run:
                    result["would_update"] = True
                else:
                    # Determine log prefix
                    if aliases:
                        # Use first alias as prefix
                        prefix = aliases[0].replace(".", "-")
                    else:
                        prefix = log_prefix

                    # Update distribution logging
                    _enable_distribution_logging(aws_auth, dist_id, log_bucket, prefix)
                    result["updated"] = True
                    result["log_prefix"] = prefix

        # Handle alarms
        if setup_alarms or remove_alarms:
            if setup_alarms:
                alarm_result = _setup_cloudfront_alarms(
                    aws_auth, dist_id, result["domain"], region, sns_topic_arn, dry_run
                )
            else:
                alarm_result = _remove_cloudfront_alarms(aws_auth, dist_id, result["domain"], region, dry_run)

            result["alarms_result"] = alarm_result

    except Exception as e:
        result["error"] = str(e)
        logger.debug(f"Error processing distribution {dist_id}: {e}")

    return result


def _get_cloudformation_stack(aws_auth: AWSAuth, distribution_id: str) -> Optional[str]:
    """Check if the distribution was created by CloudFormation."""
    try:
        cf_client = aws_auth.get_client("cloudfront")
        sts_client = aws_auth.get_client("sts")

        account_id = sts_client.get_caller_identity()["Account"]
        resource_arn = f"arn:aws:cloudfront::{account_id}:distribution/{distribution_id}"

        response = cf_client.list_tags_for_resource(Resource=resource_arn)

        for tag in response.get("Tags", {}).get("Items", []):
            if tag["Key"] == "aws:cloudformation:stack-name":
                return tag["Value"]

        return None
    except Exception as e:
        logger.debug(f"Error getting tags for distribution {distribution_id}: {e}")
        return None


def _enable_distribution_logging(aws_auth: AWSAuth, distribution_id: str, log_bucket: str, log_prefix: str) -> None:
    """Enable logging for a CloudFront distribution."""
    cf_client = aws_auth.get_client("cloudfront")

    # Get current distribution config
    response = cf_client.get_distribution_config(Id=distribution_id)
    config = response["DistributionConfig"]
    etag = response["ETag"]

    # Update logging configuration
    config["Logging"] = {
        "Enabled": True,
        "IncludeCookies": False,
        "Bucket": f"{log_bucket}.s3.amazonaws.com",
        "Prefix": log_prefix,
    }

    # Update the distribution
    cf_client.update_distribution(Id=distribution_id, DistributionConfig=config, IfMatch=etag)


def _setup_cloudfront_alarms(
    aws_auth: AWSAuth,
    distribution_id: str,
    distribution_domain: str,
    region: str,
    sns_topic_arn: Optional[str],
    dry_run: bool,
) -> Dict[str, Any]:
    """Setup CloudWatch alarms for a CloudFront distribution."""

    result = {
        "distribution_id": distribution_id,
        "distribution_domain": distribution_domain,
        "alarms_created": [],
        "alarms_skipped": [],
        "errors": [],
    }

    try:
        cw_client = aws_auth.get_client("cloudwatch", region_name=region)

        # Define alarms to create
        alarms_config = [
            {
                "name": f"CloudFront-{distribution_id}-HighErrorRate",
                "description": f"High error rate for CloudFront distribution {distribution_id}",
                "metric_name": "4xxErrorRate",
                "threshold": 5.0,
                "comparison": "GreaterThanThreshold",
            },
            {
                "name": f"CloudFront-{distribution_id}-HighOriginLatency",
                "description": f"High origin latency for CloudFront distribution {distribution_id}",
                "metric_name": "OriginLatency",
                "threshold": 3000.0,
                "comparison": "GreaterThanThreshold",
            },
            {
                "name": f"CloudFront-{distribution_id}-LowCacheHitRate",
                "description": f"Low cache hit rate for CloudFront distribution {distribution_id}",
                "metric_name": "CacheHitRate",
                "threshold": 80.0,
                "comparison": "LessThanThreshold",
            },
        ]

        for alarm_config in alarms_config:
            alarm_name = alarm_config["name"]

            try:
                # Check if alarm already exists
                existing_alarms = cw_client.describe_alarms(AlarmNames=[alarm_name])
                if existing_alarms["MetricAlarms"]:
                    result["alarms_skipped"].append(alarm_name)
                    continue

                if dry_run:
                    result["alarms_created"].append(f"[DRY RUN] {alarm_name}")
                    continue

                # Create alarm
                alarm_params = {
                    "AlarmName": alarm_name,
                    "AlarmDescription": alarm_config["description"],
                    "MetricName": alarm_config["metric_name"],
                    "Namespace": "AWS/CloudFront",
                    "Statistic": "Average",
                    "Dimensions": [{"Name": "DistributionId", "Value": distribution_id}],
                    "Period": 300,
                    "EvaluationPeriods": 2,
                    "Threshold": alarm_config["threshold"],
                    "ComparisonOperator": alarm_config["comparison"],
                    "TreatMissingData": "notBreaching",
                }

                # Add SNS action if topic ARN is provided
                if sns_topic_arn:
                    alarm_params["AlarmActions"] = [sns_topic_arn]

                cw_client.put_metric_alarm(**alarm_params)
                result["alarms_created"].append(alarm_name)

            except Exception as e:
                error_msg = f"Error creating alarm {alarm_name}: {str(e)}"
                result["errors"].append(error_msg)

    except Exception as e:
        result["errors"].append(f"Error setting up alarms: {str(e)}")

    return result


def _remove_cloudfront_alarms(
    aws_auth: AWSAuth, distribution_id: str, distribution_domain: str, region: str, dry_run: bool
) -> Dict[str, Any]:
    """Remove CloudWatch alarms for a CloudFront distribution."""

    result = {
        "distribution_id": distribution_id,
        "distribution_domain": distribution_domain,
        "alarms_removed": [],
        "alarms_not_found": [],
        "errors": [],
    }

    try:
        cw_client = aws_auth.get_client("cloudwatch", region_name=region)

        # Define alarm names to remove
        alarm_names = [
            f"CloudFront-{distribution_id}-HighErrorRate",
            f"CloudFront-{distribution_id}-HighOriginLatency",
            f"CloudFront-{distribution_id}-LowCacheHitRate",
        ]

        for alarm_name in alarm_names:
            try:
                # Check if alarm exists
                existing_alarms = cw_client.describe_alarms(AlarmNames=[alarm_name])
                if not existing_alarms["MetricAlarms"]:
                    result["alarms_not_found"].append(alarm_name)
                    continue

                if dry_run:
                    result["alarms_removed"].append(f"[DRY RUN] {alarm_name}")
                    continue

                # Remove the alarm
                cw_client.delete_alarms(AlarmNames=[alarm_name])
                result["alarms_removed"].append(alarm_name)

            except Exception as e:
                error_msg = f"Error removing alarm {alarm_name}: {str(e)}"
                result["errors"].append(error_msg)

    except Exception as e:
        result["errors"].append(f"Error removing alarms: {str(e)}")

    return result


def _display_update_results(config: Config, update_results: Dict[str, Any], dry_run: bool) -> None:
    """Display CloudFront update results."""

    # Main summary
    summary_display = {
        "Total Distributions": update_results["total_distributions"],
        "Updated" if not dry_run else "Would Update": (
            update_results["updated_count"] if not dry_run else update_results["would_update_count"]
        ),
        "Errors": update_results["error_count"],
        "CloudFormation Managed": update_results["cf_managed_count"],
        "Alarms Created": update_results["alarms_created"],
        "Alarms Removed": update_results["alarms_removed"],
        "Alarm Errors": update_results["alarm_errors"],
        "Processing Timestamp": update_results["timestamp"],
    }

    print_output(summary_display, output_format=config.aws_output_format, title="CloudFront Update Summary")

    # Show CloudFormation managed distributions that need updates
    cf_managed_to_update = [
        r
        for r in update_results["results"]
        if r["stack_name"] and (not r["logging_enabled"] or r.get("would_update", False))
    ]

    if cf_managed_to_update:
        cf_data = []
        for dist in cf_managed_to_update:
            cf_data.append(
                {
                    "Distribution ID": dist["id"],
                    "Domain": dist["domain"],
                    "Stack Name": dist["stack_name"],
                    "Current Logging": "Enabled" if dist["logging_enabled"] else "Disabled",
                    "Current Bucket": dist.get("current_bucket", ""),
                    "Aliases": ", ".join(dist.get("aliases", [])[:2])
                    + ("..." if len(dist.get("aliases", [])) > 2 else ""),
                }
            )

        print_output(
            cf_data,
            output_format=config.aws_output_format,
            title="CloudFormation Managed Distributions Requiring Updates",
        )
