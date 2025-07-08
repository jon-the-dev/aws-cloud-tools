"""Security auditing and tools commands."""

import click


@click.group(name="security")
def security_group():
    """Security auditing and tools commands."""
    pass


@security_group.command()
def blue_team():
    """Run blue team security audit."""
    click.echo("Blue team audit - Coming soon!")


@security_group.command()
def acm_cert():
    """Create ACM certificate."""
    click.echo("ACM certificate creation - Coming soon!")
