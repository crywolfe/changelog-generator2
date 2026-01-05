import logging
from typing import Dict, List

import ollama

from changelog_generator.base_ai_provider import AIProvider
from changelog_generator.config_models import AISettings

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    def __init__(self, ai_settings: AISettings):
        self.ai_settings = ai_settings
        self.model_name = ai_settings.ollama_model
        self._validate_model_availability()

    def _validate_model_availability(self):
        """Check if the specified model is available in Ollama."""
        try:
            available_models = ollama.list()
            model_names = [
                model.get("name", "") for model in available_models.get("models", [])
            ]

            if self.model_name not in model_names:
                logger.warning(
                    f"Model '{self.model_name}' not found in Ollama. Available models: {model_names}"
                )
                raise ValueError(
                    f"Model '{self.model_name}' is not available in Ollama. Run 'ollama pull {self.model_name}' to download it."
                )
        except Exception as e:
            if "Model" in str(e) and "not found" in str(e):
                raise
            logger.error(f"Failed to validate Ollama model availability: {e}")
            raise ValueError(
                "Ollama service appears to be unavailable. Ensure Ollama is running with 'ollama serve'"
            )

    def validate_connection(self) -> bool:
        """Validate that Ollama is running and the model is available."""
        try:
            ollama.list()
            return True
        except Exception as e:
            logger.error(f"Ollama connection validation failed: {e}")
            return False

    def invoke(self, changes: Dict[str, List[str]]) -> str:
        messages = self._create_messages(changes)
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={"num_predict": self.ai_settings.max_tokens},
            )
            if hasattr(response, "message") and hasattr(response.message, "content"):
                return response.message.content
            else:
                raise ValueError("Unexpected response format from Ollama")
        except Exception as e:
            logger.error(f"Error invoking Ollama API: {e}")
            raise

    def _create_messages(self, changes: Dict[str, List[str]]) -> List[Dict[str, str]]:
        return [
            {
                "role": "system",
                "content": "You are a professional changelog generator. Your task is to create clear, concise, and well-structured changelog entries based on provided updates, commits, or pull requests. Ensure each entry is categorized by type (e.g., Added, Fixed, Changed, Deprecated, Removed, Breaking Changes, etc.) and formatted consistently using markdown syntax. Include file names, commit messages, and a brief summary of the changes in each entry. Focus on readability and relevance for a technical software engineering audience. Output the changelog in markdown format.",
            },
            {
                "role": "user",
                "content": f"Generate a detailed and concise changelog for the following changes categorized by type (e.g., Added, Fixed, Changed, Deprecated, Removed, Breaking Changes, etc.): {changes}",
            },
        ]
