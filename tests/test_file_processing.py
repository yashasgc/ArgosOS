"""
Tests for file processing functionality
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.agents.ingest_agent import IngestAgent
from app.llm.provider import DisabledLLMProvider

class TestIngestAgent:
    """Test IngestAgent functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.llm_provider = DisabledLLMProvider()
        self.agent = IngestAgent(self.llm_provider)
        self.mock_db = Mock(spec=Session)
    
    def test_supported_types(self):
        """Test supported file types"""
        assert self.agent.is_supported("image/jpeg")
        assert self.agent.is_supported("application/pdf")
        assert self.agent.is_supported("text/plain")
        assert not self.agent.is_supported("application/x-executable")
    
    def test_file_size_validation(self):
        """Test file size validation"""
        # Test normal size
        normal_content = b"test content"
        document, errors = self.agent.ingest_file(
            normal_content, "test.txt", "text/plain", self.mock_db
        )
        assert "File too large" not in errors
        
        # Test oversized file
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        document, errors = self.agent.ingest_file(
            large_content, "large.txt", "text/plain", self.mock_db
        )
        assert document is None
        assert any("File too large" in error for error in errors)
    
    def test_text_extraction(self):
        """Test text extraction from different file types"""
        # Test plain text
        text_content = b"Hello, world! This is a test document."
        result = self.agent._extract_text(text_content, "text/plain", "test.txt")
        assert "Hello, world!" in result
        
        # Test unsupported type
        result = self.agent._extract_text(b"content", "application/x-unknown", "test.unknown")
        assert result == ""
    
    @patch('app.agents.ingest_agent.TESSERACT_AVAILABLE', True)
    @patch('app.agents.ingest_agent.pytesseract')
    @patch('app.agents.ingest_agent.Image')
    def test_ocr_extraction(self, mock_image, mock_tesseract):
        """Test OCR text extraction"""
        # Mock OCR response
        mock_tesseract.image_to_string.return_value = "Extracted text from image"
        
        # Create a mock image
        mock_img = Mock()
        mock_image.open.return_value = mock_img
        
        # Test OCR extraction
        result = self.agent._extract_with_ocr(b"fake_image_data", "image/jpeg", "test.jpg")
        assert "Extracted text from image" in result
        mock_tesseract.image_to_string.assert_called_once()
    
    @patch('app.agents.ingest_agent.PYMUPDF_AVAILABLE', True)
    @patch('app.agents.ingest_agent.fitz')
    def test_pdf_extraction_pymupdf(self, mock_fitz):
        """Test PDF text extraction with PyMuPDF"""
        # Mock PDF document
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "PDF content"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc
        
        result = self.agent._extract_from_pdf(b"fake_pdf_data", "application/pdf", "test.pdf")
        assert "PDF content" in result
    
    @patch('app.agents.ingest_agent.PDFMINER_AVAILABLE', True)
    @patch('app.agents.ingest_agent.pdfminer_extract')
    def test_pdf_extraction_pdfminer(self, mock_pdfminer):
        """Test PDF text extraction with pdfminer"""
        mock_pdfminer.return_value = "PDF content from pdfminer"
        
        result = self.agent._extract_from_pdf(b"fake_pdf_data", "application/pdf", "test.pdf")
        assert "PDF content from pdfminer" in result
    
    @patch('app.agents.ingest_agent.DOCX_AVAILABLE', True)
    @patch('app.agents.ingest_agent.DocxDocument')
    def test_docx_extraction(self, mock_docx):
        """Test DOCX text extraction"""
        # Mock DOCX document
        mock_doc = Mock()
        mock_paragraph = Mock()
        mock_paragraph.text = "DOCX content"
        mock_doc.paragraphs = [mock_paragraph]
        mock_docx.return_value = mock_doc
        
        result = self.agent._extract_from_docx(b"fake_docx_data", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "test.docx")
        assert "DOCX content" in result
    
    def test_content_hash_generation(self):
        """Test content hash generation for deduplication"""
        content1 = b"test content"
        content2 = b"test content"
        content3 = b"different content"
        
        hash1 = self.agent._generate_content_hash(content1)
        hash2 = self.agent._generate_content_hash(content2)
        hash3 = self.agent._generate_content_hash(content3)
        
        assert hash1 == hash2  # Same content should have same hash
        assert hash1 != hash3  # Different content should have different hash
        assert len(hash1) == 64  # SHA-256 produces 64 character hex string

class TestFileValidation:
    """Test file validation functions"""
    
    def test_mime_type_detection(self):
        """Test MIME type detection"""
        agent = IngestAgent(DisabledLLMProvider())
        
        # Test various file extensions
        assert agent._get_mime_type("test.jpg") == "image/jpeg"
        assert agent._get_mime_type("test.png") == "image/png"
        assert agent._get_mime_type("test.pdf") == "application/pdf"
        assert agent._get_mime_type("test.txt") == "text/plain"
        assert agent._get_mime_type("test.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        agent = IngestAgent(DisabledLLMProvider())
        
        # Test various problematic filenames
        assert agent._sanitize_filename("normal_file.pdf") == "normal_file.pdf"
        assert agent._sanitize_filename("file<name.pdf") == "file_name.pdf"
        assert agent._sanitize_filename("file/name.pdf") == "file_name.pdf"
        assert agent._sanitize_filename("file\\name.pdf") == "file_name.pdf"
        assert agent._sanitize_filename("") == "file_12345678"  # Should generate a name
