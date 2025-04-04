import os
import yaml
from typing import Dict, Any

DEFAULT_CONFIG = {
    "model_provider": "ollama",
    "model_name": "qwen2.5:14b",
    "verbose": False,
    "output_format": "markdown",
    "breaking_change_detection": {
        "keywords": [
            "breaking",
            "breaking change",
            "deprecated",
            "removed",
            "breaking api",
            "incompatible",
        ]
    },
    "ollama_model": "qwen2.5:14b",
    "xai_model": "grok-2",
    "output_file": "CHANGELOG_DEFAULT.md",
    "xai_api_key": None,
}


class ChangelogConfig:
    def __init__(self, config_path=None):
        self.config = DEFAULT_CONFIG.copy()

        # Check environment variables first
        self._load_env_config()

        # Load from config file if provided
        if config_path and os.path.exists(config_path):
            self._load_file_config(config_path)

    def _load_env_config(self):
        """Load configuration from environment variables."""
        env_mappings = {
            "CHANGELOG_MODEL_PROVIDER": "model_provider",
            "CHANGELOG_MODEL_NAME": "model_name",
            "CHANGELOG_VERBOSE": "verbose",
            "CHANGELOG_OLLAMA_MODEL": "ollama_model",
            "CHANGELOG_XAI_MODEL": "xai_model",
            "CHANGELOG_OUTPUT_FILE": "output_file",
            "CHANGELOG_XAI_API_KEY": "xai_api_key",
        }

        for env_key, config_key in env_mappings.items():
            value = os.environ.get(env_key)
            if value is not None:
                self.config[config_key] = value

    def _load_file_config(self, config_path):
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            file_config = yaml.safe_load(f)

        # Deep update of configuration
        self._deep_update(self.config, file_config)

    def _deep_update(self, original: Dict[str, Any], update: Dict[str, Any]):
        """Recursively update nested dictionaries."""
        for key, value in update.items():
            if isinstance(value, dict):
                original[key] = self._deep_update(original.get(key, {}), value)
            else:
                original[key] = value
        return original

    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
