# AGENTS.md

This file contains guidelines for agentic coding assistants working in this repository.

## Build, Lint, and Test Commands

### Running Tests
- Run all tests: `pytest`
- Run single test: `pytest tests/test_changelog_generator.py::test_load_config_default`
- Run with verbose output: `pytest -v`
- Run with coverage: `pytest --cov`
- Run specific test file: `pytest tests/test_changelog_generator.py`

### Code Quality
- Format code: `black changelog_generator/ tests/`
- Lint code: `flake8 changelog_generator/ tests/`
- Type check: `mypy changelog_generator/`
- Format imports (isort not configured - use manual sorting)

### Installation
- Install package: `pip install -e .`
- Install dev dependencies: `pip install -e ".[dev]"`

## Code Style Guidelines

### Import Organization
Order imports by category with blank lines between groups:
1. Standard library imports (os, sys, logging, json, re)
2. Third-party imports (git, typer, pydantic, requests, ollama)
3. Local imports (changelog_generator.*)

Example:
```python
import logging
import os
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from git import Repo

from changelog_generator.config_models import AppConfig
```

### Formatting
- Line length: 88 characters (configured in pyproject.toml)
- Use Black formatter before committing
- No trailing whitespace
- Use meaningful docstrings (Google-style with Args/Returns sections)

### Type Hints
- Type hints required for all function arguments and return values
- Import from typing module: Dict, List, Optional, Union
- Use Optional[T] for nullable types
- Use Pydantic BaseModel for configuration classes
- Use Union for multiple possible types (Union[str, git.Commit])

Example:
```python
def get_git_commits(
    repo: git.Repo,
    config: AppConfig,
    commit1_hash: Optional[str] = None,
    commit2_hash: Optional[str] = None
) -> tuple:
```

### Naming Conventions
- Functions and variables: snake_case (get_git_commits, parse_commit_message)
- Classes: PascalCase (AIProvider, AISettings, GitConfig, ChangelogConfig)
- Constants: UPPER_CASE (rarely used in this codebase)
- Private methods: _prefix (_initialize_client, _create_prompt)

### Error Handling
- Use specific exceptions (ValueError, git.exc.GitError, etc.)
- Log errors with logger.error() before raising
- Use try/except blocks with context
- Reraise exceptions after logging: `logger.error(f"Error: {e}"); raise`
- Use tenacity retry decorators for external API calls
- Validate inputs and raise ValueError with descriptive messages

Example:
```python
try:
    return repo.commit(start)
except git.exc.GitError as e:
    logger.error(f"Error validating commit: {e}")
    raise ValueError(f"Invalid commit reference: {e}")
```

### Logging
- Use logging module throughout
- Initialize logger at module level: `logger = logging.getLogger(__name__)`
- Use appropriate levels: DEBUG, INFO, WARNING, ERROR
- Include context in log messages (what, where, why)

### Pydantic Models
- Use BaseModel for all configuration classes
- Use Field for default values and validation
- Use default_factory for mutable defaults (lists, dicts)

Example:
```python
class AISettings(BaseModel):
    enabled: bool = False
    provider: str = "ollama"
    model_name: str = "qwen3:latest"
    keywords: List[str] = Field(default_factory=lambda: ["breaking", "deprecated"])
```

### Git Operations
- Use gitpython for Git operations
- Handle git.exc.GitError exceptions
- Use git.Repo() for repository access
- Validate commits before processing

### AI Provider Integration
- All AI providers inherit from base_ai_provider.AIProvider
- Implement invoke() and validate_connection() methods
- Use AISettings for configuration
- Handle API errors gracefully with logging
- Use environment variables for API keys when not in config

### CLI Development
- Use typer for CLI commands
- Use Annotated for type hints with rich help panels
- Use rich for beautiful output (console, tables, progress bars)
- Validate configuration before execution

### Testing
- Use pytest for all tests
- Use pytest fixtures for mocks (mock_ai_provider, mock_git_repo)
- Use unittest.mock for mocking external dependencies
- Test both success and failure paths
- Test error handling with pytest.raises()

Example:
```python
def test_generate_ai_changelog_success(mock_ai_provider, mock_changelog_config):
    changes = {"commits": [{"raw_message": "commit message"}]}
    result = generate_ai_changelog(changes, mock_ai_provider)
    assert result == "Mocked changelog content"
```

### Configuration
- Configuration loaded via ChangelogConfig class
- YAML files for persistent config (.changelog.yaml)
- Use environment variables for secrets (API keys)
- Validate configuration with pydantic models

### File Structure
- changelog_generator/core/: Core functionality
- changelog_generator/cli/: CLI commands and UI
- changelog_generator/templates/: Jinja2 templates
- tests/: All test files (test_*.py)

### Important Notes
- Do not use f-strings without placeholders (use string concatenation or .format() instead)
- Always run black and mypy before committing
- Test changes locally before pushing
- Check for existing patterns before adding new code
- Maintain backward compatibility when possible
