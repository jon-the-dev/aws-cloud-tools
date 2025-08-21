"""Main CLI entry point for AWS Cloud Utilities."""

import sys
import logging
from typing import Optional
import click
from rich.console import Console
from rich.traceback import install

from .core.config import Config
from .core.auth import AWSAuth
from .core.exceptions import AWSCloudUtilitiesError, ConfigurationError, AWSError
from .commands import (
    account,
    awsconfig,
    bedrock,
    billing,
    cloudformation,
    cloudfront,
    costops,
    ecr,
    inventory,
    logs,
    rds,
    security,
    stepfunctions,
    s3,
    iam,
    networking,
    support,
    waf,
)

# Install rich traceback handler
install(show_locals=True)

console = Console()
logger = logging.getLogger(__name__)


class AWSCloudUtilitiesCLI:
    """Main CLI class for AWS Cloud Utilities."""

    def __init__(self):
        """Initialize CLI."""
        self.config: Optional[Config] = None
        self.aws_auth: Optional[AWSAuth] = None

    def setup(
        self,
        profile: Optional[str] = None,
        region: Optional[str] = None,
        output_format: str = "table",
        verbose: bool = False,
        debug: bool = False,
        config_file: Optional[str] = None,
    ) -> None:
        """Set up CLI configuration and authentication.

        Args:
            profile: AWS profile name
            region: AWS region
            output_format: Output format
            verbose: Enable verbose output
            debug: Enable debug mode
            config_file: Configuration file path
        """
        # Load configuration
        self.config = Config.load_config(
            config_file=config_file,
            aws_profile=profile,
            aws_region=region,
            aws_output_format=output_format,
            verbose=verbose,
            debug=debug,
        )

        # Set up logging
        self.config.setup_logging()

        # Initialize AWS authentication
        self.aws_auth = AWSAuth(
            profile_name=self.config.aws_profile, region_name=self.config.aws_region
        )

        if verbose or debug:
            console.print(f"[dim]Configuration: {self.config}[/dim]")
            console.print(f"[dim]AWS Auth: {self.aws_auth}[/dim]")


# Global CLI instance
cli_instance = AWSCloudUtilitiesCLI()


@click.group()
@click.option("--profile", help="AWS profile to use", envvar="AWS_PROFILE")
@click.option("--region", help="AWS region", envvar="AWS_DEFAULT_REGION")
@click.option(
    "--output",
    type=click.Choice(["table", "json", "yaml", "csv"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", help="Configuration file path")
@click.version_option(version="2.1.2", prog_name="aws-cloud-utilities")
@click.pass_context
def main(
    ctx: click.Context,
    profile: Optional[str],
    region: Optional[str],
    output: str,
    verbose: bool,
    debug: bool,
    config: Optional[str],
) -> None:
    """AWS Cloud Utilities - A unified toolkit for AWS operations.

    This tool provides a comprehensive set of utilities for managing AWS resources,
    optimizing costs, auditing security, and performing various administrative tasks.

    Examples:
        aws-cloud-utilities account info
        aws-cloud-utilities inventory resources --region us-east-1
        aws-cloud-utilities costops pricing --service ec2
        aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function
    """
    try:
        cli_instance.setup(
            profile=profile,
            region=region,
            output_format=output,
            verbose=verbose,
            debug=debug,
            config_file=config,
        )

        # Store in context for subcommands
        ctx.ensure_object(dict)
        ctx.obj["config"] = cli_instance.config
        ctx.obj["aws_auth"] = cli_instance.aws_auth

    except ConfigurationError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        sys.exit(1)
    except AWSError as e:
        console.print(f"[red]AWS Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        if debug:
            console.print_exception()
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# Add command groups
main.add_command(account.account_group)
main.add_command(awsconfig.awsconfig_group)
main.add_command(bedrock.bedrock_group)
main.add_command(billing.billing_group)
main.add_command(cloudformation.cloudformation_group)
main.add_command(cloudfront.cloudfront_group)
main.add_command(costops.costops_group)
main.add_command(ecr.ecr_group)
main.add_command(inventory.inventory_group)
main.add_command(logs.logs_group)
main.add_command(rds.rds_group)
main.add_command(security.security_group)
main.add_command(stepfunctions.stepfunctions_group)
main.add_command(s3.s3_group)
main.add_command(iam.iam_group)
main.add_command(networking.networking_group)
main.add_command(support.support_group)
main.add_command(waf.waf_group)


@main.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show AWS Cloud Utilities information."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]

    try:
        # Get account information
        caller_identity = aws_auth.get_caller_identity()

        info_data = {
            "Version": "2.1.2",
            "AWS Account ID": caller_identity.get("Account", "Unknown"),
            "AWS User/Role": caller_identity.get("Arn", "Unknown"),
            "AWS Profile": config.aws_profile or "default",
            "AWS Region": config.aws_region or "Not set",
            "Output Format": config.aws_output_format,
            "Workers": config.workers,
            "Log Level": config.log_level,
        }

        from .core.utils import print_output

        print_output(
            info_data,
            output_format=config.aws_output_format,
            title="AWS Cloud Utilities Information",
        )

    except Exception as e:
        console.print(f"[red]Error getting information:[/red] {e}")
        sys.exit(1)


@main.command()
@click.pass_context
def configure(ctx: click.Context) -> None:
    """Configure AWS Cloud Utilities settings."""
    console.print("[bold blue]AWS Cloud Utilities Configuration[/bold blue]")
    console.print("\nThis will create a configuration file in your home directory.")
    console.print("You can also set these values using environment variables.\n")

    # Get current config
    config: Config = ctx.obj["config"]

    # Prompt for settings
    profile = click.prompt(
        "AWS Profile", default=config.aws_profile or "default", show_default=True
    )

    region = click.prompt(
        "Default AWS Region",
        default=config.aws_region or "us-east-1",
        show_default=True,
    )

    output_format = click.prompt(
        "Output Format",
        type=click.Choice(["table", "json", "yaml", "csv"]),
        default=config.aws_output_format,
        show_default=True,
    )

    workers = click.prompt(
        "Number of Workers", type=int, default=config.workers, show_default=True
    )

    # Create config file
    from pathlib import Path

    config_file = Path.home() / ".aws-cloud-utilities.env"

    with open(config_file, "w") as f:
        f.write(f"AWS_PROFILE={profile}\n")
        f.write(f"AWS_DEFAULT_REGION={region}\n")
        f.write(f"AWS_OUTPUT_FORMAT={output_format}\n")
        f.write(f"WORKERS={workers}\n")

    console.print(f"\n[green]Configuration saved to:[/green] {config_file}")
    console.print(
        "\n[dim]You can edit this file directly or use environment variables to override settings.[/dim]"
    )


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    elif issubclass(exc_type, AWSCloudUtilitiesError):
        console.print(f"[red]Error:[/red] {exc_value}")
        sys.exit(1)
    else:
        # Use rich traceback for unexpected errors
        console.print_exception()
        sys.exit(1)


# Set global exception handler
sys.excepthook = handle_exception


if __name__ == "__main__":
    main()
