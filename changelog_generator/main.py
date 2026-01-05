import typer
from typing_extensions import Annotated
from typing import Optional
import logging
import sys
import os
from datetime import datetime

import git
import ollama
from rich.console import Console
from pydantic import ValidationError

from changelog_generator.changelog_config import ChangelogConfig
from changelog_generator.changelog_utils import get_commit_changes
from changelog_generator.generator import (
    generate_ai_changelog,
    determine_output_format,
    generate_changelog_content,
)
from changelog_generator.git_utils import get_git_commits
from changelog_generator.version import __version__

app = typer.Typer(
    name="changelog-generator",
    help="Generate a detailed AI-powered changelog for a Git repository.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
# logger.propagate = False # Removed to allow caplog to capture logs


def validate_ai_config(ai_settings) -> list:
    """Validate AI provider configuration and return list of errors."""
    errors = []

    if ai_settings.provider == "xai" and not ai_settings.xai_api_key:
        if not os.getenv("XAI_API_KEY"):
            errors.append(
                "XAI provider requires xai_api_key in config or XAI_API_KEY environment variable"
            )

    elif ai_settings.provider == "anthropic" and not ai_settings.anthropic_api_key:
        if not os.getenv("ANTHROPIC_API_KEY"):
            errors.append(
                "Anthropic provider requires anthropic_api_key in config or ANTHROPIC_API_KEY environment variable"
            )

    elif ai_settings.provider == "ollama":
        # Check if Ollama is running
        try:
            ollama.list()
        except Exception:
            errors.append(
                "Ollama provider requires Ollama to be running (try: ollama serve)"
            )

    elif ai_settings.provider not in ["ollama", "xai", "anthropic"]:
        errors.append(
            f"Unsupported AI provider: {ai_settings.provider}. Use 'ollama', 'xai', or 'anthropic'"
        )

    return errors


def version_callback(value: bool):
    if value:
        console.print(
            f"Changelog Generator Version: [bold green]{__version__}[/bold green]"
        )
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
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
        typer.Option("--output", "-o", help="Output file for the generated changelog"),
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
        Optional[bool], typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = None,
    commit_range: Annotated[
        Optional[str],
        typer.Option(
            "--commit-range",
            help='Git commit range to generate changelog for (e.g., "576ebd6..698b4d07")',
        ),
    ] = None,
    list_models: Annotated[
        bool, typer.Option("--list-models", help="List available AI models")
    ] = False,
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

    # If no subcommand was invoked, run the generation logic
    if ctx.invoked_subcommand is None:
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
            list_models,
            version,
        )


@app.command(
    name="generate",
    help="Generate a changelog (same as default behavior)",
    hidden=True,  # Hide this since it's now the default
)
def generate_command(
    commit1: Annotated[Optional[str], typer.Argument(help="First commit hash")] = None,
    commit2: Annotated[Optional[str], typer.Argument(help="Last commit hash")] = None,
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
        typer.Option("--output", "-o", help="Output file for the generated changelog"),
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
        Optional[bool], typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = None,
    commit_range: Annotated[
        Optional[str],
        typer.Option(
            "--commit-range",
            help='Git commit range to generate changelog for (e.g., "576ebd6..698b4d07")',
        ),
    ] = None,
    list_models: Annotated[
        bool, typer.Option("--list-models", help="List available AI models")
    ] = False,
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
    """Generate a changelog (explicit command)."""
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
        list_models,
        version,
    )


def generate_changelog(
    commit1: Optional[str] = None,
    commit2: Optional[str] = None,
    config_path: Optional[str] = None,
    repo_path: Optional[str] = None,
    output_file: Optional[str] = None,
    branch: Optional[str] = None,
    model_provider: Optional[str] = None,
    model_name: Optional[str] = None,
    verbose: Optional[bool] = None,
    commit_range: Optional[str] = None,
    list_models: bool = False,
    version: Optional[bool] = None,  # Used for version display but handled by callback
):
    """Core changelog generation logic."""

    try:
        # Auto-create config if it doesn't exist and no custom path specified
        if not config_path and not os.path.exists(".changelog.yaml"):
            console.print(
                "[yellow]No .changelog.yaml found. Creating default configuration...[/yellow]"
            )
            init_config(".changelog.yaml")
            console.print(
                "[green]Configuration created! You can customize it and run the command again.[/green]"
            )
            sys.exit(0)

        # Load configuration using the new ChangelogConfig class
        config = ChangelogConfig.load_config(config_path)

        # Validate AI provider configuration
        if config.ai.enabled:
            validation_errors = validate_ai_config(config.ai)
            if validation_errors:
                console.print("[bold red]AI Configuration Issues:[/bold red]")
                for error in validation_errors:
                    console.print(f"  - {error}")
                console.print(
                    "[yellow]Fix these issues or disable AI generation (set ai.enabled: false)[/yellow]"
                )
                sys.exit(1)

    except (FileNotFoundError, ValueError, ValidationError, RuntimeError) as e:
        console.print(f"[bold red]Error loading configuration: {e}[/bold red]")
        if "not found" in str(e).lower():
            console.print(
                "[blue]Tip: Run 'changelog-generator init' to create a configuration file[/blue]"
            )
        sys.exit(1)

    # Override config with CLI arguments
    if repo_path:
        config.git.repository_path = repo_path
    if branch:
        config.git.branch = branch
    if output_file:
        config.changelog.output_file = output_file
    if model_provider:
        config.ai.provider = model_provider
    if model_name:
        config.ai.model_name = model_name
    if commit_range:
        config.git.commit_range = commit_range
    if verbose is not None:  # Check if verbose was explicitly provided
        config.logging.level = (
            "DEBUG" if verbose else config.logging.level
        )  # Keep original level if not verbose

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, config.logging.level.upper()))
    if config.logging.level.upper() == "DEBUG":
        logger.debug("Verbose logging enabled.")

    if list_models:
        try:
            models = ollama.list()
            console.print("[bold green]Available Ollama Models:[/bold green]")
            for model in models["models"]:
                console.print(f"- {model.get('name', 'Unknown')}")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]Error listing models: {e}[/bold red]")
            sys.exit(1)

    # Validate git repository
    try:
        repo = git.Repo(config.git.repository_path)

        # Check if repo has any commits
        try:
            list(repo.iter_commits(max_count=1))
        except git.exc.GitCommandError:
            console.print("[bold red]Error: Git repository has no commits.[/bold red]")
            console.print(
                "[blue]Tip: Make some commits first, then run the changelog generator.[/blue]"
            )
            sys.exit(1)

        # Check if specified branch exists
        if config.git.branch not in [branch.name for branch in repo.branches]:
            available_branches = [branch.name for branch in repo.branches]
            console.print(
                f"[bold red]Error: Branch '{config.git.branch}' not found.[/bold red]"
            )
            console.print(
                f"[blue]Available branches: {', '.join(available_branches)}[/blue]"
            )
            sys.exit(1)

    except git.exc.InvalidGitRepositoryError:
        console.print(
            f"[bold red]Error: '{config.git.repository_path}' is not a valid Git repository.[/bold red]"
        )
        console.print(
            "[blue]Tip: Make sure you're in a Git repository or specify the correct path with --repo[/blue]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error accessing Git repository: {e}[/bold red]")
        sys.exit(1)

    # Get commits with enhanced validation
    try:
        if commit_range:
            if ".." not in commit_range:
                console.print(
                    "[bold red]Error: Commit range must be in format 'commit1..commit2'[/bold red]"
                )
                console.print("[blue]Example: --commit-range abc123..def456[/blue]")
                sys.exit(1)

            start_commit_hash, end_commit_hash = commit_range.split("..", 1)

            # Validate that commits exist
            try:
                repo.commit(start_commit_hash)
                repo.commit(end_commit_hash)
            except git.exc.BadName as e:
                console.print(
                    f"[bold red]Error: Invalid commit hash in range: {e}[/bold red]"
                )
                console.print(
                    "[blue]Tip: Use 'git log --oneline' to see available commit hashes[/blue]"
                )
                sys.exit(1)

            commit1_obj, commit2_obj = get_git_commits(
                repo, config, start_commit_hash, end_commit_hash
            )
        elif commit1 and commit2:
            try:
                repo.commit(commit1)
                repo.commit(commit2)
            except git.exc.BadName as e:
                console.print(f"[bold red]Error: Invalid commit hash: {e}[/bold red]")
                sys.exit(1)
            commit1_obj, commit2_obj = get_git_commits(repo, config, commit1, commit2)
        else:
            commit1_obj, commit2_obj = get_git_commits(repo, config)

        # Check if we have any commits to process
        commits_to_process = list(
            repo.iter_commits(f"{commit1_obj.hexsha}..{commit2_obj.hexsha}")
        )
        if not commits_to_process:
            console.print(
                "[bold yellow]Warning: No commits found in the specified range.[/bold yellow]"
            )
            console.print(
                "[blue]Tip: Check your commit range or ensure there are commits between the specified points[/blue]"
            )
            sys.exit(0)

        logger.info(
            f"Generating changelog from {commit1_obj.hexsha[:7]} to {commit2_obj.hexsha[:7]} ({len(commits_to_process)} commits)"
        )
    except Exception as e:
        console.print(f"[bold red]Error processing commits: {e}[/bold red]")
        if "unknown revision" in str(e).lower():
            console.print(
                "[blue]Tip: Ensure the commit hashes exist in your repository[/blue]"
            )
        sys.exit(1)

    # Get changes between commits
    try:
        changes = get_commit_changes(
            repo, commit1_obj, commit2_obj, config.breaking_change_detection.keywords
        )

        if config.logging.level.upper() == "DEBUG":
            logger.debug("Detected Changes:")
            logger.debug(f"Added Files: {changes['added_files']}")
            logger.debug(f"Modified Files: {changes['modified_files']}")
            logger.debug(f"Deleted Files: {changes['deleted_files']}")
            logger.debug(f"Breaking Changes: {changes['breaking_changes']}")
    except Exception as e:
        logger.error(f"Failed to get changes: {e}")
        sys.exit(1)

    # Generate AI-powered changelog if enabled
    if config.ai.enabled:
        try:
            ai_changelog_content = generate_ai_changelog(
                changes, config.ai
            )  # Pass AI settings

            # Determine output file name and format
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_name = config.changelog.output_file

            # Auto-detect format from file extension or add timestamp for default
            output_format = determine_output_format(output_file_name)
            if output_file_name == "CHANGELOG.md":  # Default case, append timestamp
                output_file_name = f"CHANGELOG_{timestamp}.md"

            model_provider_used = config.ai.provider
            model_name_used = config.ai.model_name

            # Generate changelog content in the appropriate format
            final_changelog_content = generate_changelog_content(
                commits=changes["commits"],
                breaking_changes=changes["breaking_changes"],
                commit_range=f"{commit1_obj.hexsha[:7]}..{commit2_obj.hexsha[:7]}",
                model_provider=model_provider_used,
                model_name=model_name_used,
                output_format=output_format,
                ai_summary=ai_changelog_content,
            )

            # Write changelog to file
            with open(output_file_name, "w", encoding="utf-8") as f:
                f.write(final_changelog_content)

            console.print(
                f"[bold green]Changelog generated and saved to {output_file_name}[/bold green]"
            )
            console.print(
                f"[bold green]Format: {output_format.upper()} | Provider: {model_provider_used}/{model_name_used}[/bold green]"
            )

            if config.logging.level.upper() == "DEBUG":
                console.print("\n[bold blue]Changelog Preview:[/bold blue]")
                console.print(final_changelog_content)

        except Exception as e:
            console.print(
                f"[bold red]Error: Failed to generate changelog - {e}[/bold red]"
            )
            sys.exit(1)
    else:
        console.print(
            "[bold yellow]AI changelog generation is disabled. No changelog will be generated.[/bold yellow]"
        )
        sys.exit(0)


@app.command(name="init", help="Initialize a new .changelog.yaml configuration file")
def init_config(
    output_path: Annotated[
        str, typer.Option("--output", "-o", help="Output path for config file")
    ] = ".changelog.yaml",
):
    """Initialize a new configuration file."""
    if os.path.exists(output_path):
        if not typer.confirm(f"Config file {output_path} already exists. Overwrite?"):
            console.print("[yellow]Configuration initialization cancelled.[/yellow]")
            raise typer.Exit(0)

    default_config = """# Changelog Generator Configuration

# Git Repository Settings
git:
  # Path to the git repository (optional, defaults to current directory)
  repository_path: .
  
  # Branch to generate changelog for (optional, defaults to current branch)
  branch: main
  
  # Optional: specify a specific commit range
  # commit_range: 'old_commit..new_commit'

# Changelog Generation Settings
changelog:
  # Output file name
  output_file: "CHANGELOG.md"
  
  # Template to use for generation
  template: "markdown_template.j2"
  
  # Customize changelog sections
  sections:
    - type: feat
      title: "🚀 Features"
    - type: fix
      title: "🐛 Bug Fixes"
    - type: docs
      title: "📝 Documentation"
    - type: refactor
      title: "♻️ Refactoring"
    - type: test
      title: "🧪 Tests"
    - type: chore
      title: "🔧 Chores"

# AI-Powered Changelog Generation (Optional)
ai:
  # Enable AI-powered changelog generation
  enabled: true
  
  # AI Provider: 'ollama', 'xai', or 'anthropic'
  provider: ollama
  
  # Specific AI model to use (depends on provider)
  model_name: qwen3:latest
  
  # Provider-specific models (configure based on your setup)
  ollama_model: qwen3:latest
  xai_model: grok-2
  anthropic_model: claude-3-opus-20240229
  
  # API keys (can also be set as environment variables)
  # xai_api_key: your_xai_api_key_here
  # anthropic_api_key: your_anthropic_api_key_here

# Breaking Change Detection
breaking_change_detection:
  keywords:
    - "breaking"
    - "breaking change"
    - "deprecated"
    - "removed"
    - "breaking api"
    - "incompatible"

# Logging Configuration
logging:
  # Logging level: DEBUG, INFO, WARNING, ERROR
  level: INFO
"""

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(default_config)
        console.print(
            f"[bold green]Configuration file created at {output_path}[/bold green]"
        )
        console.print(
            "[blue]Edit the file to customize your changelog generation settings.[/blue]"
        )
    except Exception as e:
        console.print(f"[bold red]Error creating configuration file: {e}[/bold red]")
        raise typer.Exit(1)


@app.command(name="models", help="List available AI models for all providers")
def list_all_models():
    """List available AI models for all providers."""
    console.print("[bold blue]Available AI Models:[/bold blue]\n")

    # Ollama models
    try:
        models = ollama.list()
        console.print("[bold green]Ollama Models:[/bold green]")
        if models.get("models"):
            for model in models["models"]:
                console.print(f"  - {model.get('name', 'Unknown')}")
        else:
            console.print(
                "  [yellow]No Ollama models found or Ollama not running[/yellow]"
            )
    except Exception as e:
        console.print(f"  [red]Error listing Ollama models: {e}[/red]")

    console.print("\n[bold green]XAI Models:[/bold green]")
    console.print("  - grok-2")
    console.print("  - grok-beta")

    console.print("\n[bold green]Anthropic Models:[/bold green]")
    console.print("  - claude-3-opus-20240229")
    console.print("  - claude-3-sonnet-20240229")
    console.print("  - claude-3-haiku-20240307")

    console.print(
        "\n[blue]Note: For XAI and Anthropic models, ensure you have valid API keys configured.[/blue]"
    )


if __name__ == "__main__":
    app()
