"""UI components for the changelog generator CLI."""

from typing import Optional, Dict
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.panel import Panel

console = Console()


def create_progress_bar(description: str, total: Optional[int] = None) -> Progress:
    """Create a rich progress bar with consistent styling."""
    if total is None:
        # Spinner for indeterminate progress
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        )
    else:
        # Progress bar for determinate progress
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        )


def show_operation_summary(operation: str, details: Dict):
    """Display a summary of the completed operation."""
    table = Table(
        title=f"✅ {operation} Complete", show_header=True, header_style="bold green"
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    for key, value in details.items():
        table.add_row(key, str(value))

    console.print(table)


def show_config_panel(config_json: str, config_file: str) -> None:
    """Display configuration in a formatted panel."""
    panel = Panel(
        config_json,
        title="📋 Current Configuration",
        border_style="blue",
        expand=False,
    )
    console.print(panel)
    console.print(f"\n[dim]Configuration loaded from: {config_file}[/dim]")


def show_changelog_preview(content: str) -> None:
    """Display a preview of the generated changelog."""
    console.print("\n[bold blue]Changelog Preview:[/bold blue]")
    preview_panel = Panel(
        content[:500] + "..." if len(content) > 500 else content,
        title="📄 Generated Changelog Preview",
        border_style="blue",
        expand=False,
    )
    console.print(preview_panel)


def create_models_table() -> Table:
    """Create a table for displaying AI models."""
    table = Table(
        title="🤖 Available AI Models", show_header=True, header_style="bold blue"
    )
    table.add_column("Provider", style="cyan", width=12)
    table.add_column("Model", style="white")
    table.add_column("Status", style="green")
    return table
