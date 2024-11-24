import argparse
import git
import sys
from typing import Dict, List
from dotenv import load_dotenv
import ollama
import subprocess

# Local imports
from changelog_utils import (
    validate_commits,
    get_commit_changes,
    format_breaking_changes,
)

def list_ollama_models():
    """
    List available Ollama models.

    Returns:
        list: Available Ollama model names
    """
    try:
        # Use subprocess to run ollama list command
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Parse the output and extract model names
        models = [
            line.split()[0] 
            for line in result.stdout.split('\n')[1:] 
            if line.strip() and not line.startswith('REPOSITORY')
        ]
        
        if not models:
            print("No Ollama models found. Please pull a model first.")
        
        return models
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving Ollama models: {e}")
        print("Ensure Ollama is installed and running.")
        return []
    except FileNotFoundError:
        print("Ollama executable not found. Please install Ollama.")
        return []

# Load environment variables
load_dotenv()


class OllamaLLM:
    def __init__(self, model="llama3.2:latest"):
        self.model = model

    def _create_changelog_prompt(self, changes: Dict[str, List[str]]) -> str:
        """
        Create a detailed prompt for changelog generation.

        Args:
            changes (dict): Detailed changes between commits

        Returns:
            str: Formatted prompt for LLM
        """
        prompt = "Generate a comprehensive changelog based on the following commit changes:\n\n"

        # Added Files
        if changes["added_files"]:
            prompt += "New Files Added:\n"
            for file in changes["added_files"]:
                prompt += f"- {file}\n"

        # Modified Files
        if changes["modified_files"]:
            prompt += "\nModified Files:\n"
            for file in changes["modified_files"]:
                prompt += f"- {file}\n"

        # Deleted Files
        if changes["deleted_files"]:
            prompt += "\nDeleted Files:\n"
            for file in changes["deleted_files"]:
                prompt += f"- {file}\n"

        # Breaking Changes
        if changes["breaking_changes"]:
            prompt += "\nBreaking Changes:\n"
            for change in changes["breaking_changes"]:
                prompt += f"- {change}\n"

        # Commit Messages
        if changes["commit_messages"]:
            prompt += "\nCommit Messages:\n"
            for msg in changes["commit_messages"]:
                prompt += f"- {msg}\n"

        prompt += (
            "\nPlease generate a detailed, professional changelog that highlights key changes, "
            "new features, bug fixes, and any breaking changes. Use markdown formatting."
        )

        return prompt

    def invoke(self, changes: Dict[str, List[str]]) -> str:
        """
        Generate changelog using Ollama LLM.

        Args:
            changes (dict): Detailed changes between commits

        Returns:
            str: Generated changelog
        """
        try:
            prompt = self._create_changelog_prompt(changes)

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional software changelog generator.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            return response["message"]["content"]

        except Exception as e:
            print(f"Error generating changelog with Ollama: {e}")
            return f"Unable to generate changelog. Error: {e}"


import logging
from tenacity import retry, stop_after_attempt, wait_exponential

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

    Args:
        changes (dict): Detailed changes between commits
        model_provider (str): The AI model provider (openai or ollama)
        model_name (str): The specific model to use

    Returns:
        str: AI-generated changelog

    Raises:
        ValueError: If an unsupported model provider is specified
        Exception: For persistent generation failures
    """
    try:
        # Validate model provider
        if model_provider == "ollama":
            if not model_name:
                model_name = "llama3.2:latest"

            # Create Ollama LLM instance
            ollama_llm = OllamaLLM(model=model_name)
            changelog = ollama_llm.invoke(changes)

            if not changelog or changelog.startswith("Unable to generate"):
                raise ValueError("Changelog generation failed")

            return changelog

        elif model_provider == "openai":
            from openai import OpenAI

            client = OpenAI()
            response = client.chat.completions.create(
                model=model_name or "gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional changelog generator.",
                    },
                    {
                        "role": "user",
                        "content": f"Generate a changelog for these changes: {changes}",
                    },
                ],
            )

            return response.choices[0].message.content

        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")

    except Exception as e:
        logger.error(f"Changelog generation error: {e}")
        
        # Provide more specific guidance for model-related errors
        if "model" in str(e).lower():
            available_models = list_ollama_models()
            if available_models:
                print("\nAvailable Ollama models:")
                for model in available_models:
                    print(f"- {model}")
                print("\nTry using one of the above models with --model-name")
            else:
                print("\nNo Ollama models found. Use 'ollama pull <model>' to download a model.")
        
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
        choices=["openai", "ollama"],
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
