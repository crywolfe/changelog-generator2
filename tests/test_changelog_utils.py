import pytest
import git
from unittest.mock import Mock, patch
from changelog_utils import (
    validate_commits,
    get_commit_changes_modified,
    format_breaking_changes,
    get_commit_changes
)

@pytest.fixture
def mock_repo():
    repo = Mock()
    commit1 = Mock()
    commit2 = Mock()
    repo.commit.side_effect = [commit1, commit2]
    return repo, commit1, commit2

def test_validate_commits_success(mock_repo):
    repo, commit1, commit2 = mock_repo
    result = validate_commits(repo, "commit1", "commit2")
    assert result == (commit1, commit2)
    repo.commit.assert_any_call("commit1")
    repo.commit.assert_any_call("commit2")

def test_validate_commits_failure(mock_repo):
    repo, _, _ = mock_repo
    repo.commit.side_effect = git.exc.BadName("Invalid commit")
    with pytest.raises(SystemExit):
        validate_commits(repo, "bad1", "bad2")

def test_get_commit_changes_modified(mock_repo):
    repo, commit1, commit2 = mock_repo
    diff = Mock()
    diff.change_type = "M"
    diff.b_path = "file.txt"
    commit1.diff.return_value = [diff]
    
    result = get_commit_changes_modified(repo, commit1, commit2)
    assert result == ["file.txt"]
    commit1.diff.assert_called_once_with(commit2)

def test_format_breaking_changes_empty():
    result = format_breaking_changes([])
    assert result == "- No breaking changes"

def test_format_breaking_changes_with_changes():
    changes = ["Change 1", "Change 2"]
    result = format_breaking_changes(changes)
    assert result == "- Change 1\n- Change 2"

@patch('changelog_utils.AIProviderManager')
def test_get_commit_changes(mock_ai_provider, mock_repo):
    repo, commit1, commit2 = mock_repo
    diff = Mock()
    diff.change_type = "M"
    diff.b_path = "file.txt"
    diff.diff = b"patch content"
    commit1.diff.return_value = [diff]
    
    # Mock commit messages iteration
    mock_commit = Mock()
    mock_commit.message = "commit message"
    repo.iter_commits.return_value = [mock_commit]
    
    mock_ai_instance = Mock()
    mock_ai_provider.return_value = mock_ai_instance
    # Mock AI response to indicate no breaking changes
    mock_ai_instance.invoke.return_value = "No"
    
    # Mock structural changes detection
    mock_commit.message = "Non-breaking change"
    
    result = get_commit_changes(repo, commit1, commit2)
    
    assert result == {
        "added_files": [],
        "modified_files": ["file.txt"],
        "deleted_files": [],
        "commit_messages": ["Non-breaking change"],
        "diff_details": [{
            "file": "file.txt",
            "patch": "patch content"
        }],
        "breaking_changes": []
    }
    commit1.diff.assert_called_once_with(commit2)
    mock_ai_provider.assert_called_once_with("ollama", "qwen2.5:14b")
