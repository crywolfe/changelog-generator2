"""Core changelog generation logic."""

import os
import sys
import logging
import time
from datetime import datetime
from typing import Optional

import git
from pydantic import ValidationError

from changelog_generator.changelog_config import ChangelogConfig
from changelog_generator.changelog_utils import get_commit_changes
from changelog_generator.generator import (
    generate_ai_changelog,
    determine_output_format,
    generate_changelog_content,
)
from changelog_generator.git_utils import get_git_commits
from changelog_generator.cli.ui import (
    console,
    create_progress_bar,
    show_operation_summary,
    show_changelog_preview,
)
from changelog_generator.cli.validation import validate_ai_config

logger = logging.getLogger(__name__)


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
):
    """Core changelog generation logic."""
    from changelog_generator.cli.commands import init_config

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

    # Validate git repository and get commits
    repo, commit1_obj, commit2_obj = _validate_and_get_commits(
        config, commit1, commit2, commit_range
    )

    # Get changes between commits
    changes = _get_commit_changes(repo, commit1_obj, commit2_obj, config)

    # Generate AI-powered changelog if enabled
    if config.ai.enabled:
        _generate_ai_changelog(changes, config, commit1_obj, commit2_obj)
    else:
        console.print(
            "[bold yellow]AI changelog generation is disabled. No changelog will be generated.[/bold yellow]"
        )
        sys.exit(0)


def _validate_and_get_commits(config, commit1, commit2, commit_range):
    """Validate git repository and get commits."""
    # Validate git repository
    with create_progress_bar("Validating Git repository...") as progress:
        git_task = progress.add_task("[cyan]Validating Git repository...", total=None)
        try:
            repo = git.Repo(config.git.repository_path)

            # Check if repo has any commits
            try:
                list(repo.iter_commits(max_count=1))
            except git.exc.GitCommandError:
                console.print(
                    "[bold red]Error: Git repository has no commits.[/bold red]"
                )
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
            progress.update(git_task, description="[green]Git repository validated.")
        except git.exc.InvalidGitRepositoryError:
            progress.update(
                git_task, description="[red]Git repository validation failed."
            )
            console.print(
                f"[bold red]Error: '{config.git.repository_path}' is not a valid Git repository.[/bold red]"
            )
            console.print(
                "[blue]Tip: Make sure you're in a Git repository or specify the correct path with --repo[/blue]"
            )
            sys.exit(1)
        except Exception as e:
            progress.update(
                git_task, description="[red]Git repository validation failed."
            )
            console.print(f"[bold red]Error accessing Git repository: {e}[/bold red]")
            sys.exit(1)

    # Get commits with enhanced validation
    with create_progress_bar("Fetching commits...") as progress:
        commit_task = progress.add_task("[cyan]Fetching commits...", total=None)
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
                    console.print(
                        f"[bold red]Error: Invalid commit hash: {e}[/bold red]"
                    )
                    sys.exit(1)
                commit1_obj, commit2_obj = get_git_commits(
                    repo, config, commit1, commit2
                )
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
            progress.update(commit_task, description="[green]Commits fetched.")
        except Exception as e:
            progress.update(commit_task, description="[red]Fetching commits failed.")
            console.print(f"[bold red]Error processing commits: {e}[/bold red]")
            if "unknown revision" in str(e).lower():
                console.print(
                    "[blue]Tip: Ensure the commit hashes exist in your repository[/blue]"
                )
            sys.exit(1)

    return repo, commit1_obj, commit2_obj


def _get_commit_changes(repo, commit1_obj, commit2_obj, config):
    """Get changes between commits."""
    with create_progress_bar("Analyzing changes...") as progress:
        changes_task = progress.add_task("[cyan]Analyzing changes...", total=None)
        try:
            changes = get_commit_changes(
                repo,
                commit1_obj,
                commit2_obj,
                config.breaking_change_detection.keywords,
            )

            if config.logging.level.upper() == "DEBUG":
                logger.debug("Detected Changes:")
                logger.debug(f"Added Files: {changes['added_files']}")
                logger.debug(f"Modified Files: {changes['modified_files']}")
                logger.debug(f"Deleted Files: {changes['deleted_files']}")
                logger.debug(f"Breaking Changes: {changes['breaking_changes']}")
            progress.update(changes_task, description="[green]Changes analyzed.")
        except Exception as e:
            progress.update(changes_task, description="[red]Analyzing changes failed.")
            logger.error(f"Failed to get changes: {e}")
            sys.exit(1)

    return changes


def _generate_ai_changelog(changes, config, commit1_obj, commit2_obj):
    """Generate AI-powered changelog."""
    # Multi-step progress for AI generation
    with create_progress_bar("Generating changelog", total=4) as progress:
        # Step 1: Prepare AI input
        prep_task = progress.add_task("[cyan]Preparing AI input...", total=1)
        time.sleep(0.5)  # Simulate preparation time
        progress.update(prep_task, advance=1, description="[green]AI input prepared")

        # Step 2: Generate AI content
        ai_task = progress.add_task("[cyan]Generating AI changelog...", total=1)
        try:
            ai_changelog_content = generate_ai_changelog(
                changes, config.ai
            )  # Pass AI settings
            progress.update(
                ai_task, advance=1, description="[green]AI changelog generated"
            )
        except Exception as e:
            progress.update(ai_task, description="[red]AI changelog generation failed")
            console.print(f"[bold red]Error generating AI changelog: {e}[/bold red]")
            sys.exit(1)

        # Step 3: Format output
        format_task = progress.add_task("[cyan]Formatting output...", total=1)

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
        progress.update(format_task, advance=1, description="[green]Output formatted")

        # Step 4: Write to file
        write_task = progress.add_task("[cyan]Writing to file...", total=1)
        try:
            with open(output_file_name, "w", encoding="utf-8") as f:
                f.write(final_changelog_content)
            progress.update(
                write_task,
                advance=1,
                description="[green]File written successfully",
            )

        except Exception as e:
            progress.update(write_task, description="[red]File write failed")
            console.print(
                f"[bold red]Error: Failed to write changelog - {e}[/bold red]"
            )
            sys.exit(1)

    # Show completion summary
    summary_details = {
        "Output File": output_file_name,
        "Format": output_format.upper(),
        "AI Provider": f"{model_provider_used}/{model_name_used}",
        "Commits Processed": len(changes["commits"]),
        "Breaking Changes": len(changes["breaking_changes"]),
        "Files Modified": len(changes["modified_files"]),
    }
    show_operation_summary("Changelog Generation", summary_details)

    if config.logging.level.upper() == "DEBUG":
        show_changelog_preview(final_changelog_content)
