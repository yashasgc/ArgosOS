"""
Tests for the PostProcessorAgent
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.agents.postprocessor_agent import PostProcessorAgent
from app.llm.provider import DisabledLLMProvider


class TestPostProcessorAgent:
    """Test cases for PostProcessorAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.llm_provider = DisabledLLMProvider()
        self.agent = PostProcessorAgent(self.llm_provider)
        self.mock_db = Mock(spec=Session)
    
    def test_init(self):
        """Test PostProcessorAgent initialization"""
        assert self.agent.llm_provider == self.llm_provider
        assert self.agent.text_extractor is not None
    
    def test_process_documents_input_validation(self):
        """Test input validation for document processing"""
        # Test empty extraction query
        results = self.agent.process_documents({}, self.mock_db, "")
        assert results['errors'][0] == "Extraction query cannot be empty"
        
        # Test None extraction query
        results = self.agent.process_documents({}, self.mock_db, None)
        assert results['errors'][0] == "Extraction query cannot be empty"
        
        # Test invalid retrieval results
        results = self.agent.process_documents(None, self.mock_db, "test")
        assert results['errors'][0] == "Invalid retrieval results provided"
        
        # Test non-dict retrieval results
        results = self.agent.process_documents("not_a_dict", self.mock_db, "test")
        assert results['errors'][0] == "Invalid retrieval results provided"
    
    def test_process_documents_success(self):
        """Test successful document processing"""
        # Setup mock retrieval results
        retrieval_results = {
            'documents': [
                {
                    'id': 'doc1',
                    'title': 'Test Document 1',
                    'summary': 'Test summary'
                },
                {
                    'id': 'doc2', 
                    'title': 'Test Document 2',
                    'summary': 'Test summary'
                }
            ]
        }
        
        # Mock the internal methods
        with patch.object(self.agent, '_process_single_document') as mock_process:
            mock_process.return_value = {
                'document_id': 'doc1',
                'document_title': 'Test Document 1',
                'extracted_text': 'Test content',
                'llm_response': {'extracted_data': {}, 'needs_post_processing': False},
                'final_response': {'extracted_data': {}},
                'errors': []
            }
            
            results = self.agent.process_documents(retrieval_results, self.mock_db, "test query")
            
            # Assertions
            assert results['query'] == "test query"
            assert results['total_processed'] == 2
            assert len(results['processed_documents']) == 2
            assert len(results['errors']) == 0
    
    def test_process_documents_with_errors(self):
        """Test document processing with errors"""
        # Setup mock retrieval results
        retrieval_results = {
            'documents': [
                {
                    'id': 'doc1',
                    'title': 'Test Document 1',
                    'summary': 'Test summary'
                }
            ]
        }
        
        # Mock the internal methods to return error
        with patch.object(self.agent, '_process_single_document') as mock_process:
            mock_process.return_value = {
                'document_id': 'doc1',
                'document_title': 'Test Document 1',
                'extracted_text': '',
                'llm_response': {},
                'final_response': {},
                'errors': ['Processing failed']
            }
            
            results = self.agent.process_documents(retrieval_results, self.mock_db, "test query")
            
            # Assertions
            assert results['total_processed'] == 1
            assert len(results['processed_documents']) == 1
            assert 'Processing failed' in results['processed_documents'][0]['errors']
    
    def test_process_documents_exception(self):
        """Test document processing with exception"""
        # Setup mock retrieval results
        retrieval_results = {
            'documents': [
                {
                    'id': 'doc1',
                    'title': 'Test Document 1',
                    'summary': 'Test summary'
                }
            ]
        }
        
        # Mock the internal methods to raise exception
        with patch.object(self.agent, '_process_single_document') as mock_process:
            mock_process.side_effect = Exception("Test exception")
            
            results = self.agent.process_documents(retrieval_results, self.mock_db, "test query")
            
            # Assertions
            assert results['total_processed'] == 0
            assert len(results['processed_documents']) == 0
            assert "Processing failed" in results['errors'][0]


