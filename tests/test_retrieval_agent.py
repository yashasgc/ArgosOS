"""
Tests for the RetrievalAgent
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.agents.retrieval_agent import RetrievalAgent
from app.llm.provider import DisabledLLMProvider
from app.db.models import Document, Tag


class TestRetrievalAgent:
    """Test cases for RetrievalAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.llm_provider = DisabledLLMProvider()
        self.agent = RetrievalAgent(self.llm_provider)
        self.mock_db = Mock(spec=Session)
    
    def test_init(self):
        """Test RetrievalAgent initialization"""
        assert self.agent.llm_provider == self.llm_provider
    
    def test_search_documents_input_validation(self):
        """Test input validation for document search"""
        # Test empty query
        results = self.agent.search_documents("", self.mock_db)
        assert results['errors'][0] == "Query cannot be empty"
        
        # Test None query
        results = self.agent.search_documents(None, self.mock_db)
        assert results['errors'][0] == "Query cannot be empty"
        
        # Test whitespace-only query
        results = self.agent.search_documents("   ", self.mock_db)
        assert results['errors'][0] == "Query cannot be empty"
        
        # Test limit validation
        results = self.agent.search_documents("test", self.mock_db, limit=0)
        assert results['query'] == "test"  # Should still work with default limit
        
        results = self.agent.search_documents("test", self.mock_db, limit=2000)
        assert results['query'] == "test"  # Should still work with default limit
    
    def test_search_documents_llm_unavailable(self):
        """Test search when LLM is unavailable"""
        # Test with disabled LLM provider
        results = self.agent.search_documents("test query", self.mock_db)
        
        # Should return error
        assert "LLM provider not available" in results['errors']
        assert len(results['documents']) == 0
    
    def test_get_document_content_input_validation(self):
        """Test input validation for document content retrieval"""
        # Test empty document ID
        result = self.agent.get_document_content("", self.mock_db)
        assert result['error'] == "Document ID cannot be empty"
        
        # Test None document ID
        result = self.agent.get_document_content(None, self.mock_db)
        assert result['error'] == "Document ID cannot be empty"
        
        # Test whitespace-only document ID
        result = self.agent.get_document_content("   ", self.mock_db)
        assert result['error'] == "Document ID cannot be empty"
        
        # Test document ID too long
        long_id = "x" * 300
        result = self.agent.get_document_content(long_id, self.mock_db)
        assert result['error'] == "Document ID too long"
    
    def test_format_documents(self):
        """Test document formatting helper method"""
        # Create mock documents
        mock_doc1 = Mock(spec=Document)
        mock_doc1.id = "doc1"
        mock_doc1.title = "Test Document 1"
        mock_doc1.summary = "Test summary 1"
        mock_doc1.mime_type = "text/plain"
        mock_doc1.size_bytes = 100
        mock_doc1.created_at = 1234567890
        mock_doc1.imported_at = 1234567890
        
        mock_doc2 = Mock(spec=Document)
        mock_doc2.id = "doc2"
        mock_doc2.title = "Test Document 2"
        mock_doc2.summary = "Test summary 2"
        mock_doc2.mime_type = "application/pdf"
        mock_doc2.size_bytes = 200
        mock_doc2.created_at = 1234567891
        mock_doc2.imported_at = 1234567891
        
        # Test formatting
        formatted = self.agent._format_documents([mock_doc1, mock_doc2])
        
        # Assertions
        assert len(formatted) == 2
        assert formatted[0]['id'] == "doc1"
        assert formatted[0]['title'] == "Test Document 1"
        assert formatted[0]['tags'] == []  # Tags not available in raw SQL results
        assert formatted[1]['id'] == "doc2"
        assert formatted[1]['title'] == "Test Document 2"


