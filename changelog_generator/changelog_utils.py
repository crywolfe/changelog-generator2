import git
import re
from typing import Dict, List, Union, Optional
import logging


logger = logging.getLogger(__name__)


def format_breaking_changes(breaking_changes: List[str]) -> str:
    """
    Format breaking changes into a readable string.

    Args:
        breaking_changes (List[str]): List of breaking change messages

    Returns:
        str: Formatted breaking changes
    """
    return "- No breaking changes" if not breaking_changes else "\n".join([f"- {change}" for change in breaking_changes])

def parse_commit_message(message: str) -> Dict[str, Optional[str]]:
    """
    Parses a conventional commit message into its components.
    Expected format: type(scope): description
    
    Args:
        message (str): The commit message string.
        
    Returns:
        Dict[str, Optional[str]]: A dictionary with 'type', 'scope', and 'description'.
    """
    # Updated regex to correctly capture type with optional '!' for breaking changes
    match = re.match(r"^(?P<type>\w+)(?P<breaking>!)?(?:\((?P<scope>[^)]*)\))?: (?P<description>.*)", message)
    if match:
        result = match.groupdict()
        result["breaking"] = bool(result.pop("breaking")) # Convert '!' to True, None to False
        # If '!' was part of the type, it's already handled by the regex.
        # No need to rstrip here.
        return result
    return {"type": None, "scope": None, "description": message, "breaking": False}


def get_commit_changes(repo: git.Repo, commit1: Union[str, git.Commit], commit2: Union[str, git.Commit], breaking_change_keywords: List[str]) -> Dict[str, List[str]]:
    """
    Retrieve changes between two commits.

    Args:
        repo (git.Repo): Git repository object
        commit1 (git.Commit): First commit
        commit2 (git.Commit): Second commit
        breaking_change_keywords (List[str]): Keywords to detect breaking changes in commit messages.

    Returns:
        dict: Detailed changes between commits
    """
    try:
        # Validate input commits
        if not commit1 or not commit2:
            raise ValueError("Both commit1 and commit2 must be provided")
            
        commit1 = repo.commit(commit1) if isinstance(commit1, str) else commit1
        commit2 = repo.commit(commit2) if isinstance(commit2, str) else commit2
    except git.exc.GitError as e:
        logger.error(f"Error validating commits: {e}")
        raise ValueError(f"Invalid commit references: {e}")

    # Initialize changes dictionary with required keys
    changes = {
        "added_files": [],
        "modified_files": [],
        "deleted_files": [],
        "commits": [], # Changed from commit_messages to commits for structured data
        "diff_details": [],
        "breaking_changes": [],
        "commit_range": f"{commit1.hexsha}..{commit2.hexsha}"  # Add commit range for tracking
    }
    
    # Validate changes dictionary structure
    required_keys = ["added_files", "modified_files", "deleted_files",
                    "commits", "diff_details", "breaking_changes"]
    for key in required_keys:
        if key not in changes:
            changes[key] = []

    diff = commit1.diff(commit2)

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

    # Collect and parse all commit messages between the two commits
    for commit in repo.iter_commits(f"{commit1.hexsha}..{commit2.hexsha}"):
        parsed_message = parse_commit_message(commit.message.strip())
        changes["commits"].append({
            "hash": commit.hexsha,
            "author": commit.author.name,
            "date": commit.authored_datetime.isoformat(),
            "type": parsed_message["type"],
            "scope": parsed_message["scope"],
            "description": parsed_message["description"],
            "raw_message": commit.message.strip()
        })

    def detect_breaking_changes(message: str) -> bool:
        return any(keyword in message.lower() for keyword in breaking_change_keywords)

    # Validate changes dictionary structure before processing
    if not isinstance(changes, dict):
        logger.error("Error: changes is not a dictionary")
        return changes
        
    required_keys = ["commits", "diff_details", "breaking_changes"]
    for key in required_keys:
        if key not in changes:
            print(f"Warning: Missing key {key} in changes dictionary")
            changes[key] = []
            
    logger.info(f"Processing {len(changes['commits'])} commit messages")
    logger.info(f"Processing {len(changes['diff_details'])} file changes")

    # Process commit messages for breaking changes
    for commit_data in changes["commits"]:
        message = commit_data["raw_message"]
        if not message or not isinstance(message, str):
            continue
            
        if detect_breaking_changes(message):
            changes["breaking_changes"].append(message)
            logger.info("Breaking change detected in commit message")

    # Process diff details for structural changes
    # This part might need more sophisticated logic for true structural breaking changes
    # For now, it relies on keywords in the patch, which might be limited.
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
