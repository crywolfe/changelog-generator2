import logging
import os
from typing import Dict, List
import requests

from changelog_generator.base_ai_provider import AIProvider
from changelog_generator.config_models import AISettings

logger = logging.getLogger(__name__)


class XAIProvider(AIProvider):
    def __init__(self, ai_settings: AISettings):
        self.ai_settings = ai_settings
        self.model_name = ai_settings.xai_model

    def validate_connection(self) -> bool:
        """Validate that the XAI API is accessible."""
        api_key = self.ai_settings.xai_api_key or os.getenv("XAI_API_KEY")
        if not api_key:
            return False

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            # Simple test request to validate the connection
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10,
            }
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"XAI API validation failed: {e}")
            return False

    def invoke(self, changes: Dict[str, List[str]]) -> str:
        api_key = self.ai_settings.xai_api_key or os.getenv("XAI_API_KEY")
        if not api_key:
            raise ValueError(
                "XAI API key not found. Set 'xai_api_key' in config or 'XAI_API_KEY' environment variable."
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        messages = self._create_messages(changes)
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.ai_settings.max_tokens,
        }

        try:
            response = requests.post(
                "https://api.x.ai/v1/chat/completions", headers=headers, json=payload
            )

            if response.status_code != 200:
                raise ValueError(f"XAI API error: {response.text}")

            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error invoking XAI API: {e}")
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
