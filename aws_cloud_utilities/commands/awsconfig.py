"""AWS Config service management and compliance monitoring commands."""

import logging
import json
import csv
import re
import os
from datetime import datetime, timedelta
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
    parallel_execute
)
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="awsconfig")
def awsconfig_group():
    """AWS Config service management and compliance monitoring commands."""
    pass


@awsconfig_group.command(name="download")
@click.option(
    "--bucket",
    required=True,
    help="S3 bucket name containing AWS Config files"
)
@click.option(
    "--prefix",
    required=True,
    help="S3 prefix for Config files"
)
@click.option(
    "--start-date",
    required=True,
    help="Start date for download range (YYYY-MM-DD)"
)
@click.option(
    "--end-date",
    required=True,
    help="End date for download range (YYYY-MM-DD)"
)
@click.option(
    "--output-file",
    help="Output CSV file name (default: config_data_<timestamp>.csv)"
)
@click.option(
    "--region",
    help="AWS region for S3 access (default: current region)"
)
@click.option(
    "--format",
    type=click.Choice(["csv", "json"]),
    default="csv",
    help="Output format (default: csv)"
)
@click.option(
    "--keep-temp-files",
    is_flag=True,
    help="Keep downloaded temporary JSON files"
)
@click.pass_context
def download(
    ctx: click.Context,
    bucket: str,
    prefix: str,
    start_date: str,
    end_date: str,
    output_file: Optional[str],
    region: Optional[str],
    format: str,
    keep_temp_files: bool
) -> None:
    """Download and process AWS Config files from S3 into CSV or JSON format."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]
    
    try:
        target_region = region or config.aws_region or "us-east-1"
        
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            console.print(f"[red]Invalid date format:[/red] {e}")
            console.print("[dim]Use YYYY-MM-DD format (e.g., 2024-01-15)[/dim]")
            raise click.Abort()
        
        if start_dt > end_dt:
            console.print("[red]Start date must be before or equal to end date[/red]")
            raise click.Abort()
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = get_timestamp()
            extension = "csv" if format == "csv" else "json"
            output_file = f"config_data_{timestamp}.{extension}"
        
        console.print(f"[blue]Downloading AWS Config data from S3[/blue]")
        console.print(f"[dim]Bucket: {bucket}[/dim]")
        console.print(f"[dim]Prefix: {prefix}[/dim]")
        console.print(f"[dim]Date range: {start_date} to {end_date}[/dim]")
        console.print(f"[dim]Output: {output_file}[/dim]")
        
        # Get S3 client
        s3_client = aws_auth.get_client("s3", region_name=target_region)
        
        # Execute the download and processing
        download_summary = _download_config_files(
            s3_client, bucket, prefix, start_dt, end_dt, 
            output_file, format, keep_temp_files
        )
        
        # Display summary
        _display_download_summary(config, download_summary, output_file)
        
        console.print(f"\n[green]✅ Config data processing completed successfully![/green]")
        console.print(f"[dim]Output saved to: {output_file}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error downloading Config data:[/red] {e}")
        raise click.Abort()


@awsconfig_group.command(name="show-rules")
@click.option(
    "--region",
    help="AWS region to analyze Config rules (default: current region)"
)
@click.option(
    "--all-regions",
    is_flag=True,
    help="Analyze Config rules across all regions"
)
@click.option(
    "--rule-name",
    help="Specific Config rule to analyze"
)
@click.option(
    "--include-metrics",
    is_flag=True,
    help="Include compliance metrics and statistics"
)
@click.option(
    "--output-file",
    help="Output file for rules analysis (supports .json, .yaml, .csv)"
)
@click.pass_context
def show_rules(
    ctx: click.Context,
    region: Optional[str],
    all_regions: bool,
    rule_name: Optional[str],
    include_metrics: bool,
    output_file: Optional[str]
) -> None:
    """Show AWS Config rules with compliance metrics and meaningful statistics."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]
    
    try:
        # Determine regions to analyze
        if all_regions:
            target_regions = aws_auth.get_available_regions("config")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]
        
        console.print(f"[blue]Analyzing AWS Config rules across {len(target_regions)} regions[/blue]")
        if rule_name:
            console.print(f"[dim]Focusing on rule: {rule_name}[/dim]")
        
        # Collect rules data
        rules_analysis = _analyze_config_rules(
            aws_auth, target_regions, rule_name, include_metrics
        )
        
        # Display results
        _display_rules_analysis(config, rules_analysis, include_metrics)
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip('.') or 'json'
            
            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename
            
            save_to_file(rules_analysis, output_path, file_format)
            console.print(f"[green]Rules analysis saved to:[/green] {output_path}")
        
    except Exception as e:
        console.print(f"[red]Error analyzing Config rules:[/red] {e}")
        raise click.Abort()


@awsconfig_group.command(name="list-rules")
@click.option(
    "--region",
    help="AWS region to list Config rules from (default: current region)"
)
@click.option(
    "--all-regions",
    is_flag=True,
    help="List Config rules from all regions"
)
@click.option(
    "--compliance-state",
    type=click.Choice(["COMPLIANT", "NON_COMPLIANT", "NOT_APPLICABLE", "INSUFFICIENT_DATA"]),
    help="Filter rules by compliance state"
)
@click.option(
    "--output-file",
    help="Output file for rules list (supports .json, .yaml, .csv)"
)
@click.pass_context
def list_rules(
    ctx: click.Context,
    region: Optional[str],
    all_regions: bool,
    compliance_state: Optional[str],
    output_file: Optional[str]
) -> None:
    """List AWS Config rules with basic information."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]
    
    try:
        # Determine regions to scan
        if all_regions:
            target_regions = aws_auth.get_available_regions("config")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]
        
        all_rules = []
        
        for target_region in target_regions:
            config_client = aws_auth.get_client("config", region_name=target_region)
            
            try:
                paginator = config_client.get_paginator("describe_config_rules")
                
                for page in paginator.paginate():
                    for rule in page.get("ConfigRules", []):
                        # Get compliance information if filtering is requested
                        if compliance_state:
                            try:
                                compliance_response = config_client.get_compliance_details_by_config_rule(
                                    ConfigRuleName=rule["ConfigRuleName"]
                                )
                                
                                # Check if any evaluation result matches the filter
                                matches_filter = False
                                for result in compliance_response.get("EvaluationResults", []):
                                    if result.get("ComplianceType") == compliance_state:
                                        matches_filter = True
                                        break
                                
                                if not matches_filter:
                                    continue
                                    
                            except Exception as e:
                                logger.debug(f"Could not get compliance for rule {rule['ConfigRuleName']}: {e}")
                                continue
                        
                        all_rules.append({
                            "Rule Name": rule.get("ConfigRuleName", ""),
                            "Region": target_region,
                            "State": rule.get("ConfigRuleState", ""),
                            "Source": rule.get("Source", {}).get("Owner", ""),
                            "Source Identifier": rule.get("Source", {}).get("SourceIdentifier", ""),
                            "Description": rule.get("Description", "")[:100] + "..." if len(rule.get("Description", "")) > 100 else rule.get("Description", ""),
                            "Created": rule.get("CreatedBy", ""),
                            "Rule ARN": rule.get("ConfigRuleArn", "")
                        })
                        
            except Exception as e:
                logger.warning(f"Error listing Config rules in region {target_region}: {e}")
        
        if all_rules:
            print_output(
                all_rules,
                output_format=config.aws_output_format,
                title=f"AWS Config Rules ({len(all_rules)} found)"
            )
            
            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                file_format = output_path.suffix.lstrip('.') or 'json'
                
                # Add timestamp to filename
                timestamp = get_timestamp()
                stem = output_path.stem
                new_filename = f"{stem}_{timestamp}{output_path.suffix}"
                output_path = output_path.parent / new_filename
                
                save_to_file(all_rules, output_path, file_format)
                console.print(f"[green]Rules list saved to:[/green] {output_path}")
        else:
            console.print("[yellow]No Config rules found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error listing Config rules:[/red] {e}")
        raise click.Abort()


@awsconfig_group.command(name="compliance-status")
@click.option(
    "--region",
    help="AWS region to check compliance status (default: current region)"
)
@click.option(
    "--all-regions",
    is_flag=True,
    help="Check compliance status across all regions"
)
@click.option(
    "--resource-type",
    help="Filter by specific AWS resource type (e.g., AWS::EC2::Instance)"
)
@click.option(
    "--compliance-type",
    type=click.Choice(["COMPLIANT", "NON_COMPLIANT", "NOT_APPLICABLE", "INSUFFICIENT_DATA"]),
    help="Filter by compliance type"
)
@click.option(
    "--output-file",
    help="Output file for compliance status (supports .json, .yaml, .csv)"
)
@click.pass_context
def compliance_status(
    ctx: click.Context,
    region: Optional[str],
    all_regions: bool,
    resource_type: Optional[str],
    compliance_type: Optional[str],
    output_file: Optional[str]
) -> None:
    """Get compliance status summary across AWS Config rules and resources."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]
    
    try:
        # Determine regions to check
        if all_regions:
            target_regions = aws_auth.get_available_regions("config")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]
        
        console.print(f"[blue]Checking AWS Config compliance status across {len(target_regions)} regions[/blue]")
        
        # Collect compliance data
        compliance_data = _get_compliance_status(
            aws_auth, target_regions, resource_type, compliance_type
        )
        
        # Display results
        _display_compliance_status(config, compliance_data)
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip('.') or 'json'
            
            # Add timestamp to filename
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename
            
            save_to_file(compliance_data, output_path, file_format)
            console.print(f"[green]Compliance status saved to:[/green] {output_path}")
        
    except Exception as e:
        console.print(f"[red]Error checking compliance status:[/red] {e}")
        raise click.Abort()


def _download_config_files(
    s3_client,
    bucket: str,
    prefix: str,
    start_date: datetime,
    end_date: datetime,
    output_file: str,
    format: str,
    keep_temp_files: bool
) -> Dict[str, Any]:
    """Download and process AWS Config files from S3."""
    
    # Date pattern to match files
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
    
    all_records = []
    processed_files = 0
    skipped_files = 0
    temp_files = []
    
    try:
        # List objects in S3
        paginator = s3_client.get_paginator("list_objects_v2")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Scanning S3 objects...", total=None)
            
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                if "Contents" not in page:
                    continue
                
                for obj in page["Contents"]:
                    key = obj["Key"]
                    
                    # Extract date from key
                    match = date_pattern.search(key)
                    if match:
                        file_date_str = match.group(1)
                        try:
                            file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                        except ValueError:
                            continue
                        
                        # Check if file is in date range
                        if start_date <= file_date <= end_date:
                            progress.update(task, description=f"Processing {os.path.basename(key)}...")
                            
                            # Download file
                            local_filename = f"temp_{get_timestamp()}_{os.path.basename(key)}"
                            temp_files.append(local_filename)
                            
                            try:
                                s3_client.download_file(bucket, key, local_filename)
                                
                                # Process JSON file
                                with open(local_filename, "r", encoding="utf-8") as f:
                                    try:
                                        data = json.load(f)
                                        
                                        # Handle both single objects and arrays
                                        if isinstance(data, list):
                                            for item in data:
                                                if isinstance(item, dict):
                                                    flattened = _flatten_json(item)
                                                    flattened["_source_file"] = key
                                                    flattened["_processed_date"] = datetime.now().isoformat()
                                                    all_records.append(flattened)
                                        elif isinstance(data, dict):
                                            flattened = _flatten_json(data)
                                            flattened["_source_file"] = key
                                            flattened["_processed_date"] = datetime.now().isoformat()
                                            all_records.append(flattened)
                                        
                                        processed_files += 1
                                        
                                    except json.JSONDecodeError as e:
                                        logger.debug(f"JSON decode error in {key}: {e}")
                                        skipped_files += 1
                                
                            except Exception as e:
                                logger.debug(f"Error processing {key}: {e}")
                                skipped_files += 1
                        else:
                            skipped_files += 1
            
            progress.update(task, description="Writing output file...")
            
            # Write output file
            if format == "csv":
                _write_csv_output(all_records, output_file)
            else:
                _write_json_output(all_records, output_file)
    
    finally:
        # Clean up temp files unless requested to keep them
        if not keep_temp_files:
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logger.debug(f"Could not remove temp file {temp_file}: {e}")
    
    return {
        "total_records": len(all_records),
        "processed_files": processed_files,
        "skipped_files": skipped_files,
        "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "output_format": format
    }


def _flatten_json(nested_json: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Recursively flatten a nested JSON object."""
    items = []
    
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(_flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(_flatten_json(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))
    
    return dict(items)


def _write_csv_output(records: List[Dict[str, Any]], output_file: str) -> None:
    """Write records to CSV file."""
    if not records:
        # Create empty CSV file
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["No data found"])
        return
    
    # Get all unique field names
    header_fields = set()
    for record in records:
        header_fields.update(record.keys())
    header_fields = sorted(header_fields)
    
    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header_fields)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def _write_json_output(records: List[Dict[str, Any]], output_file: str) -> None:
    """Write records to JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)


def _display_download_summary(config: Config, summary: Dict[str, Any], output_file: str) -> None:
    """Display download summary."""
    summary_display = {
        "Total Records": summary["total_records"],
        "Processed Files": summary["processed_files"],
        "Skipped Files": summary["skipped_files"],
        "Date Range": summary["date_range"],
        "Output Format": summary["output_format"].upper(),
        "Output File": output_file
    }
    
def _analyze_config_rules(
    aws_auth: AWSAuth,
    regions: List[str],
    rule_name: Optional[str],
    include_metrics: bool
) -> Dict[str, Any]:
    """Analyze AWS Config rules with metrics and statistics."""
    
    def analyze_region(region: str) -> Tuple[str, Dict[str, Any]]:
        """Analyze Config rules in a single region."""
        region_data = {
            "rules": [],
            "summary": {
                "total_rules": 0,
                "compliant_rules": 0,
                "non_compliant_rules": 0,
                "insufficient_data_rules": 0
            }
        }
        
        try:
            config_client = aws_auth.get_client("config", region_name=region)
            
            # Get rules
            paginator = config_client.get_paginator("describe_config_rules")
            
            for page in paginator.paginate():
                for rule in page.get("ConfigRules", []):
                    rule_data = {
                        "name": rule.get("ConfigRuleName", ""),
                        "state": rule.get("ConfigRuleState", ""),
                        "source": rule.get("Source", {}).get("Owner", ""),
                        "source_identifier": rule.get("Source", {}).get("SourceIdentifier", ""),
                        "description": rule.get("Description", ""),
                        "region": region
                    }
                    
                    # Filter by rule name if specified
                    if rule_name and rule_name.lower() not in rule_data["name"].lower():
                        continue
                    
                    # Get compliance metrics if requested
                    if include_metrics:
                        try:
                            compliance_response = config_client.get_compliance_details_by_config_rule(
                                ConfigRuleName=rule_data["name"]
                            )
                            
                            compliance_summary = defaultdict(int)
                            for result in compliance_response.get("EvaluationResults", []):
                                compliance_type = result.get("ComplianceType", "UNKNOWN")
                                compliance_summary[compliance_type] += 1
                            
                            rule_data["compliance_metrics"] = dict(compliance_summary)
                            
                            # Update region summary
                            if compliance_summary.get("COMPLIANT", 0) > 0:
                                region_data["summary"]["compliant_rules"] += 1
                            if compliance_summary.get("NON_COMPLIANT", 0) > 0:
                                region_data["summary"]["non_compliant_rules"] += 1
                            if compliance_summary.get("INSUFFICIENT_DATA", 0) > 0:
                                region_data["summary"]["insufficient_data_rules"] += 1
                                
                        except Exception as e:
                            logger.debug(f"Could not get compliance for rule {rule_data['name']}: {e}")
                            rule_data["compliance_metrics"] = {"error": str(e)}
                    
                    region_data["rules"].append(rule_data)
                    region_data["summary"]["total_rules"] += 1
        
        except Exception as e:
            logger.warning(f"Error analyzing Config rules in region {region}: {e}")
            region_data["error"] = str(e)
        
        return region, region_data
    
    # Analyze regions in parallel
    region_results = parallel_execute(
        analyze_region,
        regions,
        max_workers=4,
        show_progress=True,
        description="Analyzing Config rules"
    )
    
    # Organize results
    analysis_data = {
        "timestamp": datetime.now().isoformat(),
        "regions": {},
        "global_summary": {
            "total_regions": len(regions),
            "total_rules": 0,
            "compliant_rules": 0,
            "non_compliant_rules": 0,
            "insufficient_data_rules": 0
        }
    }
    
    for region, region_data in region_results:
        analysis_data["regions"][region] = region_data
        
        # Update global summary
        summary = region_data.get("summary", {})
        analysis_data["global_summary"]["total_rules"] += summary.get("total_rules", 0)
        analysis_data["global_summary"]["compliant_rules"] += summary.get("compliant_rules", 0)
        analysis_data["global_summary"]["non_compliant_rules"] += summary.get("non_compliant_rules", 0)
        analysis_data["global_summary"]["insufficient_data_rules"] += summary.get("insufficient_data_rules", 0)
    
    return analysis_data


def _get_compliance_status(
    aws_auth: AWSAuth,
    regions: List[str],
    resource_type: Optional[str],
    compliance_type: Optional[str]
) -> Dict[str, Any]:
    """Get compliance status across regions."""
    
    def get_region_compliance(region: str) -> Tuple[str, Dict[str, Any]]:
        """Get compliance status for a single region."""
        region_data = {
            "compliance_summary": defaultdict(int),
            "resource_summary": defaultdict(int),
            "total_evaluations": 0
        }
        
        try:
            config_client = aws_auth.get_client("config", region_name=region)
            
            # Get compliance summary
            try:
                response = config_client.get_compliance_summary_by_resource_type()
                
                for summary in response.get("ComplianceSummaryByResourceType", []):
                    res_type = summary.get("ResourceType", "Unknown")
                    compliance_summary = summary.get("ComplianceSummary", {})
                    
                    # Filter by resource type if specified
                    if resource_type and resource_type != res_type:
                        continue
                    
                    for comp_type, count in compliance_summary.items():
                        if comp_type != "ComplianceSummaryTimestamp":
                            # Filter by compliance type if specified
                            if compliance_type and compliance_type != comp_type:
                                continue
                            
                            region_data["compliance_summary"][comp_type] += count
                            region_data["resource_summary"][res_type] += count
                            region_data["total_evaluations"] += count
                            
            except Exception as e:
                logger.debug(f"Could not get compliance summary for region {region}: {e}")
                region_data["error"] = str(e)
        
        except Exception as e:
            logger.warning(f"Error getting compliance status in region {region}: {e}")
            region_data["error"] = str(e)
        
        return region, region_data
    
    # Get compliance data in parallel
    region_results = parallel_execute(
        get_region_compliance,
        regions,
        max_workers=4,
        show_progress=True,
        description="Checking compliance status"
    )
    
    # Organize results
    compliance_data = {
        "timestamp": datetime.now().isoformat(),
        "regions": {},
        "global_summary": {
            "total_regions": len(regions),
            "total_evaluations": 0,
            "compliance_summary": defaultdict(int),
            "resource_summary": defaultdict(int)
        }
    }
    
    for region, region_data in region_results:
        compliance_data["regions"][region] = region_data
        
        # Update global summary
        compliance_data["global_summary"]["total_evaluations"] += region_data.get("total_evaluations", 0)
        
        for comp_type, count in region_data.get("compliance_summary", {}).items():
            compliance_data["global_summary"]["compliance_summary"][comp_type] += count
        
        for res_type, count in region_data.get("resource_summary", {}).items():
            compliance_data["global_summary"]["resource_summary"][res_type] += count
    
    # Convert defaultdicts to regular dicts
    compliance_data["global_summary"]["compliance_summary"] = dict(compliance_data["global_summary"]["compliance_summary"])
    compliance_data["global_summary"]["resource_summary"] = dict(compliance_data["global_summary"]["resource_summary"])
    
    return compliance_data


def _display_rules_analysis(config: Config, analysis_data: Dict[str, Any], include_metrics: bool) -> None:
    """Display Config rules analysis results."""
    
    # Global summary
    global_summary = analysis_data["global_summary"]
    summary_display = {
        "Total Regions": global_summary["total_regions"],
        "Total Rules": global_summary["total_rules"],
        "Compliant Rules": global_summary["compliant_rules"],
        "Non-Compliant Rules": global_summary["non_compliant_rules"],
        "Insufficient Data Rules": global_summary["insufficient_data_rules"],
        "Analysis Timestamp": analysis_data["timestamp"]
    }
    
    print_output(
        summary_display,
        output_format=config.aws_output_format,
        title="AWS Config Rules Analysis Summary"
    )
    
    # Regional breakdown
    if include_metrics:
        regional_data = []
        for region, region_data in analysis_data["regions"].items():
            if "error" not in region_data:
                summary = region_data.get("summary", {})
                regional_data.append({
                    "Region": region,
                    "Total Rules": summary.get("total_rules", 0),
                    "Compliant": summary.get("compliant_rules", 0),
                    "Non-Compliant": summary.get("non_compliant_rules", 0),
                    "Insufficient Data": summary.get("insufficient_data_rules", 0)
                })
        
        if regional_data:
            print_output(
                regional_data,
                output_format=config.aws_output_format,
                title="Rules Analysis by Region"
            )


def _display_compliance_status(config: Config, compliance_data: Dict[str, Any]) -> None:
    """Display compliance status results."""
    
    # Global summary
    global_summary = compliance_data["global_summary"]
    summary_display = {
        "Total Regions": global_summary["total_regions"],
        "Total Evaluations": global_summary["total_evaluations"],
        "Analysis Timestamp": compliance_data["timestamp"]
    }
    
    # Add compliance breakdown
    compliance_summary = global_summary.get("compliance_summary", {})
    for comp_type, count in compliance_summary.items():
        summary_display[f"{comp_type.title()} Resources"] = count
    
    print_output(
        summary_display,
        output_format=config.aws_output_format,
        title="AWS Config Compliance Status Summary"
    )
    
    # Resource type breakdown
    resource_summary = global_summary.get("resource_summary", {})
    if resource_summary:
        resource_data = [
            {"Resource Type": res_type, "Total Evaluations": count}
            for res_type, count in sorted(resource_summary.items(), key=lambda x: x[1], reverse=True)
        ][:10]  # Top 10 resource types
        
        if resource_data:
            print_output(
                resource_data,
                output_format=config.aws_output_format,
                title="Top Resource Types by Evaluation Count"
            )
