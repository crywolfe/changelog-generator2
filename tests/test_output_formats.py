import pytest
import json
import tempfile
import os
from unittest.mock import patch

from changelog_generator.generator import (
    generate_json_changelog,
    generate_changelog_content,
    determine_output_format,
)


class TestOutputFormats:
    """Test output format detection and generation."""

    def test_determine_output_format(self):
        """Test output format detection from file extensions."""
        assert determine_output_format("changelog.md") == "markdown"
        assert determine_output_format("changelog.html") == "html"
        assert determine_output_format("changelog.json") == "json"
        assert determine_output_format("CHANGELOG.md") == "markdown"
        assert determine_output_format("output.txt") == "markdown"  # default

    def test_generate_json_changelog(self):
        """Test JSON changelog generation."""
        commits = [
            {
                "hash": "abc123",
                "author": "Test Author",
                "date": "2023-01-01T00:00:00",
                "type": "feat",
                "scope": "auth",
                "description": "add login system",
                "raw_message": "feat(auth): add login system"
            },
            {
                "hash": "def456",
                "author": "Test Author",
                "date": "2023-01-02T00:00:00",
                "type": "fix",
                "scope": None,
                "description": "resolve memory leak",
                "raw_message": "fix: resolve memory leak"
            }
        ]
        
        breaking_changes = ["feat!: breaking change in API"]
        commit_range = "abc123..def456"
        model_provider = "ollama"
        model_name = "qwen3:latest"
        ai_summary = "Added authentication and fixed critical bugs"

        result = generate_json_changelog(
            commits, breaking_changes, commit_range,
            model_provider, model_name, ai_summary
        )

        # Parse the JSON result
        data = json.loads(result)
        
        # Verify structure
        assert "metadata" in data
        assert "ai_summary" in data
        assert "breaking_changes" in data
        assert "changes" in data
        assert "commits" in data
        
        # Verify metadata
        assert data["metadata"]["commit_range"] == commit_range
        assert data["metadata"]["model_provider"] == model_provider
        assert data["metadata"]["model_name"] == model_name
        assert data["metadata"]["total_commits"] == 2
        
        # Verify content
        assert data["ai_summary"] == ai_summary
        assert data["breaking_changes"] == breaking_changes
        assert len(data["commits"]) == 2
        
        # Verify grouped changes
        assert "feat" in data["changes"]
        assert "fix" in data["changes"]
        assert "auth" in data["changes"]["feat"]
        assert "general" in data["changes"]["fix"]

    @patch('changelog_generator.generator.generate_changelog_from_template')
    def test_generate_changelog_content_html(self, mock_template_gen):
        """Test HTML format generation."""
        mock_template_gen.return_value = "<html>Test HTML</html>"
        
        commits = [{"hash": "abc123", "description": "test commit"}]
        result = generate_changelog_content(
            commits, [], "abc123..def456", "ollama", "qwen3", "html"
        )
        
        assert result == "<html>Test HTML</html>"
        mock_template_gen.assert_called_once_with(
            commits, [], "abc123..def456", "ollama", "qwen3", 
            "html_template.j2", None
        )

    @patch('changelog_generator.generator.generate_changelog_from_template') 
    def test_generate_changelog_content_markdown(self, mock_template_gen):
        """Test Markdown format generation (default)."""
        mock_template_gen.return_value = "# Test Markdown"
        
        commits = [{"hash": "abc123", "description": "test commit"}]
        result = generate_changelog_content(
            commits, [], "abc123..def456", "ollama", "qwen3", "markdown"
        )
        
        assert result == "# Test Markdown"
        mock_template_gen.assert_called_once_with(
            commits, [], "abc123..def456", "ollama", "qwen3",
            "markdown_template.j2", None
        )

    def test_generate_changelog_content_json(self):
        """Test JSON format generation."""
        commits = [
            {
                "hash": "abc123",
                "type": "feat",
                "scope": "test",
                "description": "test commit"
            }
        ]
        
        result = generate_changelog_content(
            commits, [], "abc123..def456", "ollama", "qwen3", "json"
        )
        
        # Should be valid JSON
        data = json.loads(result)
        assert data["metadata"]["commit_range"] == "abc123..def456"
        assert len(data["commits"]) == 1


class TestConfigValidation:
    """Test configuration validation improvements."""

    def test_init_config_creation(self):
        """Test configuration file creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, ".changelog.yaml")
            
            # Import and call init_config function
            from changelog_generator.main import init_config
            
            # Mock typer.confirm to return True
            with patch('typer.confirm', return_value=True):
                init_config(config_path)
            
            # Verify file was created
            assert os.path.exists(config_path)
            
            # Verify content
            with open(config_path, 'r') as f:
                content = f.read()
                assert "git:" in content
                assert "changelog:" in content
                assert "ai:" in content
                assert "breaking_change_detection:" in content

    def test_config_validation_with_env_vars(self):
        """Test configuration loading with environment variables."""
        # Test environment variable handling for AI providers
        with patch.dict(os.environ, {'XAI_API_KEY': 'test-key'}):
            from changelog_generator.xai_provider import XAIProvider
            from changelog_generator.config_models import AISettings
            
            ai_settings = AISettings(
                provider="xai",
                xai_model="grok-2"
            )
            
            provider = XAIProvider(ai_settings)
            # Should not raise an error since env var is set
            assert provider.ai_settings.provider == "xai"


if __name__ == "__main__":
    pytest.main([__file__])