import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.xai_model = os.getenv("XAI_MODEL", "grok-1")
        self.output_file = os.getenv("OUTPUT_FILE", "CHANGELOG.md")
        self.xai_api_key = os.getenv("XAI_API_KEY")

    def get_model_name(self, provider):
        if provider == "ollama":
            return self.ollama_model
        elif provider == "openai":
            return self.openai_model
        elif provider == "xai":
            return self.xai_model
        else:
            raise ValueError(f"Unsupported model provider: {provider}")

    def get_output_file(self):
        return self.output_file

    def get_xai_api_key(self):
        return self.xai_api_key
