import git
import sys
from typing import Dict, List, Union

def validate_commits(repo, commit1, commit2):
    """
    Validate that both commits exist in the repository.
    
    Args:
        repo (git.Repo): Git repository object
        commit1 (str): First commit hash or reference
        commit2 (str): Second commit hash or reference
    
    Returns:
        tuple: Validated commit objects
    """
    try:
        c1 = repo.commit(commit1)
        c2 = repo.commit(commit2)
        return c1, c2
    except git.exc.BadName:
        print(f"Error: One or both commits ({commit1}, {commit2}) do not exist in the repository.")
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
    # Convert commit references to commit objects if they are strings
    if isinstance(commit1, str):
        commit1 = repo.commit(commit1)
    if isinstance(commit2, str):
        commit2 = repo.commit(commit2)
    
    # Get the diff between commits
    diff = commit1.diff(commit2)
    
    # Collect modified files
    modified_files = [
        change.b_path for change in diff if change.change_type == 'M'
    ]
    
    return modified_files

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
    diff = commit1.diff(commit2)
    
    changes = {
        'added_files': [],
        'modified_files': [],
        'deleted_files': [],
        'commit_messages': [],
        'diff_details': []
    }
    
    for change in diff:
        if change.change_type == 'A':
            changes['added_files'].append(change.b_path)
        elif change.change_type == 'M':
            changes['modified_files'].append(change.b_path)
            # Get more detailed diff information
            try:
                patch = change.diff if isinstance(change.diff, str) else change.diff.decode('utf-8')
                changes['diff_details'].append({
                    'file': change.b_path,
                    'patch': patch
                })
            except Exception as e:
                print(f"Could not process diff for {change.b_path}: {e}")
        elif change.change_type == 'D':
            changes['deleted_files'].append(change.b_path)
    
    # Collect commit messages between the two commits
    for commit in repo.iter_commits(f'{commit1.hexsha}..{commit2.hexsha}'):
        changes['commit_messages'].append(commit.message.strip())
    
    return changes
