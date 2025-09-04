import io
from pathlib import Path
from typing import Optional

from PIL import Image
import pytesseract
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from docx import Document


class TextExtractor:
    """Extract text from various file types"""
    
    @staticmethod
    def extract_from_pdf(file_path: Path) -> Optional[str]:
        """Extract text from PDF using pdfminer.six"""
        try:
            output = io.StringIO()
            extract_text_to_fp(
                open(file_path, 'rb'),
                output,
                laparams=LAParams(),
                output_type='text'
            )
            return output.getvalue()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None
    
    @staticmethod
    def extract_from_docx(file_path: Path) -> Optional[str]:
        """Extract text from DOCX using python-docx"""
        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
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
        """Main extraction method that routes to appropriate extractor"""
        if mime_type == 'application/pdf':
            return TextExtractor.extract_from_pdf(file_path)
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return TextExtractor.extract_from_docx(file_path)
        elif mime_type in ['text/plain', 'text/markdown']:
            return TextExtractor.extract_from_txt(file_path)
        elif mime_type.startswith('image/'):
            return TextExtractor.extract_from_image(file_path)
        else:
            print(f"Unsupported mime type: {mime_type}")
            return None

