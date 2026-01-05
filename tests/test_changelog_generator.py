import pytest
from unittest.mock import patch, MagicMock, mock_open
import yaml
from typer.testing import CliRunner

from changelog_generator.generator import generate_ai_changelog
from generator import load_config

runner = CliRunner()


@pytest.fixture
def mock_ai_provider():
    with patch("changelog_generator.generator.AIProviderManager") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.invoke.return_value = "Mocked changelog content"
        yield mock_instance


@pytest.fixture
def mock_ai_settings():
    from changelog_generator.config_models import AISettings

    yield AISettings(
        enabled=True,
        provider="ollama",
        model_name="qwen3:latest",
        ollama_model="qwen3:latest",
    )


def test_load_config_default():
    with patch("os.path.exists", return_value=False):
        config = load_config()
        assert config["git"]["repository_path"] == "."
        assert config["ai"]["enabled"] is False
        assert config["logging"]["level"] == "INFO"
        assert config["changelog"]["output_file"] == "CHANGELOG.md"


def test_load_config_custom_file():
    test_config = {
        "git": {"repository_path": "/custom/path"},
        "ai": {"enabled": True},
        "logging": {"level": "DEBUG"},
        "changelog": {"template": "custom.j2"},
    }

    mock_yaml = yaml.dump(test_config)
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=mock_yaml)),
    ):
        config = load_config("/custom/path/config.yaml")
        assert config["git"]["repository_path"] == "/custom/path"
        assert config["ai"]["enabled"] is True
        assert config["logging"]["level"] == "DEBUG"
        assert config["changelog"]["template"] == "custom.j2"


def test_generate_ai_changelog_success(mock_ai_provider, mock_ai_settings):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"],
        "commits": [{"raw_message": "commit message"}],
        "diff_details": [{"file": "file2", "patch": "patch content"}],
    }

    mock_ai_provider.invoke.return_value = "Mocked changelog content"

    result = generate_ai_changelog(changes, mock_ai_settings)
    assert result == "Mocked changelog content"
    mock_ai_provider.invoke.assert_called_once_with(changes)


def test_generate_ai_changelog_retry(mock_ai_provider, mock_ai_settings):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"],
        "commits": [{"raw_message": "commit message"}],
    }

    mock_ai_provider.invoke.side_effect = [
        Exception("Error 1"),
        "Mocked changelog content",
    ]

    result = generate_ai_changelog(changes, mock_ai_settings)
    assert result == "Mocked changelog content"
    assert mock_ai_provider.invoke.call_count == 2


def test_generate_ai_changelog_failure_after_retries(
    mock_ai_provider, mock_ai_settings
):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"],
        "commits": [{"raw_message": "commit message"}],
    }

    mock_ai_provider.invoke.side_effect = Exception("Persistent error")

    with pytest.raises(Exception):
        generate_ai_changelog(changes, mock_ai_settings)
    assert mock_ai_provider.invoke.call_count == 3


def test_generate_ai_changelog_failure(mock_ai_provider, mock_ai_settings):
    mock_ai_provider.invoke.side_effect = ValueError("Mock error")
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"],
        "commits": [{"raw_message": "commit message"}],
    }

    with pytest.raises(Exception):
        generate_ai_changelog(changes, mock_ai_settings)
