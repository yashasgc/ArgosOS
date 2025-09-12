"""
IngestAgent - Handles file ingestion, text extraction, and AI processing
"""
import hashlib
import time
from pathlib import Path
from typing import List, Optional, Tuple
from io import BytesIO

from sqlalchemy.orm import Session

from app.db.models import Document, Tag
from app.db.crud import DocumentCRUD, TagCRUD
from app.db.schemas import DocumentCreate
from app.llm.provider import LLMProvider

# Import OCR and text extraction libraries
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import PyMuPDF as fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    PDFMINER_AVAILABLE = True
except ImportError:

    GeneratorExit
    PDFMINER_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class IngestAgent:
    """
    Agent responsible for ingesting files, extracting text, generating tags and summaries,
    and storing everything in the database.
    """
    
    # Supported MIME types
    SUPPORTED_TYPES = {
        # Images
        'image/jpeg': 'ocr',
        'image/jpg': 'ocr', 
        'image/png': 'ocr',
        'image/gif': 'ocr',
        'image/bmp': 'ocr',
        'image/tiff': 'ocr',
        'image/webp': 'ocr',
        
        # Documents
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        
        # Text files
        'text/plain': 'text',
        'text/markdown': 'text',
        'text/csv': 'text',
    }
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the IngestAgent with an LLM provider.
        
        Args:
            llm_provider: LLM provider for generating tags and summaries
        """
        self.llm_provider = llm_provider
        self.blobs_dir = Path("./data/blobs")
        self.blobs_dir.mkdir(parents=True, exist_ok=True)
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available"""
        if not TESSERACT_AVAILABLE:
            print("Warning: pytesseract not available. OCR functionality will be limited.")
        if not PYMUPDF_AVAILABLE and not PDFMINER_AVAILABLE:
            print("Warning: No PDF libraries available. PDF processing will not work.")
        if not DOCX_AVAILABLE:
            print("Warning: python-docx not available. DOCX processing will not work.")
    
    def is_supported(self, mime_type: str) -> bool:
        """Check if the MIME type is supported for text extraction"""
        return mime_type in self.SUPPORTED_TYPES
    
    def ingest_file(
        self, 
        file_data: bytes, 
        filename: str,
        mime_type: str,
        db: Session,
        title: Optional[str] = None
    ) -> Tuple[Optional[Document], List[str]]:
        """
        Ingest a file: extract text, generate tags and summary, store in database.
        
        Args:
            file_data: Raw file data as bytes
            filename: Original filename
            mime_type: MIME type of the file
            db: Database session
            title: Optional custom title for the document
            
        Returns:
            Tuple of (Document object or None if failed, list of error messages)
        """
        errors = []
        
        # Input validation
        if not file_data:
            errors.append("File data cannot be empty")
            return None, errors
        
        if not filename:
            errors.append("Filename cannot be empty")
            return None, errors
        
        if not mime_type:
            errors.append("MIME type cannot be empty")
            return None, errors
        
        try:
            # Get file metadata
            file_size = len(file_data)
            
            # File size validation (100MB limit)
            MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
            if file_size > MAX_FILE_SIZE:
                errors.append(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE} bytes)")
                return None, errors
            
            # Calculate content hash for deduplication
            content_hash = hashlib.sha256(file_data).hexdigest()
            
            # Check if document already exists
            existing_doc = DocumentCRUD.get_by_hash(db, content_hash)
            if existing_doc:
                errors.append(f"Document with this content already exists: {existing_doc.title}")
                return existing_doc, errors
            
            # Extract text from file data
            print(f"Extracting text from {filename}...")
            extracted_text = self._extract_text(file_data, mime_type, filename)
            if not extracted_text:
                errors.append(f"Could not extract text from {filename}")
                return None, errors
            
            print(f"Successfully extracted {len(extracted_text)} characters")
            
            # Generate title if not provided
            if not title:
                title = Path(filename).stem
            
            # Generate summary using LLM
            summary = ""
            if self.llm_provider.is_available():
                try:
                    print("Generating summary using LLM...")
                    summary = self.llm_provider.summarize(extracted_text)
                    print(f"Generated summary: {summary[:100]}...")
                except Exception as e:
                    errors.append(f"Failed to generate summary: {str(e)}")
            else:
                print("LLM not available, skipping summary generation")
                errors.append("OpenAI API key not configured - summary generation skipped")
            
            # Save file to disk
            file_extension = Path(filename).suffix or '.bin'
            blob_filename = f"{content_hash}{file_extension}"
            blob_path = self.blobs_dir / blob_filename
            
            # Write file data to disk
            blob_path.write_bytes(file_data)
            print(f"File saved to: {blob_path}")
            
            # Create document record
            current_time = int(time.time() * 1000)
            document_data = DocumentCreate(
                title=title,
                mime_type=mime_type,
                size_bytes=file_size,
                content_hash=content_hash,
                storage_path=str(blob_path),  # Real file path
                summary=summary if summary else None,
                created_at=current_time,
                imported_at=current_time
            )
            
            # Save document to database
            document = DocumentCRUD.create(db, document_data)
            
            # Generate and assign tags using LLM
            tags = []
            if self.llm_provider.is_available():
                try:
                    print("Generating tags using LLM...")
                    tag_names = self.llm_provider.generate_tags(extracted_text)
                    if tag_names:
                        print(f"Generated tags: {tag_names}")
                        # Add tags to document
                        TagCRUD.add_to_document(db, document.id, tag_names)
                        tags = tag_names
                    else:
                        print("No tags generated by LLM")
                except Exception as e:
                    errors.append(f"Failed to generate tags: {str(e)}")
            else:
                print("LLM not available, skipping tag generation")
                errors.append("OpenAI API key not configured - tag generation skipped")
            
            return document, errors
            
        except Exception as e:
            errors.append(f"Unexpected error during ingestion: {str(e)}")
            return None, errors
    
    def _extract_text(self, file_data: bytes, mime_type: str, filename: str) -> Optional[str]:
        """
        Extract text from raw file data based on its MIME type
        
        Args:
            file_data: Raw file data as bytes
            mime_type: MIME type of the file
            filename: Original filename for debugging
            
        Returns:
            Extracted text or None if extraction failed
        """
        if not self.is_supported(mime_type):
            print(f"Unsupported file type: {mime_type}")
            return None
        
        extraction_method = self.SUPPORTED_TYPES[mime_type]
        
        try:
            if extraction_method == 'ocr':
                return self._extract_with_ocr(file_data)
            elif extraction_method == 'pdf':
                return self._extract_from_pdf(file_data)
            elif extraction_method == 'docx':
                return self._extract_from_docx(file_data)
            elif extraction_method == 'text':
                return self._extract_from_text(file_data)
            else:
                print(f"Unknown extraction method: {extraction_method}")
                return None
                
        except Exception as e:
            print(f"Error extracting text from {filename}: {e}")
            return None
    
    def _extract_with_ocr(self, file_data: bytes) -> Optional[str]:
        """Extract text from image bytes using OCR"""
        if not TESSERACT_AVAILABLE:
            print("OCR not available - pytesseract not installed")
            return None
        
        try:
            # Open image from bytes
            image = Image.open(BytesIO(file_data))
            
            # Convert to RGB if necessary (for some image formats)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image, lang='eng')
            
            # Clean up the text
            text = text.strip()
            
            if not text:
                print(f"No text found in image")
                return None
            
            print(f"OCR extracted {len(text)} characters from image")
            return text
            
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return None
    
    def _extract_from_pdf(self, file_data: bytes) -> Optional[str]:
        """Extract text from PDF bytes"""
        # Try PyMuPDF first (faster)
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(stream=file_data, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                
                if text.strip():
                    print(f"PyMuPDF extracted {len(text)} characters from PDF")
                    return text.strip()
            except Exception as e:
                print(f"PyMuPDF extraction failed: {e}")
        
        # Fallback to pdfminer
        if PDFMINER_AVAILABLE:
            try:
                text = pdfminer_extract(BytesIO(file_data))
                if text.strip():
                    print(f"pdfminer extracted {len(text)} characters from PDF")
                    return text.strip()
            except Exception as e:
                print(f"pdfminer extraction failed: {e}")
        
        print(f"No PDF extraction method available")
        return None
    
    def _extract_from_docx(self, file_data: bytes) -> Optional[str]:
        """Extract text from DOCX bytes"""
        if not DOCX_AVAILABLE:
            print("DOCX extraction not available - python-docx not installed")
            return None
        
        try:
            doc = DocxDocument(BytesIO(file_data))
            text = ""
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + " "
                    text += "\n"
            
            text = text.strip()
            if text:
                print(f"DOCX extracted {len(text)} characters")
                return text
            else:
                print(f"No text found in DOCX")
                return None
                
        except Exception as e:
            print(f"DOCX extraction failed: {e}")
            return None
    
    def _extract_from_text(self, file_data: bytes) -> Optional[str]:
        """Extract text from raw text bytes"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text = file_data.decode(encoding)
                    
                    if text.strip():
                        print(f"Text extracted {len(text)} characters using {encoding}")
                        return text.strip()
                        
                except UnicodeDecodeError:
                    continue
            
            print(f"Could not decode text data")
            return None
            
        except Exception as e:
            print(f"Text extraction failed: {e}")
            return None
    
    
