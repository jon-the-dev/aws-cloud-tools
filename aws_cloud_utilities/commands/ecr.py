"""AWS ECR (Elastic Container Registry) management commands."""

import logging
import json
import subprocess
import shutil
import base64
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


@click.group(name="ecr")
def ecr_group():
    """AWS ECR (Elastic Container Registry) management commands."""
    pass


@ecr_group.command(name="copy-image")
@click.argument("source_image")
@click.argument("ecr_repository")
@click.option("--tag", default="latest", help="Tag to use for the image in ECR (default: latest)")
@click.option("--region", help="AWS region for ECR repository (default: current region)")
@click.option("--create-repo", is_flag=True, help="Create ECR repository if it doesn't exist")
@click.option("--force", is_flag=True, help="Force overwrite if image already exists")
@click.pass_context
def copy_image(
    ctx: click.Context,
    source_image: str,
    ecr_repository: str,
    tag: str,
    region: Optional[str],
    create_repo: bool,
    force: bool,
) -> None:
    """Copy a Docker image from any registry to AWS ECR."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"

        # Check if Docker is available
        if not shutil.which("docker"):
            console.print("[red]Docker is not installed or not available in PATH[/red]")
            raise click.Abort()

        console.print(f"[blue]Copying image from {source_image} to ECR repository {ecr_repository}[/blue]")
        console.print(f"[dim]Region: {target_region}, Tag: {tag}[/dim]")

        # Get ECR client
        ecr_client = aws_auth.get_client("ecr", region_name=target_region)

        # Get account ID for ECR URI construction
        account_id = aws_auth.get_account_id()

        # Construct full ECR repository URI
        if not ecr_repository.startswith(f"{account_id}.dkr.ecr."):
            ecr_repo_uri = f"{account_id}.dkr.ecr.{target_region}.amazonaws.com/{ecr_repository}"
        else:
            ecr_repo_uri = ecr_repository

        # Create repository if requested
        if create_repo:
            _create_repository_if_not_exists(ecr_client, ecr_repository.split("/")[-1])

        # Check if image already exists (unless force is specified)
        if not force:
            if _image_exists_in_ecr(ecr_client, ecr_repository.split("/")[-1], tag):
                console.print(
                    f"[yellow]Image with tag '{tag}' already exists in repository. Use --force to overwrite.[/yellow]"
                )
                raise click.Abort()

        # Execute the image copy process
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:

            # Step 1: Pull source image
            task1 = progress.add_task("Pulling source image...", total=None)
            _pull_docker_image(source_image)
            progress.update(task1, description="✓ Source image pulled")

            # Step 2: ECR login
            task2 = progress.add_task("Authenticating with ECR...", total=None)
            _ecr_docker_login(ecr_client, target_region)
            progress.update(task2, description="✓ ECR authentication successful")

            # Step 3: Tag image
            target_image = f"{ecr_repo_uri}:{tag}"
            task3 = progress.add_task("Tagging image...", total=None)
            _tag_docker_image(source_image, target_image)
            progress.update(task3, description="✓ Image tagged")

            # Step 4: Push to ECR
            task4 = progress.add_task("Pushing to ECR...", total=None)
            _push_docker_image(target_image)
            progress.update(task4, description="✓ Image pushed to ECR")

        console.print(f"[green]✅ Successfully copied {source_image} to {target_image}[/green]")

        # Display image details
        try:
            image_details = _get_image_details(ecr_client, ecr_repository.split("/")[-1], tag)
            if image_details:
                details_display = {
                    "Repository": ecr_repository,
                    "Tag": tag,
                    "Image Digest": image_details.get("imageDigest", ""),
                    "Size (MB)": round(image_details.get("imageSizeInBytes", 0) / 1024 / 1024, 2),
                    "Pushed At": (
                        image_details.get("imagePushedAt", "").strftime("%Y-%m-%d %H:%M:%S")
                        if image_details.get("imagePushedAt")
                        else ""
                    ),
                    "Registry URI": ecr_repo_uri,
                }

                print_output(details_display, output_format=config.aws_output_format, title="ECR Image Details")
        except Exception as e:
            logger.debug(f"Could not retrieve image details: {e}")

    except Exception as e:
        console.print(f"[red]Error copying image to ECR:[/red] {e}")
        raise click.Abort()


@ecr_group.command(name="list-repositories")
@click.option("--region", help="AWS region to list repositories from (default: current region)")
@click.option("--all-regions", is_flag=True, help="List repositories from all regions")
@click.option("--output-file", help="Output file for repositories list (supports .json, .yaml, .csv)")
@click.pass_context
def list_repositories(ctx: click.Context, region: Optional[str], all_regions: bool, output_file: Optional[str]) -> None:
    """List ECR repositories with details."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Determine regions to scan
        if all_regions:
            target_regions = aws_auth.get_available_regions("ecr")
        else:
            target_regions = [region or config.aws_region or "us-east-1"]

        all_repositories = []

        for target_region in target_regions:
            ecr_client = aws_auth.get_client("ecr", region_name=target_region)

            try:
                paginator = ecr_client.get_paginator("describe_repositories")

                for page in paginator.paginate():
                    for repo in page.get("repositories", []):
                        all_repositories.append(
                            {
                                "Repository Name": repo.get("repositoryName", ""),
                                "Region": target_region,
                                "Registry ID": repo.get("registryId", ""),
                                "Repository URI": repo.get("repositoryUri", ""),
                                "Created": (
                                    repo.get("createdAt", "").strftime("%Y-%m-%d %H:%M")
                                    if repo.get("createdAt")
                                    else ""
                                ),
                                "Image Count": repo.get("imageTagMutability", ""),
                                "Scan on Push": (
                                    "Enabled"
                                    if repo.get("imageScanningConfiguration", {}).get("scanOnPush")
                                    else "Disabled"
                                ),
                                "Encryption": repo.get("encryptionConfiguration", {}).get("encryptionType", "AES256"),
                            }
                        )

            except Exception as e:
                logger.warning(f"Error listing repositories in region {target_region}: {e}")

        if all_repositories:
            print_output(
                all_repositories,
                output_format=config.aws_output_format,
                title=f"ECR Repositories ({len(all_repositories)} found)",
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

                save_to_file(all_repositories, output_path, file_format)
                console.print(f"[green]Repositories list saved to:[/green] {output_path}")
        else:
            console.print("[yellow]No ECR repositories found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing ECR repositories:[/red] {e}")
        raise click.Abort()


@ecr_group.command(name="list-images")
@click.argument("repository_name")
@click.option("--region", help="AWS region where the repository is located (default: current region)")
@click.option("--max-results", type=int, default=100, help="Maximum number of images to list (default: 100)")
@click.option("--output-file", help="Output file for images list (supports .json, .yaml, .csv)")
@click.pass_context
def list_images(
    ctx: click.Context, repository_name: str, region: Optional[str], max_results: int, output_file: Optional[str]
) -> None:
    """List images in an ECR repository."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        ecr_client = aws_auth.get_client("ecr", region_name=target_region)

        console.print(f"[blue]Listing images in repository: {repository_name}[/blue]")
        console.print(f"[dim]Region: {target_region}[/dim]")

        # List images
        try:
            paginator = ecr_client.get_paginator("describe_images")

            all_images = []
            for page in paginator.paginate(repositoryName=repository_name, PaginationConfig={"MaxItems": max_results}):
                for image in page.get("imageDetails", []):
                    # Handle images with and without tags
                    tags = image.get("imageTags", ["<untagged>"])
                    for tag in tags:
                        all_images.append(
                            {
                                "Repository": repository_name,
                                "Tag": tag,
                                "Image Digest": image.get("imageDigest", "")[:12] + "...",  # Truncate for display
                                "Size (MB)": round(image.get("imageSizeInBytes", 0) / 1024 / 1024, 2),
                                "Pushed": (
                                    image.get("imagePushedAt", "").strftime("%Y-%m-%d %H:%M")
                                    if image.get("imagePushedAt")
                                    else ""
                                ),
                                "Scan Status": (
                                    image.get("imageScanFindingsSummary", {})
                                    .get("findingCounts", {})
                                    .get("CRITICAL", 0)
                                    if image.get("imageScanFindingsSummary")
                                    else "Not Scanned"
                                ),
                                "Registry ID": image.get("registryId", ""),
                            }
                        )

            if all_images:
                print_output(
                    all_images,
                    output_format=config.aws_output_format,
                    title=f"ECR Images in {repository_name} ({len(all_images)} found)",
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

                    save_to_file(all_images, output_path, file_format)
                    console.print(f"[green]Images list saved to:[/green] {output_path}")
            else:
                console.print(f"[yellow]No images found in repository {repository_name}[/yellow]")

        except ecr_client.exceptions.RepositoryNotFoundException:
            console.print(f"[red]Repository '{repository_name}' not found in region {target_region}[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error listing ECR images:[/red] {e}")
        raise click.Abort()


@ecr_group.command(name="create-repository")
@click.argument("repository_name")
@click.option("--region", help="AWS region to create repository in (default: current region)")
@click.option("--scan-on-push", is_flag=True, help="Enable image scanning on push")
@click.option(
    "--image-tag-mutability",
    type=click.Choice(["MUTABLE", "IMMUTABLE"]),
    default="MUTABLE",
    help="Image tag mutability setting (default: MUTABLE)",
)
@click.option(
    "--encryption-type",
    type=click.Choice(["AES256", "KMS"]),
    default="AES256",
    help="Encryption type for the repository (default: AES256)",
)
@click.pass_context
def create_repository(
    ctx: click.Context,
    repository_name: str,
    region: Optional[str],
    scan_on_push: bool,
    image_tag_mutability: str,
    encryption_type: str,
) -> None:
    """Create a new ECR repository."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        ecr_client = aws_auth.get_client("ecr", region_name=target_region)

        console.print(f"[blue]Creating ECR repository: {repository_name}[/blue]")
        console.print(f"[dim]Region: {target_region}[/dim]")

        # Create repository
        try:
            create_params = {
                "repositoryName": repository_name,
                "imageScanningConfiguration": {"scanOnPush": scan_on_push},
                "imageTagMutability": image_tag_mutability,
                "encryptionConfiguration": {"encryptionType": encryption_type},
            }

            response = ecr_client.create_repository(**create_params)
            repository = response["repository"]

            console.print(f"[green]✅ Repository created successfully[/green]")

            # Display repository details
            repo_details = {
                "Repository Name": repository.get("repositoryName", ""),
                "Repository URI": repository.get("repositoryUri", ""),
                "Registry ID": repository.get("registryId", ""),
                "Region": target_region,
                "Created": (
                    repository.get("createdAt", "").strftime("%Y-%m-%d %H:%M:%S") if repository.get("createdAt") else ""
                ),
                "Scan on Push": "Enabled" if scan_on_push else "Disabled",
                "Tag Mutability": image_tag_mutability,
                "Encryption": encryption_type,
            }

            print_output(repo_details, output_format=config.aws_output_format, title="ECR Repository Details")

        except ecr_client.exceptions.RepositoryAlreadyExistsException:
            console.print(f"[yellow]Repository '{repository_name}' already exists in region {target_region}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error creating ECR repository:[/red] {e}")
        raise click.Abort()


@ecr_group.command(name="delete-repository")
@click.argument("repository_name")
@click.option("--region", help="AWS region where the repository is located (default: current region)")
@click.option("--force", is_flag=True, help="Force delete repository even if it contains images")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_repository(
    ctx: click.Context, repository_name: str, region: Optional[str], force: bool, confirm: bool
) -> None:
    """Delete an ECR repository."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        ecr_client = aws_auth.get_client("ecr", region_name=target_region)

        # Check if repository exists and get details
        try:
            response = ecr_client.describe_repositories(repositoryNames=[repository_name])
            repository = response["repositories"][0]
        except ecr_client.exceptions.RepositoryNotFoundException:
            console.print(f"[red]Repository '{repository_name}' not found in region {target_region}[/red]")
            raise click.Abort()

        # Show repository details
        console.print(f"[yellow]Repository to delete:[/yellow]")
        console.print(f"  Name: {repository_name}")
        console.print(f"  URI: {repository.get('repositoryUri', '')}")
        console.print(f"  Region: {target_region}")
        console.print(
            f"  Created: {repository.get('createdAt', '').strftime('%Y-%m-%d %H:%M:%S') if repository.get('createdAt') else ''}"
        )

        # Confirmation
        if not confirm:
            if not click.confirm(f"\nAre you sure you want to delete repository '{repository_name}'?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Delete repository
        try:
            ecr_client.delete_repository(repositoryName=repository_name, force=force)

            console.print(f"[green]✅ Repository '{repository_name}' deleted successfully[/green]")

        except ecr_client.exceptions.RepositoryNotEmptyException:
            console.print(f"[red]Repository '{repository_name}' contains images. Use --force to delete anyway.[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error deleting ECR repository:[/red] {e}")
        raise click.Abort()


@ecr_group.command(name="get-login")
@click.option("--region", help="AWS region for ECR login (default: current region)")
@click.option("--print-command", is_flag=True, help="Print the docker login command instead of executing it")
@click.pass_context
def get_login(ctx: click.Context, region: Optional[str], print_command: bool) -> None:
    """Get Docker login command for ECR or execute login directly."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        target_region = region or config.aws_region or "us-east-1"
        ecr_client = aws_auth.get_client("ecr", region_name=target_region)

        # Get authorization token
        response = ecr_client.get_authorization_token()
        auth_data = response["authorizationData"][0]

        token = auth_data["authorizationToken"]
        proxy_endpoint = auth_data["proxyEndpoint"]

        # Decode the token to get the password
        decoded_token = base64.b64decode(token).decode("utf-8")
        username, password = decoded_token.split(":", 1)

        login_command = f"docker login --username {username} --password-stdin {proxy_endpoint}"

        if print_command:
            console.print(f"[blue]Docker login command:[/blue]")
            console.print(f"echo '{password}' | {login_command}")
        else:
            if not shutil.which("docker"):
                console.print("[red]Docker is not installed or not available in PATH[/red]")
                console.print(f"[blue]Manual login command:[/blue]")
                console.print(f"echo '{password}' | {login_command}")
                return

            # Execute docker login
            try:
                process = subprocess.Popen(
                    ["docker", "login", "--username", username, "--password-stdin", proxy_endpoint],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                stdout, stderr = process.communicate(input=password)

                if process.returncode == 0:
                    console.print(f"[green]✅ Docker login successful for {proxy_endpoint}[/green]")
                else:
                    console.print(f"[red]Docker login failed:[/red] {stderr}")
                    raise click.Abort()

            except Exception as e:
                console.print(f"[red]Error executing docker login:[/red] {e}")
                raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error getting ECR login:[/red] {e}")
        raise click.Abort()


def _pull_docker_image(image: str) -> None:
    """Pull a Docker image."""
    try:
        result = subprocess.run(["docker", "pull", image], check=True, capture_output=True, text=True)
        logger.debug(f"Docker pull output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to pull image {image}: {e.stderr}")


def _tag_docker_image(source_image: str, target_image: str) -> None:
    """Tag a Docker image."""
    try:
        subprocess.run(["docker", "tag", source_image, target_image], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to tag image: {e.stderr}")


def _push_docker_image(target_image: str) -> None:
    """Push a Docker image."""
    try:
        subprocess.run(["docker", "push", target_image], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to push image: {e.stderr}")


def _ecr_docker_login(ecr_client, region: str) -> None:
    """Authenticate Docker with ECR."""
    try:
        response = ecr_client.get_authorization_token()
        auth_data = response["authorizationData"][0]

        token = auth_data["authorizationToken"]
        proxy_endpoint = auth_data["proxyEndpoint"]

        # Execute docker login
        process = subprocess.Popen(
            ["docker", "login", "--username", "AWS", "--password-stdin", proxy_endpoint],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, stderr = process.communicate(input=token)

        if process.returncode != 0:
            raise Exception(f"Docker login failed: {stderr}")

    except Exception as e:
        raise Exception(f"ECR authentication failed: {e}")


def _create_repository_if_not_exists(ecr_client, repository_name: str) -> None:
    """Create ECR repository if it doesn't exist."""
    try:
        ecr_client.describe_repositories(repositoryNames=[repository_name])
    except ecr_client.exceptions.RepositoryNotFoundException:
        try:
            ecr_client.create_repository(repositoryName=repository_name)
            console.print(f"[green]Created ECR repository: {repository_name}[/green]")
        except Exception as e:
            raise Exception(f"Failed to create repository {repository_name}: {e}")


def _image_exists_in_ecr(ecr_client, repository_name: str, tag: str) -> bool:
    """Check if an image with specific tag exists in ECR repository."""
    try:
        response = ecr_client.describe_images(repositoryName=repository_name, imageIds=[{"imageTag": tag}])
        return len(response.get("imageDetails", [])) > 0
    except ecr_client.exceptions.ImageNotFoundException:
        return False
    except ecr_client.exceptions.RepositoryNotFoundException:
        return False
    except Exception:
        return False


def _get_image_details(ecr_client, repository_name: str, tag: str) -> Optional[Dict[str, Any]]:
    """Get details for a specific image in ECR."""
    try:
        response = ecr_client.describe_images(repositoryName=repository_name, imageIds=[{"imageTag": tag}])

        image_details = response.get("imageDetails", [])
        return image_details[0] if image_details else None

    except Exception as e:
        logger.debug(f"Could not get image details: {e}")
        return None
