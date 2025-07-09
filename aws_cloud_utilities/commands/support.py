"""AWS support tools commands."""

import logging
from typing import Dict, Any, List
import click
import requests
from rich.console import Console

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
    help="Method to check support level (severity levels or support plans API)"
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
            "Account ID": aws_auth.get_account_id()
        }
        
        print_output(
            support_info,
            output_format=config.aws_output_format,
            title="AWS Support Level"
        )
        
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
                severity_levels_data.append({
                    "Code": severity_level["code"],
                    "Name": severity_level["name"]
                })
            
            if severity_levels_data:
                print_output(
                    severity_levels_data,
                    output_format=config.aws_output_format,
                    title="Available Support Severity Levels"
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
@click.option(
    "--status",
    type=click.Choice(["all", "open", "resolved"]),
    default="open",
    help="Filter cases by status"
)
@click.option(
    "--max-results",
    type=int,
    default=25,
    help="Maximum number of cases to return"
)
@click.pass_context
def cases(ctx: click.Context, status: str, max_results: int) -> None:
    """List AWS support cases."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]
    
    try:
        support_client = aws_auth.get_client("support", region_name="us-east-1")
        
        try:
            # Build parameters
            params = {
                "maxResults": max_results,
                "language": "en"
            }
            
            if status != "all":
                params["includeResolvedCases"] = (status == "resolved")
            else:
                params["includeResolvedCases"] = True
            
            response = support_client.describe_cases(**params)
            
            cases_data = []
            for case in response.get("cases", []):
                cases_data.append({
                    "Case ID": case.get("caseId", ""),
                    "Subject": case.get("subject", "")[:50] + "..." if len(case.get("subject", "")) > 50 else case.get("subject", ""),
                    "Status": case.get("status", ""),
                    "Severity": case.get("severityCode", ""),
                    "Service": case.get("serviceCode", ""),
                    "Submitted": case.get("timeCreated", "").split("T")[0] if case.get("timeCreated") else "",
                    "Language": case.get("language", "")
                })
            
            if cases_data:
                print_output(
                    cases_data,
                    output_format=config.aws_output_format,
                    title=f"AWS Support Cases ({status.title()})"
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
                services_data.append({
                    "Service Code": service.get("code", ""),
                    "Service Name": service.get("name", ""),
                    "Categories": len(service.get("categories", []))
                })
            
            if services_data:
                print_output(
                    services_data,
                    output_format=config.aws_output_format,
                    title="AWS Services Available for Support"
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
