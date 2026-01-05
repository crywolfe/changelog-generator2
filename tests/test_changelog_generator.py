import pytest
import unittest
from unittest.mock import patch, MagicMock, mock_open
import git
import yaml
from typer.testing import CliRunner

# Import the Typer app and relevant functions
from changelog_generator.main import app as cli_app
from changelog_generator.generator import generate_ai_changelog, load_config

runner = CliRunner()


@pytest.fixture
def mock_ai_provider():
    with patch("changelog_generator.ai_provider_manager.AIProviderManager") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.invoke.return_value = "Mocked changelog content"
        yield mock_instance


@pytest.fixture
def mock_changelog_config():
    with patch("changelog_generator.changelog_config.ChangelogConfig") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.get.side_effect = lambda key, default=None: {
            "model_provider": "ollama",
            "model_name": "qwen3:latest",
            "output_file": "CHANGELOG_DEFAULT.md",
            "changelog": {"template": "markdown_template.j2"},
        }.get(key, default)
        yield mock_instance


@pytest.fixture
def mock_git_repo():
    with patch("git.Repo") as mock:
        mock_instance = MagicMock()
        mock_commit1 = MagicMock(hexsha="1234567", message="feat: initial commit")
        mock_commit2 = MagicMock(hexsha="7654321", message="fix: resolve bug")

        mock_instance.commit.side_effect = [mock_commit1, mock_commit2]
        mock_instance.iter_commits.return_value = [
            mock_commit2,
            mock_commit1,
        ]  # Simulate commit order

        mock_branch = MagicMock()
        mock_branch.commit = mock_commit2
        mock_instance.branches = {"main": mock_branch}

        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_ollama():
    with patch("ollama.list") as mock:  # Patch ollama.list directly
        mock_models = {"models": [{"name": "model1"}, {"name": "model2"}]}
        mock.return_value = mock_models
        yield mock


@pytest.fixture
def mock_open_bytes():
    with patch(
        "builtins.open", unittest.mock.mock_open(read_data=b"test data")
    ) as mock_file:
        yield mock_file


@pytest.fixture
def mock_get_commit_changes():
    with patch("changelog_generator.changelog_utils.get_commit_changes") as mock:
        mock.return_value = {
            "added_files": ["file1.txt"],
            "modified_files": ["file2.py"],
            "deleted_files": ["file3.js"],
            "breaking_changes": ["feat!: breaking change"],
            "commits": [
                {
                    "hash": "7654321",
                    "author": "Test Author",
                    "date": "2023-01-02T10:00:00",
                    "type": "fix",
                    "scope": None,
                    "description": "resolve bug",
                    "raw_message": "fix: resolve bug",
                },
                {
                    "hash": "1234567",
                    "author": "Test Author",
                    "date": "2023-01-01T09:00:00",
                    "type": "feat",
                    "scope": None,
                    "description": "initial commit",
                    "raw_message": "feat: initial commit",
                },
            ],
            "diff_details": [],
        }
        yield mock


def test_load_config_default():
    with patch("os.path.exists", return_value=False):
        config = load_config()
        assert config["git"]["repository_path"] == "."
        assert config["ai"]["enabled"] is False
        assert config["logging"]["level"] == "INFO"
        assert config["changelog"]["template"] == "markdown_template.j2"


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


def test_generate_ai_changelog_success(mock_ai_provider, mock_changelog_config):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"],
        "commits": [{"raw_message": "commit message"}],
        "diff_details": [{"file": "file2", "patch": "patch content"}],
    }

    mock_ai_provider.invoke.return_value = "Mocked changelog content"

    result = generate_ai_changelog(changes, mock_ai_provider)
    assert result == "Mocked changelog content"
    mock_ai_provider.invoke.assert_called_once_with(changes)


def test_generate_ai_changelog_retry(mock_ai_provider):
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

    result = generate_ai_changelog(changes, ai_provider=mock_ai_provider)
    assert result == "Mocked changelog content"
    assert mock_ai_provider.invoke.call_count == 2


def test_generate_ai_changelog_failure_after_retries(mock_ai_provider):
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"],
        "commits": [{"raw_message": "commit message"}],
    }

    mock_ai_provider.invoke.side_effect = Exception("Persistent error")

    with pytest.raises(Exception):
        generate_ai_changelog(changes, ai_provider=mock_ai_provider)
    assert mock_ai_provider.invoke.call_count == 3


def test_generate_ai_changelog_failure(mock_ai_provider):
    mock_ai_provider.invoke.side_effect = ValueError("Mock error")
    changes = {
        "added_files": ["file1"],
        "modified_files": ["file2"],
        "deleted_files": ["file3"],
        "breaking_changes": ["change1"],
        "commits": [{"raw_message": "commit message"}],
    }

    with pytest.raises(Exception):
        generate_ai_changelog(changes, ai_provider=mock_ai_provider)


def test_cli_generate_success(
    mock_git_repo, mock_ai_provider, mock_get_commit_changes, caplog
):
    with (
        patch(
            "changelog_generator.main.ChangelogConfig.load_config"
        ) as mock_load_config,
        patch(
            "changelog_generator.main.generate_ai_changelog",
            return_value="AI Generated Changelog",
        ),
        patch("builtins.open", new_callable=mock_open) as mock_file_open,
        patch(
            "changelog_generator.main.generate_changelog_content",
            return_value="Generated Changelog Content",
        ) as mock_generate_changelog_content,
        patch("os.path.exists", return_value=True),  # Mock config file exists
    ):
        # Create a mock config object
        mock_config = MagicMock()
        mock_config.ai.enabled = True
        mock_config.ai.provider = "ollama"
        mock_config.ai.model_name = "qwen3:latest"
        mock_config.changelog.output_file = "CHANGELOG.md"
        mock_config.git.repository_path = "."
        mock_config.git.branch = "main"
        mock_config.logging.level = "INFO"
        mock_config.breaking_change_detection.keywords = ["breaking"]
        
        mock_load_config.return_value = mock_config
        
        result = runner.invoke(cli_app, [])  # No subcommand needed now
        assert result.exit_code == 0
        assert "Changelog generated and saved to" in result.stdout
        mock_generate_changelog_content.assert_called_once()
        mock_file_open.assert_called_once()


def test_cli_generate_with_commit_range(
    mock_git_repo, mock_ai_provider, mock_get_commit_changes, caplog
):  # Removed mock_generate_changelog_from_template
    with (
        patch(
            "changelog_generator.main.load_config",
            return_value={
                "git": {"repository_path": ".", "branch": "main", "commit_range": None},
                "changelog": {
                    "output_file": "CHANGELOG.md",
                    "template": "markdown_template.j2",
                },
                "ai": {
                    "enabled": True,
                    "provider": "ollama",
                    "model_name": "qwen3:latest",
                },
                "logging": {"level": "INFO"},
            },
        ),
        patch(
            "changelog_generator.main.generate_ai_changelog",
            return_value="AI Generated Changelog",
        ),
        patch("changelog_generator.main.ChangelogConfig") as MockMainChangelogConfig,
        patch("builtins.open", new_callable=mock_open) as mock_file_open,
        patch(
            "changelog_generator.main.generate_changelog_from_template",
            return_value="Generated Changelog Content",
        ) as mock_generate_changelog_from_template,
    ):  # Patch directly in main
        MockMainChangelogConfig.return_value.get.side_effect = (
            lambda key, default=None: {
                "model_provider": "ollama",
                "model_name": "qwen3:latest",
                "output_file": "CHANGELOG.md",  # Ensure output_file is returned
            }.get(key, default)
        )
        result = runner.invoke(
            cli_app, ["generate", "--commit-range", "abcde12..fghij34"]
        )
        assert result.exit_code == 0
        assert "Changelog generated and saved to" in result.stdout
        mock_generate_changelog_from_template.assert_called_once()
        # Verify get_git_commits was called with the range
        mock_git_repo.return_value.commit.assert_any_call("abcde12")
        mock_git_repo.return_value.commit.assert_any_call("fghij34")
        mock_file_open.assert_called_once()  # Verify file was "opened" for writing


def test_cli_generate_invalid_repo(mock_git_repo, caplog):
    mock_git_repo.side_effect = git.exc.InvalidGitRepositoryError("Invalid repository")
    with patch(
        "changelog_generator.main.load_config",
        return_value={
            "git": {
                "repository_path": "invalid",
                "branch": "main",
                "commit_range": None,
            },
            "changelog": {
                "output_file": "CHANGELOG.md",
                "template": "markdown_template.j2",
            },
            "ai": {"enabled": True, "provider": "ollama", "model_name": "qwen3:latest"},
            "logging": {"level": "INFO"},
        },
    ):
        result = runner.invoke(cli_app, ["generate", "--repo", "invalid"])
        assert result.exit_code == 1
        # The logger.error message is not printed to output, but captured by caplog
        assert "Error: Invalid git repository" in caplog.text


def test_cli_list_models(mock_ollama, caplog):
    result = runner.invoke(cli_app, ["generate", "--list-models"])
    assert result.exit_code == 0
    assert "Available Ollama Models:" in result.stdout
    assert "- model1" in result.stdout
    assert "- model2" in result.stdout
    mock_ollama.assert_called_once()


def test_cli_ai_disabled(caplog):
    with (
        patch("changelog_generator.main.ChangelogConfig.load_config") as mock_load_config,
        patch("os.path.exists", return_value=True),
        patch("git.Repo") as mock_repo,
    ):
        # Create a mock config object with AI disabled
        mock_config = MagicMock()
        mock_config.ai.enabled = False
        mock_config.git.repository_path = "."
        mock_config.git.branch = "main"
        mock_config.logging.level = "INFO"
        
        mock_load_config.return_value = mock_config
        
        # Mock repo setup
        mock_repo_instance = MagicMock()
        mock_repo_instance.branches = [MagicMock(name="main")]
        mock_repo_instance.iter_commits.return_value = [MagicMock()]  # Has commits
        mock_repo.return_value = mock_repo_instance
        
        result = runner.invoke(cli_app, [])
        assert result.exit_code == 0
        assert (
            "AI changelog generation is disabled. No changelog will be generated."
            in result.stdout
        )


def test_cli_generate_get_commit_changes_error(mock_git_repo, caplog):
    # Test the case where get_commit_changes fails
    mock_commit1 = MagicMock(hexsha="1234567")
    mock_commit2 = MagicMock(hexsha="7654321")
    with (
        patch(
            "changelog_generator.main.load_config",
            return_value={
                "git": {"repository_path": ".", "branch": "main", "commit_range": None},
                "changelog": {
                    "output_file": "CHANGELOG.md",
                    "template": "markdown_template.j2",
                },
                "ai": {
                    "enabled": True,
                    "provider": "ollama",
                    "model_name": "qwen3:latest",
                },
                "logging": {"level": "INFO"},
            },
        ),
        patch(
            "changelog_generator.main.get_git_commits",
            return_value=(mock_commit1, mock_commit2),
        ),
        patch(
            "changelog_generator.changelog_utils.get_commit_changes",
            side_effect=Exception("Failed to get changes"),
        ),
        patch("changelog_generator.main.generate_ai_changelog", return_value=""),
    ):
        result = runner.invoke(cli_app, ["generate"])
        assert result.exit_code == 1
        assert "Failed to get changes" in caplog.text
