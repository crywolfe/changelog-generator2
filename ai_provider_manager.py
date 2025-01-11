from typing import Dict, List
from dotenv import load_dotenv
import ollama
import subprocess
from openai import OpenAI
import requests
import os

class AIProviderManager:
    def __init__(self, model_provider: str, model_name: str = None):
        self.model_provider = model_provider
        self.model_name = model_name or self._get_default_model_name()

    def _get_default_model_name(self):
        if self.model_provider == "ollama":
            return "llama3.1:latest"
        elif self.model_provider == "openai":
            return "gpt-4"
        elif self.model_provider == "xai":
            return "grok-1"
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def invoke(self, changes: Dict[str, List[str]]) -> str:
        if self.model_provider == "ollama":
            return self._invoke_ollama(changes)
        elif self.model_provider == "openai":
            return self._invoke_openai(changes)
        elif self.model_provider == "xai":
            return self._invoke_xai(changes)
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def _invoke_ollama(self, changes: Dict[str, List[str]]) -> str:
        try:
            prompt = self._create_changelog_prompt(changes)
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional software changelog generator.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response["message"]["content"]
        except Exception as e:
            print(f"Error generating changelog with Ollama: {e}")
            return f"Unable to generate changelog. Error: {e}"

    def _invoke_openai(self, changes: Dict[str, List[str]]) -> str:
        client = OpenAI()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional changelog generator.",
                },
                {
                    "role": "user",
                    "content": f"Generate a changelog for these changes: {changes}",
                },
            ],
        )
        return response.choices[0].message.content

    def _invoke_xai(self, changes: Dict[str, List[str]]) -> str:
        load_dotenv()
        xai_api_key = os.getenv("XAI_API_KEY")
        if not xai_api_key:
            raise ValueError("XAI_API_KEY not found in .env file")

        headers = {
            "Authorization": f"Bearer {xai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional changelog generator.",
                },
                {
                    "role": "user",
                    "content": f"Generate a changelog for these changes: {changes}",
                },
            ],
        }

        response = requests.post(
            "https://api.x.ai/v1/chat/completions", headers=headers, json=payload
        )

        if response.status_code != 200:
            raise ValueError(f"XAI API error: {response.text}")

        return response.json()["choices"][0]["message"]["content"]

    def _create_changelog_prompt(self, changes: Dict[str, List[str]]) -> str:
        prompt = "Generate a comprehensive changelog based on the following commit changes:\n\n"

        # Added Files
        if changes["added_files"]:
            prompt += "New Files Added:\n"
            for file in changes["added_files"]:
                prompt += f"- {file}\n"

        # Modified Files
        if changes["modified_files"]:
            prompt += "\nModified Files:\n"
            for file in changes["modified_files"]:
                prompt += f"- {file}\n"

        # Deleted Files
        if changes["deleted_files"]:
            prompt += "\nDeleted Files:\n"
            for file in changes["deleted_files"]:
                prompt += f"- {file}\n"

        # Breaking Changes
        if changes["breaking_changes"]:
            prompt += "\nBreaking Changes:\n"
            for change in changes["breaking_changes"]:
                prompt += f"- {change}\n"

        # Commit Messages
        if changes["commit_messages"]:
            prompt += "\nCommit Messages:\n"
            for msg in changes["commit_messages"]:
                prompt += f"- {msg}\n"

        prompt += (
            "\nPlease generate a detailed, professional changelog that highlights key changes, "
            "new features, bug fixes, and any breaking changes. Use markdown formatting."
        )

        return prompt
