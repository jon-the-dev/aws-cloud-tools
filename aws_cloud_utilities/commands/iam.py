"""IAM management and auditing commands."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import print_output, save_to_file, get_timestamp, get_detailed_timestamp, ensure_directory
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="iam")
def iam_group():
    """IAM management and auditing commands."""
    pass


@iam_group.command(name="audit")
@click.option("--output-dir", help="Directory to save audit files (default: ./iam_audit_<account_id>_<timestamp>)")
@click.option(
    "--include-aws-managed", is_flag=True, help="Include AWS managed policies in audit (warning: large output)"
)
@click.option("--roles-only", is_flag=True, help="Audit only IAM roles")
@click.option("--policies-only", is_flag=True, help="Audit only IAM policies")
@click.option("--format", type=click.Choice(["json", "yaml"]), default="json", help="Output format for saved files")
@click.pass_context
def audit(
    ctx: click.Context,
    output_dir: Optional[str],
    include_aws_managed: bool,
    roles_only: bool,
    policies_only: bool,
    format: str,
) -> None:
    """Audit IAM roles and policies, saving them locally."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        account_id = aws_auth.get_account_id()
        timestamp = get_detailed_timestamp()

        # Determine output directory
        if not output_dir:
            output_dir = f"./iam_audit_{account_id}_{timestamp}"

        output_path = Path(output_dir)
        ensure_directory(output_path)

        console.print(f"[blue]Starting IAM audit for account {account_id}[/blue]")
        console.print(f"[dim]Output directory: {output_path.absolute()}[/dim]")

        iam_client = aws_auth.get_client("iam")

        audit_summary = {
            "account_id": account_id,
            "audit_timestamp": datetime.now().isoformat(),
            "include_aws_managed": include_aws_managed,
            "roles_processed": 0,
            "policies_processed": 0,
            "inline_policies_processed": 0,
            "attached_policies_processed": 0,
        }

        # Process roles unless policies-only is specified
        if not policies_only:
            console.print("\n[yellow]Processing IAM Roles...[/yellow]")
            roles_dir = output_path / "roles"
            ensure_directory(roles_dir)

            roles_summary = _process_roles(iam_client, account_id, roles_dir, format)
            audit_summary.update(roles_summary)

        # Process policies unless roles-only is specified
        if not roles_only:
            console.print("\n[yellow]Processing IAM Policies...[/yellow]")
            policies_dir = output_path / "policies"
            ensure_directory(policies_dir)

            policies_summary = _process_policies(iam_client, account_id, policies_dir, format, include_aws_managed)
            audit_summary.update(policies_summary)

        # Save audit summary
        summary_file = output_path / f"audit_summary_{account_id}_{timestamp}.json"
        save_to_file(audit_summary, summary_file, "json")

        # Display summary
        summary_display = {
            "Account ID": account_id,
            "Audit Timestamp": audit_summary["audit_timestamp"],
            "Output Directory": str(output_path.absolute()),
            "Roles Processed": audit_summary["roles_processed"],
            "Policies Processed": audit_summary["policies_processed"],
            "Inline Policies": audit_summary["inline_policies_processed"],
            "Attached Policies": audit_summary["attached_policies_processed"],
            "Include AWS Managed": "Yes" if include_aws_managed else "No",
            "Output Format": format.upper(),
        }

        print_output(summary_display, output_format=config.aws_output_format, title="IAM Audit Summary")

        console.print(f"\n[green]✅ IAM audit completed successfully![/green]")
        console.print(f"[dim]Files saved to: {output_path.absolute()}[/dim]")

    except Exception as e:
        console.print(f"[red]Error during IAM audit:[/red] {e}")
        raise click.Abort()


def _process_roles(iam_client, account_id: str, roles_dir: Path, format: str) -> Dict[str, int]:
    """Process IAM roles and save their policies."""
    roles_processed = 0
    inline_policies_processed = 0
    attached_policies_processed = 0

    try:
        paginator = iam_client.get_paginator("list_roles")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Processing IAM roles...", total=None)

            for page in paginator.paginate():
                roles = page["Roles"]

                for role in roles:
                    role_name = role["RoleName"]
                    roles_processed += 1

                    progress.update(task, description=f"Processing role: {role_name}")

                    # Process inline policies
                    try:
                        inline_policies = iam_client.list_role_policies(RoleName=role_name)["PolicyNames"]

                        for policy_name in inline_policies:
                            filename = f"{account_id}-{role_name}-{policy_name}.{format}"
                            file_path = roles_dir / filename

                            if not file_path.exists():
                                policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                                policy_document = policy["PolicyDocument"]

                                # Add metadata
                                policy_with_metadata = {
                                    "PolicyDocument": policy_document,
                                    "PolicyName": policy_name,
                                    "RoleName": role_name,
                                    "PolicyType": "Inline",
                                    "AccountId": account_id,
                                    "AuditTimestamp": datetime.now().isoformat(),
                                }

                                save_to_file(policy_with_metadata, file_path, format)
                                inline_policies_processed += 1

                    except Exception as e:
                        logger.warning(f"Error processing inline policies for role {role_name}: {e}")

                    # Process attached policies
                    try:
                        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)[
                            "AttachedPolicies"
                        ]

                        for attached_policy in attached_policies:
                            policy_arn = attached_policy["PolicyArn"]
                            policy_name = attached_policy["PolicyName"]
                            filename = f"{account_id}-{role_name}-{policy_name}.{format}"
                            file_path = roles_dir / filename

                            if not file_path.exists():
                                # Get policy details
                                policy = iam_client.get_policy(PolicyArn=policy_arn)
                                default_version_id = policy["Policy"]["DefaultVersionId"]

                                policy_version = iam_client.get_policy_version(
                                    PolicyArn=policy_arn, VersionId=default_version_id
                                )
                                policy_document = policy_version["PolicyVersion"]["Document"]

                                # Add metadata
                                policy_with_metadata = {
                                    "PolicyDocument": policy_document,
                                    "PolicyName": policy_name,
                                    "PolicyArn": policy_arn,
                                    "RoleName": role_name,
                                    "PolicyType": "Attached",
                                    "AccountId": account_id,
                                    "AuditTimestamp": datetime.now().isoformat(),
                                    "PolicyMetadata": policy["Policy"],
                                }

                                save_to_file(policy_with_metadata, file_path, format)
                                attached_policies_processed += 1

                    except Exception as e:
                        logger.warning(f"Error processing attached policies for role {role_name}: {e}")

    except Exception as e:
        logger.error(f"Error processing roles: {e}")
        raise

    return {
        "roles_processed": roles_processed,
        "inline_policies_processed": inline_policies_processed,
        "attached_policies_processed": attached_policies_processed,
    }


def _process_policies(
    iam_client, account_id: str, policies_dir: Path, format: str, include_aws_managed: bool
) -> Dict[str, int]:
    """Process IAM policies and save them."""
    policies_processed = 0

    try:
        paginator = iam_client.get_paginator("list_policies")

        # Determine scope
        scope = "All" if include_aws_managed else "Local"

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Processing IAM policies...", total=None)

            for page in paginator.paginate(Scope=scope):
                policies = page["Policies"]

                for policy in policies:
                    policy_name = policy["PolicyName"]
                    policy_arn = policy["Arn"]
                    policies_processed += 1

                    progress.update(task, description=f"Processing policy: {policy_name}")

                    # Skip AWS managed policies unless explicitly requested
                    if not include_aws_managed and policy_arn.startswith("arn:aws:iam::aws:"):
                        continue

                    filename = f"{account_id}-{policy_name}.{format}"
                    file_path = policies_dir / filename

                    if not file_path.exists():
                        try:
                            # Get policy version
                            policy_version = iam_client.get_policy_version(
                                PolicyArn=policy_arn, VersionId=policy["DefaultVersionId"]
                            )
                            policy_document = policy_version["PolicyVersion"]["Document"]

                            # Add metadata
                            policy_with_metadata = {
                                "PolicyDocument": policy_document,
                                "PolicyName": policy_name,
                                "PolicyArn": policy_arn,
                                "PolicyType": "Managed",
                                "IsAWSManaged": policy_arn.startswith("arn:aws:iam::aws:"),
                                "AccountId": account_id,
                                "AuditTimestamp": datetime.now().isoformat(),
                                "PolicyMetadata": policy,
                            }

                            save_to_file(policy_with_metadata, file_path, format)

                        except Exception as e:
                            logger.warning(f"Error processing policy {policy_name}: {e}")

    except Exception as e:
        logger.error(f"Error processing policies: {e}")
        raise


@iam_group.command(name="list-roles")
@click.option("--path-prefix", help="Filter roles by path prefix")
@click.option("--max-items", type=int, default=100, help="Maximum number of roles to return")
@click.pass_context
def list_roles(ctx: click.Context, path_prefix: Optional[str], max_items: int) -> None:
    """List IAM roles with details."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        iam_client = aws_auth.get_client("iam")

        params = {"MaxItems": max_items}
        if path_prefix:
            params["PathPrefix"] = path_prefix

        paginator = iam_client.get_paginator("list_roles")
        roles_data = []

        for page in paginator.paginate(**params):
            for role in page["Roles"]:
                roles_data.append(
                    {
                        "Role Name": role["RoleName"],
                        "Path": role["Path"],
                        "Created": role["CreateDate"].strftime("%Y-%m-%d %H:%M") if role.get("CreateDate") else "",
                        "Max Session Duration": f"{role.get('MaxSessionDuration', 3600)}s",
                        "Description": (
                            role.get("Description", "")[:50] + "..."
                            if len(role.get("Description", "")) > 50
                            else role.get("Description", "")
                        ),
                    }
                )

        if roles_data:
            print_output(
                roles_data, output_format=config.aws_output_format, title=f"IAM Roles ({len(roles_data)} found)"
            )
        else:
            console.print("[yellow]No IAM roles found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing IAM roles:[/red] {e}")
        raise click.Abort()


@iam_group.command(name="list-policies")
@click.option("--scope", type=click.Choice(["All", "AWS", "Local"]), default="Local", help="Policy scope to list")
@click.option("--only-attached", is_flag=True, help="Only show policies that are attached to users, groups, or roles")
@click.option("--path-prefix", help="Filter policies by path prefix")
@click.pass_context
def list_policies(ctx: click.Context, scope: str, only_attached: bool, path_prefix: Optional[str]) -> None:
    """List IAM policies."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        iam_client = aws_auth.get_client("iam")

        params = {"Scope": scope}
        if only_attached:
            params["OnlyAttached"] = True
        if path_prefix:
            params["PathPrefix"] = path_prefix

        paginator = iam_client.get_paginator("list_policies")
        policies_data = []

        for page in paginator.paginate(**params):
            for policy in page["Policies"]:
                policies_data.append(
                    {
                        "Policy Name": policy["PolicyName"],
                        "ARN": policy["Arn"],
                        "Path": policy["Path"],
                        "Created": policy["CreateDate"].strftime("%Y-%m-%d %H:%M") if policy.get("CreateDate") else "",
                        "Updated": policy["UpdateDate"].strftime("%Y-%m-%d %H:%M") if policy.get("UpdateDate") else "",
                        "Attachment Count": policy.get("AttachmentCount", 0),
                        "Is Attachable": "Yes" if policy.get("IsAttachable") else "No",
                        "Description": (
                            policy.get("Description", "")[:50] + "..."
                            if len(policy.get("Description", "")) > 50
                            else policy.get("Description", "")
                        ),
                    }
                )

        if policies_data:
            print_output(
                policies_data,
                output_format=config.aws_output_format,
                title=f"IAM Policies ({len(policies_data)} found)",
            )
        else:
            console.print("[yellow]No IAM policies found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing IAM policies:[/red] {e}")
        raise click.Abort()


@iam_group.command(name="role-details")
@click.argument("role_name")
@click.pass_context
def role_details(ctx: click.Context, role_name: str) -> None:
    """Get detailed information about a specific IAM role."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        iam_client = aws_auth.get_client("iam")

        # Get role details
        try:
            role_response = iam_client.get_role(RoleName=role_name)
            role = role_response["Role"]
        except iam_client.exceptions.NoSuchEntityException:
            console.print(f"[red]Role '{role_name}' not found[/red]")
            raise click.Abort()

        # Get attached policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]

        # Get inline policies
        inline_policies = iam_client.list_role_policies(RoleName=role_name)["PolicyNames"]

        # Get instance profiles
        try:
            instance_profiles = iam_client.list_instance_profiles_for_role(RoleName=role_name)["InstanceProfiles"]
        except Exception:
            instance_profiles = []

        role_details = {
            "Role Name": role["RoleName"],
            "ARN": role["Arn"],
            "Path": role["Path"],
            "Created": role["CreateDate"].strftime("%Y-%m-%d %H:%M:%S") if role.get("CreateDate") else "",
            "Max Session Duration": f"{role.get('MaxSessionDuration', 3600)} seconds",
            "Description": role.get("Description", "Not set"),
            "Attached Policies": len(attached_policies),
            "Inline Policies": len(inline_policies),
            "Instance Profiles": len(instance_profiles),
            "Permissions Boundary": role.get("PermissionsBoundary", {}).get("PermissionsBoundaryArn", "Not set"),
        }

        print_output(role_details, output_format=config.aws_output_format, title=f"IAM Role Details: {role_name}")

        # Show attached policies
        if attached_policies:
            attached_data = [
                {"Policy Name": policy["PolicyName"], "Policy ARN": policy["PolicyArn"]} for policy in attached_policies
            ]
            print_output(attached_data, output_format=config.aws_output_format, title="Attached Policies")

        # Show inline policies
        if inline_policies:
            inline_data = [{"Policy Name": policy} for policy in inline_policies]
            print_output(inline_data, output_format=config.aws_output_format, title="Inline Policies")

    except Exception as e:
        console.print(f"[red]Error getting role details:[/red] {e}")
        raise click.Abort()


@iam_group.command(name="policy-details")
@click.argument("policy_arn")
@click.pass_context
def policy_details(ctx: click.Context, policy_arn: str) -> None:
    """Get detailed information about a specific IAM policy."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        iam_client = aws_auth.get_client("iam")

        # Get policy details
        try:
            policy_response = iam_client.get_policy(PolicyArn=policy_arn)
            policy = policy_response["Policy"]
        except iam_client.exceptions.NoSuchEntityException:
            console.print(f"[red]Policy '{policy_arn}' not found[/red]")
            raise click.Abort()

        # Get policy document
        policy_version = iam_client.get_policy_version(PolicyArn=policy_arn, VersionId=policy["DefaultVersionId"])

        policy_details = {
            "Policy Name": policy["PolicyName"],
            "ARN": policy["Arn"],
            "Path": policy["Path"],
            "Created": policy["CreateDate"].strftime("%Y-%m-%d %H:%M:%S") if policy.get("CreateDate") else "",
            "Updated": policy["UpdateDate"].strftime("%Y-%m-%d %H:%M:%S") if policy.get("UpdateDate") else "",
            "Default Version": policy["DefaultVersionId"],
            "Attachment Count": policy.get("AttachmentCount", 0),
            "Permissions Boundary Usage Count": policy.get("PermissionsBoundaryUsageCount", 0),
            "Is Attachable": "Yes" if policy.get("IsAttachable") else "No",
            "Description": policy.get("Description", "Not set"),
        }

        print_output(
            policy_details, output_format=config.aws_output_format, title=f"IAM Policy Details: {policy['PolicyName']}"
        )

        # Show policy document
        if config.aws_output_format == "json":
            console.print("\n[bold]Policy Document:[/bold]")
            console.print_json(json.dumps(policy_version["PolicyVersion"]["Document"], indent=2))

    except Exception as e:
        console.print(f"[red]Error getting policy details:[/red] {e}")
        raise click.Abort()
