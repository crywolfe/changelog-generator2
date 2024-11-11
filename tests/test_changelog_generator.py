import pytest
import git
from unittest.mock import MagicMock
from changelog_utils import get_commit_changes_modified

def test_get_commit_changes_modified():
    """Test the get_commit_changes_modified function."""
    # Create mock objects
    mock_repo = MagicMock(spec=git.Repo)
    mock_commit1 = MagicMock()
    mock_commit2 = MagicMock()

    # Create mock diff with modified files
    mock_diff = [
        MagicMock(b_path='file1.py', change_type='M'),
        MagicMock(b_path='file2.py', change_type='A'),  # Added file should not be included
        MagicMock(b_path='file3.py', change_type='D')   # Deleted file should not be included
    ]

    # Configure mock commit to return the mock diff
    mock_commit1.diff.return_value = mock_diff

    # Mock repo.commit to return the mock commits when called with string references
    mock_repo.commit.side_effect = [mock_commit1, mock_commit2]

    # Call the function with string commit references
    modified_files = get_commit_changes_modified(mock_repo, 'commit1', 'commit2')

    # Assert that only modified files are returned
    assert modified_files == ['file1.py']

    # Verify that repo.commit was called for both commits
    assert mock_repo.commit.call_count == 2

def test_get_commit_changes_modified_with_commit_objects():
    """Test the function when commit objects are passed directly."""
    # Create mock objects
    mock_repo = MagicMock(spec=git.Repo)
    mock_commit1 = MagicMock()
    mock_commit2 = MagicMock()

    # Create mock diff with modified files
    mock_diff = [
        MagicMock(b_path='file1.py', change_type='M'),
        MagicMock(b_path='file2.py', change_type='A')
    ]

    # Configure mock commit to return the mock diff
    mock_commit1.diff.return_value = mock_diff

    # Call the function with commit objects directly
    modified_files = get_commit_changes_modified(mock_repo, mock_commit1, mock_commit2)

    # Assert that only modified files are returned
    assert modified_files == ['file1.py']
