import pytest
import git
import os
import tempfile
from changelog_utils import (
    validate_commits,
    get_commit_changes,
    get_commit_changes_modified,
    format_breaking_changes,
)

@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = os.path.abspath(temp_dir)
        repo = git.Repo.init(temp_dir)

        with repo.config_writer() as git_config:
            git_config.set_value("user", "name", "Test User")
            git_config.set_value("user", "email", "test@example.com")

        # Initial commit
        initial_file = os.path.join(temp_dir, "initial.txt")
        with open(initial_file, "w") as f:
            f.write("Initial content")
        repo.index.add([initial_file])
        initial_commit = repo.index.commit("Initial commit")

        # Second commit
        second_file = os.path.join(temp_dir, "second.txt")
        with open(second_file, "w") as f:
            f.write("Second content")
        repo.index.add([second_file])
        second_commit = repo.index.commit("Second commit")

        # Third commit with modification
        with open(initial_file, "w") as f:
            f.write("Modified content")
        repo.index.add([initial_file])
        third_commit = repo.index.commit("Modified initial file")

        yield repo, initial_commit, second_commit, third_commit

def test_validate_commits(temp_git_repo):
    """Test validate_commits with valid and invalid commits."""
    repo, initial_commit, second_commit, _ = temp_git_repo

    # Valid commits
    valid_commits = validate_commits(repo, initial_commit.hexsha, second_commit.hexsha)
    assert valid_commits[0].hexsha == initial_commit.hexsha
    assert valid_commits[1].hexsha == second_commit.hexsha

    # Invalid commit
    with pytest.raises(SystemExit):
        validate_commits(repo, "invalid_commit", second_commit.hexsha)

def test_get_commit_changes_modified(temp_git_repo):
    """Test get_commit_changes_modified with modified files."""
    repo, initial_commit, _, third_commit = temp_git_repo

    modified_files = get_commit_changes_modified(repo, initial_commit, third_commit)
    assert "initial.txt" in modified_files
    assert len(modified_files) == 1

def test_get_commit_changes_added_deleted(temp_git_repo):
    """Test get_commit_changes with added and deleted files."""
    repo, initial_commit, second_commit, _ = temp_git_repo

    changes = get_commit_changes(repo, initial_commit, second_commit)
    assert "second.txt" in changes["added_files"]
    assert len(changes["added_files"]) == 1
    assert len(changes["deleted_files"]) == 0

def test_get_commit_changes_breaking(temp_git_repo):
    """Test get_commit_changes with breaking changes."""
    repo, _, second_commit, third_commit = temp_git_repo

    # Simulate breaking change
    with open(os.path.join(repo.path, "second.txt"), "w") as f:
        f.write("Breaking content")
    repo.index.add(["second.txt"])
    breaking_commit = repo.index.commit("Breaking change: API modified")

    changes = get_commit_changes(repo, second_commit, breaking_commit)
    assert len(changes["breaking_changes"]) > 0
    assert "Breaking change: API modified" in changes["breaking_changes"]

def test_format_breaking_changes():
    """Test format_breaking_changes with and without breaking changes."""
    breaking_changes = ["API modified", "Function removed"]
    formatted = format_breaking_changes(breaking_changes)
    assert "- API modified" in formatted
    assert "- Function removed" in formatted

    no_breaking_changes = []
    formatted_empty = format_breaking_changes(no_breaking_changes)
    assert formatted_empty == "- No breaking changes"

def test_get_commit_changes_edge_cases(temp_git_repo):
    """Test edge cases for get_commit_changes."""
    repo, initial_commit, _, third_commit = temp_git_repo

    # Empty commit message
    changes_empty_message = get_commit_changes(repo, initial_commit, third_commit)
    assert changes_empty_message["commit_messages"] == ["Modified initial file"]

    # No changes between same commit
    changes_same_commit = get_commit_changes(repo, initial_commit, initial_commit)
    assert len(changes_same_commit["added_files"]) == 0
    assert len(changes_same_commit["modified_files"]) == 0
    assert len(changes_same_commit["deleted_files"]) == 0

    # Invalid commit hash
    with pytest.raises(SystemExit):
        get_commit_changes(repo, "invalid_commit", third_commit)