import os
import yaml
from typing import Optional, Dict, Any

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from changelog_generator.config_models import AppConfig

class ChangelogConfig(BaseSettings):
    """
    Manages application configuration, loading from default values,
    YAML files, and environment variables.
    """
    model_config = SettingsConfigDict(
        env_prefix='CHANGELOG_',
        env_nested_delimiter='__',
        extra='ignore'
    )

    app_config: AppConfig = AppConfig()

    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> AppConfig:
        """
        Loads configuration from a YAML file, then applies environment variables,
        and finally returns the AppConfig object.
        """
        config_data: Dict[str, Any] = {}

        # Load from YAML file if provided and exists
        if config_path:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found at {config_path}")
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config_data.update(file_config)
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML configuration file {config_path}: {e}")

        # Initialize BaseSettings to load environment variables
        # Pydantic-settings will automatically load env vars based on model_config
        # and merge them with the provided config_data.
        try:
            # We need to pass the loaded config_data to the AppConfig directly
            # and then wrap it in ChangelogConfig for env var loading.
            # This is a bit tricky with nested settings, so we'll load AppConfig directly
            # and then apply env vars.
            
            # First, load defaults and file config into AppConfig
            loaded_app_config = AppConfig(**config_data)

            # Then, load environment variables on top of it
            # This requires re-instantiating BaseSettings with the loaded config
            # and letting it apply env vars.
            # A simpler way is to let BaseSettings handle the initial load,
            # and then manually merge file config if needed.
            
            # Let's simplify: BaseSettings loads defaults + env vars.
            # Then, we'll manually merge file config on top.
            
            # This approach is more aligned with pydantic-settings:
            # 1. Load defaults (handled by AppConfig default_factory)
            # 2. Load environment variables (handled by BaseSettings env_prefix)
            # 3. Load file config (manual merge, highest precedence)

            # Create a temporary instance to get env vars applied to defaults
            temp_config_instance = cls()
            final_config_data = temp_config_instance.app_config.model_dump()

            # Deep merge file config on top of env vars and defaults
            if config_data:
                ChangelogConfig._deep_update(final_config_data, config_data)
            
            return AppConfig(**final_config_data)

        except ValidationError as e:
            raise ValueError(f"Configuration validation error: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during configuration loading: {e}")

    @staticmethod
    def _deep_update(original: Dict[str, Any], update: Dict[str, Any]):
        """Recursively update nested dictionaries."""
        for key, value in update.items():
            if isinstance(value, dict) and isinstance(original.get(key), dict):
                original[key] = ChangelogConfig._deep_update(original.get(key, {}), value)
            else:
                original[key] = value
        return original
