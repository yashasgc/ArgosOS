"""
Text extraction utilities for various file formats
"""
import logging
from typing import Optional
from io import BytesIO

logger = logging.getLogger(__name__)

# Import OCR and text extraction libraries
try:
    import pytesseract
    from PIL import Image, ImageEnhance
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from app.constants import TEXT_ENCODINGS


class TextExtractor:
    """Handles text extraction from various file formats"""
    
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
    
    def __init__(self, llm_provider=None):
        """Initialize the text extractor with optional LLM provider for Vision API"""
        self.llm_provider = llm_provider
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available"""
        if not TESSERACT_AVAILABLE:
            logger.warning("pytesseract not available. OCR functionality will be limited.")
        if not PYMUPDF_AVAILABLE and not PDFMINER_AVAILABLE:
            logger.warning("No PDF libraries available. PDF processing will not work.")
        if not DOCX_AVAILABLE:
            logger.warning("python-docx not available. DOCX processing will not work.")
    
    def is_supported(self, mime_type: str) -> bool:
        """Check if the MIME type is supported for text extraction"""
        return mime_type in self.SUPPORTED_TYPES
    
    def extract_text(self, file_data: bytes, mime_type: str, filename: str) -> Optional[str]:
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
            logger.warning(f"Unsupported file type: {mime_type}")
            return None
        
        extraction_method = self.SUPPORTED_TYPES[mime_type]
        
        try:
            if extraction_method == 'ocr':
                # Try Vision API first for images, fallback to OCR
                if mime_type.startswith('image/'):
                    extracted_text = self._extract_with_vision_api(file_data, filename)
                    if not extracted_text:
                        logger.warning("Vision API failed, trying OCR fallback...")
                        extracted_text = self._extract_with_ocr(file_data)
                    return extracted_text
                else:
                    return self._extract_with_ocr(file_data)
            elif extraction_method == 'pdf':
                return self._extract_from_pdf(file_data)
            elif extraction_method == 'docx':
                return self._extract_from_docx(file_data)
            elif extraction_method == 'text':
                return self._extract_from_text(file_data)
            else:
                logger.error(f"Unknown extraction method: {extraction_method}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return None
    
    def _extract_with_vision_api(self, file_data: bytes, filename: str) -> Optional[str]:
        """Extract text from image using OpenAI Vision API"""
        if not self.llm_provider or not hasattr(self.llm_provider, 'extract_text_from_image'):
            return None
        
        try:
            return self.llm_provider.extract_text_from_image(file_data, filename)
        except Exception as e:
            logger.error(f"Vision API extraction failed: {e}")
            return None
    
    def _extract_with_ocr(self, file_data: bytes) -> Optional[str]:
        """Extract text from image using OCR"""
        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract not available for OCR")
            return None
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(file_data))
            
            # Handle MPO format by converting to JPEG
            if image.format == "MPO":
                logger.info("Converting MPO to JPEG for OCR processing")
                # Convert to RGB and then to JPEG
                if image.mode != "RGB":
                    image = image.convert("RGB")
                # Save as JPEG in memory
                jpeg_buffer = BytesIO()
                image.save(jpeg_buffer, format="JPEG")
                image = Image.open(jpeg_buffer)
            
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast for better OCR
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Try multiple PSM modes for better text recognition
            psm_modes = [3, 4, 6, 7, 8]
            best_text = ""
            
            for psm in psm_modes:
                try:
                    config = f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%^&*()_+-=[]{{}}|;:,.<>?/~` '
                    text = pytesseract.image_to_string(image, config=config)
                    if len(text.strip()) > len(best_text.strip()):
                        best_text = text
                except Exception as e:
                    logger.debug(f"OCR PSM {psm} failed: {e}")
                    continue
            
            if best_text.strip():
                logger.info(f"OCR extracted {len(best_text)} characters")
                return best_text.strip()
            else:
                logger.warning("OCR failed to extract any text")
                return None
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return None
    
    def _extract_from_pdf(self, file_data: bytes) -> Optional[str]:
        """Extract text from PDF using direct text extraction (no OCR)"""
        try:
            # Try PyMuPDF first (fastest and most reliable)
            if PYMUPDF_AVAILABLE:
                try:
                    logger.info("Extracting text from PDF using PyMuPDF")
                    doc = fitz.open(stream=file_data, filetype="pdf")
                    text = ""
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        page_text = page.get_text()
                        if page_text.strip():
                            text += f"Page {page_num + 1}:\n{page_text.strip()}\n\n"
                            logger.info(f"Extracted {len(page_text)} characters from page {page_num + 1}")
                    
                    doc.close()
                    
                    if text.strip():
                        logger.info(f"PyMuPDF extracted {len(text)} total characters from PDF")
                        return text.strip()
                    else:
                        logger.warning("PyMuPDF found no text in PDF")
                except Exception as e:
                    logger.warning(f"PyMuPDF extraction failed: {e}")
            
            # Fallback to pdfminer
            if PDFMINER_AVAILABLE:
                try:
                    logger.info("Extracting text from PDF using pdfminer")
                    text = pdfminer_extract(BytesIO(file_data))
                    if text.strip():
                        logger.info(f"pdfminer extracted {len(text)} characters from PDF")
                        return text.strip()
                    else:
                        logger.warning("pdfminer found no text in PDF")
                except Exception as e:
                    logger.warning(f"pdfminer extraction failed: {e}")
            
            # If no text found with direct extraction, try OCR as last resort
            logger.warning("No text found with direct extraction, trying OCR as last resort")
            return self._extract_from_pdf_ocr_fallback(file_data)
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return None
    
    def _extract_from_pdf_ocr_fallback(self, file_data: bytes) -> Optional[str]:
        """Fallback: Extract text from PDF using OCR (for image-based PDFs)"""
        if not TESSERACT_AVAILABLE or not PYMUPDF_AVAILABLE:
            logger.warning("OCR fallback not available - missing Tesseract or PyMuPDF")
            return None
        
        try:
            logger.info("Using OCR fallback for PDF (likely image-based PDF)")
            doc = fitz.open(stream=file_data, filetype="pdf")
            
            if len(doc) == 0:
                logger.warning("No pages found in PDF")
                doc.close()
                return None
            
            # Extract text from each page using OCR
            all_text = []
            for i in range(len(doc)):
                try:
                    page = doc[i]
                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    
                    # Convert to PIL Image for OCR
                    image = Image.open(BytesIO(img_data))
                    
                    # Convert to grayscale for better OCR
                    if image.mode != 'L':
                        image = image.convert('L')
                    
                    # Enhance contrast for better OCR
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(2.0)
                    
                    # Try multiple PSM modes for better text recognition
                    psm_modes = [3, 4, 6, 7, 8]
                    best_text = ""
                    
                    for psm in psm_modes:
                        try:
                            config = f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%^&*()_+-=[]{{}}|;:,.<>?/~` '
                            text = pytesseract.image_to_string(image, config=config)
                            if len(text.strip()) > len(best_text.strip()):
                                best_text = text
                        except Exception as e:
                            logger.debug(f"OCR PSM {psm} failed for page {i+1}: {e}")
                            continue
                    
                    if best_text.strip():
                        all_text.append(f"Page {i+1}:\n{best_text.strip()}")
                        logger.info(f"OCR extracted {len(best_text)} characters from PDF page {i+1}")
                    else:
                        logger.warning(f"No text found on PDF page {i+1}")
                        
                except Exception as e:
                    logger.error(f"OCR failed for PDF page {i+1}: {e}")
                    continue
            
            doc.close()
            
            if all_text:
                combined_text = "\n\n".join(all_text)
                logger.info(f"OCR extracted {len(combined_text)} total characters from PDF")
                return combined_text
            else:
                logger.warning("OCR failed to extract any text from PDF")
                return None
                
        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {e}")
            return None
    
    def _extract_from_docx(self, file_data: bytes) -> Optional[str]:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            logger.warning("python-docx not available for DOCX processing")
            return None
        
        try:
            doc = DocxDocument(BytesIO(file_data))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            if text.strip():
                logger.info(f"Extracted {len(text)} characters from DOCX")
                return text.strip()
            else:
                logger.warning("No text found in DOCX file")
                return None
                
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return None
    
    def _extract_from_text(self, file_data: bytes) -> Optional[str]:
        """Extract text from plain text file"""
        try:
            # Try different encodings
            for encoding in TEXT_ENCODINGS:
                try:
                    text = file_data.decode(encoding)
                    if text.strip():
                        logger.info(f"Extracted {len(text)} characters from text file using {encoding}")
                        return text.strip()
                except UnicodeDecodeError:
                    continue
            
            logger.warning("Could not decode text file with any supported encoding")
            return None
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return None
