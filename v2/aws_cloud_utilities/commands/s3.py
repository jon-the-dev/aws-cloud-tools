"""S3 bucket operations commands."""

import click


@click.group(name="s3")
def s3_group():
    """S3 bucket operations commands."""
    pass


@s3_group.command()
def nuke_bucket():
    """Delete S3 bucket and all contents."""
    click.echo("S3 bucket nuke - Coming soon!")
