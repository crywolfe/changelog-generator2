import pytest
import git
import os
import tempfile

from ..changelog_utils import validate_commits, get_commit_changes

@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = git.Repo.init(temp_dir)
        
        # Configure test user
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()
        
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

def test_validate_commits_valid(temp_git_repo):
    """Test validate_commits with valid commits."""
    repo, initial_commit, second_commit, _ = temp_git_repo
    
    # Test valid commits
    validated_commits = validate_commits(repo, initial_commit.hexsha, second_commit.hexsha)
    assert len(validated_commits) == 2
    assert validated_commits[0] == initial_commit
    assert validated_commits[1] == second_commit

def test_validate_commits_invalid(temp_git_repo):
    """Test validate_commits with an invalid commit."""
    repo, initial_commit, _, _ = temp_git_repo
    
    # Test invalid commit
    with pytest.raises(SystemExit):
        validate_commits(repo, initial_commit.hexsha, "invalid_commit")

def test_get_commit_changes(temp_git_repo):
    """Test get_commit_changes with different scenarios."""
    repo, initial_commit, second_commit, third_commit = temp_git_repo
    
    # Test changes between initial and second commit
    changes = get_commit_changes(repo, initial_commit, second_commit)
    assert 'second.txt' in changes['added_files']
    assert len(changes['commit_messages']) == 1
    assert changes['commit_messages'][0] == "Second commit"

def test_get_commit_changes_modified(temp_git_repo):
    """Test get_commit_changes with a modified file."""
    repo, initial_commit, _, third_commit = temp_git_repo
    
    # Test changes between initial and third commit
    changes = get_commit_changes(repo, initial_commit, third_commit)
    assert 'initial.txt' in changes['modified_files']
    assert len(changes['commit_messages']) == 1
    assert changes['commit_messages'][0] == "Modified initial file"
