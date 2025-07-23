"""Account management commands."""

import logging
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import click
from rich.console import Console

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import print_output, parallel_execute
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="account")
def account_group():
    """Account information and management commands."""
    pass


@account_group.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Get AWS account information."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Get caller identity
        caller_identity = aws_auth.get_caller_identity()

        # Get account alias (if available)
        try:
            iam_client = aws_auth.get_client("iam")
            aliases_response = iam_client.list_account_aliases()
            account_alias = aliases_response.get("AccountAliases", [])
            account_alias = account_alias[0] if account_alias else "Not set"
        except Exception as e:
            logger.debug(f"Could not get account alias: {e}")
            account_alias = "Not available"

        # Get account summary (if available)
        try:
            iam_client = aws_auth.get_client("iam")
            summary_response = iam_client.get_account_summary()
            summary_map = summary_response.get("SummaryMap", {})
        except Exception as e:
            logger.debug(f"Could not get account summary: {e}")
            summary_map = {}

        # Compile account information
        account_info = {
            "Account ID": caller_identity.get("Account", "Unknown"),
            "Account Alias": account_alias,
            "User/Role ARN": caller_identity.get("Arn", "Unknown"),
            "User ID": caller_identity.get("UserId", "Unknown"),
            "Current Region": config.aws_region or "Not set",
            "Profile": config.aws_profile or "default",
        }

        # Add IAM summary if available
        if summary_map:
            account_info.update(
                {
                    "Users": summary_map.get("Users", 0),
                    "Groups": summary_map.get("Groups", 0),
                    "Roles": summary_map.get("Roles", 0),
                    "Policies": summary_map.get("Policies", 0),
                    "MFA Devices": summary_map.get("MFADevices", 0),
                }
            )

        print_output(account_info, output_format=config.aws_output_format, title="AWS Account Information")

    except AWSError as e:
        console.print(f"[red]AWS Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error getting account information:[/red] {e}")
        raise click.Abort()


@account_group.command()
@click.pass_context
def contact_info(ctx: click.Context) -> None:
    """Get AWS account contact information."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        account_client = aws_auth.get_client("account")

        # Get primary contact information
        try:
            response = account_client.get_contact_information()
            contact_info = response.get("ContactInformation", {})

            primary_contact = {
                "Full Name": contact_info.get("FullName", "Not set"),
                "Company Name": contact_info.get("CompanyName", "Not set"),
                "Address Line 1": contact_info.get("AddressLine1", "Not set"),
                "Address Line 2": contact_info.get("AddressLine2", "Not set"),
                "City": contact_info.get("City", "Not set"),
                "State/Province": contact_info.get("StateOrRegion", "Not set"),
                "Postal Code": contact_info.get("PostalCode", "Not set"),
                "Country Code": contact_info.get("CountryCode", "Not set"),
                "Phone Number": contact_info.get("PhoneNumber", "Not set"),
                "Website URL": contact_info.get("WebsiteUrl", "Not set"),
            }

            print_output(
                primary_contact, output_format=config.aws_output_format, title="Primary Account Contact Information"
            )

        except Exception as e:
            console.print(f"[yellow]Could not retrieve primary contact information: {e}[/yellow]")

        # Get alternate contacts
        try:
            alternate_types = ["BILLING", "OPERATIONS", "SECURITY"]
            alternate_contacts = []

            for contact_type in alternate_types:
                try:
                    response = account_client.get_alternate_contact(AlternateContactType=contact_type)

                    alternate_contact = response.get("AlternateContact", {})
                    alternate_contacts.append(
                        {
                            "Type": contact_type,
                            "Name": alternate_contact.get("Name", "Not set"),
                            "Title": alternate_contact.get("Title", "Not set"),
                            "Email": alternate_contact.get("EmailAddress", "Not set"),
                            "Phone": alternate_contact.get("PhoneNumber", "Not set"),
                        }
                    )

                except Exception as e:
                    logger.debug(f"Could not get {contact_type} alternate contact: {e}")
                    alternate_contacts.append(
                        {
                            "Type": contact_type,
                            "Name": "Not configured",
                            "Title": "Not configured",
                            "Email": "Not configured",
                            "Phone": "Not configured",
                        }
                    )

            if alternate_contacts:
                print_output(
                    alternate_contacts, output_format=config.aws_output_format, title="Alternate Account Contacts"
                )

        except Exception as e:
            console.print(f"[yellow]Could not retrieve alternate contact information: {e}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting contact information:[/red] {e}")
        raise click.Abort()


@account_group.command()
@click.option("--verbose", is_flag=True, help="Enable verbose output showing region-by-region progress")
@click.pass_context
def detect_control_tower(ctx: click.Context, verbose: bool) -> None:
    """Detect AWS Control Tower or Landing Zone deployments."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Get caller identity for context
        caller_identity = aws_auth.get_caller_identity()
        account_id = caller_identity.get("Account", "Unknown")

        console.print(f"[blue]Scanning account {account_id} for Control Tower/Landing Zone deployments...[/blue]")

        # Get all regions
        regions = aws_auth.get_available_regions("cloudformation")

        if verbose:
            console.print(f"[dim]Checking {len(regions)} regions for CloudFormation stacks...[/dim]")

        # Function to list stacks in a region
        def list_stacks_in_region(region: str) -> tuple[str, List[Dict[str, Any]]]:
            try:
                cf_client = aws_auth.get_client("cloudformation", region_name=region)
                paginator = cf_client.get_paginator("list_stacks")

                stack_status_filter = [
                    "CREATE_COMPLETE",
                    "UPDATE_COMPLETE",
                    "CREATE_FAILED",
                    "ROLLBACK_COMPLETE",
                    "UPDATE_ROLLBACK_COMPLETE",
                    "IMPORT_COMPLETE",
                    "IMPORT_ROLLBACK_COMPLETE",
                ]

                stacks = []
                for page in paginator.paginate(StackStatusFilter=stack_status_filter):
                    stacks.extend(page.get("StackSummaries", []))

                if verbose:
                    console.print(f"[dim]Region {region}: {len(stacks)} stacks found[/dim]")

                return region, stacks

            except Exception as e:
                if verbose:
                    console.print(f"[yellow]Region {region}: Error - {e}[/yellow]")
                return region, []

        # Get stacks from all regions in parallel
        all_stacks = []
        region_results = parallel_execute(
            list_stacks_in_region,
            regions,
            max_workers=config.workers,
            show_progress=not verbose,
            description="Scanning regions for CloudFormation stacks",
        )

        # Aggregate all stacks
        total_stacks = 0
        for region, stacks in region_results:
            if stacks:
                all_stacks.extend(stacks)
                total_stacks += len(stacks)

        console.print(f"[dim]Total stacks found across all regions: {total_stacks}[/dim]")

        # Detect Control Tower and Landing Zone patterns
        controltower_detected, landingzone_detected, detected_stacks = _detect_controltower_landingzone(all_stacks)

        # Prepare results
        detection_results = {
            "Account ID": account_id,
            "Control Tower Detected": "✓ YES" if controltower_detected else "✗ NO",
            "Landing Zone Detected": "✓ YES" if landingzone_detected else "✗ NO",
            "Total Regions Scanned": len(regions),
            "Total Stacks Analyzed": total_stacks,
            "Matching Stacks Found": len(detected_stacks),
        }

        print_output(
            detection_results,
            output_format=config.aws_output_format,
            title="Control Tower / Landing Zone Detection Results",
        )

        # Show detected stacks if any
        if detected_stacks:
            stack_details = []
            for stack in detected_stacks:
                stack_details.append(
                    {
                        "Stack Name": stack.get("StackName", ""),
                        "Status": stack.get("StackStatus", ""),
                        "Region": stack.get("Region", "Unknown"),
                        "Created": (
                            stack.get("CreationTime", "").strftime("%Y-%m-%d")
                            if stack.get("CreationTime")
                            else "Unknown"
                        ),
                    }
                )

            print_output(
                stack_details,
                output_format=config.aws_output_format,
                title="Detected Control Tower / Landing Zone Stacks",
            )

    except Exception as e:
        console.print(f"[red]Error detecting Control Tower/Landing Zone:[/red] {e}")
        raise click.Abort()


@account_group.command()
@click.pass_context
def regions(ctx: click.Context) -> None:
    """List all available AWS regions."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Get all regions
        regions_list = aws_auth.get_available_regions("ec2")

        # Format as list of dictionaries for better table output
        regions_data = [
            {"Region": region, "Current": "✓" if region == config.aws_region else ""} for region in sorted(regions_list)
        ]

        print_output(regions_data, output_format=config.aws_output_format, title="Available AWS Regions")

    except Exception as e:
        console.print(f"[red]Error listing regions:[/red] {e}")
        raise click.Abort()


@account_group.command()
@click.option("--service", default="ec2", help="AWS service to check regions for")
@click.pass_context
def service_regions(ctx: click.Context, service: str) -> None:
    """List available regions for a specific AWS service."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Get regions for specific service
        regions_list = aws_auth.get_available_regions(service)

        # Format as list of dictionaries
        regions_data = [
            {"Region": region, "Service": service, "Current": "✓" if region == config.aws_region else ""}
            for region in sorted(regions_list)
        ]

        print_output(
            regions_data, output_format=config.aws_output_format, title=f"Available Regions for {service.upper()}"
        )

    except Exception as e:
        console.print(f"[red]Error listing regions for {service}:[/red] {e}")
        raise click.Abort()


@account_group.command()
@click.pass_context
def limits(ctx: click.Context) -> None:
    """Get AWS service limits and usage."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Get service quotas (if available)
        try:
            quotas_client = aws_auth.get_client("service-quotas")

            # Get some common service quotas
            common_services = ["ec2", "lambda", "s3", "rds", "iam"]

            limits_data = []

            for service in common_services:
                try:
                    response = quotas_client.list_service_quotas(ServiceCode=service, MaxResults=10)

                    for quota in response.get("Quotas", []):
                        limits_data.append(
                            {
                                "Service": service.upper(),
                                "Quota Name": quota.get("QuotaName", "Unknown"),
                                "Value": quota.get("Value", "Unknown"),
                                "Unit": quota.get("Unit", ""),
                                "Adjustable": "Yes" if quota.get("Adjustable") else "No",
                            }
                        )

                except Exception as e:
                    logger.debug(f"Could not get quotas for {service}: {e}")
                    continue

            if limits_data:
                print_output(limits_data, output_format=config.aws_output_format, title="AWS Service Limits")
            else:
                console.print("[yellow]No service quota information available[/yellow]")

        except Exception as e:
            logger.debug(f"Service Quotas API not available: {e}")
            console.print("[yellow]Service Quotas API not available in this region[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting service limits:[/red] {e}")
        raise click.Abort()


@account_group.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Validate AWS credentials and permissions."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        validation_results = []

        # Test STS access
        try:
            caller_identity = aws_auth.get_caller_identity()
            validation_results.append(
                {
                    "Service": "STS",
                    "Test": "GetCallerIdentity",
                    "Status": "✓ PASS",
                    "Details": f"Account: {caller_identity.get('Account')}",
                }
            )
        except Exception as e:
            validation_results.append(
                {"Service": "STS", "Test": "GetCallerIdentity", "Status": "✗ FAIL", "Details": str(e)}
            )

        # Test common service access
        services_to_test = [
            ("EC2", "ec2", "describe_regions"),
            ("S3", "s3", "list_buckets"),
            ("IAM", "iam", "get_user"),
            ("CloudWatch", "cloudwatch", "list_metrics"),
        ]

        for service_name, service_code, test_method in services_to_test:
            try:
                client = aws_auth.get_client(service_code)
                method = getattr(client, test_method)

                if test_method == "get_user":
                    # IAM get_user might fail if using role
                    try:
                        method()
                        status = "✓ PASS"
                        details = "User access confirmed"
                    except Exception:
                        # Try list_users instead
                        client.list_users(MaxItems=1)
                        status = "✓ PASS"
                        details = "Role access confirmed"
                else:
                    method()
                    status = "✓ PASS"
                    details = "Access confirmed"

                validation_results.append(
                    {"Service": service_name, "Test": test_method, "Status": status, "Details": details}
                )

            except Exception as e:
                validation_results.append(
                    {
                        "Service": service_name,
                        "Test": test_method,
                        "Status": "✗ FAIL",
                        "Details": str(e)[:50] + "..." if len(str(e)) > 50 else str(e),
                    }
                )

        print_output(validation_results, output_format=config.aws_output_format, title="AWS Credentials Validation")

    except Exception as e:
        console.print(f"[red]Error validating credentials:[/red] {e}")
        raise click.Abort()


def _detect_controltower_landingzone(stacks: List[Dict[str, Any]]) -> tuple[bool, bool, List[Dict[str, Any]]]:
    """Detect Control Tower and Landing Zone deployments from CloudFormation stacks."""

    # Patterns that suggest Control Tower deployment
    controltower_patterns = ["AWSControlTower", "AWS-Control-Tower", "ControlTower"]

    # Patterns that suggest Landing Zone deployment
    landingzone_patterns = ["LandingZone", "AWS-Landing-Zone", "Landing-Zone"]

    found_controltower = False
    found_landingzone = False
    detected_stacks = []

    for stack in stacks:
        stack_name = stack.get("StackName", "")

        # Check for Control Tower patterns
        for pattern in controltower_patterns:
            if pattern in stack_name:
                found_controltower = True
                detected_stacks.append(stack)
                break

        # Check for Landing Zone patterns
        for pattern in landingzone_patterns:
            if pattern in stack_name:
                found_landingzone = True
                detected_stacks.append(stack)
                break

    return found_controltower, found_landingzone, detected_stacks
