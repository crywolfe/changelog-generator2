import argparse
import git
import os
import sys

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

def get_commit_changes(repo, commit1, commit2):
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
        'commit_messages': []
    }
    
    for change in diff:
        if change.change_type == 'A':
            changes['added_files'].append(change.b_path)
        elif change.change_type == 'M':
            changes['modified_files'].append(change.b_path)
        elif change.change_type == 'D':
            changes['deleted_files'].append(change.b_path)
    
    # Collect commit messages between the two commits
    for commit in repo.iter_commits(f'{commit1.hexsha}..{commit2.hexsha}'):
        changes['commit_messages'].append(commit.message.strip())
    
    return changes

def main():
    parser = argparse.ArgumentParser(description='Generate a detailed changelog between two Git commits.')
    parser.add_argument('commit1', help='First commit hash or reference')
    parser.add_argument('commit2', help='Second commit hash or reference')
    parser.add_argument('--repo', default='.', help='Path to the Git repository (default: current directory)')
    
    args = parser.parse_args()
    
    try:
        repo = git.Repo(args.repo)
    except git.exc.InvalidGitRepositoryError:
        print(f"Error: {args.repo} is not a valid Git repository.")
        sys.exit(1)
    
    # Validate and get commits
    commit1, commit2 = validate_commits(repo, args.commit1, args.commit2)
    
    # Get changes between commits
    changes = get_commit_changes(repo, commit1, commit2)
    
    # Print out the changes (this will be replaced with Markdown generation later)
    print("Changelog Details:")
    print(f"Comparing commits: {commit1.hexsha[:7]} to {commit2.hexsha[:7]}")
    print("\nAdded Files:")
    print("\n".join(changes['added_files']) or "No files added")
    print("\nModified Files:")
    print("\n".join(changes['modified_files']) or "No files modified")
    print("\nDeleted Files:")
    print("\n".join(changes['deleted_files']) or "No files deleted")
    print("\nCommit Messages:")
    print("\n".join(changes['commit_messages']) or "No commit messages")

if __name__ == '__main__':
    main()
