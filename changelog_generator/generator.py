import argparse
import logging
import sys
from datetime import datetime
import os
from typing import Dict, List, Optional

import git
import ollama
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed
from changelog_generator.changelog_config import ChangelogConfig

from changelog_generator.ai_provider_manager import AIProviderManager

# Local imports
from changelog_generator.changelog_utils import (
    format_breaking_changes,
    get_commit_changes,
    validate_commits,
)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Load configuration from .changelog.yaml or default configuration
    
    Args:
        config_path (Optional[str]): Path to custom config file
    
    Returns:
        Dict: Configuration dictionary
    """
    default_config = {
        'git': {
            'repository_path': '.',
            'branch': 'main',
            'commit_range': None
        },
        'changelog': {
            'output_file': 'CHANGELOG.md',
            'sections': [
                {'type': 'feat', 'title': '🚀 Features'},
                {'type': 'fix', 'title': '🐛 Bug Fixes'},
                {'type': 'docs', 'title': '📝 Documentation'},
                {'type': 'refactor', 'title': '♻️ Refactoring'},
                {'type': 'test', 'title': '🧪 Tests'},
                {'type': 'chore', 'title': '🔧 Chores'}
            ]
        },
        'ai': {
            'enabled': False,
            'provider': 'ollama',
            'model_name': 'qwen2.5:14b'
        },
        'logging': {
            'level': 'INFO'
        }
    }

    # Check for config file
    if not config_path:
        config_path = os.path.join(os.getcwd(), '.changelog.yaml')

    if os.path.exists(config_path):
        try:
            logger.info(f"Loading configuration from {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                # Deep merge default and user config
                for key, value in user_config.items():
                    if isinstance(value, dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except Exception as e:
            logger.warning(f"Error reading config file: {e}. Using default configuration.")

    return default_config

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_ai_changelog(
    changes: Dict[str, List[str]],
    ai_provider: Optional[AIProviderManager] = None
) -> str:
    """
    Generate a changelog using an AI model with robust error handling and retries.
    
    Args:
        changes: Dictionary of changes to generate changelog for
        ai_provider: Optional AIProviderManager instance for testing
        
    Returns:
        str: Generated changelog content
    """
    config = ChangelogConfig()
    try:
        if ai_provider is None:
            ai_provider = AIProviderManager(config.get("model_provider"), config.get("model_name"))
            
        changelog = ai_provider.invoke(changes)

        if not changelog:
            raise ValueError("Changelog generation failed")
        if isinstance(changelog, dict) and "error" in changelog:
            raise ValueError(changelog["error"])

        return changelog

    except Exception as e:
        logger.error(f"Changelog generation error: {e}")
        raise

def get_git_commits(repo: git.Repo, config: Dict, commit1: Optional[str] = None, commit2: Optional[str] = None) -> tuple:
    """
    Get commits based on configuration or provided commit hashes
    
    Args:
        repo (git.Repo): Git repository object
        config (Dict): Configuration dictionary
        commit1 (Optional[str]): First commit hash
        commit2 (Optional[str]): Second commit hash
    
    Returns:
        tuple: First and last commit
    """
    if commit1 and commit2:
        # If specific commits are provided, use them
        return repo.commit(commit1), repo.commit(commit2)

    branch = config['git'].get('branch', 'main')
    commit_range = config['git'].get('commit_range')

    if commit_range:
        start, end = commit_range.split('..')
        commit1 = repo.commit(start)
        commit2 = repo.commit(end)
    else:
        # Get first and last commit of specified branch
        branch_obj = repo.branches[branch]
        commit2 = branch_obj.commit
        commit1 = list(repo.iter_commits(branch, max_count=1))[-1]

    return commit1, commit2

def main():
    # Create parser without gettext translation
    parser = argparse.ArgumentParser(
        description="Generate a detailed AI-powered changelog for a Git repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  Generate changelog between two specific commits:
    python changelog_generator.py 123456 234567

  Generate changelog for current branch:
    python changelog_generator.py
"""
    )
    parser.add_argument(
        "commit1",
        nargs='?',
        help="First commit hash"
    )
    parser.add_argument(
        "commit2", 
        nargs='?',
        help="Last commit hash"
    )
    parser.add_argument(
        "--config",
        help="Path to custom configuration file"
    )
    parser.add_argument(
        "--repo", 
        default=".",
        help="Path to the Git repository (default: current directory)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for the generated changelog"
    )
    parser.add_argument(
        "--branch",
        help="Specify a branch to generate changelog for"
    )
    parser.add_argument(
        "--model-provider",
        choices=["ollama", "xai"],
        help="AI model provider"
    )
    parser.add_argument(
        "--model-name",
        help="Specific AI model to use"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    parser.add_argument('--commit-range', type=str, help='Git commit range to generate changelog for (e.g., "576ebd6..698b4d07")')
    parser.add_argument('--list-models', action='store_true', help='List available AI models')

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Override config with CLI arguments
    if args.repo:
        config['git']['repository_path'] = args.repo
    if args.branch:
        config['git']['branch'] = args.branch
    if args.output:
        config['changelog']['output_file'] = args.output
    if args.model_provider:
        config['ai']['provider'] = args.model_provider
    if args.model_name:
        config['ai']['model_name'] = args.model_name

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, config['logging']['level'].upper()))

    try:
        repo = git.Repo(config['git']['repository_path'])
    except git.exc.InvalidGitRepositoryError:
        logger.error(f"Error: Invalid git repository at {config['git']['repository_path']}")
        sys.exit(1)

    # Get commits
    try:
        # Get commits based on provided arguments or config
        commit1 = args.commit1
        commit2 = args.commit2
            
        if not commit1 and not commit2:
            # If no commits provided, use config defaults
            commit1, commit2 = get_git_commits(repo, config)
        else:
            # Validate that both commits are provided if either is
            if not commit1 or not commit2:
                logger.error("Error: Must provide both start and end commits")
                sys.exit(1)
                    
            commit1, commit2 = get_git_commits(repo, config, commit1, commit2)
        
        logger.info(f"Generating changelog from {commit1.hexsha[:7]} to {commit2.hexsha[:7]}")
    except Exception as e:
        logger.error(f"Error: Invalid commit range - {e}")
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
        logger.error(f"Error: Invalid commit range - {e}")
        sys.exit(1)

    # Generate AI-powered changelog if enabled
    if config['ai']['enabled']:
        try:
            formatted_breaking_changes = format_breaking_changes(changes['breaking_changes'])
            ai_changelog = generate_ai_changelog(
                changes
            )
            ai_changelog = f"# Breaking Changes\n{formatted_breaking_changes}\n\n{ai_changelog}"

            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"CHANGELOG_{timestamp}.md"
            
            config = ChangelogConfig()
            model_provider = config.get("model_provider")
            model_name = config.get("model_name")

            # Write changelog to file
            with open(output_file, "w", encoding='utf-8') as f:
                f.write(
                    f"# Changelog: {commit1.hexsha[:7]}..{commit2.hexsha[:7]} (via {model_provider}/{model_name})\n\n"
                )
                f.write(ai_changelog)

            logger.info(f"Changelog generated and saved to {output_file}")
            logger.info(f"Changelog generated using {model_provider}/{model_name}")

            if args.verbose:
                logger.info("\nChangelog Preview:")
                logger.info(ai_changelog)

        except Exception as e:
            logger.error(f"Error: Failed to generate changelog - {e}")
            sys.exit(1)

    if args.list_models:
        # List models and exit successfully
        try:
            models = ollama.list()  # Updated to use correct ollama API
            for model in models['models']:
                logger.info(f"Available model: {model.get('name', 'Unknown')}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            sys.exit(0)  # Exit with 0 even if there's an error
    else:
        logger.warning("AI changelog generation is disabled. No changelog will be generated.")

if __name__ == "__main__":
    main()
