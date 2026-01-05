import typer
from changelog_generator.cli.commands import setup_commands

app = typer.Typer(
    name="changelog-generator",
    help="🚀 Generate detailed AI-powered changelogs for Git repositories",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

# Set up all commands
setup_commands(app)


if __name__ == "__main__":
    app()
