"""Networking utilities commands."""

import click


@click.group(name="networking")
def networking_group():
    """Network utilities commands."""
    pass


@networking_group.command()
def ip_ranges():
    """Get AWS IP ranges."""
    click.echo("AWS IP ranges - Coming soon!")
