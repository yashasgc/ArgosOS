import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session"""
    with patch("app.api.routes.search.get_db") as mock:
        yield mock


def test_search_documents_success(mock_db):
    """Test successful document search"""
    # Mock search results
    mock_document1 = MagicMock()
    mock_document1.id = "uuid1"
    mock_document1.title = "Test Document 1"
    mock_document1.summary = "Test summary 1"
    mock_document1.tags = [MagicMock(name="test-tag")]
    
    mock_document2 = MagicMock()
    mock_document2.id = "uuid2"
    mock_document2.title = "Test Document 2"
    mock_document2.summary = "Test summary 2"
    mock_document2.tags = [MagicMock(name="another-tag")]
    
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_document1, mock_document2]
    
    search_query = {"q": "test"}
    response = client.post("/v1/search", json=search_query)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["documents"]) == 2
    assert data["documents"][0]["id"] == "uuid1"
    assert data["documents"][1]["id"] == "uuid2"


def test_search_documents_empty_query(mock_db):
    """Test search with empty query"""
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    
    search_query = {"q": ""}
    response = client.post("/v1/search", json=search_query)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["documents"]) == 0


def test_search_documents_with_pagination(mock_db):
    """Test search with pagination parameters"""
    mock_document = MagicMock()
    mock_document.id = "uuid1"
    mock_document.title = "Test Document"
    mock_document.summary = "Test summary"
    mock_document.tags = []
    
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_document]
    
    search_query = {"q": "test"}
    response = client.post("/v1/search?skip=5&limit=1", json=search_query)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["documents"]) == 1


def test_search_documents_no_results(mock_db):
    """Test search that returns no results"""
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    
    search_query = {"q": "nonexistent"}
    response = client.post("/v1/search", json=search_query)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["documents"]) == 0


def test_search_documents_invalid_request():
    """Test search with invalid request body"""
    response = client.post("/v1/search", json={})
    
    assert response.status_code == 422  # Validation error


def test_search_documents_missing_query_field():
    """Test search with missing query field"""
    response = client.post("/v1/search", json={"other_field": "value"})
    
    assert response.status_code == 422  # Validation error



