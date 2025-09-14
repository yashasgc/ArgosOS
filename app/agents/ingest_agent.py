"""
IngestAgent - Handles file ingestion, text extraction, and AI processing
"""
import logging
import time
import json
from pathlib import Path
from typing import List, Optional, Tuple
from io import BytesIO

from sqlalchemy.orm import Session

from app.db.models import Document
from app.db.crud import DocumentCRUD, TagCRUD
from app.db.schemas import DocumentCreate
from app.llm.provider import LLMProvider
from app.utils.hash import compute_bytes_hash
from app.constants import (
    MAX_FILE_SIZE, MAX_TEXT_PREVIEW, MAX_CONTENT_PREVIEW, MAX_SUMMARY_PREVIEW
)
from app.files.text_extractor import TextExtractor

logger = logging.getLogger(__name__)

# Text extraction is now handled by TextExtractor class


class IngestAgent:
    """
    Agent responsible for ingesting files, extracting text, generating tags and summaries,
    and storing everything in the database.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the IngestAgent with an LLM provider.
        
        Args:
            llm_provider: LLM provider for generating tags and summaries
        """
        self.llm_provider = llm_provider
        self.text_extractor = TextExtractor(llm_provider)
        self.blobs_dir = Path("./data/blobs")
        self.blobs_dir.mkdir(parents=True, exist_ok=True)
    
    def is_supported(self, mime_type: str) -> bool:
        """Check if the MIME type is supported for text extraction"""
        return self.text_extractor.is_supported(mime_type)
    
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
            
            # File size validation
            if file_size > MAX_FILE_SIZE:
                errors.append(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE} bytes)")
                return None, errors
            
            # Calculate content hash for deduplication
            content_hash = compute_bytes_hash(file_data)
            
            # Check if document already exists
            existing_doc = DocumentCRUD.get_by_hash(db, content_hash)
            if existing_doc:
                errors.append(f"Document with this content already exists: {existing_doc.title}")
                return existing_doc, errors
            
            # Extract text from file data
            logger.info(f"Extracting text from {filename}...")
            extracted_text = self._extract_text(file_data, mime_type, filename)
            if not extracted_text:
                logger.warning(f"Could not extract text from {filename}, creating document without content")
                extracted_text = ""  # Create empty text instead of failing
                errors.append(f"Could not extract text from {filename} - document created without content")
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters")
            
            # Generate title if not provided
            if not title:
                title = Path(filename).stem
            
            # Generate summary using LLM
            summary = ""
            if self.llm_provider.is_available():
                try:
                    logger.info("Generating summary using LLM...")
                    # For images with no extracted text, provide context about the image
                    if not extracted_text and mime_type.startswith('image/'):
                        image_context = f"Image file: {filename}, MIME type: {mime_type}, Size: {len(file_data)} bytes. This appears to be an image document that may contain text, documents, or other visual information. Please analyze the image content and provide a summary based on what you can determine from the filename and context."
                        summary = self.llm_provider.summarize(image_context)
                    else:
                        summary = self.llm_provider.summarize(extracted_text)
                    logger.info(f"Generated summary: {summary[:MAX_SUMMARY_PREVIEW]}...")
                except Exception as e:
                    errors.append(f"Failed to generate summary: {str(e)}")
            else:
                logger.warning("LLM not available, skipping summary generation")
                errors.append("OpenAI API key not configured - summary generation skipped")
            
            # Save file to disk
            file_extension = Path(filename).suffix or '.bin'
            blob_filename = f"{content_hash}{file_extension}"
            blob_path = self.blobs_dir / blob_filename
            
            # Write file data to disk
            blob_path.write_bytes(file_data)
            logger.info(f"File saved to: {blob_path}")
            
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
                    logger.info("Generating tags using LLM...")
                    # For images with no extracted text, provide context about the image
                    if not extracted_text and mime_type.startswith('image/'):
                        image_context = f"Image file: {filename}, MIME type: {mime_type}, Size: {len(file_data)} bytes. This appears to be an image document that may contain text, documents, or other visual information. Please analyze the image content and generate relevant tags based on what you can determine from the filename and context."
                        tag_names = self.llm_provider.generate_tags(image_context)
                    else:
                        tag_names = self.llm_provider.generate_tags(extracted_text)
                    
                    if tag_names:
                        logger.info(f"Generated tags: {tag_names}")
                        
                        # Add tags to tags table (get or create)
                        for tag_name in tag_names:
                            TagCRUD.get_or_create(db, tag_name)
                        
                        # Update document with tags as JSON
                        document.tags = json.dumps(tag_names)
                        db.commit()
                        tags = tag_names
                    else:
                        logger.warning("No tags generated by LLM")
                except Exception as e:
                    errors.append(f"Failed to generate tags: {str(e)}")
            else:
                logger.warning("LLM not available, skipping tag generation")
                errors.append("OpenAI API key not configured - tag generation skipped")
            
            return document, errors
            
        except Exception as e:
            errors.append(f"Unexpected error during ingestion: {str(e)}")
            return None, errors
    
    def _extract_text(self, file_data: bytes, mime_type: str, filename: str) -> Optional[str]:
        """
        Extract text from raw file data using the TextExtractor.
        
        Args:
            file_data: Raw file data as bytes
            mime_type: MIME type of the file
            filename: Original filename for debugging
            
        Returns:
            Extracted text or None if extraction failed
        """
        return self.text_extractor.extract_text(file_data, mime_type, filename)
    
