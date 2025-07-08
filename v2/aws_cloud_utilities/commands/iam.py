"""IAM management commands."""

import click


@click.group(name="iam")
def iam_group():
    """IAM management and auditing commands."""
    pass


@iam_group.command()
def audit():
    """Audit IAM roles and policies."""
    click.echo("IAM audit - Coming soon!")
