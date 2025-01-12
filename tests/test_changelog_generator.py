import pytest
from unittest.mock import patch, MagicMock
from changelog_generator import generate_ai_changelog, _list_ollama_models, main
import argparse
from datetime import datetime
import logging
import git  # Import git to use its exceptions

@pytest.fixture
def mock_ai_provider():
    with patch('changelog_generator.AIProviderManager') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.invoke.return_value = "Mocked changelog content"
        yield mock_instance

@pytest.fixture
def mock_git_repo():
    with patch('changelog_generator.git.Repo') as mock:
        # Create a mock repo that can be configured differently for each test
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock

@pytest.fixture
def mock_ollama():
    with patch('changelog_generator.ollama') as mock:
        # Create mock model objects with a 'name' attribute
        mock_models = [
            type('MockModel', (), {'name': 'model1'})(),
            type('MockModel', (), {'name': 'model2'})()
        ]
        mock.models.list.return_value = type('MockResponse', (), {'models': mock_models})()
        yield mock

@pytest.fixture
def mock_validate_commits():
    with patch('changelog_generator.validate_commits') as mock:
        # Create mock commits
        mock_commit1 = MagicMock(hexsha='1234567', message='Commit 1 message')
        mock_commit2 = MagicMock(hexsha='7654321', message='Commit 2 message')
        mock.return_value = (mock_commit1, mock_commit2)
        yield mock

@pytest.fixture
def mock_get_commit_changes():
    with patch('changelog_generator.get_commit_changes') as mock:
        # Create mock changes
        mock.return_value = {
            'added_files': ['file1'],
            'modified_files': ['file2'],
            'deleted_files': ['file3'],
            'breaking_changes': ['change1']
        }
        yield mock

def test_generate_ai_changelog_success(mock_ai_provider):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"]
    }
    
    result = generate_ai_changelog(changes)
    assert result == "Mocked changelog content"
    mock_ai_provider.invoke.assert_called_once_with(changes)
    
    from changelog_config import ChangelogConfig
    config = ChangelogConfig()
    mock_ai_provider.assert_called_once_with(changes)

def test_generate_ai_changelog_failure(mock_ai_provider):
    mock_ai_provider.invoke.side_effect = ValueError("Mock error")
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"]
    }
    
    with pytest.raises(Exception):
        generate_ai_changelog(changes)

def test_list_ollama_models_success(mock_ollama):
    models = _list_ollama_models()
    assert models == ["model1", "model2"]
    mock_ollama.models.list.assert_called_once()

def test_list_ollama_models_failure(mock_ollama):
    mock_ollama.models.list.side_effect = Exception("Mock error")
    with pytest.raises(Exception):
        _list_ollama_models()

def test_main_success(mock_git_repo, mock_ai_provider, mock_validate_commits, mock_get_commit_changes, caplog):
    test_args = ["commit1", "commit2"]
    
    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(
        commit1="commit1",
        commit2="commit2",
        repo=".",
        output=f"CHANGELOG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        model_provider="ollama",
        model_name="qwen2.5:14b",
        list_models=False,
        verbose=False
    )):
        with patch('sys.argv', ['changelog_generator.py'] + test_args):
            with caplog.at_level(logging.INFO):
                main()
                assert "Changelog generated" in caplog.text

def test_main_invalid_repo(mock_git_repo):
    test_args = ["commit1", "commit2"]
    
    # Configure the mock to raise InvalidGitRepositoryError for this specific test
    mock_git_repo.side_effect = git.exc.InvalidGitRepositoryError("Invalid repository")
    
    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(
        commit1="commit1",
        commit2="commit2",
        repo="invalid",
        output=f"CHANGELOG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        model_provider="ollama",
        model_name="qwen2.5:14b",
        list_models=False,
        verbose=False
    )):
        with patch('sys.argv', ['changelog_generator.py'] + test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

def test_main_list_models(mock_ollama, caplog):
    test_args = ["--list-models"]
    
    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(
        commit1=None,
        commit2=None,
        repo=".",
        output=None,
        model_provider="ollama",
        model_name=None,
        list_models=True,
        verbose=False
    )):
        with patch('sys.argv', ['changelog_generator.py'] + test_args):
            with caplog.at_level(logging.INFO):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
                assert "Available Ollama Models" in caplog.text
