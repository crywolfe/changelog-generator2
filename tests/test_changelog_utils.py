import pytest
import git
import os
import tempfile
import sys

from changelog_utils import validate_commits, get_commit_changes, get_commit_changes_modified

@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Ensure the directory is an absolute path
        temp_dir = os.path.abspath(temp_dir)
        
        # Initialize the repository
        repo = git.Repo.init(temp_dir)
        
        # Configure test user
        with repo.config_writer() as git_config:
            git_config.set_value("user", "name", "Test User")
            git_config.set_value("user", "email", "test@example.com")
        
        # Create initial commit
        initial_file = os.path.join(temp_dir, 'initial.txt')
        with open(initial_file, 'w') as f:
            f.write("Initial content")
        repo.index.add([initial_file])
        initial_commit = repo.index.commit("Initial commit")
        
        # Create a second commit
        second_file = os.path.join(temp_dir, 'second.txt')
        with open(second_file, 'w') as f:
            f.write("Second content")
        repo.index.add([second_file])
        second_commit = repo.index.commit("Second commit")
        
        # Create a third commit with modification
        with open(initial_file, 'w') as f:
            f.write("Modified content")
        repo.index.add([initial_file])
        third_commit = repo.index.commit("Modified initial file")
        
        yield repo, initial_commit, second_commit, third_commit

def test_get_commit_changes_modified(temp_git_repo, capfd):
    """Test get_commit_changes with a modified file."""
    repo, initial_commit, _, third_commit = temp_git_repo
    
    print(f"Initial commit: {initial_commit.hexsha}")
    print(f"Third commit: {third_commit.hexsha}")
    
    # Test changes between initial and third commit
    try:
        changes = get_commit_changes(repo, initial_commit, third_commit)
        
        # Detailed debugging
        print("Changes:", changes)
        print("Modified files:", changes.get('modified_files', []))
        print("Commit messages:", changes.get('commit_messages', []))
        
        # Assertions
        assert len(changes['modified_files']) > 0, "No modified files found"
        assert 'initial.txt' in changes['modified_files'], f"Expected 'initial.txt' in modified files, got {changes['modified_files']}"
        assert len(changes['commit_messages']) == 1, f"Expected 1 commit message, got {len(changes['commit_messages'])}"
        assert changes['commit_messages'][0] == "Modified initial file", f"Unexpected commit message: {changes['commit_messages'][0]}"
    
    except Exception as e:
        print(f"Error in test: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise

    # Capture and print any additional output
    out, err = capfd.readouterr()
    print("Captured stdout:", out)
    print("Captured stderr:", err)
