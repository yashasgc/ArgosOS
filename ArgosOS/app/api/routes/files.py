import mimetypes
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.crud import DocumentCRUD, TagCRUD
from app.db.engine import get_db
from app.db.schemas import DocumentCreate, DocumentResponse
from app.files.storage import FileStorage
from app.files.extractors import TextExtractor
from app.llm.provider import DisabledLLMProvider, LLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.utils.hash import compute_bytes_hash
from app.utils.time import get_epoch_ms

router = APIRouter()

# Initialize LLM provider
def get_llm_provider():
    if settings.llm_enabled and settings.openai_api_key:
        return OpenAIProvider()
    return DisabledLLMProvider()


@router.post("/files", response_model=DocumentResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider)
):
    """Upload and process a file"""
    
    # Read file data
    file_data = await file.read()
    if not file_data:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Compute content hash
    content_hash = compute_bytes_hash(file_data)
    
    # Check if file already exists (deduplication)
    existing_doc = DocumentCRUD.get_by_hash(db, content_hash)
    if existing_doc:
        return DocumentResponse(
            id=existing_doc.id,
            title=existing_doc.title,
            tags=[tag.name for tag in existing_doc.tags],
            summary=existing_doc.summary
        )
    
    # Determine MIME type
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    
    # Check if MIME type is supported
    supported_types = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/markdown',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/gif',
        'image/bmp'
    ]
    
    if mime_type not in supported_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {mime_type}. Supported types: {', '.join(supported_types)}"
        )
    
    # Store file
    storage = FileStorage()
    storage_path = storage.store_file(file_data, content_hash)
    
    # Extract text
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_data)
        temp_file_path = Path(temp_file.name)
    
    try:
        extracted_text = TextExtractor.extract_text(temp_file_path, mime_type)
    finally:
        temp_file_path.unlink()  # Clean up temp file
    
    # Generate summary and tags if LLM is available
    summary = ""
    tags = []
    
    if extracted_text and llm_provider.is_available():
        summary = llm_provider.summarize(extracted_text)
        tags = llm_provider.generate_tags(extracted_text)
    
    # Create document record
    document_data = DocumentCreate(
        title=file.filename,
        mime_type=mime_type,
        size_bytes=len(file_data),
        content_hash=content_hash,
        storage_path=storage_path,
        summary=summary,
        created_at=get_epoch_ms(),
        imported_at=get_epoch_ms()
    )
    
    document = DocumentCRUD.create(db, document_data)
    
    # Add tags to document
    if tags:
        TagCRUD.add_to_document(db, document.id, tags)
        # Refresh document to get updated tags
        document = DocumentCRUD.get_by_id(db, document.id)
    
    return DocumentResponse(
        id=document.id,
        title=document.title,
        tags=[tag.name for tag in document.tags],
        summary=document.summary
    )
