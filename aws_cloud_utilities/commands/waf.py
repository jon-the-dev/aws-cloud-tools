#!/usr/bin/env python3
"""
AWS WAF Statistics and Metrics Command

This module provides comprehensive WAF monitoring and troubleshooting capabilities
to help identify whether blocks are due to WAF rules, application issues, or end-user problems.
"""

import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError, BotoCoreError
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import print_output, save_to_file, get_timestamp
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


class WAFAnalyzer:
    """Analyze AWS WAF metrics and statistics for troubleshooting."""

    def __init__(self, aws_auth: AWSAuth, region: str = "us-east-1"):
        """Initialize WAF analyzer with AWS auth."""
        self.aws_auth = aws_auth
        self.region = region
        self.wafv2_client = aws_auth.get_client("wafv2", region_name=region)
        self.cloudwatch_client = aws_auth.get_client("cloudwatch", region_name=region)

    def list_web_acls(self, scope: str = "REGIONAL") -> List[Dict[str, Any]]:
        """List all Web ACLs in the account."""
        try:
            logger.info(f"Listing Web ACLs with scope: {scope}")
            response = self.wafv2_client.list_web_acls(Scope=scope)
            return response.get("WebACLs", [])
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to list Web ACLs: {e}")
            raise AWSError(f"Failed to list Web ACLs: {e}")

    def get_waf_metrics(
        self,
        web_acl_name: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        dimensions: Optional[List[Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Get CloudWatch metrics for WAF."""
        try:
            logger.info(f"Getting WAF metrics for {web_acl_name}: {metric_name}")

            metric_dimensions = [{"Name": "WebACL", "Value": web_acl_name}, {"Name": "Region", "Value": self.region}]

            if dimensions:
                metric_dimensions.extend(dimensions)

            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/WAFV2",
                MetricName=metric_name,
                Dimensions=metric_dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=["Sum", "Average", "Maximum"],
            )

            return sorted(response.get("Datapoints", []), key=lambda x: x["Timestamp"])
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get WAF metrics: {e}")
            raise AWSError(f"Failed to get WAF metrics: {e}")


@click.group(name="waf")
@click.pass_context
def waf_group(ctx: click.Context) -> None:
    """AWS WAF management and troubleshooting commands."""
    pass


@waf_group.command(name="list")
@click.option(
    "--scope", type=click.Choice(["REGIONAL", "CLOUDFRONT"]), default="REGIONAL", help="WAF scope (default: REGIONAL)"
)
@click.option("--output-file", help="Save output to file")
@click.pass_obj
def list_web_acls(config: Config, scope: str, output_file: Optional[str]):
    """List all Web ACLs in the account."""
    try:
        aws_auth = AWSAuth(config)
        analyzer = WAFAnalyzer(aws_auth, config.region)

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(f"Listing Web ACLs ({scope})...", total=None)
            web_acls = analyzer.list_web_acls(scope)
            progress.update(task, completed=True)

        if not web_acls:
            console.print(f"[yellow]No Web ACLs found with scope: {scope}[/yellow]")
            return

        # Format output
        output_data = {"scope": scope, "count": len(web_acls), "web_acls": web_acls, "timestamp": get_timestamp()}

        print_output(output_data, config.output_format)

        if output_file:
            save_to_file(output_data, output_file, config.output_format)
            console.print(f"[green]Output saved to: {output_file}[/green]")

    except Exception as e:
        logger.error(f"Error listing Web ACLs: {e}")
        console.print(f"[red]Error: {e}[/red]")


@waf_group.command(name="stats")
@click.option("--web-acl", required=True, help="Web ACL name to analyze")
@click.option("--hours", type=int, default=24, help="Hours of data to analyze (default: 24)")
@click.option(
    "--scope", type=click.Choice(["REGIONAL", "CLOUDFRONT"]), default="REGIONAL", help="WAF scope (default: REGIONAL)"
)
@click.option("--output-file", help="Save output to file")
@click.pass_obj
def get_waf_stats(config: Config, web_acl: str, hours: int, scope: str, output_file: Optional[str]):
    """Get comprehensive WAF statistics for troubleshooting."""
    try:
        aws_auth = AWSAuth(config)
        analyzer = WAFAnalyzer(aws_auth, config.region)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(f"Analyzing WAF stats for {web_acl}...", total=None)

            # Get metrics
            blocked_requests = analyzer.get_waf_metrics(web_acl, "BlockedRequests", start_time, end_time)
            allowed_requests = analyzer.get_waf_metrics(web_acl, "AllowedRequests", start_time, end_time)

            progress.update(task, completed=True)

        # Calculate totals
        total_blocked = sum(point.get("Sum", 0) for point in blocked_requests)
        total_allowed = sum(point.get("Sum", 0) for point in allowed_requests)
        total_requests = total_blocked + total_allowed

        # Prepare output
        stats = {
            "web_acl": web_acl,
            "scope": scope,
            "time_range": {"hours": hours, "start": start_time.isoformat(), "end": end_time.isoformat()},
            "summary": {
                "total_requests": int(total_requests),
                "blocked_requests": int(total_blocked),
                "allowed_requests": int(total_allowed),
                "block_rate_percent": round((total_blocked / total_requests * 100) if total_requests > 0 else 0, 2),
            },
            "recent_activity": {
                "last_hour_blocked": int(
                    sum(point.get("Sum", 0) for point in blocked_requests[-12:]) if blocked_requests else 0
                ),
                "last_hour_allowed": int(
                    sum(point.get("Sum", 0) for point in allowed_requests[-12:]) if allowed_requests else 0
                ),
            },
            "timestamp": get_timestamp(),
        }

        # Add analysis
        if stats["summary"]["block_rate_percent"] > 20:
            stats["analysis"] = ["High block rate detected - review WAF rules for false positives"]
        elif stats["summary"]["total_requests"] == 0:
            stats["analysis"] = ["No requests detected - verify WAF is properly associated with resources"]
        else:
            stats["analysis"] = ["WAF appears to be functioning normally"]

        print_output(stats, config.output_format)

        if output_file:
            save_to_file(stats, output_file, config.output_format)
            console.print(f"[green]Output saved to: {output_file}[/green]")

    except Exception as e:
        logger.error(f"Error getting WAF stats: {e}")
        console.print(f"[red]Error: {e}[/red]")


@waf_group.command(name="troubleshoot")
@click.option("--web-acl", required=True, help="Web ACL name to troubleshoot")
@click.option("--hours", type=int, default=24, help="Hours of data to analyze (default: 24)")
@click.option("--output-file", help="Save troubleshooting report to file")
@click.pass_obj
def troubleshoot_waf(config: Config, web_acl: str, hours: int, output_file: Optional[str]):
    """Generate comprehensive WAF troubleshooting report."""
    try:
        aws_auth = AWSAuth(config)
        analyzer = WAFAnalyzer(aws_auth, config.region)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(f"Generating troubleshooting report for {web_acl}...", total=None)

            # Get comprehensive metrics
            blocked_requests = analyzer.get_waf_metrics(web_acl, "BlockedRequests", start_time, end_time)
            allowed_requests = analyzer.get_waf_metrics(web_acl, "AllowedRequests", start_time, end_time)

            progress.update(task, completed=True)

        # Calculate metrics
        total_blocked = sum(point.get("Sum", 0) for point in blocked_requests)
        total_allowed = sum(point.get("Sum", 0) for point in allowed_requests)
        total_requests = total_blocked + total_allowed
        block_rate = (total_blocked / total_requests * 100) if total_requests > 0 else 0

        # Generate report
        report = {
            "web_acl": web_acl,
            "analysis_period": f"{hours} hours",
            "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "metrics": {
                "total_requests": int(total_requests),
                "total_blocked": int(total_blocked),
                "total_allowed": int(total_allowed),
                "block_rate_percent": round(block_rate, 2),
            },
            "analysis": {
                "high_block_rate": block_rate > 10,
                "very_high_block_rate": block_rate > 20,
                "no_traffic": total_requests == 0,
                "recent_spike": (
                    any(
                        point.get("Sum", 0) > (total_blocked / len(blocked_requests) * 2)
                        for point in blocked_requests[-6:]  # Last 30 minutes
                    )
                    if blocked_requests
                    else False
                ),
            },
            "recommendations": [],
            "timestamp": get_timestamp(),
        }

        # Generate recommendations
        if report["analysis"]["very_high_block_rate"]:
            report["recommendations"].append(
                "CRITICAL: Very high block rate (>20%) - review WAF rules for false positives"
            )
        elif report["analysis"]["high_block_rate"]:
            report["recommendations"].append("WARNING: High block rate (>10%) - monitor for false positives")

        if report["analysis"]["recent_spike"]:
            report["recommendations"].append(
                "ALERT: Recent spike in blocked requests - investigate potential attack or rule changes"
            )

        if report["analysis"]["no_traffic"]:
            report["recommendations"].append(
                "INFO: No requests detected - verify WAF is properly associated with resources"
            )

        if block_rate < 1 and total_requests > 1000:
            report["recommendations"].append(
                "INFO: Very low block rate - consider reviewing WAF rules for effectiveness"
            )

        if not report["recommendations"]:
            report["recommendations"].append("WAF appears to be functioning normally")

        print_output(report, config.output_format)

        if output_file:
            save_to_file(report, output_file, config.output_format)
            console.print(f"[green]Troubleshooting report saved to: {output_file}[/green]")

    except Exception as e:
        logger.error(f"Error generating troubleshooting report: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise click.ClickException(str(e))
    """Analyze AWS WAF metrics and statistics for troubleshooting."""

    def __init__(self, session: boto3.Session, region: str = "us-east-1"):
        """Initialize WAF analyzer with AWS session."""
        self.session = session
        self.region = region
        self.wafv2_client = session.client("wafv2", region_name=region)
        self.cloudwatch_client = session.client("cloudwatch", region_name=region)
        self.logs_client = session.client("logs", region_name=region)

    def list_web_acls(self, scope: str = "REGIONAL") -> List[Dict[str, Any]]:
        """List all Web ACLs in the account."""
        try:
            logger.info(f"Listing Web ACLs with scope: {scope}")
            response = self.wafv2_client.list_web_acls(Scope=scope)
            return response.get("WebACLs", [])
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to list Web ACLs: {e}")
            return []

    def get_web_acl_details(
        self, web_acl_id: str, web_acl_name: str, scope: str = "REGIONAL"
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific Web ACL."""
        try:
            logger.info(f"Getting details for Web ACL: {web_acl_name}")
            response = self.wafv2_client.get_web_acl(Name=web_acl_name, Scope=scope, Id=web_acl_id)
            return response.get("WebACL")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get Web ACL details for {web_acl_name}: {e}")
            return None

    def get_waf_metrics(
        self,
        web_acl_name: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        dimensions: Optional[List[Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Get CloudWatch metrics for WAF."""
        try:
            logger.info(f"Getting WAF metrics for {web_acl_name}: {metric_name}")

            metric_dimensions = [{"Name": "WebACL", "Value": web_acl_name}, {"Name": "Region", "Value": self.region}]

            if dimensions:
                metric_dimensions.extend(dimensions)

            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/WAFV2",
                MetricName=metric_name,
                Dimensions=metric_dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=["Sum", "Average", "Maximum"],
            )

            return sorted(response.get("Datapoints", []), key=lambda x: x["Timestamp"])
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get WAF metrics: {e}")
            return []

    def get_rule_metrics(
        self, web_acl_name: str, rule_name: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get metrics for a specific WAF rule."""
        metrics = {}

        # Get blocked requests by rule
        blocked_requests = self.get_waf_metrics(
            web_acl_name, "BlockedRequests", start_time, end_time, [{"Name": "Rule", "Value": rule_name}]
        )
        metrics["blocked_requests"] = blocked_requests

        # Get allowed requests by rule
        allowed_requests = self.get_waf_metrics(
            web_acl_name, "AllowedRequests", start_time, end_time, [{"Name": "Rule", "Value": rule_name}]
        )
        metrics["allowed_requests"] = allowed_requests

        return metrics

    def get_sampled_requests(
        self, web_acl_arn: str, rule_metric_name: str, scope: str = "REGIONAL", max_items: int = 100
    ) -> List[Dict[str, Any]]:
        """Get sampled requests for analysis."""
        try:
            logger.info(f"Getting sampled requests for rule: {rule_metric_name}")

            # Get time window (last hour)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)

            response = self.wafv2_client.get_sampled_requests(
                WebAclArn=web_acl_arn,
                RuleMetricName=rule_metric_name,
                Scope=scope,
                TimeWindow={"StartTime": start_time, "EndTime": end_time},
                MaxItems=max_items,
            )

            return response.get("SampledRequests", [])
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get sampled requests: {e}")
            return []

    def analyze_request_patterns(self, sampled_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in sampled requests."""
        if not sampled_requests:
            return {"total_samples": 0}

        patterns = {
            "total_samples": len(sampled_requests),
            "blocked_count": 0,
            "allowed_count": 0,
            "top_user_agents": {},
            "top_source_ips": {},
            "top_countries": {},
            "request_methods": {},
            "uri_patterns": {},
        }

        for request in sampled_requests:
            action = request.get("Action", "UNKNOWN")
            if action == "BLOCK":
                patterns["blocked_count"] += 1
            elif action == "ALLOW":
                patterns["allowed_count"] += 1

            # Analyze request details
            req_details = request.get("Request", {})
            headers = req_details.get("Headers", [])

            # User agents
            for header in headers:
                if header.get("Name", "").lower() == "user-agent":
                    ua = header.get("Value", "Unknown")[:50]  # Truncate for readability
                    patterns["top_user_agents"][ua] = patterns["top_user_agents"].get(ua, 0) + 1

            # Source IPs
            client_ip = req_details.get("ClientIP", "Unknown")
            patterns["top_source_ips"][client_ip] = patterns["top_source_ips"].get(client_ip, 0) + 1

            # Countries
            country = req_details.get("Country", "Unknown")
            patterns["top_countries"][country] = patterns["top_countries"].get(country, 0) + 1

            # HTTP methods
            method = req_details.get("HTTPMethod", "Unknown")
            patterns["request_methods"][method] = patterns["request_methods"].get(method, 0) + 1

            # URI patterns (first part of path)
            uri = req_details.get("URI", "/")
            uri_part = uri.split("/")[1] if len(uri.split("/")) > 1 else "/"
            patterns["uri_patterns"][uri_part] = patterns["uri_patterns"].get(uri_part, 0) + 1

        # Sort top items
        for key in ["top_user_agents", "top_source_ips", "top_countries", "request_methods", "uri_patterns"]:
            patterns[key] = dict(sorted(patterns[key].items(), key=lambda x: x[1], reverse=True)[:10])

        return patterns

    def get_rate_limiting_metrics(self, web_acl_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get rate limiting metrics and analysis."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Get rate-based rule metrics
        rate_metrics = {}

        # Get blocked requests due to rate limiting
        blocked_by_rate = self.get_waf_metrics(web_acl_name, "BlockedRequests", start_time, end_time)

        rate_metrics["blocked_requests"] = blocked_by_rate
        rate_metrics["analysis"] = {
            "total_blocked": sum(point.get("Sum", 0) for point in blocked_by_rate),
            "peak_blocks_per_minute": max((point.get("Maximum", 0) for point in blocked_by_rate), default=0),
            "average_blocks_per_minute": (
                sum(point.get("Average", 0) for point in blocked_by_rate) / len(blocked_by_rate)
                if blocked_by_rate
                else 0
            ),
        }

        return rate_metrics

    def generate_troubleshooting_report(self, web_acl_name: str, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive troubleshooting report."""
        logger.info(f"Generating troubleshooting report for {web_acl_name}")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        report = {
            "web_acl": web_acl_name,
            "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat(), "hours": hours},
            "metrics": {},
            "analysis": {},
            "recommendations": [],
        }

        # Get overall metrics
        blocked_requests = self.get_waf_metrics(web_acl_name, "BlockedRequests", start_time, end_time)
        allowed_requests = self.get_waf_metrics(web_acl_name, "AllowedRequests", start_time, end_time)

        total_blocked = sum(point.get("Sum", 0) for point in blocked_requests)
        total_allowed = sum(point.get("Sum", 0) for point in allowed_requests)
        total_requests = total_blocked + total_allowed

        report["metrics"] = {
            "total_requests": total_requests,
            "total_blocked": total_blocked,
            "total_allowed": total_allowed,
            "block_rate": (total_blocked / total_requests * 100) if total_requests > 0 else 0,
            "blocked_requests_timeline": blocked_requests,
            "allowed_requests_timeline": allowed_requests,
        }

        # Analysis
        if total_blocked > 0:
            report["analysis"]["high_block_rate"] = report["metrics"]["block_rate"] > 10
            report["analysis"]["recent_spike"] = (
                any(
                    point.get("Sum", 0) > (total_blocked / len(blocked_requests) * 2)
                    for point in blocked_requests[-6:]  # Last 30 minutes
                )
                if blocked_requests
                else False
            )

        # Recommendations
        if report["metrics"]["block_rate"] > 20:
            report["recommendations"].append("High block rate detected - review WAF rules for false positives")

        if report["analysis"].get("recent_spike"):
            report["recommendations"].append(
                "Recent spike in blocked requests - investigate potential attack or rule changes"
            )

        if total_requests == 0:
            report["recommendations"].append("No requests detected - verify WAF is properly associated with resources")

        if report["metrics"]["block_rate"] < 1 and total_requests > 1000:
            report["recommendations"].append("Very low block rate - consider reviewing WAF rules for effectiveness")

        return report


def add_waf_parser(subparsers) -> None:
    """Add WAF subcommand parser."""
    waf_parser = subparsers.add_parser(
        "waf",
        help="AWS WAF statistics and troubleshooting",
        description="Analyze AWS WAF metrics to troubleshoot blocks and performance issues",
    )

    waf_subparsers = waf_parser.add_subparsers(dest="waf_command", help="WAF commands")

    # List Web ACLs
    list_parser = waf_subparsers.add_parser("list", help="List all Web ACLs")
    list_parser.add_argument(
        "--scope", choices=["REGIONAL", "CLOUDFRONT"], default="REGIONAL", help="WAF scope (default: REGIONAL)"
    )

    # Get WAF stats
    stats_parser = waf_subparsers.add_parser("stats", help="Get WAF statistics")
    stats_parser.add_argument("--web-acl", required=True, help="Web ACL name")
    stats_parser.add_argument("--hours", type=int, default=24, help="Hours of data to analyze (default: 24)")
    stats_parser.add_argument(
        "--scope", choices=["REGIONAL", "CLOUDFRONT"], default="REGIONAL", help="WAF scope (default: REGIONAL)"
    )

    # Rule analysis
    rule_parser = waf_subparsers.add_parser("rule-stats", help="Analyze specific rule performance")
    rule_parser.add_argument("--web-acl", required=True, help="Web ACL name")
    rule_parser.add_argument("--rule", required=True, help="Rule name")
    rule_parser.add_argument("--hours", type=int, default=24, help="Hours of data to analyze (default: 24)")

    # Troubleshooting report
    troubleshoot_parser = waf_subparsers.add_parser("troubleshoot", help="Generate troubleshooting report")
    troubleshoot_parser.add_argument("--web-acl", required=True, help="Web ACL name")
    troubleshoot_parser.add_argument("--hours", type=int, default=24, help="Hours of data to analyze (default: 24)")

    # Request analysis
    requests_parser = waf_subparsers.add_parser("requests", help="Analyze sampled requests")
    requests_parser.add_argument("--web-acl-arn", required=True, help="Web ACL ARN")
    requests_parser.add_argument("--rule", required=True, help="Rule metric name")
    requests_parser.add_argument(
        "--max-items", type=int, default=100, help="Maximum number of sampled requests (default: 100)"
    )
    requests_parser.add_argument(
        "--scope", choices=["REGIONAL", "CLOUDFRONT"], default="REGIONAL", help="WAF scope (default: REGIONAL)"
    )

    # Rate limiting analysis
    rate_parser = waf_subparsers.add_parser("rate-limiting", help="Analyze rate limiting effectiveness")
    rate_parser.add_argument("--web-acl", required=True, help="Web ACL name")
    rate_parser.add_argument("--hours", type=int, default=24, help="Hours of data to analyze (default: 24)")


def handle_waf_command(args) -> None:
    """Handle WAF subcommands."""
    setup_logging(args.verbose if hasattr(args, "verbose") else False)

    session = get_aws_session(args.profile if hasattr(args, "profile") else None)
    analyzer = WAFAnalyzer(session, args.region if hasattr(args, "region") else "us-east-1")

    if args.waf_command == "list":
        web_acls = analyzer.list_web_acls(args.scope)

        if hasattr(args, "output") and args.output == "json":
            print(format_json(web_acls))
        elif hasattr(args, "output") and args.output == "yaml":
            print(format_yaml(web_acls))
        else:
            headers = ["Name", "ID", "ARN", "Description"]
            rows = []
            for acl in web_acls:
                description = acl.get("Description", "N/A")
                if len(description) > 50:
                    description = description[:50] + "..."
                rows.append(
                    [
                        acl.get("Name", "N/A"),
                        acl.get("Id", "N/A")[:20] + "..." if len(acl.get("Id", "")) > 20 else acl.get("Id", "N/A"),
                        acl.get("ARN", "N/A")[:60] + "..." if len(acl.get("ARN", "")) > 60 else acl.get("ARN", "N/A"),
                        description,
                    ]
                )
            print(format_table(headers, rows, f"Web ACLs ({args.scope})"))

    elif args.waf_command == "stats":
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=args.hours)

        # Get basic metrics
        blocked_requests = analyzer.get_waf_metrics(args.web_acl, "BlockedRequests", start_time, end_time)
        allowed_requests = analyzer.get_waf_metrics(args.web_acl, "AllowedRequests", start_time, end_time)

        total_blocked = sum(point.get("Sum", 0) for point in blocked_requests)
        total_allowed = sum(point.get("Sum", 0) for point in allowed_requests)
        total_requests = total_blocked + total_allowed

        stats = {
            "web_acl": args.web_acl,
            "time_range_hours": args.hours,
            "total_requests": total_requests,
            "blocked_requests": total_blocked,
            "allowed_requests": total_allowed,
            "block_rate_percent": round((total_blocked / total_requests * 100) if total_requests > 0 else 0, 2),
            "recent_activity": {
                "last_hour_blocked": (
                    sum(point.get("Sum", 0) for point in blocked_requests[-12:]) if blocked_requests else 0
                ),
                "last_hour_allowed": (
                    sum(point.get("Sum", 0) for point in allowed_requests[-12:]) if allowed_requests else 0
                ),
            },
        }

        if hasattr(args, "output") and args.output == "json":
            print(format_json(stats))
        elif hasattr(args, "output") and args.output == "yaml":
            print(format_yaml(stats))
        else:
            headers = ["Metric", "Value"]
            rows = [
                ["Web ACL", stats["web_acl"]],
                ["Time Range (hours)", stats["time_range_hours"]],
                ["Total Requests", f"{stats['total_requests']:,}"],
                ["Blocked Requests", f"{stats['blocked_requests']:,}"],
                ["Allowed Requests", f"{stats['allowed_requests']:,}"],
                ["Block Rate", f"{stats['block_rate_percent']}%"],
                ["Last Hour Blocked", f"{stats['recent_activity']['last_hour_blocked']:,}"],
                ["Last Hour Allowed", f"{stats['recent_activity']['last_hour_allowed']:,}"],
            ]
            print(format_table(headers, rows, f"WAF Statistics - {args.web_acl}"))

    elif args.waf_command == "rule-stats":
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=args.hours)

        rule_metrics = analyzer.get_rule_metrics(args.web_acl, args.rule, start_time, end_time)

        blocked_total = sum(point.get("Sum", 0) for point in rule_metrics.get("blocked_requests", []))
        allowed_total = sum(point.get("Sum", 0) for point in rule_metrics.get("allowed_requests", []))

        rule_stats = {
            "web_acl": args.web_acl,
            "rule": args.rule,
            "blocked_by_rule": blocked_total,
            "allowed_by_rule": allowed_total,
            "rule_effectiveness": round(
                (blocked_total / (blocked_total + allowed_total) * 100) if (blocked_total + allowed_total) > 0 else 0, 2
            ),
        }

        if hasattr(args, "output") and args.output == "json":
            print(format_json(rule_stats))
        else:
            headers = ["Metric", "Value"]
            rows = [
                ["Web ACL", rule_stats["web_acl"]],
                ["Rule", rule_stats["rule"]],
                ["Blocked by Rule", f"{rule_stats['blocked_by_rule']:,}"],
                ["Allowed by Rule", f"{rule_stats['allowed_by_rule']:,}"],
                ["Rule Effectiveness", f"{rule_stats['rule_effectiveness']}%"],
            ]
            print(format_table(headers, rows, f"Rule Statistics - {args.rule}"))

    elif args.waf_command == "troubleshoot":
        report = analyzer.generate_troubleshooting_report(args.web_acl, args.hours)

        if hasattr(args, "output") and args.output == "json":
            print(format_json(report))
        elif hasattr(args, "output") and args.output == "yaml":
            print(format_yaml(report))
        else:
            # Print summary table
            headers = ["Metric", "Value"]
            rows = [
                ["Web ACL", report["web_acl"]],
                ["Analysis Period", f"{report['time_range']['hours']} hours"],
                ["Total Requests", f"{report['metrics']['total_requests']:,}"],
                ["Blocked Requests", f"{report['metrics']['total_blocked']:,}"],
                ["Block Rate", f"{report['metrics']['block_rate']:.2f}%"],
                ["High Block Rate", "Yes" if report["analysis"].get("high_block_rate") else "No"],
                ["Recent Spike", "Yes" if report["analysis"].get("recent_spike") else "No"],
            ]
            print(format_table(headers, rows, f"WAF Troubleshooting Report - {args.web_acl}"))

            # Print recommendations
            if report["recommendations"]:
                print("\n🔍 Recommendations:")
                for i, rec in enumerate(report["recommendations"], 1):
                    print(f"  {i}. {rec}")

    elif args.waf_command == "requests":
        sampled_requests = analyzer.get_sampled_requests(args.web_acl_arn, args.rule, args.scope, args.max_items)
        patterns = analyzer.analyze_request_patterns(sampled_requests)

        if hasattr(args, "output") and args.output == "json":
            print(format_json(patterns))
        else:
            print(f"\n📊 Request Analysis for Rule: {args.rule}")
            print(f"Total Samples: {patterns['total_samples']}")
            print(f"Blocked: {patterns['blocked_count']}, Allowed: {patterns['allowed_count']}")

            if patterns["top_source_ips"]:
                print("\n🌐 Top Source IPs:")
                for ip, count in list(patterns["top_source_ips"].items())[:5]:
                    print(f"  {ip}: {count} requests")

            if patterns["top_countries"]:
                print("\n🌍 Top Countries:")
                for country, count in list(patterns["top_countries"].items())[:5]:
                    print(f"  {country}: {count} requests")

            if patterns["request_methods"]:
                print("\n📝 HTTP Methods:")
                for method, count in patterns["request_methods"].items():
                    print(f"  {method}: {count} requests")

    elif args.waf_command == "rate-limiting":
        rate_metrics = analyzer.get_rate_limiting_metrics(args.web_acl, args.hours)

        if hasattr(args, "output") and args.output == "json":
            print(format_json(rate_metrics))
        else:
            analysis = rate_metrics.get("analysis", {})
            headers = ["Metric", "Value"]
            rows = [
                ["Web ACL", args.web_acl],
                ["Analysis Period", f"{args.hours} hours"],
                ["Total Blocked", f"{analysis.get('total_blocked', 0):,}"],
                ["Peak Blocks/Min", f"{analysis.get('peak_blocks_per_minute', 0):,}"],
                ["Avg Blocks/Min", f"{analysis.get('average_blocks_per_minute', 0):.2f}"],
            ]
            print(format_table(headers, rows, f"Rate Limiting Analysis - {args.web_acl}"))

    else:
        logger.error(f"Unknown WAF command: {args.waf_command}")


if __name__ == "__main__":
    # For testing
    parser = argparse.ArgumentParser(description="WAF Statistics and Troubleshooting")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--output", choices=["json", "yaml", "table"], default="table")
    parser.add_argument("--verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="command")
    add_waf_parser(subparsers)

    args = parser.parse_args()

    if args.command == "waf":
        handle_waf_command(args)
