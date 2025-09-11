import io
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image
import pytesseract
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from docx import Document
import fitz  # PyMuPDF for PDF to image conversion


class TextExtractor:
    """Extract text from various file types"""
    
    @staticmethod
    def extract_from_pdf(file_path: Path) -> Optional[str]:
        """Extract text from PDF using OCR (convert PDF to images first)"""
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(file_path)
            text_content = []
            
            # Convert each page to image and extract text via OCR
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Extract text using OCR
                page_text = pytesseract.image_to_string(image)
                if page_text.strip():
                    text_content.append(page_text)
            
            pdf_document.close()
            return '\n'.join(text_content) if text_content else None
            
        except Exception as e:
            print(f"Error extracting text from PDF via OCR: {e}")
            return None
    
    @staticmethod
    def extract_from_docx(file_path: Path) -> Optional[str]:
        """Extract text from DOCX using OCR (convert to PDF first, then OCR)"""
        try:
            # First try to extract text directly (faster)
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            
            direct_text = '\n'.join(text).strip()
            if direct_text:
                return direct_text
            
            # If no text found, convert to PDF and use OCR
            # This is a fallback for scanned documents saved as DOCX
            return TextExtractor._extract_from_docx_via_ocr(file_path)
            
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return None
    
    @staticmethod
    def _extract_from_docx_via_ocr(file_path: Path) -> Optional[str]:
        """Fallback: Convert DOCX to PDF then use OCR"""
        try:
            # Convert DOCX to PDF using python-docx2pdf or similar
            # For now, we'll use a simple approach with docx2pdf
            import subprocess
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf_path = temp_pdf.name
            
            # Convert DOCX to PDF (requires docx2pdf package)
            try:
                subprocess.run(['docx2pdf', str(file_path), temp_pdf_path], 
                             check=True, capture_output=True)
                
                # Now extract text from PDF using OCR
                result = TextExtractor.extract_from_pdf(Path(temp_pdf_path))
                
                # Clean up temp file
                Path(temp_pdf_path).unlink(missing_ok=True)
                
                return result
            except (subprocess.CalledProcessError, FileNotFoundError):
                # If docx2pdf is not available, fall back to direct extraction
                print("docx2pdf not available, using direct text extraction")
                return None
                
        except Exception as e:
            print(f"Error in DOCX OCR fallback: {e}")
            return None
    
    @staticmethod
    def extract_from_txt(file_path: Path) -> Optional[str]:
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return None
    
    @staticmethod
    def extract_from_image(file_path: Path) -> Optional[str]:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return None
    
    @staticmethod
    def extract_text(file_path: Path, mime_type: str) -> Optional[str]:
        """Main extraction method that uses OCR for all document types"""
        print(f"Extracting text from {file_path} (MIME: {mime_type}) using OCR...")
        
        if mime_type == 'application/pdf':
            return TextExtractor.extract_from_pdf(file_path)
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return TextExtractor.extract_from_docx(file_path)
        elif mime_type in ['text/plain', 'text/markdown']:
            # For text files, we can read directly (no OCR needed)
            return TextExtractor.extract_from_txt(file_path)
        elif mime_type.startswith('image/'):
            return TextExtractor.extract_from_image(file_path)
        else:
            print(f"Unsupported mime type: {mime_type}")
            return None

