import argparse
import git
import sys
from typing import Dict, List
from dotenv import load_dotenv
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

# Local imports
from changelog_utils import (
    validate_commits,
    get_commit_changes,
    format_breaking_changes,
)
from ai_provider_manager import AIProviderManager

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
    - openai
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
        default="CHANGELOG.md",
        help="Output file for the generated changelog (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--model-provider",
        choices=["openai", "ollama", "xai"],
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
        models = list_ollama_models()
        print("Available Ollama Models:")
        for model in models:
            print(f"- {model}")
        sys.exit(0)

    try:
        repo = git.Repo(args.repo)
    except git.exc.InvalidGitRepositoryError:
        print(f"Error: {args.repo} is not a valid Git repository.")
        sys.exit(1)

    # Validate and get commits
    try:
        commit1, commit2 = validate_commits(repo, args.commit1, args.commit2)
    except Exception as e:
        print(f"Commit validation error: {e}")
        sys.exit(1)

    # Get changes between commits
    try:
        changes = get_commit_changes(repo, commit1, commit2)

        if args.verbose:
            print("Detected Changes:")
            print(f"Added Files: {changes['added_files']}")
            print(f"Modified Files: {changes['modified_files']}")
            print(f"Deleted Files: {changes['deleted_files']}")
            print(f"Breaking Changes: {changes['breaking_changes']}")
    except Exception as e:
        print(f"Error retrieving commit changes: {e}")
        sys.exit(1)

    # Generate AI-powered changelog
    try:
        # Use the model name from arguments or set a default
        model_name = args.model_name or (
            "llama3.2:latest" if args.model_provider == "ollama" else "gpt-4-turbo"
        )

        ai_changelog = generate_ai_changelog(
            changes, model_provider=args.model_provider, model_name=model_name
        )

        # Write changelog to file
        with open(args.output, "w") as f:
            f.write(
                f"# Changelog: {commit1.hexsha[:7]}..{commit2.hexsha[:7]} (via {args.model_provider}/{model_name})\n\n"
            )
            f.write(ai_changelog)

        print(f"Changelog generated and saved to {args.output}")
        print(f"\nChangelog generated using {args.model_provider}/{model_name}")

        if args.verbose:
            print("\nChangelog Preview:")
            print(ai_changelog)

    except Exception as e:
        print(f"Error generating AI changelog: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
