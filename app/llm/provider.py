from abc import ABC, abstractmethod
from typing import List

class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        pass
    
    @abstractmethod
    def summarize(self, text: str) -> str:
        """Generate a summary of the given text"""
        pass
    
    @abstractmethod
    def generate_tags(self, text: str) -> List[str]:
        """Generate tags for the given text"""
        pass

class DisabledLLMProvider(LLMProvider):
    """LLM provider that does nothing (when LLM is disabled)"""
    
    def is_available(self) -> bool:
        return False
    
    def summarize(self, text: str) -> str:
        return ""
    
    def generate_tags(self, text: str) -> List[str]:
        return []


