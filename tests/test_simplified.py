"""
Simplified tests for ArgosOS core functionality
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.models import Base, Document, Tag
from app.db.crud import DocumentCRUD, TagCRUD
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
def sample_documents(test_db):
    """Create sample documents for testing"""
    # Create tags
    tag1 = Tag(name="resume")
    tag2 = Tag(name="career")
    tag3 = Tag(name="cover-letter")
    test_db.add(tag1)
    test_db.add(tag2)
    test_db.add(tag3)
    test_db.commit()
    
    # Create documents with required fields
    doc1 = Document(
        id="doc1",
        content_hash="hash1",
        title="Software Engineer Resume",
        summary="Experienced software engineer with 5 years of experience",
        mime_type="application/pdf",
        size_bytes=1000,
        storage_path="/path/to/doc1.pdf",
        tags='["resume", "career", "software"]'
    )
    doc2 = Document(
        id="doc2",
        content_hash="hash2",
        title="Cover Letter",
        summary="Application cover letter for software position",
        mime_type="application/pdf",
        size_bytes=800,
        storage_path="/path/to/doc2.pdf",
        tags='["cover-letter", "application"]'
    )
    test_db.add(doc1)
    test_db.add(doc2)
    test_db.commit()
    
    return [doc1, doc2]

class TestRetrievalAgent:
    """Test RetrievalAgent with mocked LLM"""
    
    def test_search_documents_with_llm(self, test_db, mock_llm, sample_documents):
        """Test document search with LLM available"""
        agent = RetrievalAgent(mock_llm)
        results = agent.search_documents("software engineer resume", test_db, limit=10)
        
        # Verify results
        assert results['total_found'] > 0
        assert len(results['documents']) > 0
        assert "doc1" in results['document_ids']
    
    def test_search_documents_fallback(self, test_db, sample_documents):
        """Test document search fallback when LLM unavailable"""
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
    
    def test_process_documents(self, test_db, mock_llm, sample_documents):
        """Test document processing"""
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
        assert 'processed_documents' in results
        assert len(results['processed_documents']) > 0
        # The mock returns generic content, so we just check that content exists
        assert len(results['processed_documents'][0]['relevant_content']) > 0
    
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
        # The mock returns a generic response, so we check for the format
        assert "professional" in result.lower()

class TestDatabaseOperations:
    """Test database operations"""
    
    def test_document_crud_create(self, test_db):
        """Test document creation"""
        from app.db.schemas import DocumentCreate
        import time
        
        doc_data = DocumentCreate(
            content_hash="test_hash_123",
            title="Test Document",
            mime_type="application/pdf",
            size_bytes=1000,
            storage_path="/path/to/test.pdf",
            summary="Test summary",
            tags=["test", "document"],
            created_at=int(time.time() * 1000),
            imported_at=int(time.time() * 1000)
        )
        
        doc = DocumentCRUD.create(test_db, doc_data)
        
        assert doc.title == "Test Document"
        assert doc.mime_type == "application/pdf"
        assert doc.size_bytes == 1000
        assert doc.storage_path == "/path/to/test.pdf"
        assert doc.summary == "Test summary"
        assert "test" in doc.tags
    
    def test_document_crud_search(self, test_db, sample_documents):
        """Test document search"""
        results = DocumentCRUD.search(test_db, "software engineer", 0, 10)
        
        assert len(results) > 0
        assert any("software" in doc.title.lower() for doc in results)
    
    def test_tag_crud_operations(self, test_db):
        """Test tag CRUD operations"""
        # Create tag
        from app.db.schemas import TagCreate
        tag_data = TagCreate(name="test-tag")
        tag = TagCRUD.create(test_db, tag_data)
        
        assert tag.name == "test-tag"
        
        # Get by name
        found_tag = TagCRUD.get_by_name(test_db, "test-tag")
        assert found_tag.name == "test-tag"
        
        # Get or create
        existing_tag = TagCRUD.get_or_create(test_db, "test-tag")
        assert existing_tag.name == "test-tag"
        
        # Get all
        all_tags = TagCRUD.get_all(test_db)
        assert len(all_tags) >= 1

class TestLLMIntegration:
    """Test LLM integration"""
    
    def test_llm_mock_functionality(self, mock_llm):
        """Test that LLM mocks work correctly"""
        # Test availability
        assert mock_llm.is_available() is True
        
        # Test summarization
        summary = mock_llm.summarize("This is a test document with lots of content that should trigger the longer summary path")
        assert "Mock summary" in summary
        
        # Test tag generation
        tags = mock_llm.generate_tags("Software engineer resume with experience")
        assert "resume" in tags
        assert "career" in tags
        
        # Test chat completion
        messages = [{"role": "user", "content": "Search Query: 'software engineer'\nSelect relevant tags"}]
        response = mock_llm.mock_chat_completion(messages)
        assert response.choices[0].message.content is not None

class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_complete_search_workflow(self, test_db, mock_llm, sample_documents):
        """Test complete search workflow"""
        # Step 1: Search for documents
        retrieval_agent = RetrievalAgent(mock_llm)
        search_results = retrieval_agent.search_documents(
            "software engineer resume",
            test_db,
            limit=10
        )
        
        assert search_results['total_found'] > 0
        assert len(search_results['document_ids']) > 0
        
        # Step 2: Process documents
        postprocessor_agent = PostProcessorAgent(mock_llm)
        
        with patch('builtins.open', mock_open(read_data="Software engineer with 5 years experience")):
            with patch('app.agents.postprocessor_agent.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                
                processed_results = postprocessor_agent.process_documents(
                    query="software engineer resume",
                    document_ids=search_results['document_ids'],
                    db=test_db
                )
        
        assert 'processed_documents' in processed_results
        assert len(processed_results['processed_documents']) > 0

# Helper function for mocking file operations
def mock_open(read_data="", write_data=None):
    """Mock file open function"""
    from unittest.mock import MagicMock
    mock_file = MagicMock()
    mock_file.read.return_value = read_data
    mock_file.write.return_value = write_data
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None
    return mock_file

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
