"""AWS Billing and Cost and Usage Report (CUR) management commands."""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import click
from rich.console import Console
from rich.table import Table

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import print_output, save_to_file, get_timestamp
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


class CURManager:
    """AWS Cost and Usage Report Manager for CUR 2.0"""

    def __init__(self, aws_auth: AWSAuth):
        """
        Initialize CUR Manager

        Args:
            aws_auth: AWS authentication instance
        """
        self.logger = logging.getLogger(__name__)
        self.aws_auth = aws_auth

        try:
            # CUR API is only available in us-east-1
            self.cur_client = aws_auth.get_client("cur", region_name="us-east-1")
            self.s3_client = aws_auth.get_client("s3")

            # Get account information
            self.account_id = aws_auth.get_caller_identity()["Account"]
            self.logger.info(f"Connected to AWS Account: {self.account_id}")

        except Exception as e:
            self.logger.error(f"Failed to initialize AWS clients: {e}")
            raise AWSError(f"Failed to initialize CUR manager: {e}")

    def list_cur_reports(self) -> List[Dict[str, Any]]:
        """
        List all existing CUR reports

        Returns:
            List of CUR report definitions
        """
        self.logger.info("Fetching existing CUR reports...")

        try:
            reports = []
            paginator = self.cur_client.get_paginator("describe_report_definitions")

            for page in paginator.paginate():
                reports.extend(page.get("ReportDefinitions", []))

            self.logger.info(f"Found {len(reports)} CUR report(s)")
            return reports

        except Exception as e:
            if "AccessDenied" in str(e):
                raise AWSError("Access denied. Ensure you have 'cur:DescribeReportDefinitions' permission")
            raise AWSError(f"Failed to list CUR reports: {e}")

    def get_cur_details(self, report_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific CUR report

        Args:
            report_name: Name of the CUR report

        Returns:
            CUR report definition or None if not found
        """
        self.logger.debug(f"Getting details for CUR report: {report_name}")

        try:
            response = self.cur_client.describe_report_definitions()

            for report in response.get("ReportDefinitions", []):
                if report["ReportName"] == report_name:
                    return report

            self.logger.warning(f"CUR report '{report_name}' not found")
            return None

        except Exception as e:
            raise AWSError(f"Failed to get CUR report details: {e}")

    def validate_s3_bucket_policy(self, bucket_name: str, prefix: str = "") -> bool:
        """
        Validate if S3 bucket has proper permissions for CUR delivery

        Args:
            bucket_name: S3 bucket name
            prefix: Optional prefix for CUR files

        Returns:
            True if bucket policy is correctly configured
        """
        self.logger.info(f"Validating S3 bucket policy for: {bucket_name}")

        try:
            # Check if bucket exists and is accessible
            self.s3_client.head_bucket(Bucket=bucket_name)
            self.logger.debug(f"Bucket {bucket_name} exists and is accessible")

            # Get bucket policy
            try:
                response = self.s3_client.get_bucket_policy(Bucket=bucket_name)
                policy = json.loads(response["Policy"])

                # Check for required CUR permissions
                cur_service_principal = "billingreports.amazonaws.com"
                required_actions = ["s3:GetBucketAcl", "s3:GetBucketPolicy", "s3:PutObject"]

                for statement in policy.get("Statement", []):
                    principal = statement.get("Principal", {})
                    if isinstance(principal, dict) and principal.get("Service") == cur_service_principal:
                        actions = statement.get("Action", [])
                        if isinstance(actions, str):
                            actions = [actions]

                        if all(action in actions for action in required_actions):
                            self.logger.info(f"Bucket {bucket_name} has proper CUR permissions")
                            return True

                self.logger.warning(f"Bucket {bucket_name} may not have proper CUR permissions")
                return False

            except Exception as e:
                if "NoSuchBucketPolicy" in str(e):
                    self.logger.warning(f"No bucket policy found for {bucket_name}")
                    return False
                raise

        except Exception as e:
            if "NoSuchBucket" in str(e):
                raise AWSError(f"Bucket {bucket_name} does not exist")
            raise AWSError(f"Failed to validate bucket policy: {e}")

    def create_cur_report(
        self,
        report_name: str,
        s3_bucket: str,
        s3_prefix: str = "cur-reports",
        format_version: str = "textORcsv",
        compression: str = "GZIP",
        additional_schema_elements: List[str] = None,
    ) -> bool:
        """
        Create a new CUR 2.0 report

        Args:
            report_name: Name for the new CUR report
            s3_bucket: S3 bucket for delivery
            s3_prefix: S3 prefix for CUR files
            format_version: Report format version
            compression: Compression type
            additional_schema_elements: Additional schema elements

        Returns:
            True if report was created successfully
        """
        self.logger.info(f"Creating CUR 2.0 report: {report_name}")

        if additional_schema_elements is None:
            additional_schema_elements = ["RESOURCES"]

        report_definition = {
            "ReportName": report_name,
            "TimeUnit": "HOURLY",
            "Format": format_version,
            "Compression": compression,
            "AdditionalSchemaElements": additional_schema_elements,
            "S3Bucket": s3_bucket,
            "S3Prefix": s3_prefix,
            "S3Region": self.aws_auth.region_name,
            "AdditionalArtifacts": ["REDSHIFT", "QUICKSIGHT"],
            "RefreshClosedReports": True,
            "ReportVersioning": "OVERWRITE_REPORT",
            "BillingViewArn": None,  # CUR 2.0 specific
        }

        try:
            # Validate bucket permissions first
            if not self.validate_s3_bucket_policy(s3_bucket, s3_prefix):
                self.logger.warning("S3 bucket may not have proper permissions. Creating bucket policy...")
                self._create_bucket_policy(s3_bucket, s3_prefix)

            response = self.cur_client.put_report_definition(ReportDefinition=report_definition)
            self.logger.info(f"Successfully created CUR report: {report_name}")
            return True

        except Exception as e:
            if "DuplicateReportNameException" in str(e):
                raise AWSError(f"CUR report '{report_name}' already exists")
            raise AWSError(f"Failed to create CUR report: {e}")

    def _create_bucket_policy(self, bucket_name: str, prefix: str) -> None:
        """
        Create S3 bucket policy for CUR delivery

        Args:
            bucket_name: S3 bucket name
            prefix: S3 prefix for CUR files
        """
        self.logger.info(f"Creating bucket policy for CUR delivery: {bucket_name}")

        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "billingreports.amazonaws.com"},
                    "Action": ["s3:GetBucketAcl", "s3:GetBucketPolicy"],
                    "Resource": f"arn:aws:s3:::{bucket_name}",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceArn": f"arn:aws:cur:us-east-1:{self.account_id}:definition/*",
                            "aws:SourceAccount": self.account_id,
                        }
                    },
                },
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "billingreports.amazonaws.com"},
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/{prefix}/*",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceArn": f"arn:aws:cur:us-east-1:{self.account_id}:definition/*",
                            "aws:SourceAccount": self.account_id,
                        }
                    },
                },
            ],
        }

        try:
            self.s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))
            self.logger.info(f"Successfully created bucket policy for {bucket_name}")

        except Exception as e:
            raise AWSError(f"Failed to create bucket policy: {e}")

    def delete_cur_report(self, report_name: str) -> bool:
        """
        Delete a CUR report

        Args:
            report_name: Name of the CUR report to delete

        Returns:
            True if report was deleted successfully
        """
        self.logger.info(f"Deleting CUR report: {report_name}")

        try:
            self.cur_client.delete_report_definition(ReportName=report_name)
            self.logger.info(f"Successfully deleted CUR report: {report_name}")
            return True

        except Exception as e:
            if "InternalErrorException" in str(e):
                raise AWSError(f"CUR report '{report_name}' not found")
            raise AWSError(f"Failed to delete CUR report: {e}")


@click.group(name="billing")
def billing_group():
    """AWS billing and Cost and Usage Report (CUR) management commands."""
    pass


@billing_group.command(name="cur-list")
@click.option("--output-file", help="Output file for CUR reports list (supports .json, .yaml, .csv)")
@click.pass_context
def cur_list(ctx: click.Context, output_file: Optional[str]) -> None:
    """List all existing Cost and Usage Reports."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        console.print("[blue]Listing Cost and Usage Reports[/blue]")

        cur_manager = CURManager(aws_auth)
        reports = cur_manager.list_cur_reports()

        if not reports:
            console.print("\n[yellow]No Cost and Usage Reports found in this account[/yellow]")
            console.print("[dim]Use 'billing cur-create' to set up CUR 2.0[/dim]")
            return

        # Format reports for display
        reports_display = []
        for report in reports:
            reports_display.append(
                {
                    "Report Name": report["ReportName"],
                    "S3 Bucket": report["S3Bucket"],
                    "S3 Prefix": report.get("S3Prefix", ""),
                    "Time Unit": report["TimeUnit"],
                    "Format": report["Format"],
                    "Compression": report["Compression"],
                    "Versioning": report.get("ReportVersioning", "N/A"),
                    "Schema Elements": ", ".join(report.get("AdditionalSchemaElements", [])),
                    "Artifacts": ", ".join(report.get("AdditionalArtifacts", [])),
                }
            )

        print_output(
            reports_display,
            output_format=config.aws_output_format,
            title=f"Cost and Usage Reports ({len(reports)} found)",
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

            save_to_file(reports_display, output_path, file_format)
            console.print(f"[green]CUR reports list saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error listing CUR reports:[/red] {e}")
        raise click.Abort()


@billing_group.command(name="cur-details")
@click.argument("report_name")
@click.option("--output-file", help="Output file for CUR report details (supports .json, .yaml)")
@click.pass_context
def cur_details(ctx: click.Context, report_name: str, output_file: Optional[str]) -> None:
    """Show detailed configuration for a specific CUR report."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        console.print(f"[blue]Getting details for CUR report: {report_name}[/blue]")

        cur_manager = CURManager(aws_auth)
        report = cur_manager.get_cur_details(report_name)

        if not report:
            console.print(f"[red]CUR report '{report_name}' not found[/red]")
            raise click.Abort()

        print_output(report, output_format=config.aws_output_format, title=f"CUR Report Details: {report_name}")

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(report, output_path, file_format)
            console.print(f"[green]CUR report details saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error getting CUR report details:[/red] {e}")
        raise click.Abort()


@billing_group.command(name="cur-create")
@click.option("--report-name", required=True, help="Name for the new CUR report")
@click.option("--bucket", required=True, help="S3 bucket name for CUR delivery")
@click.option("--prefix", default="cur-reports", help="S3 prefix for CUR files (default: cur-reports)")
@click.option(
    "--format",
    type=click.Choice(["textORcsv", "Parquet"]),
    default="textORcsv",
    help="Report format (default: textORcsv)",
)
@click.option(
    "--compression",
    type=click.Choice(["GZIP", "ZIP", "Parquet"]),
    default="GZIP",
    help="Compression type (default: GZIP)",
)
@click.option(
    "--schema-elements", multiple=True, default=["RESOURCES"], help="Additional schema elements (default: RESOURCES)"
)
@click.pass_context
def cur_create(
    ctx: click.Context,
    report_name: str,
    bucket: str,
    prefix: str,
    format: str,
    compression: str,
    schema_elements: tuple,
) -> None:
    """Create a new Cost and Usage Report (CUR 2.0)."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        console.print(f"[blue]Creating CUR 2.0 report: {report_name}[/blue]")
        console.print(f"[dim]S3 Location: s3://{bucket}/{prefix}[/dim]")
        console.print(f"[dim]Format: {format}, Compression: {compression}[/dim]")

        cur_manager = CURManager(aws_auth)
        success = cur_manager.create_cur_report(
            report_name=report_name,
            s3_bucket=bucket,
            s3_prefix=prefix,
            format_version=format,
            compression=compression,
            additional_schema_elements=list(schema_elements),
        )

        if success:
            console.print(f"\n[green]✅ Successfully created CUR report: {report_name}[/green]")
            console.print(f"[dim]📍 Delivery Location: s3://{bucket}/{prefix}[/dim]")
            console.print("[dim]⏳ Reports will be generated within 24 hours[/dim]")
        else:
            console.print(f"\n[red]❌ Failed to create CUR report: {report_name}[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error creating CUR report:[/red] {e}")
        raise click.Abort()


@billing_group.command(name="cur-delete")
@click.argument("report_name")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def cur_delete(ctx: click.Context, report_name: str, confirm: bool) -> None:
    """Delete a Cost and Usage Report."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        if not confirm:
            if not click.confirm(f"Are you sure you want to delete CUR report '{report_name}'?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        console.print(f"[blue]Deleting CUR report: {report_name}[/blue]")

        cur_manager = CURManager(aws_auth)
        success = cur_manager.delete_cur_report(report_name)

        if success:
            console.print(f"\n[green]✅ Successfully deleted CUR report: {report_name}[/green]")
        else:
            console.print(f"\n[red]❌ Failed to delete CUR report: {report_name}[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error deleting CUR report:[/red] {e}")
        raise click.Abort()


@billing_group.command(name="cur-validate-bucket")
@click.argument("bucket_name")
@click.option("--prefix", default="", help="S3 prefix for CUR files (optional)")
@click.pass_context
def cur_validate_bucket(ctx: click.Context, bucket_name: str, prefix: str) -> None:
    """Validate S3 bucket permissions for CUR delivery."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        console.print(f"[blue]Validating S3 bucket permissions: {bucket_name}[/blue]")
        if prefix:
            console.print(f"[dim]Prefix: {prefix}[/dim]")

        cur_manager = CURManager(aws_auth)
        is_valid = cur_manager.validate_s3_bucket_policy(bucket_name, prefix)

        if is_valid:
            console.print(f"\n[green]✅ Bucket {bucket_name} has proper CUR permissions[/green]")
        else:
            console.print(f"\n[yellow]⚠️  Bucket {bucket_name} may not have proper CUR permissions[/yellow]")
            console.print("[dim]Use 'billing cur-create' to automatically configure bucket policy[/dim]")

    except Exception as e:
        console.print(f"[red]Error validating bucket permissions:[/red] {e}")
        raise click.Abort()
