import logging
import os
import json
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential
from jinja2 import Environment, FileSystemLoader

from changelog_generator.ai_provider_manager import AIProviderManager
from changelog_generator.config_models import AISettings

logger = logging.getLogger(__name__)

# Setup Jinja2 environment
template_loader = FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates"))
jinja_env = Environment(loader=template_loader, autoescape=True)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_ai_changelog(
    changes: Dict[str, List[str]], ai_settings: AISettings  # Accept AISettings object
) -> str:
    """
    Generate a changelog using an AI model with robust error handling and retries.

    Args:
        changes: Dictionary of changes to generate changelog for
        ai_settings: AISettings object containing AI configuration

    Returns:
        str: Generated changelog content
    """
    try:
        ai_provider = AIProviderManager(ai_settings)  # Pass AISettings to manager
        changelog = ai_provider.invoke(changes)

        if not changelog:
            raise ValueError("Changelog generation failed")
        if isinstance(changelog, dict) and "error" in changelog:
            raise ValueError(changelog["error"])

        return changelog

    except Exception as e:
        logger.error(f"Changelog generation error: {e}")
        raise


def generate_changelog_from_template(
    commits: List[Dict],
    breaking_changes: List[str],
    commit_range: str,
    model_provider: str,
    model_name: str,
    template_name: str,
    ai_summary: Optional[str] = None,  # New argument for AI summary
) -> str:
    """
    Generates a changelog using a Jinja2 template.

    Args:
        commits (List[Dict]): List of parsed commit dictionaries.
        breaking_changes (List[str]): List of breaking change messages.
        commit_range (str): The range of commits covered.
        model_provider (str): The AI model provider used.
        model_name (str): The AI model name used.
        template_name (str): The name of the Jinja2 template to use.
        ai_summary (Optional[str]): AI-generated summary of changes.

    Returns:
        str: The rendered changelog content.
    """
    template = jinja_env.get_template(template_name)

    # Group commits by type and then by scope
    grouped_commits = defaultdict(lambda: defaultdict(list))
    for commit in commits:
        commit_type = commit.get("type", "other").capitalize()
        scope = commit.get("scope", "General").capitalize()
        grouped_commits[commit_type][scope].append(commit)

    return template.render(
        grouped_commits=grouped_commits,
        breaking_changes=breaking_changes,
        commit_range=commit_range,
        model_provider=model_provider,
        model_name=model_name,
        ai_summary=ai_summary,
    )


def generate_json_changelog(
    commits: List[Dict],
    breaking_changes: List[str],
    commit_range: str,
    model_provider: str,
    model_name: str,
    ai_summary: Optional[str] = None,
) -> str:
    """
    Generates a changelog in JSON format.

    Args:
        commits (List[Dict]): List of parsed commit dictionaries.
        breaking_changes (List[str]): List of breaking change messages.
        commit_range (str): The range of commits covered.
        model_provider (str): The AI model provider used.
        model_name (str): The AI model name used.
        ai_summary (Optional[str]): AI-generated summary of changes.

    Returns:
        str: The JSON changelog content.
    """
    # Group commits by type and then by scope
    grouped_commits = defaultdict(lambda: defaultdict(list))
    for commit in commits:
        commit_type = commit.get("type", "other")
        scope = commit.get("scope", "general")
        grouped_commits[commit_type][scope].append(commit)

    changelog_data = {
        "metadata": {
            "commit_range": commit_range,
            "model_provider": model_provider,
            "model_name": model_name,
            "generated_at": datetime.now().isoformat(),
            "total_commits": len(commits),
        },
        "ai_summary": ai_summary,
        "breaking_changes": breaking_changes,
        "changes": dict(grouped_commits),
        "commits": commits,
    }

    return json.dumps(changelog_data, indent=2, ensure_ascii=False)


def determine_output_format(output_file: str) -> str:
    """Determine output format based on file extension."""
    if output_file.endswith(".json"):
        return "json"
    elif output_file.endswith(".html"):
        return "html"
    else:
        return "markdown"


def generate_changelog_content(
    commits: List[Dict],
    breaking_changes: List[str],
    commit_range: str,
    model_provider: str,
    model_name: str,
    output_format: str,
    ai_summary: Optional[str] = None,
) -> str:
    """
    Generate changelog content in the specified format.

    Args:
        commits: List of parsed commit dictionaries
        breaking_changes: List of breaking change messages
        commit_range: The range of commits covered
        model_provider: The AI model provider used
        model_name: The AI model name used
        output_format: Output format ('markdown', 'html', 'json')
        ai_summary: AI-generated summary of changes

    Returns:
        str: The generated changelog content
    """
    if output_format == "json":
        return generate_json_changelog(
            commits,
            breaking_changes,
            commit_range,
            model_provider,
            model_name,
            ai_summary,
        )
    elif output_format == "html":
        return generate_changelog_from_template(
            commits,
            breaking_changes,
            commit_range,
            model_provider,
            model_name,
            "html_template.j2",
            ai_summary,
        )
    else:  # Default to markdown
        return generate_changelog_from_template(
            commits,
            breaking_changes,
            commit_range,
            model_provider,
            model_name,
            "markdown_template.j2",
            ai_summary,
        )
