import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session"""
    with patch("app.api.routes.documents.get_db") as mock:
        yield mock


def test_get_document_success(mock_db):
    """Test successful document retrieval"""
    # Mock document data
    mock_document = MagicMock()
    mock_document.id = "test-uuid"
    mock_document.title = "Test Document"
    mock_document.summary = "Test summary"
    mock_document.tags = [MagicMock(name="test-tag")]
    
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_document
    
    response = client.get("/v1/documents/test-uuid")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-uuid"
    assert data["title"] == "Test Document"
    assert data["tags"] == ["test-tag"]
    assert data["summary"] == "Test summary"


def test_get_document_not_found(mock_db):
    """Test document retrieval when document doesn't exist"""
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    response = client.get("/v1/documents/nonexistent-uuid")
    
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


def test_get_documents_with_filters(mock_db):
    """Test document retrieval with filters"""
    # Mock documents data
    mock_document1 = MagicMock()
    mock_document1.id = "uuid1"
    mock_document1.title = "Document 1"
    mock_document1.summary = "Summary 1"
    mock_document1.tags = [MagicMock(name="tag1")]
    
    mock_document2 = MagicMock()
    mock_document2.id = "uuid2"
    mock_document2.title = "Document 2"
    mock_document2.summary = "Summary 2"
    mock_document2.tags = [MagicMock(name="tag2")]
    
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.join.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_document1, mock_document2]
    
    response = client.get("/v1/documents?tags_any=tag1&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "uuid1"
    assert data[1]["id"] == "uuid2"


def test_get_documents_pagination(mock_db):
    """Test document retrieval with pagination"""
    mock_document = MagicMock()
    mock_document.id = "uuid1"
    mock_document.title = "Document 1"
    mock_document.summary = "Summary 1"
    mock_document.tags = []
    
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_document]
    
    response = client.get("/v1/documents?skip=5&limit=1")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_documents_title_filter(mock_db):
    """Test document retrieval with title filter"""
    mock_document = MagicMock()
    mock_document.id = "uuid1"
    mock_document.title = "Test Document"
    mock_document.summary = "Summary"
    mock_document.tags = []
    
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_document]
    
    response = client.get("/v1/documents?title_like=Test")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Test" in data[0]["title"]

