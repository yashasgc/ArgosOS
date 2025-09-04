from typing import List
from .provider import LLMProvider

class OpenAIProvider(LLMProvider):
    """OpenAI GPT-based LLM provider"""
    
    def __init__(self):
        try:
            from app.config import settings
            self.api_key = getattr(settings, 'openai_api_key', None)
            self.model = getattr(settings, 'openai_model', 'gpt-3.5-turbo')
        except ImportError:
            self.api_key = None
            self.model = 'gpt-3.5-turbo'
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        return bool(self.api_key and self.api_key.strip())
    
    def summarize(self, text: str) -> str:
        """Generate a summary using OpenAI"""
        if not self.is_available():
            return ""
        
        try:
            # For now, return a simple summary
            # In a full implementation, this would call OpenAI API
            words = text.split()
            if len(words) <= 50:
                return text
            else:
                return " ".join(words[:50]) + "..."
        except Exception:
            return ""
    
    def generate_tags(self, text: str) -> List[str]:
        """Generate tags using OpenAI"""
        if not self.is_available():
            return []
        
        try:
            # For now, return some basic tags
            # In a full implementation, this would call OpenAI API
            tags = []
            text_lower = text.lower()
            
            # Simple keyword-based tagging
            if "pdf" in text_lower or "document" in text_lower:
                tags.append("document")
            if "report" in text_lower:
                tags.append("report")
            if "contract" in text_lower or "agreement" in text_lower:
                tags.append("legal")
            if "invoice" in text_lower or "bill" in text_lower:
                tags.append("financial")
            if "manual" in text_lower or "guide" in text_lower:
                tags.append("manual")
            
            return tags[:5]  # Limit to 5 tags
        except Exception:
            return []
