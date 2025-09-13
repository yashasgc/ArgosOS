"""
Comprehensive tests for all agents with mocked LLM calls
"""
import pytest
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.models import Base, Document, Tag
from app.db.crud import DocumentCRUD, TagCRUD
from app.agents.ingest_agent import IngestAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.postprocessor_agent import PostProcessorAgent
from tests.test_llm_mocks import setup_llm_mocks

# Test database setup
@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def mock_llm():
    """Setup mocked LLM provider"""
    return setup_llm_mocks()

@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing"""
    return """
    John Doe
    Software Engineer
    
    Experience:
    - 5 years of software development
    - Expertise in Python, JavaScript, and React
    - Led multiple successful projects
    
    Education:
    - Bachelor's in Computer Science
    - University of Technology
    """

@pytest.fixture
def sample_image_content():
    """Sample image content for testing"""
    return b"fake_image_data"

class TestIngestAgent:
    """Test IngestAgent with mocked LLM"""
    
    def test_ingest_pdf_document(self, test_db, mock_llm, sample_pdf_content):
        """Test PDF document ingestion"""
        agent = IngestAgent(mock_llm)
        
        # Mock file operations
        with patch('app.agents.ingest_agent.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.mkdir.return_value = None
            
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.return_value.write.return_value = None
                
                # Mock PDF extraction
                with patch('app.agents.ingest_agent.pdfminer') as mock_pdfminer:
                    mock_pdfminer.extract_text.return_value = sample_pdf_content
                    
                    result, errors = agent.ingest_file(
                        file_data=b"fake_pdf_data",
                        filename="test_resume.pdf",
                        mime_type="application/pdf",
                        title="Test Resume",
                        db=test_db
                    )
        
        # Verify document was created
        assert result is not None
        assert result.title == "Test Resume"
        assert result.mime_type == "application/pdf"
        assert "resume" in result.tags.lower() or "career" in result.tags.lower()
        assert len(errors) == 0
    
    def test_ingest_image_document(self, test_db, mock_llm, sample_image_content):
        """Test image document ingestion"""
        agent = IngestAgent(mock_llm)
        
        # Mock file operations
        with patch('app.agents.ingest_agent.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.mkdir.return_value = None
            
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.return_value.write.return_value = None
                
                # Mock OCR extraction
                with patch('app.agents.ingest_agent.Image') as mock_image:
                    mock_img = Mock()
                    mock_img.format = "JPEG"
                    mock_img.mode = "RGB"
                    mock_img.size = (100, 100)
                    mock_image.open.return_value = mock_img
                    
                    with patch('app.agents.ingest_agent.pytesseract') as mock_ocr:
                        mock_ocr.image_to_string.return_value = "Sample text from image"
                        
                        result, errors = agent.ingest_document(
                            file_data=sample_image_content,
                            filename="test_image.jpg",
                            mime_type="image/jpeg",
                            title="Test Image",
                            db=test_db
                        )
        
        # Verify document was created
        assert result is not None
        assert result.title == "Test Image"
        assert result.mime_type == "image/jpeg"
        assert "image" in result.tags.lower() or "visual" in result.tags.lower()
    
    def test_ingest_with_llm_unavailable(self, test_db, sample_pdf_content):
        """Test ingestion when LLM is unavailable"""
        # Create agent with unavailable LLM
        mock_llm_unavailable = Mock()
        mock_llm_unavailable.is_available.return_value = False
        agent = IngestAgent(mock_llm_unavailable)
        
        with patch('app.agents.ingest_agent.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.mkdir.return_value = None
            
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.return_value.write.return_value = None
                
                with patch('app.agents.ingest_agent.pdfminer_extract_text') as mock_pdf:
                    mock_pdf.return_value = sample_pdf_content
                    
                    result, errors = agent.ingest_document(
                        file_data=b"fake_pdf_data",
                        filename="test_resume.pdf",
                        mime_type="application/pdf",
                        title="Test Resume",
                        db=test_db
                    )
        
        # Verify document was created without LLM processing
        assert result is not None
        assert result.title == "Test Resume"
        assert result.summary == ""  # No summary generated
        assert result.tags == "[]"  # No tags generated

class TestRetrievalAgent:
    """Test RetrievalAgent with mocked LLM"""
    
    def test_search_documents_with_llm(self, test_db, mock_llm):
        """Test document search with LLM available"""
        # Create test documents
        doc1 = Document(
            id="doc1",
            title="Software Engineer Resume",
            summary="Experienced software engineer",
            mime_type="application/pdf",
            size_bytes=1000,
            storage_path="/path/to/doc1.pdf",
            tags='["resume", "career", "software"]'
        )
        doc2 = Document(
            id="doc2",
            title="Cover Letter",
            summary="Application cover letter",
            mime_type="application/pdf",
            size_bytes=800,
            storage_path="/path/to/doc2.pdf",
            tags='["cover-letter", "application"]'
        )
        test_db.add(doc1)
        test_db.add(doc2)
        test_db.commit()
        
        # Create tags
        tag1 = Tag(name="resume")
        tag2 = Tag(name="career")
        tag3 = Tag(name="cover-letter")
        test_db.add(tag1)
        test_db.add(tag2)
        test_db.add(tag3)
        test_db.commit()
        
        agent = RetrievalAgent(mock_llm)
        results = agent.search_documents("software engineer resume", test_db, limit=10)
        
        # Verify results
        assert results['total_found'] > 0
        assert len(results['documents']) > 0
        assert "doc1" in results['document_ids']
    
    def test_search_documents_fallback(self, test_db):
        """Test document search fallback when LLM unavailable"""
        # Create test documents
        doc1 = Document(
            id="doc1",
            title="Software Engineer Resume",
            summary="Experienced software engineer",
            mime_type="application/pdf",
            size_bytes=1000,
            storage_path="/path/to/doc1.pdf",
            tags='["resume", "career"]'
        )
        test_db.add(doc1)
        test_db.commit()
        
        # Create agent with unavailable LLM
        mock_llm_unavailable = Mock()
        mock_llm_unavailable.is_available.return_value = False
        agent = RetrievalAgent(mock_llm_unavailable)
        
        results = agent.search_documents("software engineer", test_db, limit=10)
        
        # Verify fallback search works
        assert results['total_found'] > 0
        assert len(results['documents']) > 0
    
    def test_generate_relevant_tags_json_parsing(self, test_db, mock_llm):
        """Test JSON parsing in tag generation"""
        agent = RetrievalAgent(mock_llm)
        available_tags = ["resume", "career", "software"]
        
        # Test with valid JSON response
        with patch.object(mock_llm.client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = '["resume", "career"]'
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response
            
            tags = agent._generate_relevant_tags("software engineer", available_tags, test_db, 10)
            
            assert tags == ["resume", "career"]
    
    def test_generate_relevant_tags_fallback_parsing(self, test_db, mock_llm):
        """Test fallback parsing when JSON fails"""
        agent = RetrievalAgent(mock_llm)
        available_tags = ["resume", "career", "software"]
        
        # Test with invalid JSON response
        with patch.object(mock_llm.client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = 'resume, career, software'  # Not JSON
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response
            
            tags = agent._generate_relevant_tags("software engineer", available_tags, test_db, 10)
            
            # Should fallback to comma parsing
            assert "resume" in tags
            assert "career" in tags

class TestPostProcessorAgent:
    """Test PostProcessorAgent with mocked LLM"""
    
    def test_process_documents(self, test_db, mock_llm):
        """Test document processing"""
        # Create test documents
        doc1 = Document(
            id="doc1",
            title="Software Engineer Resume",
            summary="Experienced software engineer",
            mime_type="application/pdf",
            size_bytes=1000,
            storage_path="/path/to/doc1.pdf",
            tags='["resume", "career"]'
        )
        test_db.add(doc1)
        test_db.commit()
        
        agent = PostProcessorAgent(mock_llm)
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data="Software engineer with 5 years experience")):
            with patch('app.agents.postprocessor_agent.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                
                results = agent.process_documents(
                    query="software engineer experience",
                    document_ids=["doc1"],
                    db=test_db
                )
        
        # Verify processing results
        assert results['success'] is True
        assert len(results['processed_documents']) > 0
        assert "software engineer" in results['processed_documents'][0]['content'].lower()
    
    def test_decide_additional_processing(self, test_db, mock_llm):
        """Test processing decision logic"""
        agent = PostProcessorAgent(mock_llm)
        
        # Test with resume content (should need processing)
        decision = agent._decide_additional_processing(
            query="software engineer resume",
            relevant_content="John Doe, Software Engineer, 5 years experience"
        )
        
        assert decision['needs_processing'] is True
        assert decision['instructions'] is not None
    
    def test_perform_additional_processing(self, test_db, mock_llm):
        """Test additional processing execution"""
        agent = PostProcessorAgent(mock_llm)
        
        result = agent._perform_additional_processing(
            query="software engineer resume",
            relevant_content="John Doe, Software Engineer",
            instructions="Format as professional summary"
        )
        
        assert "PROFESSIONAL SUMMARY" in result
        assert "John Doe" in result

class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_complete_workflow(self, test_db, mock_llm, sample_pdf_content):
        """Test complete workflow from ingestion to search"""
        # Step 1: Ingest document
        ingest_agent = IngestAgent(mock_llm)
        
        with patch('app.agents.ingest_agent.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.mkdir.return_value = None
            
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.return_value.write.return_value = None
                
                with patch('app.agents.ingest_agent.pdfminer_extract_text') as mock_pdf:
                    mock_pdf.return_value = sample_pdf_content
                    
                    doc, errors = ingest_agent.ingest_document(
                        file_data=b"fake_pdf_data",
                        filename="test_resume.pdf",
                        mime_type="application/pdf",
                        title="Test Resume",
                        db=test_db
                    )
        
        assert doc is not None
        assert len(errors) == 0
        
        # Step 2: Search for document
        retrieval_agent = RetrievalAgent(mock_llm)
        search_results = retrieval_agent.search_documents(
            "software engineer resume",
            test_db,
            limit=10
        )
        
        assert search_results['total_found'] > 0
        assert doc.id in search_results['document_ids']
        
        # Step 3: Process documents
        postprocessor_agent = PostProcessorAgent(mock_llm)
        
        with patch('builtins.open', mock_open(read_data=sample_pdf_content)):
            with patch('app.agents.postprocessor_agent.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                
                processed_results = postprocessor_agent.process_documents(
                    query="software engineer resume",
                    document_ids=search_results['document_ids'],
                    db=test_db
                )
        
        assert processed_results['success'] is True
        assert len(processed_results['processed_documents']) > 0

# Helper function for mocking file operations
def mock_open(read_data="", write_data=None):
    """Mock file open function"""
    mock_file = MagicMock()
    mock_file.read.return_value = read_data
    mock_file.write.return_value = write_data
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None
    return mock_file

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
