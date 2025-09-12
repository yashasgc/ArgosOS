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

app = FastAPI(
    title="ArgosOS Backend",
    description="Intelligent file analysis and document management backend",
    version="1.0.0"
)

# CORS middleware - restrict to specific origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
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
        return {"configured": False, "encrypted": False, "error": "Failed to check API key status"}

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
        print(f"Uploading file: {file.filename} ({file.content_type})")
        
        # Security validations
        is_valid, error = FileValidator.validate_filename(file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        is_valid, error = FileValidator.validate_mime_type(file.content_type)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        is_valid, error = FileValidator.validate_file_size(content)
        if not is_valid:
            raise HTTPException(status_code=413, detail=error)
        
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
                    "tags": [{"name": tag.name} for tag in document.tags]
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
            raise HTTPException(status_code=400, detail=error)
        
        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        retrieval_agent = get_retrieval_agent()
        results = retrieval_agent.search_documents(query, db, limit)
        
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
        from app.db.crud import DocumentCRUD
        documents = DocumentCRUD.get_all(db, skip=skip, limit=limit)
        
        return {
            "success": True,
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "summary": doc.summary,
                    "mime_type": doc.mime_type,
                    "size_bytes": doc.size_bytes,
                    "created_at": doc.created_at,
                    "tags": [{"name": tag.name} for tag in doc.tags]
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

# Delete document endpoint
@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document and its associated file"""
    try:
        from app.db.crud import DocumentCRUD
        
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

