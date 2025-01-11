import pytest
import git
from unittest.mock import MagicMock, patch
from changelog_utils import get_commit_changes_modified, format_breaking_changes
from changelog_generator import generate_ai_changelog


def test_breaking_changes_detection():
    """Test advanced breaking changes detection."""
    test_cases = [
        ("Major refactoring of API", "- Major refactoring of API"),  # Assuming this counts as a breaking change
        ("Fix minor bug in utility function", "- No breaking changes"),
        ("Deprecated old method", "- Deprecated old method"),  # Assuming this counts as a breaking change
        ("Breaking change: Removed legacy support", "- Breaking change: Removed legacy support"),
        ("v2.0.0 release", "- v2.0.0 release"),  # Assuming version releases don't automatically imply a breaking change
        ("Update documentation", "- No breaking changes"),
    ]

    for message, expected in test_cases:
        result = format_breaking_changes([message])
        assert result == f"- {expected}" if expected != "- No breaking changes" else format_breaking_changes([]) == expected


@patch("ollama.chat")
def test_generate_ai_changelog_ollama(mock_ollama_chat):
    """Test AI changelog generation with Ollama."""
    mock_ollama_chat.return_value = {"message": {"content": "Mocked Ollama changelog"}}

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



def test_changelog_config():
    """Test changelog configuration management."""
    from changelog_config import ChangelogConfig

    # Test default configuration
    config = ChangelogConfig()
    assert config.get("model_provider") == "ollama"
    assert config.get("model_name") == "qwen2.5:14b"

    # Test environment variable override
    import os

    os.environ["CHANGELOG_MODEL_PROVIDER"] = "openai"
    config = ChangelogConfig()
    assert config.get("model_provider") == "openai"


def test_unsupported_provider():
    """Test AI provider manager with an unsupported provider."""
    from ai_provider_manager import AIProviderManager
    with pytest.raises(ValueError, match=r"Unsupported model provider: test_provider"):
        AIProviderManager(model_provider="test_provider")

class TestAIProviderManager:
    def test_init_with_ollama(self):
        """Test AI provider manager initialization with Ollama."""
        from ai_provider_manager import AIProviderManager
        ai_provider = AIProviderManager(model_provider="ollama")
        assert ai_provider.model_name == "qwen2.5:14b"

    @patch("ollama.chat")
    def test_ollama_invoke(self, mock_ollama_chat):
        """Test AI provider manager invoke method with Ollama."""
        mock_ollama_chat.return_value = {"message": {"content": "Mocked Ollama response"}}
        from ai_provider_manager import AIProviderManager
        ai_provider = AIProviderManager(model_provider="ollama")
        changes = {
            "added_files": ["new_feature.py"],
            "modified_files": ["existing_module.py"],
            "deleted_files": [],
            "commit_messages": ["Add new feature"],
            "breaking_changes": [],
        }
        response = ai_provider.invoke(changes)
        assert response is not None
        assert len(response) > 0
