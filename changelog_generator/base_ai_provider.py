from abc import ABC, abstractmethod
from typing import Dict, List


class AIProvider(ABC):
    @abstractmethod
    def invoke(self, changes: Dict[str, List[str]]) -> str:
        """Generate changelog content from changes."""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the AI provider is accessible and ready to use."""
        pass
