from typing import Dict, List
from dotenv import load_dotenv
import ollama
import requests
import os


class AIProviderManager:
    def __init__(self, model_provider: str, model_name: str = None):
        load_dotenv()
        self.model_provider = model_provider
        self.model_name = model_name or self._get_default_model_name()
        self.invoke_methods = {
            "ollama": self._invoke_ollama,
            "xai": self._invoke_xai,
        }

    def _get_default_model_name(self) -> str:
        model_mapping = {
            "ollama": os.getenv("OLLAMA_MODEL", "qwen2.5:14b"),
            "xai": os.getenv("XAI_MODEL", "grok-2"),
        }
        return model_mapping.get(self.model_provider, "Unsupported model provider")

    def _generate_messages(self, changes: Dict[str, List[str]]) -> List[Dict[str, str]]:
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

    def invoke(self, changes: Dict[str, List[str]]) -> str:
        if not changes or not isinstance(changes, dict):
            raise ValueError(
                "Invalid changes format. Expected a dictionary with change categories."
            )

        invoke_method = self.invoke_methods.get(self.model_provider)
        if not invoke_method:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

        try:
            return invoke_method(changes)
        except (ValueError, requests.exceptions.RequestException, Exception) as e:
            print(f"Error in {self.model_provider} provider: {str(e)}")
            raise

    def _invoke_ollama(self, changes: Dict[str, List[str]]) -> str:
        response = ollama.chat(
            model=self.model_name, messages=self._generate_messages(changes)
        )
        # Print the response object to inspect its structure
        # print(f"Ollama Response: {response.__dict__}")

        # Access the content from the nested message attribute
        if hasattr(response, "message") and hasattr(response.message, "content"):
            return response.message.content
        else:
            raise ValueError("Unexpected response format from Ollama")

    def _invoke_xai(self, changes: Dict[str, List[str]]) -> str:
        xai_api_key = os.getenv("XAI_API_KEY")
        if not xai_api_key:
            raise ValueError("XAI_API_KEY not found in .env file")

        headers = {
            "Authorization": f"Bearer {xai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "messages": self._generate_messages(changes),
        }

        response = requests.post(
            "https://api.x.ai/v1/chat/completions", headers=headers, json=payload
        )

        if response.status_code != 200:
            raise ValueError(f"XAI API error: {response.text}")

        return response.json()["choices"][0]["message"]["content"]
