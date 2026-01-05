from typing import Dict, List
import requests
import logging

from changelog_generator.config_models import AISettings
from changelog_generator.anthropic_provider import AnthropicProvider
from changelog_generator.ollama_provider import OllamaProvider
from changelog_generator.xai_provider import XAIProvider

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AIProviderManager:
    def __init__(self, ai_settings: AISettings):
        self.ai_settings = ai_settings
        self.model_provider = ai_settings.provider
        self.model_name = self._get_actual_model_name()
        self._providers = {
            "ollama": OllamaProvider,
            "xai": XAIProvider,
            "anthropic": self._invoke_anthropic,
        }

    def _get_actual_model_name(self) -> str:
        """Determines the specific model name based on the configured provider."""
        if self.model_provider == "ollama":
            return self.ai_settings.ollama_model
        elif self.model_provider == "xai":
            return self.ai_settings.xai_model
        elif self.model_provider == "anthropic":
            return self.ai_settings.anthropic_model
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def invoke(self, changes: Dict[str, List[str]]) -> str:
        if not changes or not isinstance(changes, dict):
            raise ValueError(
                "Invalid changes format. Expected a dictionary with change categories."
            )

        provider = self._providers.get(self.model_provider)
        if not provider:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

        try:
            if isinstance(provider, type):  # If provider is a class (OllamaProvider, XAIProvider)
                provider_instance = provider(self.ai_settings)
                return provider_instance.invoke(changes)
            else:  # If provider is a function (_invoke_anthropic)
                return provider(changes)
        except (ValueError, requests.exceptions.RequestException, Exception) as e:
            logger.error(f"Error in {self.model_provider} provider: {str(e)}")
            raise

    def _invoke_anthropic(self, changes: Dict[str, List[str]]) -> str:
        # Pass AISettings to AnthropicProvider
        anthropic_provider = AnthropicProvider(self.ai_settings)
        return anthropic_provider.invoke(changes)
