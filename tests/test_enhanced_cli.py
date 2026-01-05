"""
Tests for the enhanced CLI functionality.
"""

import pytest
from typer.testing import CliRunner

from changelog_generator.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_main_help(runner):
    """Test that the main help command works and shows enhanced structure."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "🚀 Generate detailed AI-powered changelogs" in result.stdout
    assert "config" in result.stdout
    assert "providers" in result.stdout
    assert "generate" in result.stdout
    assert "init" in result.stdout


def test_config_help(runner):
    """Test that the config subcommand help works."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "🔧 Manage changelog generator configuration" in result.stdout
    assert "show" in result.stdout
    assert "set" in result.stdout
    assert "reset" in result.stdout


def test_providers_help(runner):
    """Test that the providers subcommand help works."""
    result = runner.invoke(app, ["providers", "--help"])
    assert result.exit_code == 0
    assert "🤖 Manage AI providers and models" in result.stdout
    assert "list" in result.stdout
    assert "test" in result.stdout


def test_generate_help(runner):
    """Test that the generate command help works."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    assert "Generate a changelog for a Git repository" in result.stdout
    assert "--config" in result.stdout
    assert "--repo" in result.stdout
    assert "--output" in result.stdout


def test_init_help(runner):
    """Test that the init command help works."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize a new .changelog.yaml configuration file" in result.stdout


def test_version_option(runner):
    """Test the version option works."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Changelog Generator Version" in result.stdout
