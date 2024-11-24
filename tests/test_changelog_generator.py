import pytest
import git
from unittest.mock import MagicMock, patch
from changelog_utils import get_commit_changes_modified, detect_breaking_changes
from changelog_generator import generate_ai_changelog

def test_breaking_changes_detection():
    """Test advanced breaking changes detection."""
    test_cases = [
        ("Major refactoring of API", True),
        ("Fix minor bug in utility function", False),
        ("Deprecated old method", True),
        ("Breaking change: Removed legacy support", True),
        ("v2.0.0 release", True),
        ("Update documentation", False)
    ]

    for message, expected in test_cases:
        assert detect_breaking_changes(message) == expected

@patch('ollama.chat')
def test_generate_ai_changelog_ollama(mock_ollama_chat):
    """Test AI changelog generation with Ollama."""
    mock_ollama_chat.return_value = {
        'message': {'content': 'Mocked Ollama changelog'}
    }

    changes = {
        'added_files': ['new_feature.py'],
        'modified_files': ['existing_module.py'],
        'deleted_files': [],
        'commit_messages': ['Add new feature'],
        'breaking_changes': []
    }

    changelog = generate_ai_changelog(changes)
    assert changelog is not None
    assert len(changelog) > 0

@patch('openai.OpenAI')
def test_generate_ai_changelog_openai(mock_openai):
    """Test AI changelog generation with OpenAI."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='Mocked OpenAI changelog'))]
    )
    mock_openai.return_value = mock_client

    changes = {
        'added_files': ['new_feature.py'],
        'modified_files': ['existing_module.py'],
        'deleted_files': [],
        'commit_messages': ['Add new feature'],
        'breaking_changes': []
    }

    changelog = generate_ai_changelog(changes, model_provider='openai')
    assert changelog is not None
    assert len(changelog) > 0

def test_changelog_config():
    """Test changelog configuration management."""
    from changelog_config import ChangelogConfig

    # Test default configuration
    config = ChangelogConfig()
    assert config.get('model_provider') == 'ollama'
    assert config.get('model_name') == 'llama2'

    # Test environment variable override
    import os
    os.environ['CHANGELOG_MODEL_PROVIDER'] = 'openai'
    config = ChangelogConfig()
    assert config.get('model_provider') == 'openai'
