from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, List, Optional
from changelog_generator.ai_provider_manager import AIProviderManager
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_ai_changelog(
    changes: Dict[str, List[str]],
    model_provider: str = "ollama",
    model_name: str = None,
) -> str:
    """
    Generate a changelog using an AI model with robust error handling and retries.
    """
    try:
        ai_provider = AIProviderManager(model_provider, model_name)
        changelog = ai_provider.invoke(changes)

        if not changelog or changelog.startswith("Unable to generate"):
            raise ValueError("Changelog generation failed")

        return changelog

    except Exception as e:
        logger.error(f"Changelog generation error: {e}")
        raise
