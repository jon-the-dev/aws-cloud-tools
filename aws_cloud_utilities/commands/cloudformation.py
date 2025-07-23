"""AWS CloudFormation management and backup commands."""

import logging
import json
from datetime import datetime
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


@click.group(name="cloudformation")
def cloudformation_group():
    """AWS CloudFormation management and backup commands."""
    pass


@cloudformation_group.command(name="backup")
@click.option("--regions", help="Comma-separated list of regions to backup (default: all regions)")
@click.option(
    "--output-dir", help="Directory to save CloudFormation backups (default: ./cfn_backup_<account_id>_<timestamp>)"
)
@click.option(
    "--stack-status",
    multiple=True,
    default=["CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"],
    help="Stack statuses to include in backup (can be specified multiple times)",
)
@click.option("--parallel-regions", type=int, help="Number of regions to process in parallel (default: from config)")
@click.option("--parallel-stacks", type=int, default=2, help="Number of stacks to process in parallel per region")
@click.option(
    "--format", type=click.Choice(["json", "yaml"]), default="json", help="Output format for templates and parameters"
)
@click.pass_context
def backup(
    ctx: click.Context,
    regions: Optional[str],
    output_dir: Optional[str],
    stack_status: List[str],
    parallel_regions: Optional[int],
    parallel_stacks: int,
    format: str,
) -> None:
    """Backup CloudFormation stacks and templates across regions."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        account_id = aws_auth.get_account_id()
        timestamp = get_detailed_timestamp()

        # Determine output directory
        if not output_dir:
            output_dir = f"./cfn_backup_{account_id}_{timestamp}"

        output_path = Path(output_dir)
        ensure_directory(output_path)

        console.print(f"[blue]Starting CloudFormation backup for account {account_id}[/blue]")
        console.print(f"[dim]Output directory: {output_path.absolute()}[/dim]")

        # Determine regions to scan
        if regions:
            target_regions = [r.strip() for r in regions.split(",")]
        else:
            target_regions = aws_auth.get_available_regions("cloudformation")

        console.print(f"[dim]Backing up CloudFormation stacks across {len(target_regions)} regions[/dim]")

        # Set up parallel processing
        max_workers = parallel_regions or config.workers

        # Initialize backup summary
        backup_summary = {
            "account_id": account_id,
            "backup_timestamp": datetime.now().isoformat(),
            "regions_processed": target_regions,
            "stack_statuses": list(stack_status),
            "output_format": format,
            "total_stacks": 0,
            "total_templates": 0,
            "total_parameters": 0,
            "regions_summary": {},
            "errors": [],
        }

        # Execute CloudFormation backup
        _execute_cloudformation_backup(
            aws_auth, target_regions, output_path, stack_status, max_workers, parallel_stacks, backup_summary, format
        )

        # Save backup summary
        summary_file = output_path / f"backup_summary_{account_id}_{timestamp}.json"
        save_to_file(backup_summary, summary_file, "json")

        # Display summary
        _display_cloudformation_summary(config, backup_summary, output_path)

        console.print(f"\n[green]✅ CloudFormation backup completed successfully![/green]")
        console.print(f"[dim]Files saved to: {output_path.absolute()}[/dim]")

    except Exception as e:
        console.print(f"[red]Error during CloudFormation backup:[/red] {e}")
        raise click.Abort()


@cloudformation_group.command(name="list-stacks")
@click.option("--region", help="AWS region to list stacks from (default: current region)")
@click.option("--stack-status", multiple=True, help="Filter by stack status (can be specified multiple times)")
@click.option("--all-regions", is_flag=True, help="List stacks from all regions")
@click.pass_context
def list_stacks(ctx: click.Context, region: Optional[str], stack_status: List[str], all_regions: bool) -> None:
    """List CloudFormation stacks with details."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        if all_regions:
            target_regions = aws_auth.get_available_regions("cloudformation")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]

        all_stacks = []

        for target_region in target_regions:
            cfn_client = aws_auth.get_client("cloudformation", region_name=target_region)

            try:
                paginator = cfn_client.get_paginator("describe_stacks")

                for page in paginator.paginate():
                    for stack in page.get("Stacks", []):
                        # Filter by status if specified
                        if stack_status and stack.get("StackStatus") not in stack_status:
                            continue

                        all_stacks.append(
                            {
                                "Stack Name": stack.get("StackName", ""),
                                "Region": target_region,
                                "Status": stack.get("StackStatus", ""),
                                "Created": (
                                    stack.get("CreationTime", "").strftime("%Y-%m-%d %H:%M")
                                    if stack.get("CreationTime")
                                    else ""
                                ),
                                "Updated": (
                                    stack.get("LastUpdatedTime", "").strftime("%Y-%m-%d %H:%M")
                                    if stack.get("LastUpdatedTime")
                                    else ""
                                ),
                                "Description": (
                                    (stack.get("Description", "")[:50] + "...")
                                    if len(stack.get("Description", "")) > 50
                                    else stack.get("Description", "")
                                ),
                                "Parameters": len(stack.get("Parameters", [])),
                                "Outputs": len(stack.get("Outputs", [])),
                            }
                        )

            except Exception as e:
                logger.warning(f"Error listing stacks in region {target_region}: {e}")

        if all_stacks:
            print_output(
                all_stacks,
                output_format=config.aws_output_format,
                title=f"CloudFormation Stacks ({len(all_stacks)} found)",
            )
        else:
            console.print("[yellow]No CloudFormation stacks found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing CloudFormation stacks:[/red] {e}")
        raise click.Abort()


@cloudformation_group.command(name="stack-details")
@click.argument("stack_name")
@click.option("--region", help="AWS region where the stack is located (default: current region)")
@click.option("--show-template", is_flag=True, help="Show the stack template")
@click.option("--show-parameters", is_flag=True, help="Show stack parameters")
@click.option("--show-outputs", is_flag=True, help="Show stack outputs")
@click.pass_context
def stack_details(
    ctx: click.Context,
    stack_name: str,
    region: Optional[str],
    show_template: bool,
    show_parameters: bool,
    show_outputs: bool,
) -> None:
    """Get detailed information about a specific CloudFormation stack."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        cfn_client = aws_auth.get_client("cloudformation", region_name=target_region)

        # Get stack details
        try:
            response = cfn_client.describe_stacks(StackName=stack_name)
            stacks = response.get("Stacks", [])

            if not stacks:
                console.print(f"[red]Stack '{stack_name}' not found in region {target_region}[/red]")
                raise click.Abort()

            stack = stacks[0]

        except cfn_client.exceptions.ClientError as e:
            if "does not exist" in str(e):
                console.print(f"[red]Stack '{stack_name}' not found in region {target_region}[/red]")
            else:
                console.print(f"[red]Error retrieving stack details:[/red] {e}")
            raise click.Abort()

        # Display basic stack information
        stack_info = {
            "Stack Name": stack.get("StackName", ""),
            "Region": target_region,
            "Status": stack.get("StackStatus", ""),
            "Created": stack.get("CreationTime", "").strftime("%Y-%m-%d %H:%M:%S") if stack.get("CreationTime") else "",
            "Updated": (
                stack.get("LastUpdatedTime", "").strftime("%Y-%m-%d %H:%M:%S") if stack.get("LastUpdatedTime") else ""
            ),
            "Description": stack.get("Description", "Not set"),
            "Parameters Count": len(stack.get("Parameters", [])),
            "Outputs Count": len(stack.get("Outputs", [])),
            "Capabilities": ", ".join(stack.get("Capabilities", [])),
            "Rollback Configuration": "Enabled" if stack.get("RollbackConfiguration") else "Disabled",
        }

        print_output(
            stack_info, output_format=config.aws_output_format, title=f"CloudFormation Stack Details: {stack_name}"
        )

        # Show parameters if requested
        if show_parameters and stack.get("Parameters"):
            params_data = [
                {"Parameter Key": param.get("ParameterKey", ""), "Parameter Value": param.get("ParameterValue", "")}
                for param in stack.get("Parameters", [])
            ]
            print_output(params_data, output_format=config.aws_output_format, title="Stack Parameters")

        # Show outputs if requested
        if show_outputs and stack.get("Outputs"):
            outputs_data = [
                {
                    "Output Key": output.get("OutputKey", ""),
                    "Output Value": output.get("OutputValue", ""),
                    "Description": output.get("Description", ""),
                }
                for output in stack.get("Outputs", [])
            ]
            print_output(outputs_data, output_format=config.aws_output_format, title="Stack Outputs")

        # Show template if requested
        if show_template:
            try:
                template_response = cfn_client.get_template(StackName=stack_name)
                template_body = template_response.get("TemplateBody", {})

                console.print("\n[bold]Stack Template:[/bold]")
                if config.aws_output_format == "json":
                    console.print_json(json.dumps(template_body, indent=2, default=str))
                else:
                    console.print(json.dumps(template_body, indent=2, default=str))

            except Exception as e:
                console.print(f"[yellow]Could not retrieve template: {e}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting stack details:[/red] {e}")
        raise click.Abort()


def _execute_cloudformation_backup(
    aws_auth: AWSAuth,
    regions: List[str],
    output_path: Path,
    stack_statuses: List[str],
    max_workers: int,
    parallel_stacks: int,
    backup_summary: Dict[str, Any],
    format: str,
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
                    template_file = region_dir / f"{stack_name}.{format}"
                    params_file = region_dir / f"{stack_name}-parameters.{format}"

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
                            # Save template in requested format
                            save_to_file(template_body, template_file, format)
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

                            save_to_file(params_dict, params_file, format)
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
        "Output Format": backup_summary["output_format"].upper(),
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
    if backup_summary["errors"]:
        console.print(f"\n[yellow]Errors encountered ({len(backup_summary['errors'])}):[/yellow]")
        for error in backup_summary["errors"][:10]:  # Show first 10 errors
            console.print(f"  [dim]• {error}[/dim]")
        if len(backup_summary["errors"]) > 10:
            console.print(f"  [dim]... and {len(backup_summary['errors']) - 10} more errors[/dim]")
