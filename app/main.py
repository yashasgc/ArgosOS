import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.engine import get_db
from app.agents.ingest_agent import IngestAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.postprocessor_agent import PostProcessorAgent
from app.llm.openai_provider import OpenAIProvider
from openai import OpenAI
from app.utils.validation import FileValidator, ContentValidator, APIKeyValidator, ValidationError
from app.constants import (
    MAX_DOCUMENT_LIMIT, MAX_SEARCH_LIMIT, HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND, HTTP_413_PAYLOAD_TOO_LARGE, HTTP_500_INTERNAL_SERVER_ERROR,
    ALLOWED_ORIGINS
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ArgosOS Backend",
    description="Intelligent file analysis and document management backend",
    version="1.0.0"
)

# CORS middleware - restrict to specific origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],  # Restrict headers for security
)

# Configuration file paths
CONFIG_DIR = Path("./config")
ENCRYPTED_KEY_FILE = CONFIG_DIR / "api_keys.enc"
SECRET_KEY_FILE = CONFIG_DIR / "secret.key"

# Ensure config directory exists
CONFIG_DIR.mkdir(exist_ok=True)

# Use validation utilities

# Generate or load encryption key
def get_encryption_key():
    if SECRET_KEY_FILE.exists():
        with open(SECRET_KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(SECRET_KEY_FILE, "wb") as f:
            f.write(key)
        return key

def get_fernet():
    return Fernet(get_encryption_key())

def load_encrypted_api_keys():
    """Load encrypted API keys from file"""
    if not ENCRYPTED_KEY_FILE.exists():
        return {}
    
    try:
        with open(ENCRYPTED_KEY_FILE, "rb") as f:
            encrypted_data = f.read()
        
        fernet = get_fernet()
        decrypted_data = fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    except Exception:
        return {}

def save_encrypted_api_keys(api_keys: dict):
    """Save API keys encrypted to file"""
    try:
        fernet = get_fernet()
        json_data = json.dumps(api_keys)
        encrypted_data = fernet.encrypt(json_data.encode())
        
        with open(ENCRYPTED_KEY_FILE, "wb") as f:
            f.write(encrypted_data)
        return True
    except Exception:
        return False

class ApiKeyRequest(BaseModel):
    api_key: str
    service: str = "openai"

class ApiKeyResponse(BaseModel):
    message: str
    encrypted: bool

@app.get("/")
async def root():
    return {"message": "ArgosOS Backend API", "version": "1.0.0"}

@app.post("/v1/api-key", response_model=ApiKeyResponse)
async def store_api_key(request: ApiKeyRequest):
    """Store the API key encrypted in a file"""
    try:
        # Validate API key based on service
        if request.service == "openai":
            is_valid, error = APIKeyValidator.validate_openai_key(request.api_key)
            if not is_valid:
                return ApiKeyResponse(
                    message=f"Invalid API key: {error}",
                    encrypted=False
                )
        
        # Load existing keys
        api_keys = load_encrypted_api_keys()
        
        # Store the new key
        api_keys[request.service] = request.api_key
        
        # Save encrypted keys
        if save_encrypted_api_keys(api_keys):
            return ApiKeyResponse(
                message=f"API key for {request.service} stored successfully",
                encrypted=True
            )
        else:
            return ApiKeyResponse(
                message="Failed to save encrypted API key",
                encrypted=False
            )
    except ValidationError as e:
        return ApiKeyResponse(
            message=f"Validation error: {str(e)}",
            encrypted=False
        )
    except Exception as e:
        return ApiKeyResponse(
            message=f"Failed to store API key: {str(e)}",
            encrypted=False
        )

@app.get("/v1/api-key/status")
async def get_api_key_status():
    """Check if API key is configured (without exposing the actual key)"""
    try:
        api_keys = load_encrypted_api_keys()
        openai_configured = "openai" in api_keys and bool(api_keys["openai"])
        
        return {
            "configured": openai_configured,
            "encrypted": True,
            "services": list(api_keys.keys()) if api_keys else []
        }
    except Exception as e:
        return {"configured": False, "encrypted": False, "error": f"Failed to check API key status: {str(e)}"}

@app.delete("/v1/api-key")
async def clear_api_key():
    """Clear the stored API key"""
    try:
        api_keys = load_encrypted_api_keys()
        if "openai" in api_keys:
            del api_keys["openai"]
            save_encrypted_api_keys(api_keys)
            return {"message": "OpenAI API key cleared successfully"}
        else:
            return {"message": "No OpenAI API key found"}
    except Exception as e:
        return {"message": f"Failed to clear API key: {str(e)}"}

# REMOVED: /v1/api-key/decrypt endpoint - SECURITY RISK
# API keys should never be exposed via HTTP endpoints

# Initialize agents
def get_ingest_agent():
    """Get IngestAgent instance"""
    api_keys = load_encrypted_api_keys()
    openai_key = api_keys.get("openai")
    
    if openai_key:
        llm_provider = OpenAIProvider()
        llm_provider.api_key = openai_key
        llm_provider.client = OpenAI(api_key=openai_key)  # Recreate client with correct key
    else:
        from app.llm.provider import DisabledLLMProvider
        llm_provider = DisabledLLMProvider()
    
    return IngestAgent(llm_provider)

def get_retrieval_agent():
    """Get RetrievalAgent instance"""
    api_keys = load_encrypted_api_keys()
    openai_key = api_keys.get("openai")
    
    if openai_key:
        llm_provider = OpenAIProvider()
        llm_provider.api_key = openai_key
        llm_provider.client = OpenAI(api_key=openai_key)
    else:
        from app.llm.provider import DisabledLLMProvider
        llm_provider = DisabledLLMProvider()
    
    return RetrievalAgent(llm_provider)

def get_postprocessor_agent():
    """Get PostProcessorAgent instance"""
    api_keys = load_encrypted_api_keys()
    openai_key = api_keys.get("openai")
    
    if openai_key:
        llm_provider = OpenAIProvider()
        llm_provider.api_key = openai_key
        llm_provider.client = OpenAI(api_key=openai_key)
    else:
        from app.llm.provider import DisabledLLMProvider
        llm_provider = DisabledLLMProvider()
    
    return PostProcessorAgent(llm_provider)

# File upload endpoint
@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a file with security validation"""
    try:
        # Log file upload details
        logger.info(f"Uploading file: {file.filename} ({file.content_type})")
        
        # Security validations
        is_valid, error = FileValidator.validate_filename(file.filename)
        if not is_valid:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=error)
        
        is_valid, error = FileValidator.validate_mime_type(file.content_type)
        if not is_valid:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=error)
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        is_valid, error = FileValidator.validate_file_size(content)
        if not is_valid:
            raise HTTPException(status_code=HTTP_413_PAYLOAD_TOO_LARGE, detail=error)
        
        # Additional validation for PDF files - removed overly restrictive size check
        
        # Sanitize filename
        safe_filename = FileValidator.sanitize_filename(file.filename)
        
        # Process with IngestAgent (no temporary file needed)
        ingest_agent = get_ingest_agent()
        document, errors = ingest_agent.ingest_file(content, safe_filename, file.content_type, db)
        
        if document:
            return {
                "success": True,
                "document": {
                    "id": document.id,
                    "title": document.title,
                    "summary": document.summary,
                    "mime_type": document.mime_type,
                    "size_bytes": document.size_bytes,
                    "created_at": document.created_at,
                    "tags": json.loads(document.tags) if document.tags else []
                },
                "errors": errors
            }
        else:
            return {
                "success": False,
                "error": "Failed to process file",
                "errors": errors
            }
            
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": f"Upload failed: {str(e)}"
        }

# Search endpoint
@app.get("/api/search")
async def search_documents(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search documents with query validation"""
    try:
        # Validate search query
        is_valid, error = ContentValidator.validate_search_query(query)
        if not is_valid:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=error)
        
        # Validate limit
        if limit < 1 or limit > MAX_SEARCH_LIMIT:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"Limit must be between 1 and {MAX_SEARCH_LIMIT}")
        
        retrieval_agent = get_retrieval_agent()
        results = retrieval_agent.search_documents(query, db, limit)
        
        # Check if LLM is available
        llm_available = retrieval_agent.llm_provider.is_available()
        results['llm_available'] = llm_available
        
        # If we have document IDs, process them with postprocessor agent
        if results.get('document_ids') and results['document_ids']:
            postprocessor_agent = get_postprocessor_agent()
            processed_results = postprocessor_agent.process_documents(
                query=query,
                document_ids=results['document_ids'],
                db=db
            )
            results['processed_content'] = processed_results
        
        return {
            "success": True,
            "query": query,
            "results": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }

# Get all documents
@app.get("/api/documents")
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all documents with pagination"""
    try:
        from app.db.crud import DocumentCRUD, TagCRUD
        documents = DocumentCRUD.get_all(db, skip=skip, limit=limit)
        
        return {
            "success": True,
            "documents":             [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "summary": doc.summary,
                    "mime_type": doc.mime_type,
                    "size_bytes": doc.size_bytes,
                    "created_at": doc.created_at,
                    "storage_path": doc.storage_path,
                    "tags": json.loads(doc.tags) if doc.tags else []
                }
                for doc in documents
            ],
            "total": len(documents)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get documents: {str(e)}"
        }


@app.get("/api/tags")
async def get_tags(db: Session = Depends(get_db)):
    """Get all available tags"""
    try:
        from app.db.crud import DocumentCRUD, TagCRUD
        tags = TagCRUD.get_all(db)
        
        return {
            "success": True,
            "tags": [{"id": tag.id, "name": tag.name} for tag in tags]
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch tags: {str(e)}"
        }


# Get document content
@app.get("/api/documents/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get document content by ID"""
    try:
        retrieval_agent = get_retrieval_agent()
        content = retrieval_agent.get_document_content(document_id, db)
        
        if content:
            return {
                "success": True,
                "content": content
            }
        else:
            return {
                "success": False,
                "error": "Document not found"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get document: {str(e)}"
        }

# Process documents endpoint
@app.post("/api/process")
async def process_documents(
    query: str,
    document_ids: list[str],
    db: Session = Depends(get_db)
):
    """Process documents with PostProcessorAgent"""
    try:
        postprocessor_agent = get_postprocessor_agent()
        results = postprocessor_agent.process_documents(query, document_ids, db)
        
        return {
            "success": True,
            "query": query,
            "results": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Processing failed: {str(e)}"
        }

# Get document content endpoint
@app.get("/api/documents/{document_id}/content")
async def get_document_content(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get the content of a document"""
    try:
        from app.db.crud import DocumentCRUD
        
        # Get document from database
        document = DocumentCRUD.get_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Document not found")
        
        # Read file content
        if not document.storage_path or not Path(document.storage_path).exists():
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Document file not found")
        
        with open(document.storage_path, 'rb') as f:
            content = f.read()
        
        # Return content based on file type
        if document.mime_type.startswith('text/') or document.mime_type == 'application/pdf':
            # For text files and PDFs, return extracted text content
            if document.mime_type == 'application/pdf':
                # For PDFs, we need to extract text content using the ingest agent
                try:
                    from app.agents.ingest_agent import IngestAgent
                    from app.llm.openai_provider import OpenAIProvider
                    
                    # Create a minimal ingest agent for text extraction
                    llm_provider = OpenAIProvider()
                    ingest_agent = IngestAgent(llm_provider)
                    extracted_text = ingest_agent._extract_text(content, document.mime_type, document.title)
                    
                    if extracted_text:
                        return {
                            "success": True,
                            "content": extracted_text,
                            "mime_type": document.mime_type,
                            "title": document.title
                        }
                    else:
                        # Fallback to base64 if extraction fails
                        import base64
                        return {
                            "success": True,
                            "content": base64.b64encode(content).decode('utf-8'),
                            "mime_type": document.mime_type,
                            "title": document.title,
                            "is_binary": True
                        }
                except Exception as e:
                    logger.error(f"PDF extraction error: {e}")
                    # Fallback to base64 if extraction fails
                    import base64
                    return {
                        "success": True,
                        "content": base64.b64encode(content).decode('utf-8'),
                        "mime_type": document.mime_type,
                        "title": document.title,
                        "is_binary": True
                    }
            else:
                # For text files, return decoded content
                return {
                    "success": True,
                    "content": content.decode('utf-8'),
                    "mime_type": document.mime_type,
                    "title": document.title
                }
        else:
            # For other binary files, return base64 encoded content
            import base64
            return {
                "success": True,
                "content": base64.b64encode(content).decode('utf-8'),
                "mime_type": document.mime_type,
                "title": document.title,
                "is_binary": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get document content: {str(e)}"
        }

# Download document endpoint
@app.get("/api/documents/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Download a document file"""
    try:
        from app.db.crud import DocumentCRUD
        from fastapi.responses import FileResponse
        
        # Get document from database
        document = DocumentCRUD.get_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Document not found")
        
        # Check if file exists
        if not document.storage_path or not Path(document.storage_path).exists():
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Document file not found")
        
        # Return file for opening (not downloading)
        return FileResponse(
            path=document.storage_path,
            media_type=document.mime_type,
            headers={"Content-Disposition": f"inline; filename=\"{document.title}\""}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to download document: {str(e)}")

# Delete document endpoint
@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document and its associated file"""
    try:
        from app.db.crud import DocumentCRUD, TagCRUD
        
        success = DocumentCRUD.delete(db, document_id)
        
        if success:
            return {
                "success": True,
                "message": f"Document {document_id} deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": "Document not found or deletion failed"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete document: {str(e)}"
        }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "ArgosOS Backend is running"}

