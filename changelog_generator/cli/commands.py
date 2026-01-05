"""CLI command definitions for the changelog generator."""

import os
import sys
import typer
import ollama
from typing_extensions import Annotated
from typing import Optional
from pydantic import ValidationError
from rich.prompt import Confirm

from changelog_generator.changelog_config import ChangelogConfig
from changelog_generator.core.changelog_generator import generate_changelog
from changelog_generator.cli.ui import (
    console,
    show_config_panel,
    create_models_table,
    create_progress_bar,
)
from changelog_generator.version import __version__


def version_callback(value: bool):
    if value:
        console.print(
            f"Changelog Generator Version: [bold green]{__version__}[/bold green]"
        )
        raise typer.Exit()


def setup_commands(app: typer.Typer):
    """Set up all CLI commands for the application."""

    @app.callback()
    def main(
        ctx: typer.Context,
        version: Annotated[
            Optional[bool],
            typer.Option(
                "--version",
                "-V",
                help="Show the application's version and exit.",
                callback=version_callback,
                is_eager=True,
            ),
        ] = None,
    ):
        """Entry point for the changelog generator CLI."""
        pass

    @app.command(
        name="generate",
        help="Generate a changelog for a Git repository.",
    )
    def generate_command(
        commit1: Annotated[
            Optional[str], typer.Argument(help="First commit hash (optional)")
        ] = None,
        commit2: Annotated[
            Optional[str], typer.Argument(help="Last commit hash (optional)")
        ] = None,
        config_path: Annotated[
            Optional[str],
            typer.Option("--config", "-c", help="Path to custom configuration file"),
        ] = None,
        repo_path: Annotated[
            Optional[str],
            typer.Option(
                "--repo",
                "-r",
                help="Path to the Git repository (default: current directory)",
            ),
        ] = None,
        output_file: Annotated[
            Optional[str],
            typer.Option(
                "--output", "-o", help="Output file for the generated changelog"
            ),
        ] = None,
        branch: Annotated[
            Optional[str],
            typer.Option(
                "--branch", "-b", help="Specify a branch to generate changelog for"
            ),
        ] = None,
        model_provider: Annotated[
            Optional[str],
            typer.Option(
                "--model-provider",
                "-p",
                help="AI model provider",
                rich_help_panel="AI Options",
            ),
        ] = None,
        model_name: Annotated[
            Optional[str],
            typer.Option(
                "--model-name",
                "-m",
                help="Specific AI model to use",
                rich_help_panel="AI Options",
            ),
        ] = None,
        verbose: Annotated[
            Optional[bool],
            typer.Option("--verbose", "-v", help="Enable verbose logging"),
        ] = None,
        commit_range: Annotated[
            Optional[str],
            typer.Option(
                "--commit-range",
                help='Git commit range to generate changelog for (e.g., "576ebd6..698b4d07")',
            ),
        ] = None,
    ):
        """Generate a changelog."""
        generate_changelog(
            commit1,
            commit2,
            config_path,
            repo_path,
            output_file,
            branch,
            model_provider,
            model_name,
            verbose,
            commit_range,
        )

    # Config commands
    config_app = typer.Typer(
        name="config",
        help="🔧 Manage changelog generator configuration",
        rich_markup_mode="rich",
    )
    app.add_typer(config_app, name="config")

    @config_app.command(name="show", help="📋 Show the current configuration")
    def show_config(
        config_path: Annotated[
            Optional[str],
            typer.Option("--config", "-c", help="Path to custom configuration file"),
        ] = None,
    ):
        """Show the current configuration in a formatted display."""
        try:
            config = ChangelogConfig.load_config(config_path)
            config_file = config_path or ".changelog.yaml"

            show_config_panel(
                config.model_dump_json(indent=2),
                config_file if os.path.exists(config_file) else "default configuration",
            )

        except (FileNotFoundError, ValueError, ValidationError, RuntimeError) as e:
            console.print(f"[bold red]Error loading configuration: {e}[/bold red]")
            sys.exit(1)

    @config_app.command(name="set", help="⚙️ Set a configuration value")
    def set_config(
        key: Annotated[
            str, typer.Argument(help="Configuration key (e.g., 'ai.provider')")
        ],
        value: Annotated[str, typer.Argument(help="Configuration value")],
        config_path: Annotated[
            Optional[str],
            typer.Option("--config", "-c", help="Path to configuration file"),
        ] = ".changelog.yaml",
    ):
        """Set a configuration value."""
        try:
            # Load existing config or create new one
            if os.path.exists(config_path):
                config = ChangelogConfig.load_config(config_path)
            else:
                config = ChangelogConfig()
                console.print(
                    f"[yellow]Creating new configuration file: {config_path}[/yellow]"
                )

            # Parse the key path (e.g., "ai.provider" -> ["ai", "provider"])
            key_parts = key.split(".")

            # Convert string value to appropriate type
            if value.lower() in ("true", "false"):
                typed_value = value.lower() == "true"
            elif value.isdigit():
                typed_value = int(value)
            else:
                typed_value = value

            # Set the value (this is a simplified implementation)
            # In a real implementation, you'd want to properly navigate the config structure
            console.print(f"[yellow]Setting {key} = {typed_value}[/yellow]")
            console.print(
                "[blue]Note: Full configuration setting implementation would go here[/blue]"
            )

        except Exception as e:
            console.print(f"[bold red]Error setting configuration: {e}[/bold red]")
            sys.exit(1)

    @config_app.command(name="reset", help="🔄 Reset configuration to defaults")
    def reset_config(
        config_path: Annotated[
            Optional[str],
            typer.Option("--config", "-c", help="Path to configuration file"),
        ] = ".changelog.yaml",
        force: Annotated[
            bool,
            typer.Option("--force", "-f", help="Skip confirmation prompt"),
        ] = False,
    ):
        """Reset configuration to default values."""
        if not force:
            if not Confirm.ask(
                f"Reset configuration file '{config_path}' to defaults?"
            ):
                console.print("[yellow]Configuration reset cancelled.[/yellow]")
                return

        try:
            default_config = ChangelogConfig()
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(default_config.to_yaml())

            console.print(
                f"[bold green]Configuration reset to defaults: {config_path}[/bold green]"
            )

        except Exception as e:
            console.print(f"[bold red]Error resetting configuration: {e}[/bold red]")
            sys.exit(1)

    # Providers commands
    providers_app = typer.Typer(
        name="providers",
        help="🤖 Manage AI providers and models",
        rich_markup_mode="rich",
    )
    app.add_typer(providers_app, name="providers")

    @providers_app.command(
        name="list", help="📋 List available AI models for all providers"
    )
    def list_all_models(
        config_path: Annotated[
            Optional[str],
            typer.Option("--config", "-c", help="Path to custom configuration file"),
        ] = None,
        provider: Annotated[
            Optional[str],
            typer.Option(
                "--provider", "-p", help="Show models for specific provider only"
            ),
        ] = None,
    ):
        """List available AI models for all providers with enhanced display."""
        table = create_models_table()

        try:
            config = ChangelogConfig.load_config(config_path)
            current_provider = config.ai.provider

            # Show Ollama models
            if not provider or provider == "ollama":
                try:
                    models = ollama.list()
                    if models.get("models"):
                        for model in models["models"]:
                            status = (
                                "✅ Available"
                                if current_provider == "ollama"
                                else "Available"
                            )
                            table.add_row(
                                "Ollama", model.get("name", "Unknown"), status
                            )
                    else:
                        table.add_row("Ollama", "No models found", "❌ Not running")
                except Exception:
                    table.add_row("Ollama", "Connection failed", "❌ Not running")

            # Show XAI models
            if not provider or provider == "xai":
                xai_models = ["grok-2", "grok-beta"]
                for model in xai_models:
                    status = "✅ Current" if current_provider == "xai" else "Available"
                    table.add_row("XAI", model, status)

            # Show Anthropic models
            if not provider or provider == "anthropic":
                anthropic_models = [
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                ]
                for model in anthropic_models:
                    status = (
                        "✅ Current" if current_provider == "anthropic" else "Available"
                    )
                    table.add_row("Anthropic", model, status)

            console.print(table)

            # Show current configuration
            console.print(f"\n[dim]Current provider: {current_provider}[/dim]")
            console.print(f"[dim]Current model: {config.ai.model_name}[/dim]")

        except Exception as e:
            console.print(f"[bold red]Error listing models: {e}[/bold red]")
            sys.exit(1)

    @providers_app.command(name="test", help="🔍 Test AI provider connection")
    def test_provider(
        provider: Annotated[
            Optional[str],
            typer.Option(
                "--provider", "-p", help="Provider to test (ollama, xai, anthropic)"
            ),
        ] = None,
        config_path: Annotated[
            Optional[str],
            typer.Option("--config", "-c", help="Path to custom configuration file"),
        ] = None,
    ):
        """Test connection to AI providers."""
        try:
            config = ChangelogConfig.load_config(config_path)
            test_provider_name = provider or config.ai.provider

            with create_progress_bar(
                f"Testing {test_provider_name} connection..."
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Testing {test_provider_name} connection...", total=None
                )

                if test_provider_name == "ollama":
                    try:
                        models = ollama.list()
                        progress.update(
                            task, description="[green]Ollama connection successful"
                        )
                        console.print(
                            f"[bold green]✅ Ollama is running with {len(models.get('models', []))} models[/bold green]"
                        )
                    except Exception as e:
                        progress.update(
                            task, description="[red]Ollama connection failed"
                        )
                        console.print(
                            f"[bold red]❌ Ollama connection failed: {e}[/bold red]"
                        )

                elif test_provider_name == "xai":
                    # Test XAI connection (would need API key validation)
                    progress.update(
                        task, description="[yellow]XAI connection test not implemented"
                    )
                    console.print(
                        "[bold yellow]⚠️ XAI connection test requires API key validation[/bold yellow]"
                    )

                elif test_provider_name == "anthropic":
                    # Test Anthropic connection (would need API key validation)
                    progress.update(
                        task,
                        description="[yellow]Anthropic connection test not implemented",
                    )
                    console.print(
                        "[bold yellow]⚠️ Anthropic connection test requires API key validation[/bold yellow]"
                    )

                else:
                    console.print(
                        f"[bold red]❌ Unknown provider: {test_provider_name}[/bold red]"
                    )

        except Exception as e:
            console.print(f"[bold red]Error testing provider: {e}[/bold red]")
            sys.exit(1)

    @app.command(
        name="init", help="Initialize a new .changelog.yaml configuration file"
    )
    def init_config(
        output_path: Annotated[
            Optional[str],
            typer.Argument(
                help="Path to output the default configuration file (default: .changelog.yaml)"
            ),
        ] = ".changelog.yaml",
    ):
        """Initialize a new configuration file."""
        try:
            if os.path.exists(output_path):
                if not typer.confirm(
                    f"File '{output_path}' already exists. Overwrite?", abort=True
                ):
                    sys.exit(0)

            default_config = ChangelogConfig()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(default_config.to_yaml())
            console.print(
                f"[bold green]Default configuration written to {output_path}[/bold green]"
            )
        except Exception as e:
            console.print(f"[bold red]Error initializing configuration: {e}[/bold red]")
            sys.exit(1)
