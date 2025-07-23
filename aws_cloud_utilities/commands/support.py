"""AWS support tools commands."""

import csv
import datetime
import logging
import os
from typing import Dict, Any, List, Tuple
import click
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import print_output
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="support")
def support_group():
    """AWS support tools commands."""
    pass


@support_group.command(name="check-level")
@click.option(
    "--method",
    type=click.Choice(["api", "severity"]),
    default="severity",
    help="Method to check support level (severity levels or support plans API)",
)
@click.pass_context
def check_level(ctx: click.Context, method: str) -> None:
    """Check AWS support level using different methods."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        if method == "severity":
            support_level = _check_support_via_severity_levels(aws_auth)
        else:
            support_level = _check_support_via_api(aws_auth)

        support_info = {
            "Support Level": support_level,
            "Detection Method": method.upper(),
            "Account ID": aws_auth.get_account_id(),
        }

        print_output(support_info, output_format=config.aws_output_format, title="AWS Support Level")

    except Exception as e:
        console.print(f"[red]Error checking support level:[/red] {e}")
        raise click.Abort()


@support_group.command(name="severity-levels")
@click.pass_context
def severity_levels(ctx: click.Context) -> None:
    """List available support severity levels."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        support_client = aws_auth.get_client("support", region_name="us-east-1")

        try:
            response = support_client.describe_severity_levels(language="en")
            severity_levels_data = []

            for severity_level in response["severityLevels"]:
                severity_levels_data.append({"Code": severity_level["code"], "Name": severity_level["name"]})

            if severity_levels_data:
                print_output(
                    severity_levels_data,
                    output_format=config.aws_output_format,
                    title="Available Support Severity Levels",
                )
            else:
                console.print("[yellow]No severity levels available - Basic support plan[/yellow]")

        except support_client.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "SubscriptionRequiredException":
                console.print("[yellow]Basic support plan - No premium support features available[/yellow]")
            else:
                raise AWSError(f"Error getting severity levels: {err}")

    except Exception as e:
        console.print(f"[red]Error listing severity levels:[/red] {e}")
        raise click.Abort()


@support_group.command(name="cases")
@click.option("--status", type=click.Choice(["all", "open", "resolved"]), default="open", help="Filter cases by status")
@click.option("--max-results", type=int, default=25, help="Maximum number of cases to return")
@click.pass_context
def cases(ctx: click.Context, status: str, max_results: int) -> None:
    """List AWS support cases."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        support_client = aws_auth.get_client("support", region_name="us-east-1")

        try:
            # Build parameters
            params = {"maxResults": max_results, "language": "en"}

            if status != "all":
                params["includeResolvedCases"] = status == "resolved"
            else:
                params["includeResolvedCases"] = True

            response = support_client.describe_cases(**params)

            cases_data = []
            for case in response.get("cases", []):
                cases_data.append(
                    {
                        "Case ID": case.get("caseId", ""),
                        "Subject": (
                            case.get("subject", "")[:50] + "..."
                            if len(case.get("subject", "")) > 50
                            else case.get("subject", "")
                        ),
                        "Status": case.get("status", ""),
                        "Severity": case.get("severityCode", ""),
                        "Service": case.get("serviceCode", ""),
                        "Submitted": case.get("timeCreated", "").split("T")[0] if case.get("timeCreated") else "",
                        "Language": case.get("language", ""),
                    }
                )

            if cases_data:
                print_output(
                    cases_data, output_format=config.aws_output_format, title=f"AWS Support Cases ({status.title()})"
                )
            else:
                console.print(f"[yellow]No {status} support cases found[/yellow]")

        except support_client.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "SubscriptionRequiredException":
                console.print("[yellow]Basic support plan - Cannot access support cases[/yellow]")
            else:
                raise AWSError(f"Error getting support cases: {err}")

    except Exception as e:
        console.print(f"[red]Error listing support cases:[/red] {e}")
        raise click.Abort()


@support_group.command(name="services")
@click.pass_context
def services(ctx: click.Context) -> None:
    """List AWS services available for support cases."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        support_client = aws_auth.get_client("support", region_name="us-east-1")

        try:
            response = support_client.describe_services(language="en")

            services_data = []
            for service in response.get("services", []):
                services_data.append(
                    {
                        "Service Code": service.get("code", ""),
                        "Service Name": service.get("name", ""),
                        "Categories": len(service.get("categories", [])),
                    }
                )

            if services_data:
                print_output(
                    services_data, output_format=config.aws_output_format, title="AWS Services Available for Support"
                )
            else:
                console.print("[yellow]No services information available[/yellow]")

        except support_client.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "SubscriptionRequiredException":
                console.print("[yellow]Basic support plan - Limited service information available[/yellow]")
            else:
                raise AWSError(f"Error getting services: {err}")

    except Exception as e:
        console.print(f"[red]Error listing support services:[/red] {e}")
        raise click.Abort()


def _check_support_via_severity_levels(aws_auth: AWSAuth) -> str:
    """Check support level via severity levels method."""
    support_client = aws_auth.get_client("support", region_name="us-east-1")

    # Support level mapping based on available severity levels
    SUPPORT_LEVELS = {
        "critical": "ENTERPRISE",
        "urgent": "BUSINESS",
        "high": "BUSINESS",
        "normal": "DEVELOPER",
        "low": "DEVELOPER",
    }

    try:
        response = support_client.describe_severity_levels(language="en")

        severity_levels = []
        for severity_level in response["severityLevels"]:
            severity_levels.append(severity_level["code"])

        # Determine support level based on available severity levels
        for level, support_level in SUPPORT_LEVELS.items():
            if level in severity_levels:
                return support_level

        return "BASIC"

    except support_client.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "SubscriptionRequiredException":
            return "BASIC"
        raise AWSError(f"Error checking support via severity levels: {err}")


def _check_support_via_api(aws_auth: AWSAuth) -> str:
    """Check support level via Support Plans API method."""
    try:
        # This method requires additional dependencies and AWS CRT
        # For now, we'll use a simplified approach
        console.print("[yellow]Support Plans API method requires additional setup[/yellow]")
        console.print("[dim]Falling back to severity levels method...[/dim]")
        return _check_support_via_severity_levels(aws_auth)

    except Exception as e:
        logger.debug(f"Support Plans API method failed: {e}")
        # Fallback to severity levels method
        return _check_support_via_severity_levels(aws_auth)


@click.group(name="trusted-advisor")
def trusted_advisor_group():
    """AWS Trusted Advisor tools commands."""
    pass


@trusted_advisor_group.command(name="cost-savings")
@click.option(
    "--csv-file",
    default="ta_cost_savings.csv",
    help="CSV file to store historical data",
)
@click.option(
    "--export-only",
    is_flag=True,
    help="Only export current month data without updating CSV",
)
@click.option(
    "--show-details",
    is_flag=True,
    help="Show detailed breakdown by check type",
)
@click.pass_context
def cost_savings(ctx: click.Context, csv_file: str, export_only: bool, show_details: bool) -> None:
    """Analyze AWS Trusted Advisor cost optimization opportunities."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing Trusted Advisor cost optimization checks...", total=None)

            total_savings, total_opportunities, check_details = _get_cost_savings_data(aws_auth, show_details)
            progress.remove_task(task)

        # Display current results
        current_data = {
            "Total Monthly Savings": f"${total_savings:,.2f}",
            "Total Opportunities": total_opportunities,
            "Analysis Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        print_output(
            current_data, output_format=config.aws_output_format, title="AWS Trusted Advisor Cost Savings Analysis"
        )

        # Show detailed breakdown if requested
        if show_details and check_details:
            _display_cost_savings_details(check_details, config.aws_output_format)

        # Update CSV file unless export-only mode
        if not export_only:
            month_str = datetime.datetime.now().strftime("%Y-%m")
            _update_cost_savings_csv(csv_file, month_str, total_savings, total_opportunities)
            console.print(f"[green]Historical data updated in '{csv_file}'[/green]")

    except Exception as e:
        console.print(f"[red]Error analyzing cost savings:[/red] {e}")
        logger.error(f"Cost savings analysis failed: {e}")
        raise click.Abort()


# Add trusted-advisor group to support group
support_group.add_command(trusted_advisor_group)


def _get_cost_savings_data(aws_auth: AWSAuth, include_details: bool = False) -> Tuple[float, int, List[Dict[str, Any]]]:
    """
    Retrieve cost optimization check results from Trusted Advisor.

    Args:
        aws_auth: AWS authentication helper
        include_details: Whether to include detailed breakdown by check type

    Returns:
        Tuple of (total_savings, total_opportunities, check_details)
    """
    support_client = aws_auth.get_client("support", region_name="us-east-1")
    total_savings = 0.0
    total_opportunities = 0
    check_details = []

    try:
        response = support_client.describe_trusted_advisor_checks(language="en")
    except support_client.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "SubscriptionRequiredException":
            raise AWSError("Business or Enterprise support plan required for Trusted Advisor access")
        raise AWSError(f"Error accessing Trusted Advisor: {err}")

    for check in response.get("checks", []):
        if check.get("category") == "cost_optimizing":
            check_id = check.get("id")
            check_name = check.get("name", "Unknown Check")

            try:
                result_response = support_client.describe_trusted_advisor_check_result(checkId=check_id, language="en")
            except Exception as e:
                logger.warning(f"Skipping check {check_name}: {e}")
                continue

            result = result_response.get("result", {})
            metadata_headers = result.get("metadata", [])
            flagged_resources = result.get("flaggedResources", [])

            # Find the savings column
            savings_index = None
            for i, header in enumerate(metadata_headers):
                if "Savings" in header:
                    savings_index = i
                    break

            check_savings = 0.0
            check_opportunities = len(flagged_resources)

            if savings_index is not None:
                for resource in flagged_resources:
                    try:
                        savings_str = resource[savings_index]
                        savings_value = float(savings_str.replace("$", "").replace(",", "").strip())
                        check_savings += savings_value
                    except (ValueError, IndexError, TypeError):
                        continue

            total_savings += check_savings
            total_opportunities += check_opportunities

            if include_details and (check_savings > 0 or check_opportunities > 0):
                check_details.append(
                    {
                        "Check Name": check_name,
                        "Monthly Savings": f"${check_savings:,.2f}",
                        "Opportunities": check_opportunities,
                        "Status": result.get("status", "unknown"),
                    }
                )

    return total_savings, total_opportunities, check_details


def _display_cost_savings_details(check_details: List[Dict[str, Any]], output_format: str) -> None:
    """Display detailed breakdown of cost savings by check type."""
    if not check_details:
        return

    print_output(check_details, output_format=output_format, title="Cost Savings Breakdown by Check Type")


def _update_cost_savings_csv(csv_filename: str, month_str: str, total_savings: float, total_opportunities: int) -> None:
    """
    Update the CSV file with cost savings data for the current month.

    Args:
        csv_filename: Path to the CSV file
        month_str: Month string in YYYY-MM format
        total_savings: Total monthly savings amount
        total_opportunities: Total number of opportunities
    """
    rows = []
    header = ["Month", "TotalSavings", "TotalOpportunities"]

    # Read existing data if file exists
    if os.path.exists(csv_filename):
        try:
            with open(csv_filename, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    rows.append(row)
        except Exception as e:
            logger.warning(f"Error reading existing CSV file: {e}")

    # Update existing record for the month if found
    updated = False
    for row in rows:
        if row["Month"] == month_str:
            row["TotalSavings"] = str(total_savings)
            row["TotalOpportunities"] = str(total_opportunities)
            updated = True
            break

    # Add new record if not found
    if not updated:
        rows.append(
            {
                "Month": month_str,
                "TotalSavings": str(total_savings),
                "TotalOpportunities": str(total_opportunities),
            }
        )

    # Write sorted data back to CSV
    try:
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()
            for row in sorted(rows, key=lambda x: x["Month"]):
                writer.writerow(row)
    except Exception as e:
        logger.error(f"Error updating CSV file: {e}")
        raise AWSError(f"Failed to update CSV file '{csv_filename}': {e}")
