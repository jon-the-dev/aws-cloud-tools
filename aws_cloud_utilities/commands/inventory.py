"""AWS resource inventory and discovery commands."""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
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


@click.group(name="inventory")
def inventory_group():
    """AWS resource inventory and discovery commands."""
    pass


@inventory_group.command(name="scan")
@click.option("--output-dir", help="Directory to save inventory files (default: ./inventory_<account_id>_<timestamp>)")
@click.option("--services", help="Comma-separated list of services to scan (default: all supported services)")
@click.option("--regions", help="Comma-separated list of regions to scan (default: all regions)")
@click.option("--format", type=click.Choice(["json", "yaml"]), default="json", help="Output format for saved files")
@click.option(
    "--include-tags", is_flag=True, help="Include resource tags where available (slower but more comprehensive)"
)
@click.option("--parallel-regions", type=int, help="Number of regions to process in parallel (default: from config)")
@click.pass_context
def scan(
    ctx: click.Context,
    output_dir: Optional[str],
    services: Optional[str],
    regions: Optional[str],
    format: str,
    include_tags: bool,
    parallel_regions: Optional[int],
) -> None:
    """Comprehensive AWS resource inventory scan across services and regions."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        account_id = aws_auth.get_account_id()
        timestamp = get_detailed_timestamp()

        # Determine output directory
        if not output_dir:
            output_dir = f"./inventory_{account_id}_{timestamp}"

        output_path = Path(output_dir)
        ensure_directory(output_path)

        console.print(f"[blue]Starting comprehensive AWS inventory scan for account {account_id}[/blue]")
        console.print(f"[dim]Output directory: {output_path.absolute()}[/dim]")

        # Determine regions to scan
        if regions:
            target_regions = [r.strip() for r in regions.split(",")]
        else:
            target_regions = aws_auth.get_available_regions("ec2")

        # Determine services to scan
        if services:
            target_services = [s.strip() for s in services.split(",")]
            # Validate services
            supported_services = _get_supported_services()
            invalid_services = [s for s in target_services if s not in supported_services]
            if invalid_services:
                console.print(f"[yellow]Warning: Unsupported services will be skipped: {invalid_services}[/yellow]")
                target_services = [s for s in target_services if s in supported_services]
        else:
            target_services = list(_get_supported_services().keys())

        console.print(f"[dim]Scanning {len(target_services)} services across {len(target_regions)} regions[/dim]")

        # Set up parallel processing
        max_workers = parallel_regions or config.workers

        # Initialize scan summary
        scan_summary = {
            "account_id": account_id,
            "scan_timestamp": datetime.now().isoformat(),
            "regions_scanned": target_regions,
            "services_scanned": target_services,
            "include_tags": include_tags,
            "output_format": format,
            "total_resources": 0,
            "services_summary": {},
            "regions_summary": {},
            "errors": [],
        }

        # Execute comprehensive scan
        all_resources = _execute_comprehensive_scan(
            aws_auth, target_services, target_regions, output_path, format, include_tags, max_workers, scan_summary
        )

        # Save scan summary
        summary_file = output_path / f"scan_summary_{account_id}_{timestamp}.json"
        save_to_file(scan_summary, summary_file, "json")

        # Display summary
        _display_scan_summary(config, scan_summary, output_path)

        console.print(f"\n[green]✅ AWS inventory scan completed successfully![/green]")
        console.print(f"[dim]Files saved to: {output_path.absolute()}[/dim]")

    except Exception as e:
        console.print(f"[red]Error during inventory scan:[/red] {e}")
        raise click.Abort()


@inventory_group.command(name="workspaces")
@click.option("--region", help="AWS region to scan for WorkSpaces (default: current region)")
@click.option("--output-file", help="Output file for WorkSpaces report (supports .csv, .json, .yaml)")
@click.option("--include-metrics", is_flag=True, help="Include CloudWatch metrics for each WorkSpace (slower)")
@click.option("--lookback-days", type=int, default=30, help="Number of days to look back for metrics")
@click.option("--metric-names", default="Available", help="Comma-separated list of CloudWatch metrics to collect")
@click.pass_context
def workspaces(
    ctx: click.Context,
    region: Optional[str],
    output_file: Optional[str],
    include_metrics: bool,
    lookback_days: int,
    metric_names: str,
) -> None:
    """Generate comprehensive WorkSpaces inventory report with optional metrics."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        account_id = aws_auth.get_account_id()
        timestamp = get_timestamp()

        console.print(f"[blue]Scanning WorkSpaces in region {target_region}[/blue]")

        # Get WorkSpaces client
        workspaces_client = aws_auth.get_client("workspaces", region_name=target_region)

        # Get all WorkSpaces
        console.print("[dim]Retrieving WorkSpaces...[/dim]")
        workspaces_data = _get_all_workspaces(workspaces_client)

        if not workspaces_data:
            console.print("[yellow]No WorkSpaces found in the specified region[/yellow]")
            return

        console.print(f"[dim]Found {len(workspaces_data)} WorkSpaces[/dim]")

        # Enrich with tags and metrics if requested
        enriched_workspaces = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing WorkSpaces...", total=len(workspaces_data))

            for ws in workspaces_data:
                workspace_id = ws.get("WorkspaceId", "")

                # Get tags
                try:
                    tags = _get_workspace_tags(workspaces_client, workspace_id)
                    ws["Tags"] = tags
                except Exception as e:
                    logger.debug(f"Could not get tags for WorkSpace {workspace_id}: {e}")
                    ws["Tags"] = {}

                # Get metrics if requested
                if include_metrics:
                    try:
                        metrics = _get_workspace_metrics(
                            aws_auth, target_region, workspace_id, metric_names.split(","), lookback_days
                        )
                        ws["Metrics"] = metrics
                    except Exception as e:
                        logger.debug(f"Could not get metrics for WorkSpace {workspace_id}: {e}")
                        ws["Metrics"] = {}

                enriched_workspaces.append(ws)
                progress.update(task, advance=1, description=f"Processing: {workspace_id}")

        # Format for output
        formatted_workspaces = []
        for ws in enriched_workspaces:
            formatted_ws = {
                "WorkSpace ID": ws.get("WorkspaceId", ""),
                "Directory ID": ws.get("DirectoryId", ""),
                "User Name": ws.get("UserName", ""),
                "State": ws.get("State", ""),
                "Bundle ID": ws.get("BundleId", ""),
                "Computer Name": ws.get("ComputerName", ""),
                "IP Address": ws.get("IpAddress", ""),
                "Root Volume Encrypted": "Yes" if ws.get("RootVolumeEncryptionEnabled") else "No",
                "User Volume Encrypted": "Yes" if ws.get("UserVolumeEncryptionEnabled") else "No",
                "Volume Encryption Key": ws.get("VolumeEncryptionKey", ""),
                "Tags": ws.get("Tags", {}),
            }

            # Add metrics if included
            if include_metrics and "Metrics" in ws:
                for metric_name, value in ws["Metrics"].items():
                    formatted_ws[f"{metric_name} Metric"] = value

            formatted_workspaces.append(formatted_ws)

        # Display results
        print_output(
            formatted_workspaces,
            output_format=config.aws_output_format,
            title=f"WorkSpaces Inventory - {target_region}",
        )

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "csv"

            # Add timestamp and account ID to filename
            stem = output_path.stem
            new_filename = f"{stem}_{account_id}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(formatted_workspaces, output_path, file_format)
            console.print(f"[green]WorkSpaces report saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error generating WorkSpaces inventory:[/red] {e}")
        raise click.Abort()


@inventory_group.command(name="services")
@click.pass_context
def services(ctx: click.Context) -> None:
    """List all supported services for inventory scanning."""
    config: Config = ctx.obj["config"]

    supported_services = _get_supported_services()

    services_data = []
    for service, methods in supported_services.items():
        services_data.append(
            {"Service": service, "Methods": len(methods), "Description": _get_service_description(service)}
        )

    print_output(
        services_data,
        output_format=config.aws_output_format,
        title=f"Supported Services for Inventory ({len(services_data)} total)",
    )


def _get_supported_services() -> Dict[str, List[Tuple[str, str]]]:
    """Get the comprehensive list of supported services and their methods."""
    return {
        "acm": [("list_certificates", "CertificateSummaryList")],
        "autoscaling": [
            ("describe_auto_scaling_groups", "AutoScalingGroups"),
            ("describe_launch_configurations", "LaunchConfigurations"),
            ("describe_auto_scaling_instances", "AutoScalingInstances"),
        ],
        "athena": [("list_data_catalogs", "DataCatalogsSummary")],
        "appstream": [
            ("describe_fleets", "Fleets"),
            ("describe_images", "Images"),
            ("describe_stacks", "Stacks"),
        ],
        "config": [
            ("describe_config_rules", "ConfigRules"),
            ("describe_configuration_aggregators", "ConfigurationAggregators"),
            ("list_resource_evaluations", "ResourceEvaluations"),
        ],
        "backup": [
            ("list_backup_plans", "BackupPlansList"),
            ("list_backup_vaults", "BackupVaultList"),
            ("list_backup_jobs", "BackupJobs"),
        ],
        "cloudfront": [
            ("list_distributions", "DistributionList"),
            ("list_cloud_front_origin_access_identities", "CloudFrontOriginAccessIdentityList"),
        ],
        "codedeploy": [
            ("list_applications", "Applications"),
            ("list_deployments", "Deployments"),
        ],
        "ec2": [
            ("describe_instances", "Reservations"),
            ("describe_security_groups", "SecurityGroups"),
            ("describe_vpcs", "Vpcs"),
            ("describe_volumes", "Volumes"),
            ("describe_subnets", "Subnets"),
            ("describe_network_interfaces", "NetworkInterfaces"),
            ("describe_addresses", "Addresses"),
        ],
        "ecr": [("describe_repositories", "Repositories")],
        "efs": [("describe_file_systems", "FileSystems")],
        "eks": [("list_clusters", "Clusters")],
        "elasticache": [("describe_cache_clusters", "CacheClusters")],
        "elasticbeanstalk": [("describe_environments", "Environments")],
        "elb": [("describe_load_balancers", "LoadBalancerDescriptions")],
        "elbv2": [("describe_load_balancers", "LoadBalancers")],
        "es": [("describe_reserved_elasticsearch_instances", "ReservedElasticsearchInstances")],
        "lambda": [("list_functions", "Functions")],
        "rds": [
            ("describe_db_instances", "DBInstances"),
            ("describe_db_snapshots", "DBSnapshots"),
            ("describe_db_subnet_groups", "DBSubnetGroups"),
            ("describe_db_clusters", "DBClusters"),
        ],
        "s3": [("list_buckets", "Buckets")],
        "secretsmanager": [("list_secrets", "SecretList")],
        "sagemaker": [
            ("list_clusters", "ClusterSummaries"),
            ("list_endpoints", "Endpoints"),
            ("list_notebook_instances", "NotebookInstances"),
        ],
        "sns": [("list_topics", "Topics")],
        "sqs": [("list_queues", "QueueUrls")],
        "cloudformation": [("describe_stacks", "Stacks")],
        "cloudwatch": [("describe_alarms", "MetricAlarms")],
        "iam": [
            ("list_users", "Users"),
            ("list_roles", "Roles"),
            ("list_policies", "Policies"),
        ],
        "route53": [("list_hosted_zones", "HostedZones")],
        "route53domains": [("list_domains", "Domains")],
        "dynamodb": [
            ("list_tables", "TableNames"),
            ("list_backups", "BackupSummaries"),
        ],
        "ecs": [("list_clusters", "ClusterArns")],
        "workspaces": [("describe_workspaces", "Workspaces")],
        "fsx": [("describe_file_systems", "FileSystems")],
        "glacier": [("list_vaults", "VaultList")],
        "guardduty": [("list_detectors", "DetectorIds")],
        "redshift": [("describe_clusters", "Clusters")],
        "network-firewall": [("list_firewalls", "Firewalls")],
        "apigatewayv2": [("get_apis", "Items")],
        "ssm": [("get_parameters_by_path", "Parameters")],
        "kms": [("list_keys", "Keys")],
        "cloudtrail": [("describe_trails", "trailList")],
        "codebuild": [("list_projects", "Projects")],
        "waf": [("list_web_acls", "WebACLs")],
    }


def _get_service_description(service: str) -> str:
    """Get a human-readable description for a service."""
    descriptions = {
        "acm": "AWS Certificate Manager",
        "autoscaling": "Auto Scaling Groups",
        "athena": "Amazon Athena",
        "appstream": "Amazon AppStream 2.0",
        "config": "AWS Config",
        "backup": "AWS Backup",
        "cloudfront": "Amazon CloudFront",
        "codedeploy": "AWS CodeDeploy",
        "ec2": "Amazon EC2",
        "ecr": "Amazon ECR",
        "efs": "Amazon EFS",
        "eks": "Amazon EKS",
        "elasticache": "Amazon ElastiCache",
        "elasticbeanstalk": "AWS Elastic Beanstalk",
        "elb": "Elastic Load Balancing (Classic)",
        "elbv2": "Elastic Load Balancing (v2)",
        "es": "Amazon Elasticsearch Service",
        "lambda": "AWS Lambda",
        "rds": "Amazon RDS",
        "s3": "Amazon S3",
        "secretsmanager": "AWS Secrets Manager",
        "sagemaker": "Amazon SageMaker",
        "sns": "Amazon SNS",
        "sqs": "Amazon SQS",
        "cloudformation": "AWS CloudFormation",
        "cloudwatch": "Amazon CloudWatch",
        "iam": "AWS IAM",
        "route53": "Amazon Route 53",
        "route53domains": "Route 53 Domains",
        "dynamodb": "Amazon DynamoDB",
        "ecs": "Amazon ECS",
        "workspaces": "Amazon WorkSpaces",
        "fsx": "Amazon FSx",
        "glacier": "Amazon S3 Glacier",
        "guardduty": "Amazon GuardDuty",
        "redshift": "Amazon Redshift",
        "network-firewall": "AWS Network Firewall",
        "apigatewayv2": "Amazon API Gateway v2",
        "ssm": "AWS Systems Manager",
        "kms": "AWS KMS",
        "cloudtrail": "AWS CloudTrail",
        "codebuild": "AWS CodeBuild",
        "waf": "AWS WAF",
    }


def _execute_comprehensive_scan(
    aws_auth: AWSAuth,
    services: List[str],
    regions: List[str],
    output_path: Path,
    format: str,
    include_tags: bool,
    max_workers: int,
    scan_summary: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """Execute comprehensive inventory scan across services and regions."""

    supported_services = _get_supported_services()
    all_resources = {}

    # Create tasks for parallel execution
    scan_tasks = []
    for service in services:
        if service not in supported_services:
            continue

        for region in regions:
            for method, key in supported_services[service]:
                scan_tasks.append((service, region, method, key))

    console.print(f"[dim]Executing {len(scan_tasks)} scan tasks across {max_workers} workers[/dim]")

    def scan_service_region(task_data: Tuple[str, str, str, str]) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Scan a specific service in a specific region."""
        service, region, method, key = task_data

        try:
            client = aws_auth.get_client(service, region_name=region)

            # Handle different pagination patterns
            if hasattr(client, "get_paginator"):
                try:
                    paginator = client.get_paginator(method)
                    resources = []
                    for page in paginator.paginate():
                        resources.extend(page.get(key, []))
                except Exception:
                    # Fallback to direct method call
                    resources = _handle_non_paginated_service(client, method, key, service)
            else:
                resources = _handle_non_paginated_service(client, method, key, service)

            # Enrich with tags if requested and supported
            if include_tags and resources:
                resources = _enrich_with_tags(client, resources, service)

            # Save individual service/region file
            if resources:
                filename = f"{aws_auth.get_account_id()}-{service}-{region}-{method}-{key}.{format}"
                file_path = output_path / filename
                save_to_file(resources, file_path, format)

            return service, region, resources

        except Exception as e:
            logger.warning(f"Error scanning {service} in {region}: {e}")
            scan_summary["errors"].append(f"{service}/{region}: {str(e)}")
            return service, region, []

    # Execute scans in parallel
    results = parallel_execute(
        scan_service_region,
        scan_tasks,
        max_workers=max_workers,
        show_progress=True,
        description="Scanning AWS resources",
    )

    # Process results
    for service, region, resources in results:
        if service not in all_resources:
            all_resources[service] = []
        all_resources[service].extend(resources)

        # Update summary
        if service not in scan_summary["services_summary"]:
            scan_summary["services_summary"][service] = 0
        if region not in scan_summary["regions_summary"]:
            scan_summary["regions_summary"][region] = 0

        resource_count = len(resources)
        scan_summary["services_summary"][service] += resource_count
        scan_summary["regions_summary"][region] += resource_count
        scan_summary["total_resources"] += resource_count

    return all_resources


def _handle_non_paginated_service(client, method_name: str, key: str, service: str) -> List[Dict[str, Any]]:
    """Handle services that don't support pagination."""
    method = getattr(client, method_name)
    params = {}

    # Special handling for services that require specific parameters
    if service == "ssm" and method_name == "get_parameters_by_path":
        params["Path"] = "/"

    resources = []
    while True:
        try:
            response = method(**params)
            resources.extend(response.get(key, []))

            if "NextToken" in response:
                params["NextToken"] = response["NextToken"]
            else:
                break
        except Exception as e:
            logger.debug(f"Error in non-paginated service {service}.{method_name}: {e}")
            break

    return resources


def _enrich_with_tags(client, resources: List[Dict[str, Any]], service: str) -> List[Dict[str, Any]]:
    """Enrich resources with tags where supported."""
    # Only enrich for services that commonly support tagging
    tagging_services = {
        "ec2": ["Instances", "SecurityGroups", "Vpcs", "Volumes", "Subnets"],
        "s3": ["Buckets"],
        "rds": ["DBInstances", "DBClusters"],
        "lambda": ["Functions"],
        "sns": ["Topics"],
    }

    if service not in tagging_services:
        return resources

    # This is a simplified implementation - in practice, each service
    # has different ways to get tags
    try:
        for resource in resources:
            if service == "ec2" and "InstanceId" in resource:
                # EC2 instances already have tags in the response
                continue
            elif service == "sns" and "TopicArn" in resource:
                try:
                    response = client.list_tags_for_resource(ResourceArn=resource["TopicArn"])
                    resource["Tags"] = response.get("Tags", [])
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"Error enriching tags for {service}: {e}")

    return resources


def _display_scan_summary(config: Config, scan_summary: Dict[str, Any], output_path: Path) -> None:
    """Display a comprehensive scan summary."""

    # Main summary
    summary_display = {
        "Account ID": scan_summary["account_id"],
        "Scan Timestamp": scan_summary["scan_timestamp"],
        "Total Resources": scan_summary["total_resources"],
        "Services Scanned": len(scan_summary["services_scanned"]),
        "Regions Scanned": len(scan_summary["regions_scanned"]),
        "Include Tags": "Yes" if scan_summary["include_tags"] else "No",
        "Output Format": scan_summary["output_format"].upper(),
        "Output Directory": str(output_path.absolute()),
        "Errors": len(scan_summary["errors"]),
    }

    print_output(summary_display, output_format=config.aws_output_format, title="AWS Inventory Scan Summary")

    # Services summary
    if scan_summary["services_summary"]:
        services_data = [
            {"Service": service, "Resources": count}
            for service, count in sorted(scan_summary["services_summary"].items(), key=lambda x: x[1], reverse=True)
            if count > 0
        ]

        if services_data:
            print_output(services_data, output_format=config.aws_output_format, title="Resources by Service")

    # Show errors if any
    if scan_summary["errors"]:
        console.print(f"\n[yellow]Errors encountered ({len(scan_summary['errors'])}):[/yellow]")
        for error in scan_summary["errors"][:10]:  # Show first 10 errors
            console.print(f"  [dim]• {error}[/dim]")
        if len(scan_summary["errors"]) > 10:
            console.print(f"  [dim]... and {len(scan_summary['errors']) - 10} more errors[/dim]")


def _get_all_workspaces(client) -> List[Dict[str, Any]]:
    """Get all WorkSpaces using pagination."""
    workspaces = []
    next_token = None

    while True:
        params = {}
        if next_token:
            params["NextToken"] = next_token

        response = client.describe_workspaces(**params)
        workspaces.extend(response.get("Workspaces", []))

        next_token = response.get("NextToken")
        if not next_token:
            break

    return workspaces


def _get_workspace_tags(client, workspace_id: str) -> Dict[str, str]:
    """Get tags for a specific WorkSpace."""
    try:
        response = client.describe_tags(ResourceId=workspace_id)
        tag_list = response.get("TagList", [])
        return {tag["Key"]: tag["Value"] for tag in tag_list}
    except Exception as e:
        logger.debug(f"Could not get tags for WorkSpace {workspace_id}: {e}")
        return {}


def _get_workspace_metrics(
    aws_auth: AWSAuth, region: str, workspace_id: str, metric_names: List[str], lookback_days: int
) -> Dict[str, float]:
    """Get CloudWatch metrics for a WorkSpace."""
    try:
        cloudwatch_client = aws_auth.get_client("cloudwatch", region_name=region)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=lookback_days)

        metrics = {}

        for metric_name in metric_names:
            metric_name = metric_name.strip()

            try:
                query_id = f"m_{workspace_id}_{metric_name}"

                metric_query = {
                    "Id": query_id,
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/WorkSpaces",
                            "MetricName": metric_name,
                            "Dimensions": [{"Name": "WorkspaceId", "Value": workspace_id}],
                        },
                        "Period": 86400,  # 1 day
                        "Stat": "Sum",
                    },
                    "ReturnData": True,
                }

                response = cloudwatch_client.get_metric_data(
                    MetricDataQueries=[metric_query], StartTime=start_time, EndTime=end_time
                )

                results = response.get("MetricDataResults", [])
                if results:
                    values = results[0].get("Values", [])
                    metrics[metric_name] = sum(values) if values else 0
                else:
                    metrics[metric_name] = 0

            except Exception as e:
                logger.debug(f"Could not get metric {metric_name} for WorkSpace {workspace_id}: {e}")
                metrics[metric_name] = 0

        return metrics

    except Exception as e:
        logger.debug(f"Could not get metrics for WorkSpace {workspace_id}: {e}")
        return {}


@inventory_group.command(name="download-all")
@click.option(
    "--output-dir", help="Directory to save all inventory files (default: ./full_inventory_<account_id>_<timestamp>)"
)
@click.option("--services", help="Comma-separated list of services to include (default: all supported services)")
@click.option("--regions", help="Comma-separated list of regions to scan (default: all regions)")
@click.option("--format", type=click.Choice(["json", "yaml"]), default="json", help="Output format for saved files")
@click.option(
    "--include-tags", is_flag=True, help="Include resource tags where available (slower but more comprehensive)"
)
@click.option("--include-cloudformation", is_flag=True, help="Include CloudFormation stack backups")
@click.option("--include-workspaces-metrics", is_flag=True, help="Include WorkSpaces CloudWatch metrics")
@click.option("--parallel-regions", type=int, help="Number of regions to process in parallel (default: from config)")
@click.pass_context
def download_all(
    ctx: click.Context,
    output_dir: Optional[str],
    services: Optional[str],
    regions: Optional[str],
    format: str,
    include_tags: bool,
    include_cloudformation: bool,
    include_workspaces_metrics: bool,
    parallel_regions: Optional[int],
) -> None:
    """Download comprehensive inventory of all AWS resources including optional CloudFormation backups."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        account_id = aws_auth.get_account_id()
        timestamp = get_detailed_timestamp()

        # Determine output directory
        if not output_dir:
            output_dir = f"./full_inventory_{account_id}_{timestamp}"

        output_path = Path(output_dir)
        ensure_directory(output_path)

        console.print(f"[blue]Starting comprehensive AWS inventory download for account {account_id}[/blue]")
        console.print(f"[dim]Output directory: {output_path.absolute()}[/dim]")

        # Determine regions to scan
        if regions:
            target_regions = [r.strip() for r in regions.split(",")]
        else:
            target_regions = aws_auth.get_available_regions("ec2")

        # Determine services to scan
        if services:
            target_services = [s.strip() for s in services.split(",")]
            # Validate services
            supported_services = _get_supported_services()
            invalid_services = [s for s in target_services if s not in supported_services]
            if invalid_services:
                console.print(f"[yellow]Warning: Unsupported services will be skipped: {invalid_services}[/yellow]")
                target_services = [s for s in target_services if s in supported_services]
        else:
            target_services = list(_get_supported_services().keys())

        console.print(
            f"[dim]Downloading inventory for {len(target_services)} services across {len(target_regions)} regions[/dim]"
        )

        # Set up parallel processing
        max_workers = parallel_regions or config.workers

        # Initialize comprehensive download summary
        download_summary = {
            "account_id": account_id,
            "download_timestamp": datetime.now().isoformat(),
            "regions_scanned": target_regions,
            "services_scanned": target_services,
            "include_tags": include_tags,
            "include_cloudformation": include_cloudformation,
            "include_workspaces_metrics": include_workspaces_metrics,
            "output_format": format,
            "total_resources": 0,
            "cloudformation_stacks": 0,
            "workspaces_processed": 0,
            "services_summary": {},
            "regions_summary": {},
            "errors": [],
        }

        # Execute comprehensive resource scan
        console.print("[yellow]Phase 1: Scanning AWS resources...[/yellow]")
        all_resources = _execute_comprehensive_scan(
            aws_auth,
            target_services,
            target_regions,
            output_path / "resources",
            format,
            include_tags,
            max_workers,
            download_summary,
        )

        # Execute CloudFormation backup if requested
        if include_cloudformation:
            console.print("[yellow]Phase 2: Backing up CloudFormation stacks...[/yellow]")
            cfn_summary = _execute_cloudformation_download(
                aws_auth, target_regions, output_path / "cloudformation", max_workers, format, download_summary
            )
            download_summary["cloudformation_stacks"] = cfn_summary.get("total_stacks", 0)

        # Execute WorkSpaces inventory with metrics if requested
        if include_workspaces_metrics:
            console.print("[yellow]Phase 3: Collecting WorkSpaces with metrics...[/yellow]")
            workspaces_summary = _execute_workspaces_download(
                aws_auth, target_regions, output_path / "workspaces", format, download_summary
            )
            download_summary["workspaces_processed"] = workspaces_summary.get("total_workspaces", 0)

        # Save comprehensive download summary
        summary_file = output_path / f"full_inventory_summary_{account_id}_{timestamp}.json"
        save_to_file(download_summary, summary_file, "json")

        # Display comprehensive summary
        _display_comprehensive_download_summary(config, download_summary, output_path)

        console.print(f"\n[green]✅ Comprehensive AWS inventory download completed successfully![/green]")
        console.print(f"[dim]Files saved to: {output_path.absolute()}[/dim]")

    except Exception as e:
        console.print(f"[red]Error during comprehensive inventory download:[/red] {e}")
        raise click.Abort()


def _execute_cloudformation_backup(
    aws_auth: AWSAuth,
    regions: List[str],
    output_path: Path,
    stack_statuses: List[str],
    max_workers: int,
    parallel_stacks: int,
    backup_summary: Dict[str, Any],
) -> None:
    """Execute CloudFormation backup across regions."""

    def backup_region(region: str) -> Tuple[str, int, int, int, List[str]]:
        """Backup all stacks in a specific region."""
        region_errors = []
        stacks_count = 0
        templates_count = 0
        parameters_count = 0

        try:
            cfn_client = aws_auth.get_client("cloudformation", region_name=region)

            # Get all stacks in the region
            stacks = []
            paginator = cfn_client.get_paginator("describe_stacks")

            for page in paginator.paginate():
                for stack in page.get("Stacks", []):
                    if stack.get("StackStatus") in stack_statuses:
                        stacks.append(stack)

            if not stacks:
                logger.debug(f"No stacks found in region {region}")
                return region, 0, 0, 0, []

            stacks_count = len(stacks)

            # Create region directory
            region_dir = output_path / region
            ensure_directory(region_dir)

            # Backup stacks in parallel within the region
            def backup_single_stack(stack: Dict[str, Any]) -> Tuple[bool, bool]:
                """Backup a single stack's template and parameters."""
                stack_name = stack.get("StackName")
                template_saved = False
                parameters_saved = False

                try:
                    # Define file paths
                    template_file = region_dir / f"{stack_name}.json"
                    params_file = region_dir / f"{stack_name}-parameters.json"

                    # Check if backup already exists
                    parameters = stack.get("Parameters", [])
                    if template_file.exists() and (not parameters or params_file.exists()):
                        logger.debug(f"Stack {stack_name} in region {region} already backed up")
                        return True, bool(parameters)

                    # Get stack template
                    try:
                        template_response = cfn_client.get_template(StackName=stack_name)
                        template_body = template_response.get("TemplateBody", "")

                        if template_body:
                            # Ensure template is properly formatted JSON
                            if isinstance(template_body, dict):
                                template_str = json.dumps(template_body, indent=2, default=str)
                            else:
                                template_str = template_body

                            # Save template
                            with open(template_file, "w", encoding="utf-8") as f:
                                f.write(template_str)
                            template_saved = True
                            logger.debug(f"Template saved for stack {stack_name}")

                    except Exception as e:
                        region_errors.append(f"Template for {stack_name}: {str(e)}")

                    # Save parameters if they exist
                    if parameters:
                        try:
                            params_dict = {
                                param.get("ParameterKey"): param.get("ParameterValue") for param in parameters
                            }

                            with open(params_file, "w", encoding="utf-8") as f:
                                json.dump(params_dict, f, indent=2, default=str)
                            parameters_saved = True
                            logger.debug(f"Parameters saved for stack {stack_name}")

                        except Exception as e:
                            region_errors.append(f"Parameters for {stack_name}: {str(e)}")

                    return template_saved, parameters_saved

                except Exception as e:
                    region_errors.append(f"Stack {stack_name}: {str(e)}")
                    return False, False

            # Execute stack backups in parallel
            stack_results = parallel_execute(
                backup_single_stack, stacks, max_workers=parallel_stacks, show_progress=False
            )

            # Count results
            for template_saved, parameters_saved in stack_results:
                if template_saved:
                    templates_count += 1
                if parameters_saved:
                    parameters_count += 1

        except Exception as e:
            region_errors.append(f"Region {region}: {str(e)}")

        return region, stacks_count, templates_count, parameters_count, region_errors

    # Execute region backups in parallel
    console.print(f"[dim]Processing {len(regions)} regions with {max_workers} workers[/dim]")

    region_results = parallel_execute(
        backup_region,
        regions,
        max_workers=max_workers,
        show_progress=True,
        description="Backing up CloudFormation stacks",
    )

    # Process results
    for region, stacks_count, templates_count, parameters_count, region_errors in region_results:
        backup_summary["regions_summary"][region] = {
            "stacks": stacks_count,
            "templates": templates_count,
            "parameters": parameters_count,
        }

        backup_summary["total_stacks"] += stacks_count
        backup_summary["total_templates"] += templates_count
        backup_summary["total_parameters"] += parameters_count
        backup_summary["errors"].extend(region_errors)


def _display_cloudformation_summary(config: Config, backup_summary: Dict[str, Any], output_path: Path) -> None:
    """Display CloudFormation backup summary."""

    # Main summary
    summary_display = {
        "Account ID": backup_summary["account_id"],
        "Backup Timestamp": backup_summary["backup_timestamp"],
        "Total Stacks": backup_summary["total_stacks"],
        "Total Templates": backup_summary["total_templates"],
        "Total Parameters": backup_summary["total_parameters"],
        "Regions Processed": len(backup_summary["regions_processed"]),
        "Stack Statuses": ", ".join(backup_summary["stack_statuses"]),
        "Output Directory": str(output_path.absolute()),
        "Errors": len(backup_summary["errors"]),
    }

    print_output(summary_display, output_format=config.aws_output_format, title="CloudFormation Backup Summary")

    # Regions summary
    if backup_summary["regions_summary"]:
        regions_data = []
        for region, stats in backup_summary["regions_summary"].items():
            if stats["stacks"] > 0:
                regions_data.append(
                    {
                        "Region": region,
                        "Stacks": stats["stacks"],
                        "Templates": stats["templates"],
                        "Parameters": stats["parameters"],
                    }
                )

        if regions_data:
            print_output(regions_data, output_format=config.aws_output_format, title="Backup by Region")

    # Show errors if any
    if download_summary["errors"]:
        console.print(f"\n[yellow]Errors encountered ({len(download_summary['errors'])}):[/yellow]")
        for error in download_summary["errors"][:10]:  # Show first 10 errors
            console.print(f"  [dim]• {error}[/dim]")
        if len(download_summary["errors"]) > 10:
            console.print(f"  [dim]... and {len(download_summary['errors']) - 10} more errors[/dim]")


def _execute_cloudformation_download(
    aws_auth: AWSAuth,
    regions: List[str],
    output_path: Path,
    max_workers: int,
    format: str,
    download_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute CloudFormation backup as part of comprehensive download."""
    ensure_directory(output_path)

    # Use the CloudFormation backup logic but with simplified status filtering
    stack_statuses = ["CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"]

    cfn_summary = {"total_stacks": 0, "total_templates": 0, "total_parameters": 0, "regions_summary": {}}

    def backup_region(region: str) -> Tuple[str, int, int, int]:
        """Backup CloudFormation stacks in a region."""
        stacks_count = 0
        templates_count = 0
        parameters_count = 0

        try:
            cfn_client = aws_auth.get_client("cloudformation", region_name=region)

            # Get all stacks in the region
            stacks = []
            paginator = cfn_client.get_paginator("describe_stacks")

            for page in paginator.paginate():
                for stack in page.get("Stacks", []):
                    if stack.get("StackStatus") in stack_statuses:
                        stacks.append(stack)

            if not stacks:
                return region, 0, 0, 0

            stacks_count = len(stacks)

            # Create region directory
            region_dir = output_path / region
            ensure_directory(region_dir)

            # Backup each stack
            for stack in stacks:
                stack_name = stack.get("StackName")

                try:
                    # Save template
                    template_file = region_dir / f"{stack_name}.{format}"
                    if not template_file.exists():
                        template_response = cfn_client.get_template(StackName=stack_name)
                        template_body = template_response.get("TemplateBody", "")

                        if template_body:
                            save_to_file(template_body, template_file, format)
                            templates_count += 1

                    # Save parameters if they exist
                    parameters = stack.get("Parameters", [])
                    if parameters:
                        params_file = region_dir / f"{stack_name}-parameters.{format}"
                        if not params_file.exists():
                            params_dict = {
                                param.get("ParameterKey"): param.get("ParameterValue") for param in parameters
                            }
                            save_to_file(params_dict, params_file, format)
                            parameters_count += 1

                except Exception as e:
                    download_summary["errors"].append(f"CloudFormation {stack_name} in {region}: {str(e)}")

        except Exception as e:
            download_summary["errors"].append(f"CloudFormation region {region}: {str(e)}")

        return region, stacks_count, templates_count, parameters_count

    # Execute CloudFormation backup in parallel
    region_results = parallel_execute(
        backup_region,
        regions,
        max_workers=max_workers,
        show_progress=True,
        description="Backing up CloudFormation stacks",
    )

    # Process results
    for region, stacks_count, templates_count, parameters_count in region_results:
        cfn_summary["regions_summary"][region] = {
            "stacks": stacks_count,
            "templates": templates_count,
            "parameters": parameters_count,
        }

        cfn_summary["total_stacks"] += stacks_count
        cfn_summary["total_templates"] += templates_count
        cfn_summary["total_parameters"] += parameters_count

    return cfn_summary


def _execute_workspaces_download(
    aws_auth: AWSAuth, regions: List[str], output_path: Path, format: str, download_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute WorkSpaces inventory with metrics as part of comprehensive download."""
    ensure_directory(output_path)

    workspaces_summary = {"total_workspaces": 0, "regions_summary": {}}

    def process_workspaces_region(region: str) -> Tuple[str, int]:
        """Process WorkSpaces in a region."""
        workspaces_count = 0

        try:
            workspaces_client = aws_auth.get_client("workspaces", region_name=region)

            # Get all WorkSpaces
            workspaces_data = _get_all_workspaces(workspaces_client)

            if not workspaces_data:
                return region, 0

            workspaces_count = len(workspaces_data)

            # Enrich with tags and metrics
            enriched_workspaces = []
            for ws in workspaces_data:
                workspace_id = ws.get("WorkspaceId", "")

                # Get tags
                try:
                    tags = _get_workspace_tags(workspaces_client, workspace_id)
                    ws["Tags"] = tags
                except Exception:
                    ws["Tags"] = {}

                # Get basic metrics (last 7 days)
                try:
                    metrics = _get_workspace_metrics(aws_auth, region, workspace_id, ["Available"], 7)
                    ws["Metrics"] = metrics
                except Exception:
                    ws["Metrics"] = {}

                enriched_workspaces.append(ws)

            # Save WorkSpaces data for this region
            region_file = output_path / f"workspaces_{region}.{format}"
            save_to_file(enriched_workspaces, region_file, format)

        except Exception as e:
            download_summary["errors"].append(f"WorkSpaces region {region}: {str(e)}")

        return region, workspaces_count

    # Execute WorkSpaces processing in parallel
    region_results = parallel_execute(
        process_workspaces_region,
        regions,
        max_workers=4,  # Limit WorkSpaces processing to avoid rate limits
        show_progress=True,
        description="Processing WorkSpaces with metrics",
    )

    # Process results
    for region, workspaces_count in region_results:
        workspaces_summary["regions_summary"][region] = workspaces_count
        workspaces_summary["total_workspaces"] += workspaces_count

    return workspaces_summary


def _display_comprehensive_download_summary(
    config: Config, download_summary: Dict[str, Any], output_path: Path
) -> None:
    """Display comprehensive download summary."""

    # Main summary
    summary_display = {
        "Account ID": download_summary["account_id"],
        "Download Timestamp": download_summary["download_timestamp"],
        "Total Resources": download_summary["total_resources"],
        "CloudFormation Stacks": download_summary.get("cloudformation_stacks", 0),
        "WorkSpaces Processed": download_summary.get("workspaces_processed", 0),
        "Services Scanned": len(download_summary["services_scanned"]),
        "Regions Scanned": len(download_summary["regions_scanned"]),
        "Include Tags": "Yes" if download_summary["include_tags"] else "No",
        "Include CloudFormation": "Yes" if download_summary["include_cloudformation"] else "No",
        "Include WorkSpaces Metrics": "Yes" if download_summary["include_workspaces_metrics"] else "No",
        "Output Format": download_summary["output_format"].upper(),
        "Output Directory": str(output_path.absolute()),
        "Errors": len(download_summary["errors"]),
    }

    print_output(
        summary_display, output_format=config.aws_output_format, title="Comprehensive AWS Inventory Download Summary"
    )

    # Services summary (top 10)
    if download_summary["services_summary"]:
        services_data = [
            {"Service": service, "Resources": count}
            for service, count in sorted(download_summary["services_summary"].items(), key=lambda x: x[1], reverse=True)
            if count > 0
        ][
            :10
        ]  # Top 10 services

        if services_data:
            print_output(services_data, output_format=config.aws_output_format, title="Top Resources by Service")

    # Show errors if any
    if download_summary["errors"]:
        console.print(f"\n[yellow]Errors encountered ({len(download_summary['errors'])}):[/yellow]")
        for error in download_summary["errors"][:10]:  # Show first 10 errors
            console.print(f"  [dim]• {error}[/dim]")
        if len(download_summary["errors"]) > 10:
            console.print(f"  [dim]... and {len(download_summary['errors']) - 10} more errors[/dim]")
