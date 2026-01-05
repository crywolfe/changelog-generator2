"""Validation functions for the changelog generator CLI."""

import os
import ollama
from typing import List
from changelog_generator.config_models import AISettings


def validate_ai_config(ai_settings: AISettings) -> List[str]:
    """Validate AI provider configuration and return list of errors."""
    errors = []

    if ai_settings.provider == "xai" and not ai_settings.xai_api_key:
        if not os.getenv("XAI_API_KEY"):
            errors.append(
                "XAI provider requires xai_api_key in config or XAI_API_KEY environment variable"
            )

    elif ai_settings.provider == "anthropic" and not ai_settings.anthropic_api_key:
        if not os.getenv("ANTHROPIC_API_KEY"):
            errors.append(
                "Anthropic provider requires anthropic_api_key in config or ANTHROPIC_API_KEY environment variable"
            )

    elif ai_settings.provider == "ollama":
        # Check if Ollama is running
        try:
            ollama.list()
        except Exception:
            errors.append(
                "Ollama provider requires Ollama to be running (try: ollama serve)"
            )

    elif ai_settings.provider not in ["ollama", "xai", "anthropic"]:
        errors.append(
            f"Unsupported AI provider: {ai_settings.provider}. Use 'ollama', 'xai', or 'anthropic'"
        )

    return errors
