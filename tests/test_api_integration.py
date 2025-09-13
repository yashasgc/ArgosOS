"""
API integration tests with mocked LLM calls
"""
import pytest
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.db.models import Base, Document, Tag
from app.db.crud import DocumentCRUD, TagCRUD
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
def client(test_db):
    """Create test client with dependency override"""
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

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
    
    # Create documents
    doc1 = Document(
        id="doc1",
        title="Software Engineer Resume",
        summary="Experienced software engineer with 5 years of experience",
        mime_type="application/pdf",
        size_bytes=1000,
        storage_path="/path/to/doc1.pdf",
        tags='["resume", "career", "software"]'
    )
    doc2 = Document(
        id="doc2",
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

class TestDocumentAPI:
    """Test document-related API endpoints"""
    
    def test_get_documents(self, client, sample_documents):
        """Test GET /api/documents endpoint"""
        response = client.get("/api/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["documents"]) == 2
        assert data["total"] == 2
        
        # Check document structure
        doc = data["documents"][0]
        assert "id" in doc
        assert "title" in doc
        assert "summary" in doc
        assert "tags" in doc
        assert "storage_path" in doc
    
    def test_upload_pdf_document(self, client, mock_llm):
        """Test PDF document upload"""
        # Mock file operations
        with patch('app.agents.ingest_agent.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.mkdir.return_value = None
            
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.return_value.write.return_value = None
                
                with patch('app.agents.ingest_agent.pdfminer_extract_text') as mock_pdf:
                    mock_pdf.return_value = "Sample PDF content for testing"
                    
                    # Mock LLM calls
                    with patch('app.llm.openai_provider.OpenAIProvider') as mock_provider_class:
                        mock_provider = mock_llm
                        mock_provider_class.return_value = mock_provider
                        
                        files = {"file": ("test.pdf", b"fake_pdf_data", "application/pdf")}
                        response = client.post("/api/files/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data
        assert data["title"] == "test.pdf"
    
    def test_upload_image_document(self, client, mock_llm):
        """Test image document upload"""
        with patch('app.agents.ingest_agent.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.mkdir.return_value = None
            
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.return_value.write.return_value = None
                
                with patch('app.agents.ingest_agent.Image') as mock_image:
                    mock_img = Mock()
                    mock_img.format = "JPEG"
                    mock_img.mode = "RGB"
                    mock_img.size = (100, 100)
                    mock_image.open.return_value = mock_img
                    
                    with patch('app.agents.ingest_agent.pytesseract') as mock_ocr:
                        mock_ocr.image_to_string.return_value = "Sample text from image"
                        
                        with patch('app.llm.openai_provider.OpenAIProvider') as mock_provider_class:
                            mock_provider = mock_llm
                            mock_provider_class.return_value = mock_provider
                            
                            files = {"file": ("test.jpg", b"fake_image_data", "image/jpeg")}
                            response = client.post("/api/files/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["title"] == "test.jpg"
    
    def test_delete_document(self, client, sample_documents):
        """Test document deletion"""
        doc_id = sample_documents[0].id
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('os.remove') as mock_remove:
                response = client.delete(f"/api/documents/{doc_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Document deleted successfully"
    
    def test_get_document_content(self, client, sample_documents):
        """Test document content retrieval"""
        doc_id = sample_documents[0].id
        
        with patch('builtins.open', mock_open(read_data="Sample document content")):
            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.return_value = True
                
                response = client.get(f"/api/documents/{doc_id}/content")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content" in data
        assert data["title"] == "Software Engineer Resume"
    
    def test_download_document(self, client, sample_documents):
        """Test document download"""
        doc_id = sample_documents[0].id
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('fastapi.responses.FileResponse') as mock_file_response:
                mock_file_response.return_value = Mock()
                
                response = client.get(f"/api/documents/{doc_id}/download")
        
        assert response.status_code == 200

class TestSearchAPI:
    """Test search-related API endpoints"""
    
    def test_search_documents_with_llm(self, client, sample_documents, mock_llm):
        """Test search with LLM available"""
        with patch('app.llm.openai_provider.OpenAIProvider') as mock_provider_class:
            mock_provider = mock_llm
            mock_provider_class.return_value = mock_provider
            
            response = client.get("/api/search?query=software engineer&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert data["results"]["llm_available"] is True
        assert len(data["results"]["documents"]) > 0
    
    def test_search_documents_fallback(self, client, sample_documents):
        """Test search fallback when LLM unavailable"""
        with patch('app.llm.openai_provider.OpenAIProvider') as mock_provider_class:
            mock_provider = Mock()
            mock_provider.is_available.return_value = False
            mock_provider_class.return_value = mock_provider
            
            response = client.get("/api/search?query=software engineer&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["results"]["llm_available"] is False
        assert len(data["results"]["documents"]) > 0
    
    def test_search_with_postprocessing(self, client, sample_documents, mock_llm):
        """Test search with postprocessing"""
        with patch('app.llm.openai_provider.OpenAIProvider') as mock_provider_class:
            mock_provider = mock_llm
            mock_provider_class.return_value = mock_provider
            
            with patch('builtins.open', mock_open(read_data="Sample document content")):
                with patch('pathlib.Path.exists') as mock_exists:
                    mock_exists.return_value = True
                    
                    response = client.get("/api/search?query=software engineer&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "processed_content" in data["results"]

class TestHealthAPI:
    """Test health and utility endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "ArgosOS" in data["message"]

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        files = {"file": ("test.txt", b"content", "text/plain")}
        response = client.post("/api/files/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Unsupported file type" in data["error"]
    
    def test_upload_file_too_large(self, client):
        """Test upload with file too large"""
        # Create a large file (simulate)
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        
        files = {"file": ("large.pdf", large_content, "application/pdf")}
        response = client.post("/api/files/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "File too large" in data["error"]
    
    def test_search_empty_query(self, client):
        """Test search with empty query"""
        response = client.get("/api/search?query=")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]["documents"]) == 0
    
    def test_get_nonexistent_document(self, client):
        """Test getting non-existent document"""
        response = client.get("/api/documents/nonexistent/content")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Document not found" in data["error"]
    
    def test_delete_nonexistent_document(self, client):
        """Test deleting non-existent document"""
        response = client.delete("/api/documents/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Document not found" in data["error"]

# Import get_db for dependency override
from app.db.engine import get_db

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
