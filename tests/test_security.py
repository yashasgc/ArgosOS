"""
Security tests for ArgosOS backend
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.validation import FileValidator, ContentValidator, APIKeyValidator

client = TestClient(app)

class TestSecurityValidation:
    """Test security validation functions"""
    
    def test_validate_filename_good_cases(self):
        """Test valid filenames"""
        valid_filenames = [
            "document.pdf",
            "image.jpg",
            "file_name.txt",
            "test-file.docx",
            "a" * 100  # Long but valid
        ]
        
        for filename in valid_filenames:
            is_valid, _ = FileValidator.validate_filename(filename)
            assert is_valid, f"Should accept: {filename}"
    
    def test_validate_filename_bad_cases(self):
        """Test invalid filenames"""
        invalid_filenames = [
            "",  # Empty
            None,  # None
            "../file.pdf",  # Path traversal
            "file/name.pdf",  # Path separator
            "file\\name.pdf",  # Windows path separator
            "file<name.pdf",  # Dangerous character
            "file>name.pdf",  # Dangerous character
            "file:name.pdf",  # Dangerous character
            "file\"name.pdf",  # Dangerous character
            "file|name.pdf",  # Dangerous character
            "file?name.pdf",  # Dangerous character
            "file*name.pdf",  # Dangerous character
            "a" * 300,  # Too long
        ]
        
        for filename in invalid_filenames:
            if filename is not None:
                is_valid, _ = FileValidator.validate_filename(filename)
                assert not is_valid, f"Should reject: {filename}"
    
    def test_validate_file_type(self):
        """Test file type validation"""
        valid_types = [
            "image/jpeg",
            "image/png",
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        for mime_type in valid_types:
            assert FileValidator.validate_mime_type(mime_type), f"Should accept: {mime_type}"
        
        invalid_types = [
            "application/x-executable",
            "text/html",
            "application/zip",
            "image/svg+xml"
        ]
        
        for mime_type in invalid_types:
            assert not FileValidator.validate_mime_type(mime_type), f"Should reject: {mime_type}"
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        test_cases = [
            ("normal_file.pdf", "normal_file.pdf"),
            ("file<name.pdf", "file_name.pdf"),
            ("file>name.pdf", "file_name.pdf"),
            ("file:name.pdf", "file_name.pdf"),
            ("file/name.pdf", "file_name.pdf"),
            ("file\\name.pdf", "file_name.pdf"),
            ("file|name.pdf", "file_name.pdf"),
            ("file?name.pdf", "file_name.pdf"),
            ("file*name.pdf", "file_name.pdf"),
            ("file\"name.pdf", "file_name.pdf"),
            ("file___name.pdf", "file_name.pdf"),  # Multiple underscores
            ("___file.pdf", "file.pdf"),  # Leading underscores
            ("file.pdf___", "file.pdf"),  # Trailing underscores
            ("", "file_12345678"),  # Empty filename
        ]
        
        for input_name, expected in test_cases:
            result = FileValidator.sanitize_filename(input_name)
            assert result == expected, f"Input: {input_name}, Expected: {expected}, Got: {result}"

class TestFileUploadSecurity:
    """Test file upload security"""
    
    def test_upload_no_filename(self):
        """Test upload without filename"""
        response = client.post("/api/files/upload", files={"file": ("", b"content")})
        assert response.status_code == 400
        assert "No filename provided" in response.json()["detail"]
    
    def test_upload_invalid_filename(self):
        """Test upload with invalid filename"""
        response = client.post("/api/files/upload", files={"file": ("../etc/passwd", b"content", "text/plain")})
        assert response.status_code == 400
        assert "Invalid filename" in response.json()["detail"]
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        response = client.post("/api/files/upload", files={"file": ("test.exe", b"content", "application/x-executable")})
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]
    
    def test_upload_large_file(self):
        """Test upload with file too large"""
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        response = client.post("/api/files/upload", files={"file": ("large.txt", large_content, "text/plain")})
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]

class TestAPIKeySecurity:
    """Test API key security"""
    
    def test_api_key_status_no_exposure(self):
        """Test that API key status doesn't expose the actual key"""
        response = client.get("/v1/api-key/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "encrypted" in data
        assert "services" in data
        
        # Should not contain the actual API key
        response_text = response.text
        assert "sk-" not in response_text  # OpenAI keys start with sk-
    
    def test_api_key_storage(self):
        """Test API key storage and retrieval"""
        test_key = "sk-test123456789"
        
        # Store API key
        response = client.post("/v1/api-key", json={"api_key": test_key, "service": "openai"})
        assert response.status_code == 200
        assert response.json()["encrypted"] is True
        
        # Check status
        response = client.get("/v1/api-key/status")
        assert response.status_code == 200
        assert response.json()["configured"] is True
        
        # Clear API key
        response = client.delete("/v1/api-key")
        assert response.status_code == 200
        
        # Check status after clearing
        response = client.get("/v1/api-key/status")
        assert response.status_code == 200
        assert response.json()["configured"] is False

class TestCORSecurity:
    """Test CORS security"""
    
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = client.options("/api/files/upload")
        assert response.status_code == 200
        
        # Check that CORS headers are present
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers
