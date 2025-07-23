"""Amazon Bedrock management commands."""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import click
from rich.console import Console

from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import print_output, parallel_execute, save_to_file, get_timestamp
from ..core.exceptions import AWSError

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="bedrock")
def bedrock_group():
    """Amazon Bedrock management commands."""
    pass


@bedrock_group.command(name="list-models")
@click.option("--region", help="Specific region to list models from (default: all regions)")
@click.option("--output-file", help="Save results to file (supports .json, .csv, .yaml)")
@click.option(
    "--model-type",
    type=click.Choice(["foundation", "custom", "all"]),
    default="foundation",
    help="Type of models to list",
)
@click.option("--provider", help="Filter by model provider (e.g., amazon, anthropic, ai21, cohere)")
@click.pass_context
def list_models(
    ctx: click.Context, region: Optional[str], output_file: Optional[str], model_type: str, provider: Optional[str]
) -> None:
    """List Amazon Bedrock foundation models across regions."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Determine regions to scan
        if region:
            regions = [region]
            if not aws_auth.validate_region(region, "bedrock"):
                console.print(f"[yellow]Warning: Region {region} may not support Bedrock[/yellow]")
        else:
            regions = aws_auth.get_available_regions("bedrock")
            console.print(f"[blue]Scanning {len(regions)} regions for Bedrock models...[/blue]")

        # Function to list models in a region
        def list_models_in_region(region_name: str) -> List[Dict[str, Any]]:
            models_list = []
            try:
                bedrock_client = aws_auth.get_client("bedrock", region_name=region_name)

                # List foundation models
                if model_type in ["foundation", "all"]:
                    paginator = bedrock_client.get_paginator("list_foundation_models")

                    for page in paginator.paginate():
                        for model in page.get("modelSummaries", []):
                            model_info = {
                                "Region": region_name,
                                "Model ID": model.get("modelId", ""),
                                "Model Name": model.get("modelName", ""),
                                "Provider": model.get("providerName", ""),
                                "Type": "Foundation",
                                "Input Modalities": ", ".join(model.get("inputModalities", [])),
                                "Output Modalities": ", ".join(model.get("outputModalities", [])),
                                "Response Streaming": "Yes" if model.get("responseStreamingSupported") else "No",
                                "Customization": ", ".join(model.get("customizationsSupported", [])) or "None",
                            }

                            # Apply provider filter if specified
                            if provider and provider.lower() not in model_info["Provider"].lower():
                                continue

                            models_list.append(model_info)

                # List custom models
                if model_type in ["custom", "all"]:
                    try:
                        paginator = bedrock_client.get_paginator("list_custom_models")

                        for page in paginator.paginate():
                            for model in page.get("modelSummaries", []):
                                model_info = {
                                    "Region": region_name,
                                    "Model ID": model.get("modelArn", ""),
                                    "Model Name": model.get("modelName", ""),
                                    "Provider": "Custom",
                                    "Type": "Custom",
                                    "Base Model": (
                                        model.get("baseModelArn", "").split("/")[-1]
                                        if model.get("baseModelArn")
                                        else ""
                                    ),
                                    "Status": model.get("status", ""),
                                    "Created": (
                                        model.get("creationTime", "").strftime("%Y-%m-%d")
                                        if model.get("creationTime")
                                        else ""
                                    ),
                                }

                                models_list.append(model_info)

                    except Exception as e:
                        logger.debug(f"Could not list custom models in {region_name}: {e}")

                logger.debug(f"Found {len(models_list)} models in region {region_name}")
                return models_list

            except Exception as e:
                logger.warning(f"Error listing models in region {region_name}: {e}")
                return []

        # Get models from all regions in parallel
        all_models = []
        region_results = parallel_execute(
            list_models_in_region,
            regions,
            max_workers=config.workers,
            show_progress=len(regions) > 1,
            description="Scanning regions for Bedrock models",
        )

        # Flatten results
        for region_models in region_results:
            if region_models:
                all_models.extend(region_models)

        if not all_models:
            console.print("[yellow]No Bedrock models found in the specified regions[/yellow]")
            return

        # Sort by region and model name
        all_models.sort(key=lambda x: (x["Region"], x["Model Name"]))

        # Display results
        print_output(
            all_models, output_format=config.aws_output_format, title=f"Amazon Bedrock Models ({len(all_models)} found)"
        )

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            file_format = output_path.suffix.lstrip(".") or "json"

            # Add timestamp and account ID to filename
            account_id = aws_auth.get_account_id()
            timestamp = get_timestamp()
            stem = output_path.stem
            new_filename = f"{stem}_{account_id}_{timestamp}{output_path.suffix}"
            output_path = output_path.parent / new_filename

            save_to_file(all_models, output_path, file_format)
            console.print(f"[green]Results saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Error listing Bedrock models:[/red] {e}")
        raise click.Abort()


@bedrock_group.command(name="model-details")
@click.argument("model_id")
@click.option("--region", help="Region where the model is available (default: current region)")
@click.pass_context
def model_details(ctx: click.Context, model_id: str, region: Optional[str]) -> None:
    """Get detailed information about a specific Bedrock model."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        bedrock_client = aws_auth.get_client("bedrock", region_name=target_region)

        try:
            # Try to get foundation model details
            response = bedrock_client.get_foundation_model(modelIdentifier=model_id)
            model_details = response.get("modelDetails", {})

            model_info = {
                "Model ID": model_details.get("modelId", ""),
                "Model Name": model_details.get("modelName", ""),
                "Provider": model_details.get("providerName", ""),
                "Model ARN": model_details.get("modelArn", ""),
                "Input Modalities": ", ".join(model_details.get("inputModalities", [])),
                "Output Modalities": ", ".join(model_details.get("outputModalities", [])),
                "Response Streaming": "Yes" if model_details.get("responseStreamingSupported") else "No",
                "Customization Supported": ", ".join(model_details.get("customizationsSupported", [])) or "None",
                "Inference Types": ", ".join(model_details.get("inferenceTypesSupported", [])),
                "Region": target_region,
            }

            print_output(model_info, output_format=config.aws_output_format, title=f"Bedrock Model Details: {model_id}")

        except bedrock_client.exceptions.ResourceNotFoundException:
            console.print(f"[red]Model '{model_id}' not found in region {target_region}[/red]")
            console.print("[dim]Try using 'list-models' to see available models[/dim]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error getting model details:[/red] {e}")
        raise click.Abort()


@bedrock_group.command(name="list-custom-models")
@click.option("--region", help="Specific region to list custom models from (default: current region)")
@click.option(
    "--status",
    type=click.Choice(["InProgress", "Completed", "Failed", "Stopping", "Stopped"]),
    help="Filter by model status",
)
@click.pass_context
def list_custom_models(ctx: click.Context, region: Optional[str], status: Optional[str]) -> None:
    """List custom Bedrock models."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        bedrock_client = aws_auth.get_client("bedrock", region_name=target_region)

        try:
            params = {}
            if status:
                params["byStatus"] = status

            paginator = bedrock_client.get_paginator("list_custom_models")

            custom_models = []
            for page in paginator.paginate(**params):
                for model in page.get("modelSummaries", []):
                    model_info = {
                        "Model Name": model.get("modelName", ""),
                        "Model ARN": model.get("modelArn", ""),
                        "Base Model": model.get("baseModelArn", "").split("/")[-1] if model.get("baseModelArn") else "",
                        "Status": model.get("status", ""),
                        "Created": (
                            model.get("creationTime", "").strftime("%Y-%m-%d %H:%M")
                            if model.get("creationTime")
                            else ""
                        ),
                        "Job Name": model.get("jobName", ""),
                        "Job ARN": model.get("jobArn", ""),
                    }
                    custom_models.append(model_info)

            if custom_models:
                print_output(
                    custom_models,
                    output_format=config.aws_output_format,
                    title=f"Custom Bedrock Models in {target_region}",
                )
            else:
                console.print(f"[yellow]No custom models found in region {target_region}[/yellow]")

        except Exception as e:
            console.print(f"[red]Error listing custom models:[/red] {e}")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error accessing Bedrock in region {target_region}:[/red] {e}")
        raise click.Abort()


@bedrock_group.command(name="list-model-jobs")
@click.option("--region", help="Specific region to list model customization jobs from (default: current region)")
@click.option(
    "--status",
    type=click.Choice(["InProgress", "Completed", "Failed", "Stopping", "Stopped"]),
    help="Filter by job status",
)
@click.pass_context
def list_model_jobs(ctx: click.Context, region: Optional[str], status: Optional[str]) -> None:
    """List Bedrock model customization jobs."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        bedrock_client = aws_auth.get_client("bedrock", region_name=target_region)

        try:
            params = {}
            if status:
                params["statusEquals"] = status

            paginator = bedrock_client.get_paginator("list_model_customization_jobs")

            jobs = []
            for page in paginator.paginate(**params):
                for job in page.get("modelCustomizationJobSummaries", []):
                    job_info = {
                        "Job Name": job.get("jobName", ""),
                        "Job ARN": job.get("jobArn", ""),
                        "Base Model": job.get("baseModelArn", "").split("/")[-1] if job.get("baseModelArn") else "",
                        "Status": job.get("status", ""),
                        "Created": (
                            job.get("creationTime", "").strftime("%Y-%m-%d %H:%M") if job.get("creationTime") else ""
                        ),
                        "Ended": job.get("endTime", "").strftime("%Y-%m-%d %H:%M") if job.get("endTime") else "N/A",
                        "Custom Model Name": job.get("customModelName", ""),
                        "Custom Model ARN": job.get("customModelArn", ""),
                    }
                    jobs.append(job_info)

            if jobs:
                print_output(
                    jobs,
                    output_format=config.aws_output_format,
                    title=f"Bedrock Model Customization Jobs in {target_region}",
                )
            else:
                console.print(f"[yellow]No model customization jobs found in region {target_region}[/yellow]")

        except Exception as e:
            console.print(f"[red]Error listing model customization jobs:[/red] {e}")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error accessing Bedrock in region {target_region}:[/red] {e}")
        raise click.Abort()


@bedrock_group.command(name="regions")
@click.pass_context
def regions(ctx: click.Context) -> None:
    """List regions where Amazon Bedrock is available."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        bedrock_regions = aws_auth.get_available_regions("bedrock")

        regions_data = [
            {"Region": region, "Current": "✓" if region == config.aws_region else ""}
            for region in sorted(bedrock_regions)
        ]

        print_output(regions_data, output_format=config.aws_output_format, title="Amazon Bedrock Available Regions")

    except Exception as e:
        console.print(f"[red]Error listing Bedrock regions:[/red] {e}")
        raise click.Abort()
