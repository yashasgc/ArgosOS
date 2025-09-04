import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os

from app.main import app
from app.db.engine import get_db
from app.files.storage import FileStorage
from app.llm.provider import DisabledLLMProvider

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session"""
    with patch("app.api.routes.files.get_db") as mock:
        yield mock


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider"""
    with patch("app.api.routes.files.get_llm_provider") as mock:
        mock.return_value = DisabledLLMProvider()
        yield mock


@pytest.fixture
def mock_file_storage():
    """Mock file storage"""
    with patch("app.files.storage.FileStorage") as mock:
        mock_instance = MagicMock()
        mock_instance.store_file.return_value = "/data/blobs/ab/test_hash"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_text_extractor():
    """Mock text extractor"""
    with patch("app.files.extractors.TextExtractor") as mock:
        mock.extract_text.return_value = "This is test content"
        yield mock


def test_upload_file_success(mock_db, mock_llm_provider, mock_file_storage, mock_text_extractor):
    """Test successful file upload"""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
        temp_file.write(b"This is test content")
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                "/v1/files",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "test.txt"
        assert data["tags"] == []
        assert data["summary"] == ""
        
    finally:
        os.unlink(temp_file_path)


def test_upload_file_empty():
    """Test upload of empty file"""
    response = client.post(
        "/v1/files",
        files={"file": ("empty.txt", b"", "text/plain")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]


def test_upload_unsupported_file_type():
    """Test upload of unsupported file type"""
    response = client.post(
        "/v1/files",
        files={"file": ("test.exe", b"binary data", "application/x-executable")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_pdf_file(mock_db, mock_llm_provider, mock_file_storage, mock_text_extractor):
    """Test PDF file upload"""
    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(b"%PDF-1.4\nThis is a test PDF")
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                "/v1/files",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "test.pdf"
        
    finally:
        os.unlink(temp_file_path)


def test_upload_docx_file(mock_db, mock_llm_provider, mock_file_storage, mock_text_extractor):
    """Test DOCX file upload"""
    # Create a temporary DOCX file (simplified)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file.write(b"PK\x03\x04")  # ZIP header for DOCX
        temp_file_path = temp_file.name
    
    try:
        with open(temp_file_path, "rb") as f:
            response = client.post(
                "/v1/files",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "test.docx"
        
    finally:
        os.unlink(temp_file_path)



