from .generator import generate_ai_changelog
from .main import app as cli_app  # Expose the Typer app
from .version import __version__  # Import version from version.py

__all__ = ["generate_ai_changelog", "cli_app"]
