import pytest
import unittest
from unittest.mock import patch, MagicMock, mock_open
from changelog_generator import generate_ai_changelog, main, load_config
import argparse
from datetime import datetime
import logging
import git
import yaml
import os

@pytest.fixture
def mock_ai_provider():
    with patch('changelog_generator.ai_provider_manager.AIProviderManager') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.invoke.return_value = "Mocked changelog content"
        yield mock_instance

@pytest.fixture
def mock_changelog_config():
    with patch('changelog_generator.changelog_config.ChangelogConfig') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.get.side_effect = lambda key, default=None: {
            "model_provider": "ollama",
            "model_name": "qwen2.5:14b"
        }.get(key, default)
        yield mock_instance

@pytest.fixture
def mock_git_repo():
    with patch('git.Repo') as mock:
        # Create a mock repo that can be configured differently for each test
        mock_instance = MagicMock()
        
        # Create mock commits
        mock_commit1 = MagicMock(hexsha='1234567')
        mock_commit2 = MagicMock(hexsha='7654321')
        
        # Configure mock repository methods
        mock_instance.commit.side_effect = [mock_commit1, mock_commit2]
        
        # Configure iter_commits to return a list with at least one commit
        mock_instance.iter_commits.return_value = [mock_commit1]
        
        # Configure branches
        mock_branch = MagicMock()
        mock_branch.commit = mock_commit2
        mock_instance.branches = {'main': mock_branch}
        
        mock.return_value = mock_instance
        yield mock

@pytest.fixture
def mock_ollama():
    with patch('changelog_generator.ai_provider_manager.ollama') as mock:
        # Create mock model objects with a 'name' attribute
        mock_models = {
            'models': [
                {'name': 'model1'},
                {'name': 'model2'}
            ]
        }
        mock.list.return_value = mock_models
        yield mock

@pytest.fixture
def mock_open_bytes():
    """
    A fixture to mock open() to return bytes instead of str
    """
    with patch('builtins.open', unittest.mock.mock_open(read_data=b'test data')) as mock_file:
        yield mock_file

@pytest.fixture
def mock_validate_commits():
    with patch('changelog_generator.changelog_utils.validate_commits') as mock:
        # Create mock commits
        mock_commit1 = MagicMock(hexsha='1234567', message='Commit 1 message')
        mock_commit2 = MagicMock(hexsha='7654321', message='Commit 2 message')
        mock.return_value = (mock_commit1, mock_commit2)
        yield mock

@pytest.fixture
def mock_get_commit_changes():
    with patch('changelog_generator.changelog_utils.get_commit_changes') as mock:
        # Create mock changes
        mock.return_value = {
            'added_files': ['file1'],
            'modified_files': ['file2'],
            'deleted_files': ['file3'],
            'breaking_changes': ['change1']
        }
        yield mock

def test_load_config_default():
    with patch('os.path.exists', return_value=False):
        config = load_config()
        assert config['git']['repository_path'] == '.'
        assert config['ai']['enabled'] is False
        assert config['logging']['level'] == 'INFO'

def test_load_config_custom_file():
    test_config = {
        'git': {'repository_path': '/custom/path'},
        'ai': {'enabled': True},
        'logging': {'level': 'DEBUG'}
    }
    
    mock_yaml = yaml.dump(test_config)
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=mock_yaml)):
        config = load_config('/custom/path/config.yaml')
        assert config['git']['repository_path'] == '/custom/path'
        assert config['ai']['enabled'] is True
        assert config['logging']['level'] == 'DEBUG'

def test_generate_ai_changelog_success(mock_ai_provider, mock_changelog_config):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"],
        "commit_messages": ["commit message"],
        "diff_details": [{"file": "file2", "patch": "patch content"}]
    }
    
    # Mock the AI response to return exactly what we expect
    mock_ai_provider.invoke.return_value = "Mocked changelog content"
    
    result = generate_ai_changelog(changes, mock_ai_provider)
    assert result == "Mocked changelog content"
    mock_ai_provider.invoke.assert_called_once_with(changes)

def test_generate_ai_changelog_retry(mock_ai_provider):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"], 
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"]
    }
        
    # First attempt fails, second succeeds
    mock_ai_provider.invoke.side_effect = [Exception("Error 1"), "Mocked changelog content"]
        
    result = generate_ai_changelog(changes, ai_provider=mock_ai_provider)
    assert result == "Mocked changelog content"
    assert mock_ai_provider.invoke.call_count == 2

def test_generate_ai_changelog_failure_after_retries(mock_ai_provider):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"]
    }
    
    mock_ai_provider.invoke.side_effect = Exception("Persistent error")
    
    with pytest.raises(Exception):
        generate_ai_changelog(changes, ai_provider=mock_ai_provider)
    assert mock_ai_provider.invoke.call_count == 3  # Should match retry count

def test_generate_ai_changelog_failure(mock_ai_provider):
    mock_ai_provider.invoke.side_effect = ValueError("Mock error")
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"]
    }
    
    with pytest.raises(Exception):
        generate_ai_changelog(changes, ai_provider=mock_ai_provider)


def test_main_with_config_file(mock_git_repo, mock_ai_provider, mock_validate_commits, mock_get_commit_changes, caplog):
    test_args = ["--config", ".changelog.yaml", "commit1", "commit2"]
    
    test_config = {
        'git': {'repository_path': '/custom/path'},
        'ai': {'enabled': True},
        'logging': {'level': 'DEBUG'}
    }
    
    mock_yaml = yaml.dump(test_config)
    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(
        commit1="commit1",
        commit2="commit2",
        repo=".",
        output=None,
        model_provider="ollama",
        model_name="qwen2.5:14b",
        list_models=False,
        verbose=False,
        config=".changelog.yaml",
        branch=None  # Added missing branch attribute
    )), \
    patch('builtins.open', mock_open(read_data=mock_yaml.encode())), \
    patch('os.path.exists', return_value=True):
        mock_ai_provider.invoke.return_value = "Mocked changelog content"
        with patch('sys.argv', ['changelog_generator.py'] + test_args):
            with caplog.at_level(logging.DEBUG):
                main()
                assert "Loading configuration from" in caplog.text
                assert "DEBUG" in caplog.text

def test_main_with_commit_range(mock_git_repo, mock_ai_provider, mock_validate_commits, mock_get_commit_changes, caplog, mock_open_bytes):
    test_args = ["--commit-range", "576ebd6..698b4d07"]

    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(
        commit1=None,
        commit2=None,
        repo=".",
        output=None,
        model_provider="ollama",
        model_name="qwen2.5:14b",
        list_models=False,
        verbose=False,
        commit_range="576ebd6..698b4d07",
        config=None,  # Added missing config attribute
        branch=None   # Added missing branch attribute
    )), \
    patch('os.path.exists', return_value=True):
        mock_ai_provider.invoke.return_value = "Mocked changelog content"
        with patch('sys.argv', ['changelog_generator.py'] + test_args):
            with caplog.at_level(logging.INFO):
                main()
                assert "Generating changelog from" in caplog.text

def test_main_invalid_commit_range(mock_git_repo, caplog):
    test_args = ["commit1", "commit2"]
    
    # Configure the mock to raise a ValueError for an invalid commit range
    mock_git_repo.return_value.iter_commits.side_effect = ValueError("Invalid commit range")

    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(
        commit1="commit1",
        commit2="commit2",
        repo=".",
        output=f"CHANGELOG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        model_provider="ollama",
        model_name="qwen2.5:14b",
        list_models=False,
        verbose=False,
        config=None,
        branch=None  # Added missing branch attribute
    )):
        with patch('sys.argv', ['changelog_generator.py'] + test_args):
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
                assert "Error: Invalid commit range" in caplog.text

def test_main_invalid_repo(mock_git_repo, caplog):
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
        verbose=False,
        config=None,  # Added missing config attribute
        branch=None   # Added missing branch attribute
    )):
        with patch('sys.argv', ['changelog_generator.py'] + test_args):
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
                assert "Error: Invalid git repository" in caplog.text

