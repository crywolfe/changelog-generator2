import pytest
import os
import tempfile
import git
from unittest.mock import patch, MagicMock

from changelog_generator import generate_ai_changelog, main

@pytest.fixture
def sample_changes():
    """Provide sample changes for testing."""
    return {
        'added_files': ['new_file.py'],
        'modified_files': ['existing_file.py'],
        'deleted_files': ['old_file.py'],
        'commit_messages': ['Added new feature', 'Fixed bug']
    }

def test_generate_ai_changelog_ollama(sample_changes):
    """Test generate_ai_changelog with Ollama provider."""
    with patch('changelog_generator.OllamaLLM') as mock_ollama:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = "Mocked Ollama changelog"
        mock_ollama.return_value = mock_instance
        
        result = generate_ai_changelog(sample_changes, model_provider='ollama', model_name='llama3.2')
        assert result == "Mocked Ollama changelog"
        mock_ollama.assert_called_once_with(model='llama3.2')

def test_generate_ai_changelog_unsupported_provider(sample_changes):
    """Test generate_ai_changelog with an unsupported provider."""
    with pytest.raises(ValueError, match="Unsupported model provider: azure"):
        generate_ai_changelog(sample_changes, model_provider='azure')

@patch('changelog_generator.git.Repo')
@patch('changelog_generator.validate_commits')
@patch('changelog_generator.get_commit_changes')
@patch('changelog_generator.generate_ai_changelog')
def test_main_basic_flow(mock_generate_ai_changelog, mock_get_commit_changes, 
                          mock_validate_commits, mock_repo, sample_changes, tmp_path):
    """Test the main function with a basic flow."""
    # Setup mocks
    mock_repo_instance = MagicMock()
    mock_repo.return_value = mock_repo_instance
    
    mock_validate_commits.return_value = (MagicMock(), MagicMock())
    mock_get_commit_changes.return_value = sample_changes
    mock_generate_ai_changelog.return_value = "Generated Changelog"
    
    # Prepare temporary output file
    output_file = tmp_path / "CHANGELOG.md"
    
    # Simulate command-line arguments
    with patch('sys.argv', ['changelog_generator.py', 'commit1', 'commit2', 
                             '--output', str(output_file)]):
        main()
    
    # Verify interactions
    mock_validate_commits.assert_called_once()
    mock_get_commit_changes.assert_called_once()
    mock_generate_ai_changelog.assert_called_once()
    
    # Check output file
    assert output_file.exists()
    content = output_file.read_text()
    assert "Generated Changelog" in content
