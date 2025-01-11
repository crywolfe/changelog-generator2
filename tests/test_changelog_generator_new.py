import pytest
from unittest.mock import patch
from changelog_generator import generate_ai_changelog
import os
import tempfile
import git
from unittest.mock import MagicMock

@patch("ollama.chat")
def test_generate_ai_changelog_ollama(mock_ollama_chat):
    mock_ollama_chat.return_value = {"message": {"content": "Mocked Ollama response"}}
    changes = {
        "added_files": ["new_feature.py"],
        "modified_files": ["existing_module.py"],
        "deleted_files": [],
        "commit_messages": ["Add new feature"],
        "breaking_changes": [],
    }
    changelog = generate_ai_changelog(changes)
    assert changelog is not None
    assert len(changelog) > 0

@patch("git.Repo")
@patch("ollama.chat")
def test_main_function(mock_ollama_chat, mock_git_repo, tmp_path):
    """Test the main function of changelog_generator.py."""
    mock_ollama_chat.return_value = {"message": {"content": "Mocked Ollama response"}}
    
    # Create a dummy git repo
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    mock_repo = MagicMock()
    mock_repo.working_dir = str(repo_path)
    mock_git_repo.return_value = mock_repo

    # Create dummy commits
    mock_commit1 = MagicMock()
    mock_commit1.hexsha = "commit1"
    mock_commit1.message = "Initial commit"
    mock_commit2 = MagicMock()
    mock_commit2.hexsha = "commit2"
    mock_commit2.message = "Second commit"
    mock_repo.commit.side_effect = [mock_commit1, mock_commit2]
    mock_repo.iter_commits.return_value = [mock_commit1, mock_commit2]

    # Create a dummy file
    test_file = repo_path / "test.txt"
    test_file.write_text("test content")

    from changelog_generator import main
    output_file = tmp_path / "test_changelog.md"
    sys_args = ["changelog_generator.py", "commit1", "commit2", "--repo", str(repo_path), "--output", str(output_file)]
    with patch("sys.argv", sys_args):
        main()
    assert output_file.exists()
    assert output_file.read_text() != ""
