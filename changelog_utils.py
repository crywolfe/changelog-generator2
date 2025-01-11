import git
import sys
from typing import Dict, List, Union
from ai_provider_manager import AIProviderManager

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
    commit1 = repo.commit(commit1) if isinstance(commit1, str) else commit1
    commit2 = repo.commit(commit2) if isinstance(commit2, str) else commit2

    diff = commit1.diff(commit2)
    changes = {
        "added_files": [],
        "modified_files": [],
        "deleted_files": [],
        "commit_messages": [],
        "diff_details": [],
        "breaking_changes": [],
    }

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
        try:
            # Initialize AI provider with default model
            ai_provider = AIProviderManager("ollama", "qwen2.5:14b")
            
            # Create prompt for breaking change detection
            prompt = f"""Analyze the following commit message and determine if it contains breaking changes.
    A breaking change is any modification that requires users to modify their code or configuration to maintain compatibility.

    Commit message: {message}

    Does this commit contain breaking changes? Respond with only 'Yes' or 'No'."""
            
            # Get AI response
            response = ai_provider.invoke(prompt)
            
            # Return True only if AI response is "Yes"
            return response.strip().lower() == "yes"
        except Exception as e:
            print(f"Error detecting breaking changes: {e}")
            return False

    for message in changes["commit_messages"]:
        if detect_breaking_changes(message):
            changes["breaking_changes"].append(message)

    for diff_detail in changes.get("diff_details", []):
        patch = diff_detail.get("patch", "").lower()
        structural_changes = [
            "class renamed", "method signature changed", "interface modified",
            "function removed", "parameter type changed",
        ]
        if any(change in patch for change in structural_changes):
            changes["breaking_changes"].append(f"Structural change in {diff_detail.get('file', 'unknown file')}")


    return changes
