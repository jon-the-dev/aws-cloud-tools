"""AWS security monitoring and certificate management commands."""

import logging
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
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


@click.group(name="security")
def security_group():
    """AWS security monitoring and certificate management commands."""
    pass


@security_group.command(name="metrics")
@click.option("--region", help="AWS region to collect metrics from (default: current region)")
@click.option("--time-range", type=int, default=24, help="Time range in hours for metrics collection (default: 24)")
@click.option("--services", help="Comma-separated list of services to include (waf,guardduty,securityhub)")
@click.option("--output-file", help="Output file for security metrics (supports .json, .yaml, .csv)")
@click.option("--all-regions", is_flag=True, help="Collect metrics from all regions")
@click.pass_context
def metrics(
    ctx: click.Context,
    region: Optional[str],
    time_range: int,
    services: Optional[str],
    output_file: Optional[str],
    all_regions: bool,
) -> None:
    """Collect security metrics from AWS WAF, GuardDuty, and Security Hub."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Determine regions to scan
        if all_regions:
            target_regions = aws_auth.get_available_regions("wafv2")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]

        # Determine services to include
        if services:
            target_services = [s.strip().lower() for s in services.split(",")]
        else:
            target_services = ["waf", "guardduty", "securityhub"]

        console.print(
            f"[blue]Collecting security metrics for {time_range} hours across {len(target_regions)} regions[/blue]"
        )
        console.print(f"[dim]Services: {', '.join(target_services)}[/dim]")

        # Initialize metrics summary
        metrics_summary = {
            "collection_timestamp": datetime.now().isoformat(),
            "time_range_hours": time_range,
            "regions": target_regions,
            "services": target_services,
            "metrics": {},
            "errors": [],
        }

        # Collect metrics from all regions
        all_metrics = _collect_security_metrics(aws_auth, target_regions, target_services, time_range, metrics_summary)

        # Display results
        _display_security_metrics(config, all_metrics, metrics_summary)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(all_metrics, output_path, file_format)
            console.print(f"[green]Security metrics saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error collecting security metrics:[/red] {e}")
        raise click.Abort()


@security_group.command(name="create-certificate")
@click.argument("domain")
@click.option("--alt-names", help="Comma-separated list of alternative domain names")
@click.option("--hosted-zone-id", help="Route53 hosted zone ID for validation (auto-detected if not provided)")
@click.option("--region", default="us-east-1", help="AWS region for certificate (default: us-east-1 for CloudFront)")
@click.option("--wait-for-validation", is_flag=True, help="Wait for certificate validation to complete")
@click.option("--timeout", type=int, default=300, help="Timeout in seconds for validation wait (default: 300)")
@click.pass_context
def create_certificate(
    ctx: click.Context,
    domain: str,
    alt_names: Optional[str],
    hosted_zone_id: Optional[str],
    region: str,
    wait_for_validation: bool,
    timeout: int,
) -> None:
    """Create an ACM certificate with Route53 DNS validation."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Parse alternative names
        alternative_names = []
        if alt_names:
            alternative_names = [name.strip() for name in alt_names.split(",")]

        console.print(f"[blue]Creating ACM certificate for domain: {domain}[/blue]")
        if alternative_names:
            console.print(f"[dim]Alternative names: {', '.join(alternative_names)}[/dim]")

        # Get ACM and Route53 clients
        acm_client = aws_auth.get_client("acm", region_name=region)
        route53_client = aws_auth.get_client("route53")

        # Find hosted zone if not provided
        if not hosted_zone_id:
            hosted_zone_id = _find_hosted_zone(route53_client, domain)
            if not hosted_zone_id:
                console.print(f"[red]Could not find hosted zone for domain: {domain}[/red]")
                raise click.Abort()
            console.print(f"[green]Found hosted zone:[/green] {hosted_zone_id}")

        # Request certificate
        cert_response = _request_certificate(acm_client, domain, alternative_names)
        certificate_arn = cert_response["CertificateArn"]

        console.print(f"[green]Certificate requested:[/green] {certificate_arn}")

        # Get validation records
        validation_records = _get_validation_records(acm_client, certificate_arn)

        # Create DNS validation records
        _create_validation_records(route53_client, hosted_zone_id, validation_records)

        console.print("[green]DNS validation records created successfully[/green]")

        # Wait for validation if requested
        if wait_for_validation:
            console.print("[yellow]Waiting for certificate validation...[/yellow]")

            if _wait_for_validation(acm_client, certificate_arn, timeout):
                console.print("[green]✅ Certificate validated successfully![/green]")
            else:
                console.print("[yellow]⚠️  Certificate validation timed out[/yellow]")

        # Display certificate details
        cert_details = {
            "Certificate ARN": certificate_arn,
            "Domain": domain,
            "Alternative Names": ", ".join(alternative_names) if alternative_names else "None",
            "Region": region,
            "Hosted Zone ID": hosted_zone_id,
            "Validation Status": "In Progress" if not wait_for_validation else "Completed",
        }

        print_output(cert_details, output_format=config.aws_output_format, title="ACM Certificate Details")

    except Exception as e:
        console.print(f"[red]Error creating certificate:[/red] {e}")
        raise click.Abort()


@security_group.command(name="list-certificates")
@click.option("--region", help="AWS region to list certificates from (default: current region)")
@click.option(
    "--status",
    type=click.Choice(
        ["PENDING_VALIDATION", "ISSUED", "INACTIVE", "EXPIRED", "VALIDATION_TIMED_OUT", "REVOKED", "FAILED"]
    ),
    help="Filter certificates by status",
)
@click.option("--all-regions", is_flag=True, help="List certificates from all regions")
@click.pass_context
def list_certificates(ctx: click.Context, region: Optional[str], status: Optional[str], all_regions: bool) -> None:
    """List ACM certificates with details."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Determine regions to scan
        if all_regions:
            target_regions = aws_auth.get_available_regions("acm")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]

        all_certificates = []

        for target_region in target_regions:
            acm_client = aws_auth.get_client("acm", region_name=target_region)

            try:
                # List certificates
                paginator = acm_client.get_paginator("list_certificates")

                for page in paginator.paginate():
                    for cert in page.get("CertificateSummaryList", []):
                        # Filter by status if specified
                        if status and cert.get("Status") != status:
                            continue

                        # Get detailed certificate information
                        try:
                            cert_details = acm_client.describe_certificate(CertificateArn=cert["CertificateArn"])[
                                "Certificate"
                            ]

                            all_certificates.append(
                                {
                                    "Domain": cert_details.get("DomainName", ""),
                                    "Status": cert_details.get("Status", ""),
                                    "Region": target_region,
                                    "Type": cert_details.get("Type", ""),
                                    "Key Algorithm": cert_details.get("KeyAlgorithm", ""),
                                    "Created": (
                                        cert_details.get("CreatedAt", "").strftime("%Y-%m-%d")
                                        if cert_details.get("CreatedAt")
                                        else ""
                                    ),
                                    "Expires": (
                                        cert_details.get("NotAfter", "").strftime("%Y-%m-%d")
                                        if cert_details.get("NotAfter")
                                        else ""
                                    ),
                                    "Alternative Names": len(cert_details.get("SubjectAlternativeNames", [])),
                                    "Certificate ARN": cert["CertificateArn"],
                                }
                            )

                        except Exception as e:
                            logger.debug(f"Could not get details for certificate {cert['CertificateArn']}: {e}")

            except Exception as e:
                logger.warning(f"Error listing certificates in region {target_region}: {e}")

        if all_certificates:
            print_output(
                all_certificates,
                output_format=config.aws_output_format,
                title=f"ACM Certificates ({len(all_certificates)} found)",
            )
        else:
            console.print("[yellow]No certificates found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing certificates:[/red] {e}")
        raise click.Abort()


def _collect_security_metrics(
    aws_auth: AWSAuth, regions: List[str], services: List[str], time_range: int, metrics_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """Collect security metrics from specified services and regions."""

    def collect_region_metrics(region: str) -> Tuple[str, Dict[str, Any]]:
        """Collect metrics for a single region."""
        region_metrics = {}

        if "waf" in services:
            try:
                waf_metrics = _get_waf_metrics(aws_auth, region, time_range)
                region_metrics["WAF"] = waf_metrics
            except Exception as e:
                metrics_summary["errors"].append(f"WAF in {region}: {str(e)}")
                region_metrics["WAF"] = {"error": str(e)}

        if "guardduty" in services:
            try:
                guardduty_metrics = _get_guardduty_metrics(aws_auth, region, time_range)
                region_metrics["GuardDuty"] = guardduty_metrics
            except Exception as e:
                metrics_summary["errors"].append(f"GuardDuty in {region}: {str(e)}")
                region_metrics["GuardDuty"] = {"error": str(e)}

        if "securityhub" in services:
            try:
                securityhub_metrics = _get_securityhub_metrics(aws_auth, region, time_range)
                region_metrics["SecurityHub"] = securityhub_metrics
            except Exception as e:
                metrics_summary["errors"].append(f"SecurityHub in {region}: {str(e)}")
                region_metrics["SecurityHub"] = {"error": str(e)}

        return region, region_metrics

    # Collect metrics in parallel
    region_results = parallel_execute(
        collect_region_metrics,
        regions,
        max_workers=4,  # Limit to avoid rate limits
        show_progress=True,
        description="Collecting security metrics",
    )

    # Organize results
    all_metrics = {}
    for region, region_metrics in region_results:
        all_metrics[region] = region_metrics
        metrics_summary["metrics"][region] = region_metrics


def _get_waf_metrics(aws_auth: AWSAuth, region: str, time_range: int) -> Dict[str, Any]:
    """Get WAF metrics for a region."""
    waf_client = aws_auth.get_client("wafv2", region_name=region)
    cloudwatch_client = aws_auth.get_client("cloudwatch", region_name=region)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=time_range)
    period = 300  # 5 minutes

    waf_metrics = {}

    # List REGIONAL web ACLs
    try:
        response = waf_client.list_web_acls(Scope="REGIONAL")
        web_acls = response.get("WebACLs", [])

        # Handle pagination
        while "NextMarker" in response:
            response = waf_client.list_web_acls(Scope="REGIONAL", NextMarker=response["NextMarker"])
            web_acls.extend(response.get("WebACLs", []))
    except Exception as e:
        return {"error": f"Error retrieving WAF ACLs: {e}"}

    if not web_acls:
        return {"message": "No WAF ACLs found in region"}

    for acl in web_acls:
        acl_name = acl.get("Name")
        acl_id = acl.get("Id")

        # Query overall metrics for the web ACL
        dimensions = [{"Name": "WebACL", "Value": acl_name}]

        allowed = _get_cloudwatch_metric_sum(
            cloudwatch_client, "AWS/WAFV2", "AllowedRequests", dimensions, start_time, end_time, period
        )

        blocked = _get_cloudwatch_metric_sum(
            cloudwatch_client, "AWS/WAFV2", "BlockedRequests", dimensions, start_time, end_time, period
        )

        # Get detailed ACL info to retrieve rule names
        try:
            details = waf_client.get_web_acl(Id=acl_id, Name=acl_name, Scope="REGIONAL")
            rules = details.get("WebACL", {}).get("Rules", [])

            rule_metrics = {}
            for rule in rules:
                rule_name = rule.get("Name")
                rule_dimensions = [
                    {"Name": "WebACL", "Value": acl_name},
                    {"Name": "Rule", "Value": rule_name},
                ]

                rule_blocked = _get_cloudwatch_metric_sum(
                    cloudwatch_client, "AWS/WAFV2", "BlockedRequests", rule_dimensions, start_time, end_time, period
                )
                rule_metrics[rule_name] = rule_blocked

            waf_metrics[acl_name] = {
                "AllowedRequests": allowed,
                "BlockedRequests": blocked,
                "Rules": rule_metrics,
            }
        except Exception as e:
            logger.debug(f"Error getting WAF ACL details for {acl_name}: {e}")

    return waf_metrics


def _get_guardduty_metrics(aws_auth: AWSAuth, region: str, time_range: int) -> Dict[str, Any]:
    """Get GuardDuty metrics for a region."""
    guardduty_client = aws_auth.get_client("guardduty", region_name=region)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=time_range)

    try:
        detectors_response = guardduty_client.list_detectors()
        detector_ids = detectors_response.get("DetectorIds", [])
    except Exception as e:
        return {"error": f"Error retrieving GuardDuty detectors: {e}"}

    if not detector_ids:
        return {"message": "No GuardDuty detectors found in region"}

    gd_metrics = defaultdict(int)

    for detector_id in detector_ids:
        try:
            paginator = guardduty_client.get_paginator("list_findings")
            finding_ids = []

            for page in paginator.paginate(DetectorId=detector_id):
                finding_ids.extend(page.get("FindingIds", []))

            if not finding_ids:
                continue

            # Get finding details in batches
            batch_size = 50
            for i in range(0, len(finding_ids), batch_size):
                batch = finding_ids[i : i + batch_size]

                findings_response = guardduty_client.get_findings(DetectorId=detector_id, FindingIds=batch)

                for finding in findings_response.get("Findings", []):
                    updated_at_str = finding.get("UpdatedAt")
                    if updated_at_str:
                        try:
                            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                            if start_time <= updated_at <= end_time:
                                finding_type = finding.get("Type", "Unknown")
                                gd_metrics[finding_type] += 1
                        except ValueError:
                            continue
        except Exception as e:
            logger.debug(f"Error processing GuardDuty detector {detector_id}: {e}")

    if not gd_metrics:
        return {"message": "No GuardDuty findings found in time range"}

    return dict(gd_metrics)


def _get_securityhub_metrics(aws_auth: AWSAuth, region: str, time_range: int) -> Dict[str, Any]:
    """Get Security Hub metrics for a region."""
    securityhub_client = aws_auth.get_client("securityhub", region_name=region)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=time_range)

    sh_metrics = defaultdict(int)

    try:
        paginator = securityhub_client.get_paginator("get_findings")

        for page in paginator.paginate():
            for finding in page.get("Findings", []):
                created_at_str = finding.get("CreatedAt")
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if start_time <= created_at <= end_time:
                            types = finding.get("Types", [])
                            if types:
                                primary_type = types[0]
                                sh_metrics[primary_type] += 1
                    except ValueError:
                        continue
    except Exception as e:
        return {"error": f"Error retrieving SecurityHub findings: {e}"}

    if not sh_metrics:
        return {"message": "No SecurityHub findings found in time range"}

    return dict(sh_metrics)


def _get_cloudwatch_metric_sum(
    cloudwatch_client,
    namespace: str,
    metric_name: str,
    dimensions: List[Dict],
    start_time: datetime,
    end_time: datetime,
    period: int,
) -> float:
    """Query CloudWatch for metric sum over time window."""
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=["Sum"],
        )
        return sum(dp["Sum"] for dp in response.get("Datapoints", []))
    except Exception:
        return 0.0


def _display_security_metrics(config: Config, all_metrics: Dict[str, Any], metrics_summary: Dict[str, Any]) -> None:
    """Display security metrics summary."""

    # Overall summary
    total_regions = len(all_metrics)
    total_errors = len(metrics_summary["errors"])

    summary_display = {
        "Collection Timestamp": metrics_summary["collection_timestamp"],
        "Time Range (Hours)": metrics_summary["time_range_hours"],
        "Regions Processed": total_regions,
        "Services": ", ".join(metrics_summary["services"]),
        "Total Errors": total_errors,
    }

    print_output(summary_display, output_format=config.aws_output_format, title="Security Metrics Collection Summary")

    # Display metrics by region
    for region, region_metrics in all_metrics.items():
        if not region_metrics:
            continue

        console.print(f"\n[bold blue]Region: {region}[/bold blue]")

        for service, service_metrics in region_metrics.items():
            if (
                isinstance(service_metrics, dict)
                and "error" not in service_metrics
                and "message" not in service_metrics
            ):
                console.print(f"[green]{service}:[/green]")

                if service == "WAF":
                    for acl_name, acl_metrics in service_metrics.items():
                        console.print(f"  WebACL: {acl_name}")
                        console.print(f"    Allowed: {acl_metrics.get('AllowedRequests', 0)}")
                        console.print(f"    Blocked: {acl_metrics.get('BlockedRequests', 0)}")

                        rules = acl_metrics.get("Rules", {})
                        if rules:
                            console.print(f"    Rules:")
                            for rule_name, blocked_count in rules.items():
                                if blocked_count > 0:
                                    console.print(f"      {rule_name}: {blocked_count} blocked")

                elif service in ["GuardDuty", "SecurityHub"]:
                    for finding_type, count in service_metrics.items():
                        if count > 0:
                            console.print(f"  {finding_type}: {count}")

            elif isinstance(service_metrics, dict) and ("error" in service_metrics or "message" in service_metrics):
                status = service_metrics.get("error") or service_metrics.get("message")
                console.print(f"[yellow]{service}:[/yellow] {status}")

    # Show errors if any
    if metrics_summary["errors"]:
        console.print(f"\n[yellow]Errors encountered ({len(metrics_summary['errors'])}):[/yellow]")
        for error in metrics_summary["errors"][:10]:
            console.print(f"  [dim]• {error}[/dim]")
        if len(metrics_summary["errors"]) > 10:
            console.print(f"  [dim]... and {len(metrics_summary['errors']) - 10} more errors[/dim]")


def _find_hosted_zone(route53_client, domain: str) -> Optional[str]:
    """Find the hosted zone ID for a domain."""
    try:
        paginator = route53_client.get_paginator("list_hosted_zones")

        for page in paginator.paginate():
            for zone in page.get("HostedZones", []):
                zone_name = zone["Name"].rstrip(".")
                if domain.endswith(zone_name):
                    return zone["Id"].split("/")[-1]  # Extract ID from full path

        return None
    except Exception as e:
        logger.error(f"Error finding hosted zone: {e}")
        return None


def _request_certificate(acm_client, domain: str, alternative_names: List[str]) -> Dict[str, Any]:
    """Request an ACM certificate."""
    request_params = {"DomainName": domain, "ValidationMethod": "DNS"}

    if alternative_names:
        request_params["SubjectAlternativeNames"] = alternative_names

    return acm_client.request_certificate(**request_params)


def _get_validation_records(acm_client, certificate_arn: str) -> List[Dict[str, Any]]:
    """Get DNS validation records for a certificate."""
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        try:
            response = acm_client.describe_certificate(CertificateArn=certificate_arn)
            validation_options = response["Certificate"].get("DomainValidationOptions", [])

            # Check if all validation records are available
            validation_records = []
            for option in validation_options:
                if "ResourceRecord" in option:
                    validation_records.append(option["ResourceRecord"])

            if len(validation_records) == len(validation_options):
                return validation_records

        except Exception as e:
            logger.debug(f"Attempt {attempt + 1}: Error getting validation records: {e}")

        attempt += 1
        if attempt < max_attempts:
            import time

            time.sleep(2)

    raise Exception("Timeout waiting for validation records")


def _create_validation_records(route53_client, hosted_zone_id: str, validation_records: List[Dict[str, Any]]) -> None:
    """Create DNS validation records in Route53."""
    changes = []

    for record in validation_records:
        changes.append(
            {
                "Action": "CREATE",
                "ResourceRecordSet": {
                    "Name": record["Name"],
                    "Type": record["Type"],
                    "TTL": 300,
                    "ResourceRecords": [{"Value": record["Value"]}],
                },
            }
        )

    if changes:
        route53_client.change_resource_record_sets(HostedZoneId=hosted_zone_id, ChangeBatch={"Changes": changes})


def _wait_for_validation(acm_client, certificate_arn: str, timeout: int) -> bool:
    """Wait for certificate validation to complete."""
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = acm_client.describe_certificate(CertificateArn=certificate_arn)
            status = response["Certificate"]["Status"]

            if status == "ISSUED":
                return True
            elif status in ["VALIDATION_TIMED_OUT", "FAILED", "REVOKED"]:
                return False

        except Exception as e:
            logger.debug(f"Error checking certificate status: {e}")

        time.sleep(10)

    return False
