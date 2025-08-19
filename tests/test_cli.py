"""Tests for CLI functionality."""

import pytest
from click.testing import CliRunner
from aws_cloud_utilities.cli import main


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "AWS Cloud Utilities" in result.output


def test_cli_version():
    """Test CLI version output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "2.1.2" in result.output


def test_account_help():
    """Test account command help."""
    runner = CliRunner()
    result = runner.invoke(main, ["account", "--help"])
    assert result.exit_code == 0
    assert "Account information" in result.output
