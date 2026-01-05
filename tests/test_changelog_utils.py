import pytest
import git
from unittest.mock import Mock, patch
from datetime import datetime # Import datetime
from changelog_generator.changelog_utils import (
    validate_commits,
    get_commit_changes_modified,
    format_breaking_changes,
    get_commit_changes,
    parse_commit_message # Import the new function
)

@pytest.fixture
def mock_repo():
    repo = Mock()
    commit1 = Mock(hexsha="commit1_hash")
    commit2 = Mock(hexsha="commit2_hash")
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

# New test for parse_commit_message
@pytest.mark.parametrize(
    "message, expected_type, expected_scope, expected_description",
    [
        ("feat(scope): add new feature", "feat", "scope", "add new feature"),
        ("fix: bug fix", "fix", None, "bug fix"),
        ("chore(deps): update dependencies", "chore", "deps", "update dependencies"),
        ("docs: update readme", "docs", None, "update readme"),
        ("refactor!: breaking change", "refactor", None, "breaking change"), # Example with ! for breaking
        ("feat!: new feature with breaking change", "feat", None, "new feature with breaking change"),
        ("initial commit", None, None, "initial commit"), # Non-conventional
    ]
)
def test_parse_commit_message(message, expected_type, expected_scope, expected_description):
    result = parse_commit_message(message)
    assert result["type"] == expected_type
    assert result["scope"] == expected_scope
    assert result["description"] == expected_description
    
    # Additional check for breaking changes
    if '!' in message:
        assert result.get("breaking") is True
    else:
        assert result.get("breaking") is False

def test_get_commit_changes_breaking_change_from_diff(mock_repo):
    repo, commit1, commit2 = mock_repo

    # Mock diff with a structural change keyword
    diff_mock = Mock()
    diff_mock.change_type = "M"
    diff_mock.b_path = "src/api.py"
    diff_mock.diff = b"--- a/src/api.py\n+++ b/src/api.py\n@@ -1,5 +1,4 @@\n-class OldAPI:\n+class NewAPI:\n# This is a class renamed breaking change\n" # Simulate class renamed with keyword
    commit1.diff.return_value = [diff_mock]

    # Mock commit objects (no breaking change in message)
    mock_commit = Mock()
    mock_commit.message = "feat: update API"
    mock_commit.hexsha = "abcdef12345"
    mock_commit.author.name = "Test Author"
    mock_commit.authored_datetime = datetime.now()
    repo.iter_commits.return_value = [mock_commit]

    result = get_commit_changes(repo, commit1, commit2)

    assert "breaking_changes" in result
    assert len(result["breaking_changes"]) == 1
    assert "Structural change in src/api.py" in result["breaking_changes"]
    assert result["modified_files"] == ["src/api.py"]
    assert result["diff_details"][0]["file"] == "src/api.py"
    assert "class renamed" in result["diff_details"][0]["patch"].lower()

def test_get_commit_changes_with_parsed_commits(mock_repo):
    repo, commit1, commit2 = mock_repo
    
    # Mock diff
    diff_mock = Mock()
    diff_mock.change_type = "M"
    diff_mock.b_path = "file.txt"
    diff_mock.diff = b"patch content"
    commit1.diff.return_value = [diff_mock]
    
    # Mock commit objects with conventional messages
    mock_commit_feat = Mock()
    mock_commit_feat.message = "feat(api): add new endpoint\n\nBody of commit"
    mock_commit_feat.hexsha = "abcdef12345"
    mock_commit_feat.author.name = "Test Author"
    mock_commit_feat.authored_datetime = datetime.now()

    mock_commit_fix = Mock()
    mock_commit_fix.message = "fix: resolve bug #123"
    mock_commit_fix.hexsha = "1234567890a"
    mock_commit_fix.author.name = "Another Author"
    mock_commit_fix.authored_datetime = datetime.now()

    repo.iter_commits.return_value = [mock_commit_fix, mock_commit_feat] # Simulate order of commits

    result = get_commit_changes(repo, commit1, commit2)
    
    assert "commits" in result
    assert len(result["commits"]) == 2

    # Assert parsed data for feat commit
    feat_commit_data = next(c for c in result["commits"] if c["type"] == "feat")
    assert feat_commit_data["type"] == "feat"
    assert feat_commit_data["scope"] == "api"
    assert feat_commit_data["description"] == "add new endpoint"
    assert feat_commit_data["raw_message"] == "feat(api): add new endpoint\n\nBody of commit"

    # Assert parsed data for fix commit
    fix_commit_data = next(c for c in result["commits"] if c["type"] == "fix")
    assert fix_commit_data["type"] == "fix"
    assert fix_commit_data["scope"] is None
    assert fix_commit_data["description"] == "resolve bug #123"
    assert fix_commit_data["raw_message"] == "fix: resolve bug #123"

    assert result["modified_files"] == ["file.txt"]
    assert result["diff_details"][0]["file"] == "file.txt"
    assert result["diff_details"][0]["patch"] == "patch content"
    assert result["breaking_changes"] == [] # Assuming no breaking changes in these mocks
    assert result["commit_range"] == f"{commit1.hexsha}..{commit2.hexsha}"
