"""
Tests for the IngestAgent
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.agents.ingest_agent import IngestAgent
from app.llm.provider import DisabledLLMProvider
from app.db.models import Document, Tag


class TestIngestAgent:
    """Test cases for IngestAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.llm_provider = DisabledLLMProvider()
        self.agent = IngestAgent(self.llm_provider)
        self.mock_db = Mock(spec=Session)
    
    def test_init(self):
        """Test IngestAgent initialization"""
        assert self.agent.llm_provider == self.llm_provider
        assert self.agent.text_extractor is not None
    
    def test_ingest_file_input_validation(self):
        """Test input validation for file ingestion"""
        # Test None file path
        document, errors = self.agent.ingest_file(None, self.mock_db)
        assert document is None
        assert "File path cannot be None" in errors[0]
        
        # Test invalid file path type
        document, errors = self.agent.ingest_file("not_a_path", self.mock_db)
        assert document is None
        assert "Invalid file path" in errors[0]
    
    @patch('app.agents.ingest_agent.compute_file_hash')
    @patch('app.agents.ingest_agent.TextExtractor.extract_text')
    @patch('app.agents.ingest_agent.DocumentCRUD.get_by_hash')
    @patch('app.agents.ingest_agent.DocumentCRUD.create')
    def test_ingest_file_success(self, mock_create, mock_get_by_hash, mock_extract_text, mock_compute_hash):
        """Test successful file ingestion"""
        # Setup mocks
        mock_compute_hash.return_value = "test_hash"
        mock_get_by_hash.return_value = None  # No existing document
        mock_extract_text.return_value = "Test document content"
        
        # Mock document creation
        mock_document = Mock(spec=Document)
        mock_document.id = "test_id"
        mock_document.title = "test.pdf"
        mock_create.return_value = mock_document
        
        # Create a temporary file for testing
        test_file = Path("test_document.txt")
        test_file.write_text("Test content")
        
        try:
            # Test ingestion
            document, errors = self.agent.ingest_file(test_file, self.mock_db)
            
            # Assertions
            assert document is not None
            assert len(errors) == 0
            mock_compute_hash.assert_called_once_with(test_file)
            mock_extract_text.assert_called_once()
            mock_create.assert_called_once()
        
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
    
    def test_ingest_file_not_found(self):
        """Test file not found error"""
        non_existent_file = Path("non_existent_file.txt")
        
        document, errors = self.agent.ingest_file(non_existent_file, self.mock_db)
        
        assert document is None
        assert len(errors) == 1
        assert "File not found" in errors[0]
    
    @patch('app.agents.ingest_agent.compute_file_hash')
    @patch('app.agents.ingest_agent.DocumentCRUD.get_by_hash')
    def test_ingest_file_duplicate(self, mock_get_by_hash, mock_compute_hash):
        """Test duplicate file detection"""
        # Setup mocks
        mock_compute_hash.return_value = "test_hash"
        existing_doc = Mock(spec=Document)
        existing_doc.title = "existing_document.pdf"
        mock_get_by_hash.return_value = existing_doc
        
        test_file = Path("test_document.txt")
        test_file.write_text("Test content")
        
        try:
            document, errors = self.agent.ingest_file(test_file, self.mock_db)
            
            assert document == existing_doc
            assert len(errors) == 1
            assert "already exists" in errors[0]
        
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_ingest_multiple_files(self):
        """Test batch file ingestion"""
        # Create test files
        test_files = []
        for i in range(3):
            test_file = Path(f"test_document_{i}.txt")
            test_file.write_text(f"Test content {i}")
            test_files.append(test_file)
        
        try:
            with patch('app.agents.ingest_agent.compute_file_hash') as mock_hash, \
                 patch('app.agents.ingest_agent.TextExtractor.extract_text') as mock_extract, \
                 patch('app.agents.ingest_agent.DocumentCRUD.get_by_hash') as mock_get_hash, \
                 patch('app.agents.ingest_agent.DocumentCRUD.create') as mock_create:
                
                # Setup mocks
                mock_hash.return_value = "test_hash"
                mock_get_hash.return_value = None
                mock_extract.return_value = "Test content"
                
                # Mock document creation
                mock_doc = Mock(spec=Document)
                mock_doc.id = "test_id"
                mock_doc.title = "test"
                mock_create.return_value = mock_doc
                
                # Test batch ingestion
                documents, errors = self.agent.ingest_multiple_files(test_files, self.mock_db)
                
                assert len(documents) == 3
                assert len(errors) == 0
        
        finally:
            # Cleanup
            for test_file in test_files:
                if test_file.exists():
                    test_file.unlink()
    
    def test_reprocess_document_not_found(self):
        """Test reprocessing non-existent document"""
        with patch('app.agents.ingest_agent.DocumentCRUD.get_by_id') as mock_get:
            mock_get.return_value = None
            
            success, errors = self.agent.reprocess_document("non_existent_id", self.mock_db)
            
            assert success == False
            assert len(errors) == 1
            assert "Document not found" in errors[0]


