import argparse
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

import git
import ollama
import yaml
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
            with open(config_path, 'r') as f:
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
    model_provider: str = "ollama",
    model_name: str = None,
) -> str:
    """
    Generate a changelog using an AI model with robust error handling and retries.
    """
    try:
        ai_provider = AIProviderManager(model_provider, model_name)
        changelog = ai_provider.invoke(changes)

        if not changelog or changelog.startswith("Unable to generate"):
            raise ValueError("Changelog generation failed")

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
        "commits",
        nargs='*',
        help="Two commit hashes to compare (first and last commit)"
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the Git repository (default: current directory)"
    )
    parser.add_argument(
        "--config",
        help="Path to custom configuration file"
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
        logger.error(f"Error: {config['git']['repository_path']} is not a valid Git repository.")
        sys.exit(1)

    # Get commits
    try:
        # Support both old and new commit specification methods
        if len(args.commits) == 2:
            commit1, commit2 = get_git_commits(repo, config, args.commits[0], args.commits[1])
        else:
            commit1, commit2 = get_git_commits(repo, config)
        
        logger.info(f"Generating changelog from {commit1.hexsha[:7]} to {commit2.hexsha[:7]}")
    except Exception as e:
        logger.error(f"Commit retrieval error: {e}")
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

    # Generate AI-powered changelog if enabled
    if config['ai']['enabled']:
        try:
            model_name = config['ai']['model_name']
            model_provider = config['ai']['provider']

            formatted_breaking_changes = format_breaking_changes(changes['breaking_changes'])
            ai_changelog = generate_ai_changelog(
                changes, model_provider=model_provider, model_name=model_name
            )
            ai_changelog = f"# Breaking Changes\n{formatted_breaking_changes}\n\n{ai_changelog}"

            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"CHANGELOG_{timestamp}.md"
            
            # Write changelog to file
            with open(output_file, "w") as f:
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
            logger.error(f"Error generating AI changelog: {e}")
            sys.exit(1)
    else:
        logger.warning("AI changelog generation is disabled. No changelog will be generated.")

if __name__ == "__main__":
    main()
