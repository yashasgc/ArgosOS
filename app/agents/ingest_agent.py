"""
IngestAgent - Handles file ingestion, text extraction, and AI processing
"""
import hashlib
import mimetypes
import time
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.models import Document, Tag
from app.db.crud import DocumentCRUD, TagCRUD
from app.db.schemas import DocumentCreate
from app.files.extractors import TextExtractor
from app.llm.provider import LLMProvider
from app.utils.hash import compute_file_hash


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
        self.text_extractor = TextExtractor()
    
    def ingest_file(
        self, 
        file_path: Path, 
        db: Session,
        title: Optional[str] = None
    ) -> Tuple[Optional[Document], List[str]]:
        """
        Ingest a file: extract text, generate tags and summary, store in database.
        
        Args:
            file_path: Path to the file to ingest
            db: Database session
            title: Optional custom title for the document
            
        Returns:
            Tuple of (Document object or None if failed, list of error messages)
        """
        errors = []
        
        # Input validation
        if not file_path:
            errors.append("File path cannot be None")
            return None, errors
        
        if not isinstance(file_path, Path):
            try:
                file_path = Path(file_path)
            except (TypeError, ValueError) as e:
                errors.append(f"Invalid file path: {e}")
                return None, errors
        
        try:
            # Validate file exists
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                return None, errors
            
            # Get file metadata
            file_size = file_path.stat().st_size
            
            # File size validation (100MB limit)
            MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
            if file_size > MAX_FILE_SIZE:
                errors.append(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE} bytes)")
                return None, errors
            
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            if not mime_type:
                errors.append(f"Could not determine MIME type for {file_path}")
                return None, errors
            
            # Calculate content hash for deduplication
            content_hash = compute_file_hash(file_path)
            
            # Check if document already exists
            existing_doc = DocumentCRUD.get_by_hash(db, content_hash)
            if existing_doc:
                errors.append(f"Document with this content already exists: {existing_doc.title}")
                return existing_doc, errors
            
            # Extract text from file using OCR
            print(f"Extracting text from {file_path} using OCR...")
            extracted_text = self.text_extractor.extract_text(file_path, mime_type)
            if not extracted_text:
                errors.append(f"Could not extract text from {file_path} using OCR")
                return None, errors
            
            print(f"Successfully extracted {len(extracted_text)} characters using OCR")
            
            # Generate title if not provided
            if not title:
                title = file_path.stem
            
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
            
            # Create document record
            current_time = int(time.time() * 1000)
            document_data = DocumentCreate(
                title=title,
                mime_type=mime_type,
                size_bytes=file_size,
                content_hash=content_hash,
                storage_path=str(file_path),
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
            
            return document, errors
            
        except Exception as e:
            errors.append(f"Unexpected error during ingestion: {str(e)}")
            return None, errors
    
    def ingest_multiple_files(
        self, 
        file_paths: List[Path], 
        db: Session
    ) -> Tuple[List[Document], List[str]]:
        """
        Ingest multiple files in batch.
        
        Args:
            file_paths: List of file paths to ingest
            db: Database session
            
        Returns:
            Tuple of (list of successfully ingested documents, list of all errors)
        """
        documents = []
        all_errors = []
        
        for file_path in file_paths:
            doc, errors = self.ingest_file(file_path, db)
            if doc:
                documents.append(doc)
            all_errors.extend(errors)
        
        return documents, all_errors
    
    def reprocess_document(
        self, 
        document_id: str, 
        db: Session
    ) -> Tuple[bool, List[str]]:
        """
        Reprocess an existing document to update tags and summary.
        
        Args:
            document_id: ID of the document to reprocess
            db: Database session
            
        Returns:
            Tuple of (success boolean, list of error messages)
        """
        errors = []
        
        try:
            # Get existing document
            document = DocumentCRUD.get_by_id(db, document_id)
            if not document:
                errors.append(f"Document not found: {document_id}")
                return False, errors
            
            # Read the file
            file_path = Path(document.storage_path)
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                return False, errors
            
            # Extract text again
            extracted_text = self.text_extractor.extract_text(file_path, document.mime_type)
            if not extracted_text:
                errors.append(f"Could not extract text from {file_path}")
                return False, errors
            
            # Generate new summary
            if self.llm_provider.is_available():
                try:
                    new_summary = self.llm_provider.summarize(extracted_text)
                    document.summary = new_summary
                except Exception as e:
                    errors.append(f"Failed to generate new summary: {str(e)}")
            
            # Generate new tags
            if self.llm_provider.is_available():
                try:
                    # Clear existing tags
                    document.tags.clear()
                    
                    # Generate new tags
                    tag_names = self.llm_provider.generate_tags(extracted_text)
                    if tag_names:
                        TagCRUD.add_to_document(db, document_id, tag_names)
                except Exception as e:
                    errors.append(f"Failed to generate new tags: {str(e)}")
            
            # Save changes
            db.commit()
            return True, errors
            
        except Exception as e:
            errors.append(f"Unexpected error during reprocessing: {str(e)}")
            return False, errors
    
