"""Common utilities for AWS Cloud Utilities."""

import os
import json
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from tabulate import tabulate

from .exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


def get_aws_account_id() -> str:
    """Get the current AWS account ID.

    Returns:
        AWS account ID

    Raises:
        AWSError: If unable to get account ID
    """
    try:
        sts_client = boto3.client("sts")
        response = sts_client.get_caller_identity()
        return response["Account"]
    except ClientError as e:
        raise AWSError(f"Failed to get AWS account ID: {e}")


def get_all_regions(service_name: str = "ec2") -> List[str]:
    """Get all available AWS regions for a service.

    Args:
        service_name: AWS service name

    Returns:
        List of region names
    """
    try:
        client = boto3.client(service_name)
        if hasattr(client, "describe_regions"):
            response = client.describe_regions()
            return [region["RegionName"] for region in response["Regions"]]
        else:
            session = boto3.Session()
            return list(session.get_available_regions(service_name))
    except Exception as e:
        logger.warning(f"Failed to get regions for {service_name}: {e}")
        # Return common regions as fallback
        return [
            "us-east-1",
            "us-east-2",
            "us-west-1",
            "us-west-2",
            "eu-west-1",
            "eu-west-2",
            "eu-central-1",
            "eu-north-1",
            "ap-southeast-1",
            "ap-southeast-2",
            "ap-northeast-1",
            "ap-northeast-2",
            "ap-south-1",
            "ca-central-1",
            "sa-east-1",
        ]


def format_output(data: Any, output_format: str = "table", headers: Optional[List[str]] = None) -> str:
    """Format data for output.

    Args:
        data: Data to format
        output_format: Output format (table, json, yaml, csv)
        headers: Table headers (for table format)

    Returns:
        Formatted string
    """
    if output_format == "json":
        return json.dumps(data, indent=2, default=str)
    elif output_format == "yaml":
        return yaml.dump(data, default_flow_style=False)
    elif output_format == "csv":
        if isinstance(data, list) and data and isinstance(data[0], dict):
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        else:
            return str(data)
    elif output_format == "table":
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                headers = headers or list(data[0].keys())
                rows = [[item.get(header, "") for header in headers] for item in data]
                return tabulate(rows, headers=headers, tablefmt="grid")
            else:
                return tabulate(data, headers=headers or [], tablefmt="grid")
        elif isinstance(data, dict):
            rows = [[k, v] for k, v in data.items()]
            return tabulate(rows, headers=["Key", "Value"], tablefmt="grid")
        else:
            return str(data)
    else:
        return str(data)


def print_output(
    data: Any, output_format: str = "table", headers: Optional[List[str]] = None, title: Optional[str] = None
) -> None:
    """Print formatted output to console.

    Args:
        data: Data to print
        output_format: Output format
        headers: Table headers
        title: Optional title
    """
    if title:
        console.print(f"\n[bold blue]{title}[/bold blue]")

    formatted_output = format_output(data, output_format, headers)

    if output_format == "table":
        console.print(formatted_output)
    else:
        console.print_json(formatted_output) if output_format == "json" else console.print(formatted_output)


def create_rich_table(
    data: List[Dict[str, Any]], title: Optional[str] = None, headers: Optional[List[str]] = None
) -> Table:
    """Create a rich table from data.

    Args:
        data: List of dictionaries
        title: Table title
        headers: Column headers

    Returns:
        Rich Table object
    """
    if not data:
        table = Table(title=title or "No Data")
        table.add_column("Message")
        table.add_row("No data available")
        return table

    table = Table(title=title, show_header=True, header_style="bold magenta")

    # Add columns
    columns = headers or list(data[0].keys())
    for column in columns:
        table.add_column(column)

    # Add rows
    for item in data:
        row = [str(item.get(col, "")) for col in columns]
        table.add_row(*row)

    return table


def parallel_execute(
    func: callable, items: List[Any], max_workers: int = 4, show_progress: bool = True, description: str = "Processing"
) -> List[Any]:
    """Execute function in parallel for multiple items.

    Args:
        func: Function to execute
        items: List of items to process
        max_workers: Maximum number of worker threads
        show_progress: Show progress bar
        description: Progress description

    Returns:
        List of results
    """
    results = []

    if show_progress:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(description, total=len(items))

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_item = {executor.submit(func, item): item for item in items}

                for future in as_completed(future_to_item):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing item: {e}")
                        results.append(None)
                    finally:
                        progress.advance(task)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {executor.submit(func, item): item for item in items}

            for future in as_completed(future_to_item):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing item: {e}")
                    results.append(None)

    return results


def save_to_file(data: Any, filepath: Union[str, Path], file_format: str = "json") -> None:
    """Save data to file.

    Args:
        data: Data to save
        filepath: File path
        file_format: File format (json, yaml, csv)
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        if file_format == "json":
            json.dump(data, f, indent=2, default=str)
        elif file_format == "yaml":
            yaml.dump(data, f, default_flow_style=False)
        elif file_format == "csv":
            if isinstance(data, list) and data and isinstance(data[0], dict):
                import csv

                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                f.write(str(data))
        else:
            f.write(str(data))


def load_from_file(filepath: Union[str, Path]) -> Any:
    """Load data from file.

    Args:
        filepath: File path

    Returns:
        Loaded data
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        if filepath.suffix == ".json":
            return json.load(f)
        elif filepath.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        else:
            return f.read()


def get_timestamp() -> str:
    """Get current timestamp string.

    Returns:
        Timestamp in YYYY-MM-DD format
    """
    return datetime.now().strftime("%Y-%m-%d")


def get_detailed_timestamp() -> str:
    """Get detailed timestamp string.

    Returns:
        Timestamp in YYYY-MM-DD_HH-MM-SS format
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(filepath: Union[str, Path]) -> int:
    """Get file size in bytes.

    Args:
        filepath: File path

    Returns:
        File size in bytes
    """
    return Path(filepath).stat().st_size


def format_bytes(size: int) -> str:
    """Format bytes to human readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
