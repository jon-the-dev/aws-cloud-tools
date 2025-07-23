"""RDS command module for AWS Cloud Utilities."""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.exceptions import AWSCloudUtilitiesError

console = Console()
logger = logging.getLogger(__name__)


class RDSManager:
    """RDS management and troubleshooting operations."""

    def __init__(self, config: Config, aws_auth: AWSAuth):
        """Initialize RDS manager.

        Args:
            config: Configuration object
            aws_auth: AWS authentication object
        """
        self.config = config
        self.aws_auth = aws_auth
        self.session = aws_auth.session
        self.rds_client = self.session.client("rds")
        self.cloudwatch_client = self.session.client("cloudwatch")

    def troubleshoot_mysql_connections(self, db_instance_identifier: str) -> Dict[str, Any]:
        """Troubleshoot MySQL RDS connection issues.

        Args:
            db_instance_identifier: RDS instance identifier

        Returns:
            Dictionary containing troubleshooting information
        """
        logger.info(f"Troubleshooting MySQL connections for {db_instance_identifier}")

        results = {
            "instance_info": {},
            "connection_metrics": {},
            "parameter_info": {},
            "error_logs": {},
            "recommendations": [],
        }

        try:
            # Get instance information
            results["instance_info"] = self._get_instance_info(db_instance_identifier)

            # Get connection metrics from CloudWatch
            results["connection_metrics"] = self._get_connection_metrics(db_instance_identifier)

            # Get parameter group information
            results["parameter_info"] = self._get_parameter_info(db_instance_identifier)

            # Get error logs
            results["error_logs"] = self._get_error_logs(db_instance_identifier)

            # Generate recommendations
            results["recommendations"] = self._generate_recommendations(results)

        except Exception as e:
            logger.error(f"Error troubleshooting MySQL connections: {e}")
            results["error"] = str(e)

        return results

    def _get_instance_info(self, db_instance_identifier: str) -> Dict[str, Any]:
        """Get RDS instance information."""
        try:
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)

            instance = response["DBInstances"][0]

            return {
                "instance_class": instance.get("DBInstanceClass"),
                "engine": instance.get("Engine"),
                "engine_version": instance.get("EngineVersion"),
                "status": instance.get("DBInstanceStatus"),
                "allocated_storage": instance.get("AllocatedStorage"),
                "max_allocated_storage": instance.get("MaxAllocatedStorage"),
                "multi_az": instance.get("MultiAZ"),
                "vpc_security_groups": [sg["VpcSecurityGroupId"] for sg in instance.get("VpcSecurityGroups", [])],
                "parameter_groups": [pg["DBParameterGroupName"] for pg in instance.get("DBParameterGroups", [])],
                "endpoint": instance.get("Endpoint", {}).get("Address"),
                "port": instance.get("Endpoint", {}).get("Port"),
                "backup_retention_period": instance.get("BackupRetentionPeriod"),
                "preferred_backup_window": instance.get("PreferredBackupWindow"),
                "preferred_maintenance_window": instance.get("PreferredMaintenanceWindow"),
                "performance_insights_enabled": instance.get("PerformanceInsightsEnabled", False),
            }

        except Exception as e:
            logger.error(f"Error getting instance info: {e}")
            return {"error": str(e)}

    def _get_connection_metrics(self, db_instance_identifier: str) -> Dict[str, Any]:
        """Get connection-related CloudWatch metrics."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        metrics_to_fetch = [
            "DatabaseConnections",
            "ConnectionAttempts",
            "AbortedConnections",
            "ThreadsConnected",
            "ThreadsRunning",
        ]

        metrics_data = {}

        for metric_name in metrics_to_fetch:
            try:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace="AWS/RDS",
                    MetricName=metric_name,
                    Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_instance_identifier}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5 minutes
                    Statistics=["Average", "Maximum"],
                )

                if response["Datapoints"]:
                    # Sort by timestamp
                    datapoints = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])

                    metrics_data[metric_name] = {
                        "current_avg": round(datapoints[-1].get("Average", 0), 2),
                        "current_max": round(datapoints[-1].get("Maximum", 0), 2),
                        "peak_avg": round(max(dp.get("Average", 0) for dp in datapoints), 2),
                        "peak_max": round(max(dp.get("Maximum", 0) for dp in datapoints), 2),
                        "datapoints_count": len(datapoints),
                    }
                else:
                    metrics_data[metric_name] = {"error": "No data available"}

            except Exception as e:
                logger.error(f"Error getting metric {metric_name}: {e}")
                metrics_data[metric_name] = {"error": str(e)}

        return metrics_data

    def _get_parameter_info(self, db_instance_identifier: str) -> Dict[str, Any]:
        """Get parameter group information."""
        try:
            # Get instance info first
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)

            instance = response["DBInstances"][0]
            parameter_groups = instance.get("DBParameterGroups", [])

            results = {}

            for pg in parameter_groups:
                pg_name = pg["DBParameterGroupName"]

                # Get parameters
                params_response = self.rds_client.describe_db_parameters(DBParameterGroupName=pg_name)

                # Filter connection-related parameters
                connection_params = {}
                for param in params_response.get("Parameters", []):
                    param_name = param.get("ParameterName", "")
                    if any(
                        keyword in param_name.lower()
                        for keyword in [
                            "max_connections",
                            "connect_timeout",
                            "wait_timeout",
                            "interactive_timeout",
                            "thread_cache_size",
                            "thread_stack",
                            "max_user_connections",
                        ]
                    ):
                        connection_params[param_name] = {
                            "value": param.get("ParameterValue", "Not Set"),
                            "source": param.get("Source"),
                            "is_modifiable": param.get("IsModifiable"),
                            "description": (
                                param.get("Description", "")[:100] + "..." if param.get("Description", "") else ""
                            ),
                        }

                results[pg_name] = {
                    "status": pg.get("ParameterApplyStatus"),
                    "connection_parameters": connection_params,
                }

            return results

        except Exception as e:
            logger.error(f"Error getting parameter groups: {e}")
            return {"error": str(e)}

    def _get_error_logs(self, db_instance_identifier: str) -> Dict[str, Any]:
        """Get MySQL error logs."""
        try:
            # List log files
            response = self.rds_client.describe_db_log_files(DBInstanceIdentifier=db_instance_identifier)

            error_logs = [
                log for log in response.get("DescribeDBLogFiles", []) if "error" in log.get("LogFileName", "").lower()
            ]

            if not error_logs:
                return {"error": "No error logs found"}

            # Get the most recent error log
            latest_log = max(error_logs, key=lambda x: x.get("LastWritten", 0))
            log_file_name = latest_log["LogFileName"]

            # Download log file content (last 500 lines)
            response = self.rds_client.download_db_log_file_portion(
                DBInstanceIdentifier=db_instance_identifier, LogFileName=log_file_name, NumberOfLines=500
            )

            log_content = response.get("LogFileData", "")

            # Look for connection-related errors
            connection_errors = []
            for line in log_content.split("\n"):
                if any(
                    keyword in line.lower()
                    for keyword in [
                        "too many connections",
                        "connection refused",
                        "max_connections",
                        "aborted connection",
                        "got timeout",
                        "connection reset",
                        "user limit",
                    ]
                ):
                    connection_errors.append(line.strip())

            return {
                "log_file_name": log_file_name,
                "log_size": latest_log.get("Size", 0),
                "last_written": latest_log.get("LastWritten"),
                "connection_errors": connection_errors[-10:],  # Last 10 connection errors
                "total_connection_errors": len(connection_errors),
            }

        except Exception as e:
            logger.error(f"Error getting error logs: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate troubleshooting recommendations."""
        recommendations = []

        # Check connection metrics
        metrics = results.get("connection_metrics", {})
        db_connections = metrics.get("DatabaseConnections", {})

        if isinstance(db_connections, dict) and "peak_max" in db_connections:
            peak_connections = db_connections["peak_max"]

            if peak_connections > 80:  # Assuming default max_connections is around 100
                recommendations.append(
                    f"🔴 HIGH: Peak connection count detected ({peak_connections}). "
                    "Consider increasing max_connections parameter or implementing connection pooling."
                )

        # Check for aborted connections
        aborted_connections = metrics.get("AbortedConnections", {})
        if isinstance(aborted_connections, dict) and "peak_max" in aborted_connections:
            if aborted_connections["peak_max"] > 10:
                recommendations.append(
                    f"🟡 MEDIUM: High aborted connections ({aborted_connections['peak_max']}). "
                    "Check for network issues, connection timeouts, or application connection handling."
                )

        # Check error logs
        error_logs = results.get("error_logs", {})
        if "total_connection_errors" in error_logs and error_logs["total_connection_errors"] > 0:
            recommendations.append(
                f"🔴 HIGH: Found {error_logs['total_connection_errors']} connection-related errors in logs. "
                "Review error log details for specific issues."
            )

        # Check instance class
        instance_info = results.get("instance_info", {})
        instance_class = instance_info.get("instance_class", "")
        if instance_class and ("t2." in instance_class or "t3." in instance_class):
            recommendations.append(
                "🟡 MEDIUM: Using burstable instance type. Consider upgrading to a larger instance class "
                "if consistent performance is needed."
            )

        # Check Performance Insights
        if not instance_info.get("performance_insights_enabled", False):
            recommendations.append("🟢 LOW: Enable Performance Insights for detailed query and connection analysis.")

        # General recommendations
        recommendations.extend(
            [
                "🟢 LOW: Review application connection pooling configuration.",
                "🟢 LOW: Check security group rules for unnecessary open connections.",
                "🟢 LOW: Monitor CloudWatch metrics regularly for connection patterns.",
                "🟢 LOW: Consider implementing read replicas to distribute connection load.",
            ]
        )

        return recommendations


def display_troubleshooting_results(results: Dict[str, Any], db_instance_identifier: str) -> None:
    """Display troubleshooting results in a formatted way."""

    console.print(f"\n[bold blue]MySQL Connection Troubleshooting Report[/bold blue]")
    console.print(f"[dim]Instance: {db_instance_identifier}[/dim]\n")

    # Instance Information
    instance_info = results.get("instance_info", {})
    if instance_info and "error" not in instance_info:
        table = Table(title="Instance Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        for key, value in instance_info.items():
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            table.add_row(key.replace("_", " ").title(), str(value))

        console.print(table)
        console.print()

    # Connection Metrics
    metrics = results.get("connection_metrics", {})
    if metrics:
        table = Table(title="Connection Metrics (Last 24 Hours)", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Current Avg", style="white")
        table.add_column("Current Max", style="white")
        table.add_column("Peak Avg", style="yellow")
        table.add_column("Peak Max", style="red")

        for metric_name, data in metrics.items():
            if isinstance(data, dict) and "error" not in data:
                table.add_row(
                    metric_name,
                    str(data.get("current_avg", "N/A")),
                    str(data.get("current_max", "N/A")),
                    str(data.get("peak_avg", "N/A")),
                    str(data.get("peak_max", "N/A")),
                )

        console.print(table)
        console.print()

    # Parameter Information
    param_info = results.get("parameter_info", {})
    if param_info and "error" not in param_info:
        for pg_name, pg_data in param_info.items():
            connection_params = pg_data.get("connection_parameters", {})
            if connection_params:
                table = Table(title=f"Connection Parameters - {pg_name}", show_header=True, header_style="bold magenta")
                table.add_column("Parameter", style="cyan")
                table.add_column("Value", style="white")
                table.add_column("Source", style="yellow")
                table.add_column("Modifiable", style="green")

                for param_name, param_data in connection_params.items():
                    table.add_row(
                        param_name,
                        str(param_data.get("value", "N/A")),
                        str(param_data.get("source", "N/A")),
                        str(param_data.get("is_modifiable", "N/A")),
                    )

                console.print(table)
                console.print()

    # Error Logs
    error_logs = results.get("error_logs", {})
    if error_logs and "error" not in error_logs:
        if error_logs.get("connection_errors"):
            console.print(
                Panel.fit(
                    "\n".join(error_logs["connection_errors"]),
                    title=f"Recent Connection Errors ({error_logs.get('total_connection_errors', 0)} total)",
                    border_style="red",
                )
            )
            console.print()

    # Recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        console.print("[bold green]Recommendations:[/bold green]")
        for i, rec in enumerate(recommendations, 1):
            console.print(f"{i}. {rec}")
        console.print()


@click.group(name="rds")
@click.pass_context
def rds_group(ctx: click.Context) -> None:
    """RDS management and troubleshooting commands."""
    pass


@rds_group.command(name="troubleshoot-mysql")
@click.argument("db_instance_identifier")
@click.option("--output-file", help="Save detailed results to JSON file")
@click.pass_context
def troubleshoot_mysql(ctx: click.Context, db_instance_identifier: str, output_file: Optional[str]) -> None:
    """Troubleshoot MySQL RDS connection issues.

    This command analyzes your MySQL RDS instance for connection-related issues
    including 'too many connections' errors. It examines CloudWatch metrics,
    parameter groups, error logs, and provides actionable recommendations.

    Args:
        DB_INSTANCE_IDENTIFIER: The RDS instance identifier to troubleshoot

    Examples:
        aws-cloud-utilities rds troubleshoot-mysql my-mysql-db
        aws-cloud-utilities rds troubleshoot-mysql my-mysql-db --output-file results.json
    """
    try:
        config: Config = ctx.obj["config"]
        aws_auth: AWSAuth = ctx.obj["aws_auth"]

        rds_manager = RDSManager(config, aws_auth)

        with console.status(f"[bold green]Analyzing MySQL instance {db_instance_identifier}..."):
            results = rds_manager.troubleshoot_mysql_connections(db_instance_identifier)

        if "error" in results:
            console.print(f"[red]Error:[/red] {results['error']}")
            return

        # Display results
        display_troubleshooting_results(results, db_instance_identifier)

        # Save to file if requested
        if output_file:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
            console.print(f"[green]Detailed results saved to {output_file}[/green]")

    except AWSCloudUtilitiesError as e:
        console.print(f"[red]AWS Cloud Utilities Error:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        if ctx.obj.get("config", {}).debug:
            console.print_exception()


@rds_group.command(name="list-instances")
@click.option("--engine", help="Filter by database engine (e.g., mysql, postgres)")
@click.option("--status", help="Filter by instance status (e.g., available, stopped)")
@click.pass_context
def list_instances(ctx: click.Context, engine: Optional[str], status: Optional[str]) -> None:
    """List RDS instances in the current region.

    Examples:
        aws-cloud-utilities rds list-instances
        aws-cloud-utilities rds list-instances --engine mysql
        aws-cloud-utilities rds list-instances --status available
    """
    try:
        config: Config = ctx.obj["config"]
        aws_auth: AWSAuth = ctx.obj["aws_auth"]

        session = aws_auth.session
        rds_client = session.client("rds")

        with console.status("[bold green]Fetching RDS instances..."):
            response = rds_client.describe_db_instances()

        instances = response.get("DBInstances", [])

        # Apply filters
        if engine:
            instances = [i for i in instances if i.get("Engine", "").lower() == engine.lower()]

        if status:
            instances = [i for i in instances if i.get("DBInstanceStatus", "").lower() == status.lower()]

        if not instances:
            console.print("[yellow]No RDS instances found matching the criteria.[/yellow]")
            return

        # Display results
        table = Table(title="RDS Instances", show_header=True, header_style="bold magenta")
        table.add_column("Instance ID", style="cyan")
        table.add_column("Engine", style="white")
        table.add_column("Version", style="white")
        table.add_column("Class", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Multi-AZ", style="blue")
        table.add_column("Endpoint", style="dim")

        for instance in instances:
            table.add_row(
                instance.get("DBInstanceIdentifier", "N/A"),
                instance.get("Engine", "N/A"),
                instance.get("EngineVersion", "N/A"),
                instance.get("DBInstanceClass", "N/A"),
                instance.get("DBInstanceStatus", "N/A"),
                str(instance.get("MultiAZ", False)),
                instance.get("Endpoint", {}).get("Address", "N/A"),
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(instances)} instances[/dim]")

    except AWSCloudUtilitiesError as e:
        console.print(f"[red]AWS Cloud Utilities Error:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        if ctx.obj.get("config", {}).debug:
            console.print_exception()
