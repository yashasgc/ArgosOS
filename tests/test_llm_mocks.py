"""
Mock LLM responses for testing
"""
import json
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock

class MockLLMProvider:
    """Mock LLM provider for testing"""
    
    def __init__(self):
        self.client = Mock()
        self.api_key = "test-key"
        self.model = "gpt-3.5-turbo"
    
    def is_available(self) -> bool:
        return True
    
    def summarize(self, text: str) -> str:
        """Mock summarization"""
        if not text or len(text) < 50:
            return "Short document summary"
        return f"Mock summary for document with {len(text)} characters"
    
    def generate_tags(self, text: str) -> List[str]:
        """Mock tag generation"""
        # Simulate different tag generation based on content
        if "resume" in text.lower() or "cv" in text.lower():
            return ["resume", "career", "professional", "experience"]
        elif "cover" in text.lower() or "letter" in text.lower():
            return ["cover-letter", "application", "professional"]
        elif "report" in text.lower():
            return ["report", "analysis", "data"]
        elif "image" in text.lower() or "photo" in text.lower():
            return ["image", "visual", "photo"]
        else:
            return ["document", "text", "content"]
    
    def mock_chat_completion(self, messages: List[Dict], **kwargs):
        """Mock chat completion responses"""
        user_message = messages[-1]["content"]
        
        # Mock different responses based on content
        if "select the most relevant tags" in user_message or "Select relevant tags" in user_message:
            # Mock tag selection response
            return self._mock_tag_selection_response(user_message)
        elif "extract only the most relevant information" in user_message or "Extract relevant information" in user_message:
            # Mock content extraction response
            return self._mock_content_extraction_response(user_message)
        elif "determine if additional processing is needed" in user_message:
            # Mock processing decision response
            return self._mock_processing_decision_response(user_message)
        elif "Process the following content according to the specific instructions" in user_message:
            # Mock additional processing response
            return self._mock_additional_processing_response(user_message)
        else:
            # Default response
            return self._mock_default_response(user_message)
    
    def _mock_tag_selection_response(self, user_message: str) -> Mock:
        """Mock tag selection response"""
        mock_response = Mock()
        mock_choice = Mock()
        
        # Extract query from user message
        if "Search Query:" in user_message:
            query = user_message.split("Search Query:")[1].split("\n")[0].strip().strip('"')
            if "resume" in query.lower():
                tags = ["resume", "career"]
            elif "cover" in query.lower():
                tags = ["cover-letter", "application"]
            elif "report" in query.lower():
                tags = ["report", "analysis"]
            else:
                tags = ["document", "text"]
        else:
            tags = ["document"]
        
        mock_choice.message.content = json.dumps(tags)
        mock_response.choices = [mock_choice]
        return mock_response
    
    def _mock_content_extraction_response(self, user_message: str) -> Mock:
        """Mock content extraction response"""
        mock_response = Mock()
        mock_choice = Mock()
        
        # Extract relevant content based on query
        if "resume" in user_message.lower():
            content = "This is a professional resume highlighting relevant work experience and skills."
        elif "cover" in user_message.lower():
            content = "This is a cover letter expressing interest in a specific position."
        else:
            content = "This is relevant information extracted from the document."
        
        mock_choice.message.content = content
        mock_response.choices = [mock_choice]
        return mock_response
    
    def _mock_processing_decision_response(self, user_message: str) -> Mock:
        """Mock processing decision response"""
        mock_response = Mock()
        mock_choice = Mock()
        
        # Decide if processing is needed based on content
        if "resume" in user_message.lower() or "cover" in user_message.lower():
            decision = {
                "needs_processing": True,
                "instructions": "Format as a professional summary with key highlights"
            }
        else:
            decision = {
                "needs_processing": False,
                "instructions": None
            }
        
        mock_choice.message.content = json.dumps(decision)
        mock_response.choices = [mock_choice]
        return mock_response
    
    def _mock_additional_processing_response(self, user_message: str) -> Mock:
        """Mock additional processing response"""
        mock_response = Mock()
        mock_choice = Mock()
        
        # Process content based on instructions
        if "professional summary" in user_message.lower():
            content = "PROFESSIONAL SUMMARY:\n• Experienced professional with relevant skills\n• Strong background in key areas\n• Ready for new opportunities"
        else:
            content = "Processed content with enhanced formatting and structure."
        
        mock_choice.message.content = content
        mock_response.choices = [mock_choice]
        return mock_response
    
    def _mock_default_response(self, user_message: str) -> Mock:
        """Mock default response"""
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Mock response for testing"
        mock_response.choices = [mock_choice]
        return mock_response

# Global mock instance
mock_llm = MockLLMProvider()

def setup_llm_mocks():
    """Setup LLM mocks for all agents"""
    # Mock the OpenAI client
    mock_llm.client.chat.completions.create = mock_llm.mock_chat_completion
    return mock_llm

# Test functions
def test_mock_llm_availability():
    """Test mock LLM availability"""
    mock = MockLLMProvider()
    assert mock.is_available() is True
    assert mock.api_key == "test-key"
    assert mock.model == "gpt-3.5-turbo"

def test_mock_summarization():
    """Test mock summarization"""
    mock = MockLLMProvider()
    
    # Test with short text
    short_text = "Short text"
    summary = mock.summarize(short_text)
    assert summary == "Short document summary"
    
    # Test with long text
    long_text = "This is a very long document with lots of content that should trigger the longer summary path"
    summary = mock.summarize(long_text)
    assert "Mock summary" in summary
    assert "characters" in summary

def test_mock_tag_generation():
    """Test mock tag generation"""
    mock = MockLLMProvider()
    
    # Test resume content
    resume_text = "John Doe Software Engineer Resume with 5 years experience"
    tags = mock.generate_tags(resume_text)
    assert "resume" in tags
    assert "career" in tags
    
    # Test cover letter content
    cover_text = "Cover letter for software position"
    tags = mock.generate_tags(cover_text)
    assert "cover-letter" in tags
    assert "application" in tags
    
    # Test image content
    image_text = "This is an image or photo content"
    tags = mock.generate_tags(image_text)
    assert "image" in tags or "visual" in tags

def test_mock_chat_completion():
    """Test mock chat completion"""
    mock = MockLLMProvider()
    
    # Test tag selection
    messages = [{"role": "user", "content": "Search Query: 'software engineer resume'\nSelect relevant tags"}]
    response = mock.mock_chat_completion(messages)
    assert response.choices[0].message.content is not None
    # Should return JSON array for tag selection
    content = response.choices[0].message.content
    assert content.startswith('[') and content.endswith(']')
    
    # Test content extraction
    messages = [{"role": "user", "content": "Extract relevant information from software engineer resume"}]
    response = mock.mock_chat_completion(messages)
    content = response.choices[0].message.content
    assert "software engineer" in content.lower() or "resume" in content.lower()

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
