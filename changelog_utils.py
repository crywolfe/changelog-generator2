import git
import sys
from typing import Dict, List, Union
from ai_provider_manager import AIProviderManager
import logging
import yaml


logger = logging.getLogger(__name__)

# Function to load the model name from the .changelog.yaml file
def load_provider_model_from_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config['ai']['provider'], config['ai']['model_name']

def validate_commits(repo, commit1, commit2):
    """
    Validate that both commits exist in the repository.

    Args:
        repo (git.Repo): Git repository object
        commit1 (str): First commit hash or reference
        commit2 (str): Second commit hash or reference

    Returns:
        tuple: Validated commit objects

    Raises:
        SystemExit: If either commit is invalid.
    """
    try:
        return repo.commit(commit1), repo.commit(commit2)
    except git.exc.BadName as e:
        print(f"Error: Invalid commit reference - {e}. Commits ({commit1}, {commit2}) do not exist in the repository.")
        sys.exit(1)


def get_commit_changes_modified(repo: git.Repo, commit1: Union[str, git.Commit], commit2: Union[str, git.Commit]) -> List[str]:
    """
    Retrieve modified files between two commits.

    Args:
        repo (git.Repo): Git repository object
        commit1 (str or git.Commit): First commit
        commit2 (str or git.Commit): Second commit

    Returns:
        list: List of modified files
    """
    commit1 = repo.commit(commit1) if isinstance(commit1, str) else commit1
    commit2 = repo.commit(commit2) if isinstance(commit2, str) else commit2

    diff = commit1.diff(commit2)
    return [change.b_path for change in diff if change.change_type == "M"]


def format_breaking_changes(breaking_changes: List[str]) -> str:
    """
    Format breaking changes into a readable string.

    Args:
        breaking_changes (List[str]): List of breaking change messages

    Returns:
        str: Formatted breaking changes
    """
    return "- No breaking changes" if not breaking_changes else "\n".join([f"- {change}" for change in breaking_changes])


def get_commit_changes(repo, commit1, commit2) -> Dict[str, List[str]]:
    """
    Retrieve changes between two commits.

    Args:
        repo (git.Repo): Git repository object
        commit1 (git.Commit): First commit
        commit2 (git.Commit): Second commit

    Returns:
        dict: Detailed changes between commits
    """
    # Validate input commits
    if not commit1 or not commit2:
        raise ValueError("Both commit1 and commit2 must be provided")
        
    commit1 = repo.commit(commit1) if isinstance(commit1, str) else commit1
    commit2 = repo.commit(commit2) if isinstance(commit2, str) else commit2

    # Initialize changes dictionary with required keys
    changes = {
        "added_files": [],
        "modified_files": [],
        "deleted_files": [],
        "commit_messages": [],
        "diff_details": [],
        "breaking_changes": [],
    }
    
    # Validate changes dictionary structure
    required_keys = ["added_files", "modified_files", "deleted_files",
                    "commit_messages", "diff_details", "breaking_changes"]
    for key in required_keys:
        if key not in changes:
            changes[key] = []

    # Log initial changes structure
    # print("Initial changes structure:", changes)

    diff = commit1.diff(commit2)
    # print(f"Found {len(diff)} changes between commits")

    for change in diff:
        if change.change_type == "A":
            changes["added_files"].append(change.b_path)
        elif change.change_type == "M":
            changes["modified_files"].append(change.b_path)
            try:
                patch = change.diff if isinstance(change.diff, str) else change.diff.decode("utf-8")
                changes["diff_details"].append({
                    "file": change.b_path,
                    "patch": patch
                })
            except Exception as e:
                print(f"Could not process diff for {change.b_path}: {e}")
        elif change.change_type == "D":
            changes["deleted_files"].append(change.b_path)

    # Collect all commit messages between the two commits
    changes["commit_messages"] = []
    for commit in repo.iter_commits(f"{commit1.hexsha}..{commit2.hexsha}"):
        changes["commit_messages"].append(commit.message.strip())

    def detect_breaking_changes(message):
        if not message or not isinstance(message, str):
            print("Invalid commit message format")
            return False
            
        try:
            # Initialize AI provider with default model
            config_path = '.changelog.yaml'

            provider, model_name = load_provider_model_from_config(config_path)

            logger.info(f"Initializing AI provider {provider} {model_name}...")
            ai_provider = AIProviderManager(provider, model_name)
            if not ai_provider:
                print("Failed to initialize AI provider")
                return False
                
            # Create prompt that explicitly requests Yes/No response
            prompt = {
                "task": "detect_breaking_changes",
                "parameters": {
                    "commit_message": message,
                    "instructions": """Analyze the following commit message and determine if it contains breaking changes.
Definition: A breaking change is any modification to the codebase that requires existing users to alter their code, configuration, or usage patterns to maintain compatibility with the updated version.

Consider the following in your analysis:

API Changes: Were any public APIs added, removed, or modified?
Data Format Changes: Did the format of any data structures, files, or databases change?
Behavioral Changes: Were there any significant changes in the software's behavior that could affect existing integrations or workflows?
Dependency Updates: Did any dependency updates introduce breaking changes?
Configuration Changes: Were there any changes to required configurations or environment variables?

Respond with ONLY "Yes" or "No". Do not include any additional explanation or formatting."""
                }
            }
                        # Get AI response
            response = ai_provider.invoke(prompt)
            if not response or not isinstance(response, dict):
                return False
                
            # Extract response content
            response_content = None
            if "message" in response and hasattr(response["message"], "content"):
                response_content = response["message"].content
            elif "result" in response:
                response_content = response["result"]
            else:
                return False
                
            # Clean and validate response
            response_content = str(response_content).strip().lower()
            if response_content not in ["yes", "no"]:
                logger.error(f"Invalid response content: {response_content}")
                return False
                
            return response_content == "yes"
        except Exception as e:
            logger.error(f"Error detecting breaking changes: {str(e)}")
            # Fallback to simple keyword detection if AI fails
            breaking_keywords = ["break", "breaking", "incompatible", "remove", "deprecate"]
            if any(keyword in message.lower() for keyword in breaking_keywords):
                print("Fallback detection: Found breaking change keyword")
                return True
            return False

    # Validate changes dictionary structure before processing
    if not isinstance(changes, dict):
        logger.error("Error: changes is not a dictionary")
        return changes
        
    required_keys = ["commit_messages", "diff_details", "breaking_changes"]
    for key in required_keys:
        if key not in changes:
            print(f"Warning: Missing key {key} in changes dictionary")
            changes[key] = []
            
    logger.info(f"Processing {len(changes['commit_messages'])} commit messages")
    logger.info(f"Processing {len(changes['diff_details'])} file changes")

    # Process commit messages for breaking changes
    for message in changes["commit_messages"]:
        if not message or not isinstance(message, str):
            continue
            
        if detect_breaking_changes(message):
            changes["breaking_changes"].append(message)
            logger.info("Breaking change detected in commit message")

    # Process diff details for structural changes
    for diff_detail in changes.get("diff_details", []):
        if not isinstance(diff_detail, dict):
            continue
            
        patch = diff_detail.get("patch", "").lower()
        if not patch:
            continue
            
        structural_changes = [
            "class renamed", "method signature changed", "interface modified",
            "function removed", "parameter type changed",
        ]
        if any(change in patch for change in structural_changes):
            changes["breaking_changes"].append(f"Structural change in {diff_detail.get('file', 'unknown file')}")
            logger.info(f"Structural change detected in {diff_detail.get('file', 'unknown file')}")

    logger.info(f"Found {len(changes['breaking_changes'])} breaking changes")


    return changes
