import logging
import os
from typing import Dict, List

from anthropic import Anthropic

from changelog_generator.base_ai_provider import AIProvider
from changelog_generator.config_models import AISettings

logger = logging.getLogger(__name__)

class AnthropicProvider(AIProvider):
    def __init__(self, ai_settings: AISettings):
        self.ai_settings = ai_settings
        self.model_name = ai_settings.anthropic_model
        self.client = self._initialize_client()

    def _initialize_client(self):
        api_key = self.ai_settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Set 'anthropic_api_key' in config or 'ANTHROPIC_API_KEY' environment variable."
            )
        
        try:
            return Anthropic(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Anthropic client: {e}")

    def validate_connection(self) -> bool:
        """Validate that the Anthropic API is accessible."""
        try:
            # Simple test request to validate the connection
            self.client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic API validation failed: {e}")
            return False

    def invoke(self, changes: Dict[str, List[str]]) -> str:
        prompt = self._create_prompt(changes)
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.ai_settings.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error invoking Anthropic API: {e}")
            raise

    def _create_prompt(self, changes: Dict[str, List[str]]) -> str:
        # This prompt can be further refined based on desired changelog output
        prompt_parts = [
            "Generate a concise changelog entry based on the following Git changes:",
            "\n---",
            "Commit Messages:",
            "\n".join([f"- {msg['raw_message']}" for msg in changes.get("commits", [])]),
            "\n---",
            "Added Files:",
            "\n".join([f"- {f}" for f in changes.get("added_files", [])]),
            "\n---",
            "Modified Files:",
            "\n".join([f"- {f}" for f in changes.get("modified_files", [])]),
            "\n---",
            "Deleted Files:",
            "\n".join([f"- {f}" for f in changes.get("deleted_files", [])]),
            "\n---",
            "Breaking Changes Detected:",
            "\n".join([f"- {bc}" for bc in changes.get("breaking_changes", [])]),
            "\n---",
            "Please provide a summary of these changes suitable for a changelog. Focus on user-facing changes, new features, bug fixes, and breaking changes. Group related changes logically."
        ]
        return "\n".join(prompt_parts)
