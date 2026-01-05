import yaml
from pydantic import BaseModel, Field
from typing import List, Optional


class GitConfig(BaseModel):
    repository_path: str = "."
    branch: str = "main"
    commit_range: Optional[str] = None


class ChangelogSection(BaseModel):
    type: str
    title: str


class ChangelogSettings(BaseModel):
    output_file: str = "CHANGELOG.md"
    sections: List[ChangelogSection] = Field(
        default_factory=lambda: [
            ChangelogSection(type="feat", title="🚀 Features"),
            ChangelogSection(type="fix", title="🐛 Bug Fixes"),
            ChangelogSection(type="docs", title="📝 Documentation"),
            ChangelogSection(type="refactor", title="♻️ Refactoring"),
            ChangelogSection(type="test", title="🧪 Tests"),
            ChangelogSection(type="chore", title="🔧 Chores"),
        ]
    )
    template: str = "markdown_template.j2"


class BreakingChangeDetection(BaseModel):
    keywords: List[str] = Field(
        default_factory=lambda: [
            "breaking",
            "breaking change",
            "deprecated",
            "removed",
            "breaking api",
            "incompatible",
        ]
    )


class AISettings(BaseModel):
    enabled: bool = False
    provider: str = "ollama"
    model_name: str = "qwen3:latest"
    ollama_model: str = "qwen3:latest"
    xai_model: str = "grok-2"
    anthropic_model: str = "claude-3-opus-20240229"
    xai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    max_tokens: int = 2048  # Added max_tokens for AI models


class LoggingSettings(BaseModel):
    level: str = "INFO"


class AppConfig(BaseModel):
    git: GitConfig = Field(default_factory=GitConfig)
    changelog: ChangelogSettings = Field(default_factory=ChangelogSettings)
    ai: AISettings = Field(default_factory=AISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    breaking_change_detection: BreakingChangeDetection = Field(
        default_factory=BreakingChangeDetection
    )

    def to_yaml(self) -> str:
        """Convert config to YAML string."""
        return yaml.dump(self.model_dump(), default_flow_style=False, sort_keys=False)
