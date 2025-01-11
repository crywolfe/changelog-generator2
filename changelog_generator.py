import argparse
import logging
import sys
from datetime import datetime
from typing import Dict, List

import git
import ollama  # Ensure ollama is imported
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from ai_provider_manager import AIProviderManager

# Local imports
from changelog_utils import (
    format_breaking_changes,
    get_commit_changes,
    validate_commits,
)

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_ai_changelog(
    changes: Dict[str, List[str]],
    model_provider: str = "ollama",
    model_name: str = None,
) -> str:
    """
    Generate a changelog using an AI model with robust error handling and retries.

    Supported model providers:
    - ollama
    - xai (Grok)
    """
    try:
        # Create AIProviderManager instance
        ai_provider = AIProviderManager(model_provider, model_name)
        changelog = ai_provider.invoke(changes)

        if not changelog or changelog.startswith("Unable to generate"):
            raise ValueError("Changelog generation failed")

        return changelog

    except Exception as e:
        logger.error(f"Changelog generation error: {e}")
        raise


def _list_ollama_models():
    try:
        response = ollama.models.list()
        return [model.name for model in response.models]
    except Exception as e:
        logger.error(f"Error listing Ollama models: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Generate a detailed AI-powered changelog between two Git commits."
    )
    parser.add_argument("commit1", help="First commit hash or reference")
    parser.add_argument("commit2", help="Second commit hash or reference")
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the Git repository (default: current directory)",
    )
    
    parser.add_argument(
        "--output",
        "-o",
        default=f"CHANGELOG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        help="Output file for the generated changelog (default: CHANGELOG[date_time].md)",
    )
    parser.add_argument(
        "--model-provider",
        choices=["ollama", "xai"],
        default="ollama",
        help="AI model provider (default: ollama)",
    )
    parser.add_argument(
        "--model-name",
        default="qwen2.5:14b",
        help="Specific Ollama model to use (default: qwen2.5:14b)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available Ollama models",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # List Ollama models if requested
    if args.list_models:
        models = _list_ollama_models()
        logger.info("Available Ollama Models:")
        for model in models:
            logger.info(f"- {model}")
        sys.exit(0)

    try:
        repo = git.Repo(args.repo)
    except git.exc.InvalidGitRepositoryError:
        logger.error(f"Error: {args.repo} is not a valid Git repository.")
        sys.exit(1)

    # Validate and get commits
    try:
        commit1, commit2 = validate_commits(repo, args.commit1, args.commit2)
        logger.info(f"Commit 1: {commit1.hexsha[:7]} - {commit1.message.strip()}")
        logger.info(f"Commit 2: {commit2.hexsha[:7]} - {commit2.message.strip()}")
    except Exception as e:
        logger.error(f"Commit validation error: {e}")
        sys.exit(1)

    # Get changes between commits
    try:
        changes = get_commit_changes(repo, commit1, commit2)

        if args.verbose:
            logger.info("Detected Changes:")
            logger.info(f"Added Files: {changes['added_files']}")
            logger.info(f"Modified Files: {changes['modified_files']}")
            logger.info(f"Deleted Files: {changes['deleted_files']}")
            logger.info(f"Breaking Changes: {changes['breaking_changes']}")
    except Exception as e:
        logger.error(f"Error retrieving commit changes: {e}")
        sys.exit(1)

    # Generate AI-powered changelog
    try:
        # Use the model name from arguments or set a default
        model_name = args.model_name or "qwen2.5:14b"

        formatted_breaking_changes = format_breaking_changes(changes['breaking_changes'])
        ai_changelog = generate_ai_changelog(
            changes, model_provider=args.model_provider, model_name=model_name
        )
        ai_changelog = f"# Breaking Changes\n{formatted_breaking_changes}\n\n{ai_changelog}"

        # Write changelog to file
        with open(args.output, "w") as f:
            f.write(
                f"# Changelog: {commit1.hexsha[:7]}..{commit2.hexsha[:7]} (via {args.model_provider}/{model_name})\n\n"
            )
            f.write(ai_changelog)

        logger.info(f"Changelog generated and saved to {args.output}")
        logger.info(f"\nChangelog generated using {args.model_provider}/{model_name}")

        if args.verbose:
            logger.info("\nChangelog Preview:")
            logger.info(ai_changelog)

    except Exception as e:
        logger.error(f"Error generating AI changelog: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
