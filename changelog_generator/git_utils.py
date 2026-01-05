import git
from typing import Optional
from changelog_generator.config_models import AppConfig

def get_git_commits(repo: git.Repo, config: AppConfig, commit1_hash: Optional[str] = None, commit2_hash: Optional[str] = None) -> tuple:
    """
    Get commits based on configuration or provided commit hashes
    
    Args:
        repo (git.Repo): Git repository object
        config (AppConfig): Configuration object
        commit1_hash (Optional[str]): First commit hash
        commit2_hash (Optional[str]): Second commit hash
    
    Returns:
        tuple: First and last commit
    """
    if commit1_hash and commit2_hash:
        # If specific commits are provided, use them
        return repo.commit(commit1_hash), repo.commit(commit2_hash)

    branch = config.git.branch
    commit_range = config.git.commit_range

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