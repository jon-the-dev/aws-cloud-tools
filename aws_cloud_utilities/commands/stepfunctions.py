"""AWS Step Functions management and monitoring commands."""

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
from ..core.utils import print_output, save_to_file, get_timestamp, get_detailed_timestamp, ensure_directory
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="stepfunctions")
def stepfunctions_group():
    """AWS Step Functions management and monitoring commands."""
    pass


@stepfunctions_group.command(name="list")
@click.option("--region", help="AWS region to list state machines from (default: current region)")
@click.option("--all-regions", is_flag=True, help="List state machines from all regions")
@click.option("--output-file", help="Output file for state machines list (supports .json, .yaml, .csv)")
@click.pass_context
def list_state_machines(
    ctx: click.Context, region: Optional[str], all_regions: bool, output_file: Optional[str]
) -> None:
    """List all Step Functions state machines."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Determine regions to scan
        if all_regions:
            target_regions = aws_auth.get_available_regions("stepfunctions")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]

        all_state_machines = []

        for target_region in target_regions:
            sf_client = aws_auth.get_client("stepfunctions", region_name=target_region)

            try:
                paginator = sf_client.get_paginator("list_state_machines")

                for page in paginator.paginate():
                    for machine in page.get("stateMachines", []):
                        all_state_machines.append(
                            {
                                "Name": machine.get("name", ""),
                                "Region": target_region,
                                "Type": machine.get("type", ""),
                                "Status": machine.get("status", ""),
                                "Created": (
                                    machine.get("creationDate", "").strftime("%Y-%m-%d %H:%M")
                                    if machine.get("creationDate")
                                    else ""
                                ),
                                "State Machine ARN": machine.get("stateMachineArn", ""),
                            }
                        )

            except Exception as e:
                logger.warning(f"Error listing state machines in region {target_region}: {e}")

        if all_state_machines:
            print_output(
                all_state_machines,
                output_format=config.aws_output_format,
                title=f"Step Functions State Machines ({len(all_state_machines)} found)",
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

                save_to_file(all_state_machines, output_path, file_format)
                console.print(f"[green]State machines list saved to:[/green] {output_path}")
        else:
            console.print("[yellow]No Step Functions state machines found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing state machines:[/red] {e}")
        raise click.Abort()


@stepfunctions_group.command(name="describe")
@click.argument("state_machine_arn")
@click.option("--show-definition", is_flag=True, help="Show the state machine definition")
@click.option("--output-file", help="Output file for state machine details (supports .json, .yaml)")
@click.pass_context
def describe_state_machine(
    ctx: click.Context, state_machine_arn: str, show_definition: bool, output_file: Optional[str]
) -> None:
    """Get detailed information about a Step Functions state machine."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Extract region from ARN
        region = _extract_region_from_arn(state_machine_arn)
        sf_client = aws_auth.get_client("stepfunctions", region_name=region)

        # Get state machine details
        try:
            response = sf_client.describe_state_machine(stateMachineArn=state_machine_arn)
        except sf_client.exceptions.StateMachineDoesNotExist:
            console.print(f"[red]State machine not found:[/red] {state_machine_arn}")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]Error describing state machine:[/red] {e}")
            raise click.Abort()

        # Format basic information
        machine_info = {
            "Name": response.get("name", ""),
            "ARN": response.get("stateMachineArn", ""),
            "Status": response.get("status", ""),
            "Type": response.get("type", ""),
            "Role ARN": response.get("roleArn", ""),
            "Created": (
                response.get("creationDate", "").strftime("%Y-%m-%d %H:%M:%S") if response.get("creationDate") else ""
            ),
            "Updated": (
                response.get("updateDate", "").strftime("%Y-%m-%d %H:%M:%S") if response.get("updateDate") else ""
            ),
            "Region": region,
        }

        print_output(
            machine_info,
            output_format=config.aws_output_format,
            title=f"State Machine Details: {response.get('name', '')}",
        )

        # Show definition if requested
        if show_definition:
            definition = response.get("definition", "")
            if definition:
                console.print("\n[bold]State Machine Definition:[/bold]")
                try:
                    # Try to parse and pretty-print JSON
                    parsed_definition = json.loads(definition)
                    console.print_json(json.dumps(parsed_definition, indent=2))
                except json.JSONDecodeError:
                    console.print(definition)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            # Include definition in saved data
            save_data = response.copy()
            if "creationDate" in save_data:
                save_data["creationDate"] = save_data["creationDate"].isoformat()
            if "updateDate" in save_data:
                save_data["updateDate"] = save_data["updateDate"].isoformat()

            save_to_file(save_data, output_path, file_format)
            console.print(f"[green]State machine details saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error describing state machine:[/red] {e}")
        raise click.Abort()


@stepfunctions_group.command(name="execute")
@click.argument("state_machine_arn")
@click.option("--input", default="{}", help="JSON input for the execution (default: {})")
@click.option("--name", help="Name for the execution (auto-generated if not provided)")
@click.option("--wait", is_flag=True, help="Wait for execution to complete")
@click.option("--timeout", type=int, default=300, help="Timeout in seconds for execution wait (default: 300)")
@click.pass_context
def execute_state_machine(
    ctx: click.Context, state_machine_arn: str, input: str, name: Optional[str], wait: bool, timeout: int
) -> None:
    """Start an execution of a Step Functions state machine."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Extract region from ARN
        region = _extract_region_from_arn(state_machine_arn)
        sf_client = aws_auth.get_client("stepfunctions", region_name=region)

        # Validate JSON input
        try:
            input_data = json.loads(input)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON input provided[/red]")
            raise click.Abort()

        # Generate execution name if not provided
        if not name:
            name = f"execution-{get_timestamp()}"

        console.print(f"[blue]Starting execution:[/blue] {name}")
        console.print(f"[dim]State Machine: {state_machine_arn}[/dim]")

        # Start execution
        try:
            response = sf_client.start_execution(
                stateMachineArn=state_machine_arn, name=name, input=json.dumps(input_data)
            )
            execution_arn = response["executionArn"]

            console.print(f"[green]✅ Execution started successfully[/green]")
            console.print(f"[dim]Execution ARN: {execution_arn}[/dim]")

        except Exception as e:
            console.print(f"[red]Error starting execution:[/red] {e}")
            raise click.Abort()

        # Wait for completion if requested
        if wait:
            console.print("[yellow]Waiting for execution to complete...[/yellow]")

            execution_result = _wait_for_execution(sf_client, execution_arn, timeout)

            if execution_result:
                status = execution_result.get("status", "UNKNOWN")

                if status == "SUCCEEDED":
                    console.print("[green]✅ Execution completed successfully[/green]")

                    output = execution_result.get("output")
                    if output:
                        console.print("\n[bold]Execution Output:[/bold]")
                        try:
                            parsed_output = json.loads(output)
                            console.print_json(json.dumps(parsed_output, indent=2))
                        except json.JSONDecodeError:
                            console.print(output)

                elif status == "FAILED":
                    console.print("[red]❌ Execution failed[/red]")
                    error = execution_result.get("error", "Unknown error")
                    console.print(f"[red]Error:[/red] {error}")

                elif status == "TIMED_OUT":
                    console.print("[yellow]⏰ Execution timed out[/yellow]")

                else:
                    console.print(f"[yellow]Execution status:[/yellow] {status}")
            else:
                console.print("[yellow]⚠️  Execution monitoring timed out[/yellow]")

    except Exception as e:
        console.print(f"[red]Error executing state machine:[/red] {e}")
        raise click.Abort()


@stepfunctions_group.command(name="list-executions")
@click.argument("state_machine_arn")
@click.option(
    "--status",
    type=click.Choice(["RUNNING", "SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"]),
    help="Filter executions by status",
)
@click.option("--max-results", type=int, default=10, help="Maximum number of executions to list (default: 10)")
@click.option("--output-file", help="Output file for executions list (supports .json, .yaml, .csv)")
@click.pass_context
def list_executions(
    ctx: click.Context, state_machine_arn: str, status: Optional[str], max_results: int, output_file: Optional[str]
) -> None:
    """List executions of a Step Functions state machine."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Extract region from ARN
        region = _extract_region_from_arn(state_machine_arn)
        sf_client = aws_auth.get_client("stepfunctions", region_name=region)

        # List executions
        list_params = {"stateMachineArn": state_machine_arn, "maxResults": max_results}

        if status:
            list_params["statusFilter"] = status

        try:
            response = sf_client.list_executions(**list_params)
            executions = response.get("executions", [])
        except Exception as e:
            console.print(f"[red]Error listing executions:[/red] {e}")
            raise click.Abort()

        if executions:
            formatted_executions = []
            for execution in executions:
                formatted_executions.append(
                    {
                        "Name": execution.get("name", ""),
                        "Status": execution.get("status", ""),
                        "Started": (
                            execution.get("startDate", "").strftime("%Y-%m-%d %H:%M:%S")
                            if execution.get("startDate")
                            else ""
                        ),
                        "Stopped": (
                            execution.get("stopDate", "").strftime("%Y-%m-%d %H:%M:%S")
                            if execution.get("stopDate")
                            else ""
                        ),
                        "Execution ARN": execution.get("executionArn", ""),
                    }
                )

            print_output(
                formatted_executions,
                output_format=config.aws_output_format,
                title=f"Step Functions Executions ({len(formatted_executions)} found)",
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

                save_to_file(formatted_executions, output_path, file_format)
                console.print(f"[green]Executions list saved to:[/green] {output_path}")
        else:
            console.print("[yellow]No executions found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing executions:[/red] {e}")
        raise click.Abort()


@stepfunctions_group.command(name="logs")
@click.argument("execution_arn")
@click.argument("log_group")
@click.option("--lines", type=int, default=100, help="Maximum number of log lines to retrieve (default: 100)")
@click.option("--output-file", help="Output file for logs (supports .txt, .json)")
@click.pass_context
def show_execution_logs(
    ctx: click.Context, execution_arn: str, log_group: str, lines: int, output_file: Optional[str]
) -> None:
    """Show CloudWatch logs for a Step Functions execution."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Extract region from ARN
        region = _extract_region_from_arn(execution_arn)
        sf_client = aws_auth.get_client("stepfunctions", region_name=region)
        logs_client = aws_auth.get_client("logs", region_name=region)

        # Get execution details to determine time range
        try:
            execution_details = sf_client.describe_execution(executionArn=execution_arn)
            start_time = execution_details.get("startDate")
            stop_time = execution_details.get("stopDate") or datetime.now()
        except Exception as e:
            console.print(f"[red]Error getting execution details:[/red] {e}")
            raise click.Abort()

        # Convert to milliseconds for CloudWatch Logs
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(stop_time.timestamp() * 1000)

        # Extract execution name for filtering
        execution_name = execution_arn.split(":")[-1]
        filter_pattern = f'"{execution_name}"'

        console.print(f"[blue]Retrieving logs for execution:[/blue] {execution_name}")
        console.print(f"[dim]Log Group: {log_group}[/dim]")

        # Get logs
        try:
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time_ms,
                endTime=end_time_ms,
                filterPattern=filter_pattern,
                limit=lines,
            )

            events = response.get("events", [])

            if events:
                console.print(f"\n[green]Found {len(events)} log events:[/green]\n")

                log_lines = []
                for event in events:
                    timestamp = datetime.fromtimestamp(event["timestamp"] / 1000)
                    message = event["message"]
                    log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {message}"
                    console.print(log_line)
                    log_lines.append(log_line)

                # Save to file if requested
                if output_file:
                    output_path = Path(output_file)

                    # Add timestamp to filename
                    timestamp = get_timestamp()
                    stem = output_path.stem
                    suffix = output_path.suffix or ".txt"
                    new_filename = f"{stem}_{timestamp}{suffix}"
                    output_path = output_path.parent / new_filename

                    if suffix.lower() == ".json":
                        # Save as JSON with structured data
                        log_data = {
                            "execution_arn": execution_arn,
                            "log_group": log_group,
                            "retrieved_at": datetime.now().isoformat(),
                            "events": [
                                {
                                    "timestamp": datetime.fromtimestamp(event["timestamp"] / 1000).isoformat(),
                                    "message": event["message"],
                                }
                                for event in events
                            ],
                        }
                        save_to_file(log_data, output_path, "json")
                    else:
                        # Save as plain text
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(log_lines))

                    console.print(f"\n[green]Logs saved to:[/green] {output_path}")
            else:
                console.print("[yellow]No log events found for the specified execution[/yellow]")

        except Exception as e:
            console.print(f"[red]Error retrieving logs:[/red] {e}")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error showing execution logs:[/red] {e}")
        raise click.Abort()


def _extract_region_from_arn(arn: str) -> str:
    """Extract AWS region from an ARN."""
    try:
        return arn.split(":")[3]
    except IndexError:
        raise ValueError(f"Invalid ARN format: {arn}")


def _wait_for_execution(sf_client, execution_arn: str, timeout: int) -> Optional[Dict[str, Any]]:
    """Wait for Step Functions execution to complete."""
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = sf_client.describe_execution(executionArn=execution_arn)
            status = response.get("status")

            if status in ["SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"]:
                return response

        except Exception as e:
            logger.debug(f"Error checking execution status: {e}")

        time.sleep(5)

    return None
