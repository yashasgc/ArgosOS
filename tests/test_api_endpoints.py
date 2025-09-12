"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app

client = TestClient(app)

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

class TestFileUploadEndpoints:
    """Test file upload endpoints"""
    
    def test_upload_valid_file(self):
        """Test uploading a valid file"""
        with patch('app.main.get_ingest_agent') as mock_get_agent:
            # Mock the ingest agent
            mock_agent = Mock()
            mock_document = Mock()
            mock_document.id = "test-id"
            mock_document.title = "test.txt"
            mock_document.summary = "Test summary"
            mock_document.mime_type = "text/plain"
            mock_document.size_bytes = 10
            mock_document.created_at = 1234567890
            mock_document.tags = []
            
            mock_agent.ingest_file.return_value = (mock_document, [])
            mock_get_agent.return_value = mock_agent
            
            response = client.post(
                "/api/files/upload",
                files={"file": ("test.txt", b"test content", "text/plain")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["document"]["title"] == "test.txt"
    
    def test_upload_invalid_file_type(self):
        """Test uploading invalid file type"""
        response = client.post(
            "/api/files/upload",
            files={"file": ("test.exe", b"content", "application/x-executable")}
        )
        
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]
    
    def test_upload_missing_filename(self):
        """Test uploading file without filename"""
        response = client.post(
            "/api/files/upload",
            files={"file": ("", b"content", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "No filename provided" in response.json()["detail"]

class TestSearchEndpoints:
    """Test search endpoints"""
    
    def test_search_documents(self):
        """Test document search"""
        with patch('app.main.get_retrieval_agent') as mock_get_agent:
            # Mock the retrieval agent
            mock_agent = Mock()
            mock_agent.search.return_value = []
            mock_get_agent.return_value = mock_agent
            
            response = client.get("/api/search?query=test")
            assert response.status_code == 200
    
    def test_search_with_limit(self):
        """Test search with custom limit"""
        with patch('app.main.get_retrieval_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.search.return_value = []
            mock_get_agent.return_value = mock_agent
            
            response = client.get("/api/search?query=test&limit=5")
            assert response.status_code == 200

class TestDocumentsEndpoints:
    """Test documents endpoints"""
    
    def test_get_documents(self):
        """Test getting all documents"""
        with patch('app.main.DocumentCRUD.get_all') as mock_get_all:
            mock_get_all.return_value = []
            
            response = client.get("/api/documents")
            assert response.status_code == 200
    
    def test_get_document_by_id(self):
        """Test getting document by ID"""
        with patch('app.main.DocumentCRUD.get_by_id') as mock_get_by_id:
            mock_document = Mock()
            mock_document.id = "test-id"
            mock_document.title = "test.txt"
            mock_get_by_id.return_value = mock_document
            
            response = client.get("/api/documents/test-id")
            assert response.status_code == 200
    
    def test_get_document_not_found(self):
        """Test getting non-existent document"""
        with patch('app.main.DocumentCRUD.get_by_id') as mock_get_by_id:
            mock_get_by_id.return_value = None
            
            response = client.get("/api/documents/non-existent")
            assert response.status_code == 404

class TestTagsEndpoints:
    """Test tags endpoints"""
    
    def test_get_tags(self):
        """Test getting all tags"""
        with patch('app.main.TagCRUD.get_all') as mock_get_all:
            mock_get_all.return_value = []
            
            response = client.get("/api/tags")
            assert response.status_code == 200
    
    def test_get_documents_by_tag(self):
        """Test getting documents by tag"""
        with patch('app.main.TagCRUD.get_documents_by_tag') as mock_get_docs:
            mock_get_docs.return_value = []
            
            response = client.get("/api/tags/test-tag/documents")
            assert response.status_code == 200

class TestErrorHandling:
    """Test error handling"""
    
    def test_internal_server_error(self):
        """Test internal server error handling"""
        with patch('app.main.get_ingest_agent') as mock_get_agent:
            mock_get_agent.side_effect = Exception("Test error")
            
            response = client.post(
                "/api/files/upload",
                files={"file": ("test.txt", b"content", "text/plain")}
            )
            
            assert response.status_code == 200  # Returns error in response body
            data = response.json()
            assert data["success"] is False
            assert "Upload failed" in data["error"]
