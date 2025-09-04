from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from cryptography.fernet import Fernet
import base64
import os
from app.config import settings

router = APIRouter()

# Generate or load encryption key
def get_encryption_key():
    key_file = "secret.key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        return key

def get_fernet():
    return Fernet(get_encryption_key())

class ApiKeyRequest(BaseModel):
    api_key: str

class ApiKeyResponse(BaseModel):
    message: str
    encrypted: bool

@router.post("/api-key", response_model=ApiKeyResponse)
async def store_api_key(request: ApiKeyRequest):
    """Store the OpenAI API key encrypted"""
    try:
        fernet = get_fernet()
        encrypted_key = fernet.encrypt(request.api_key.encode())
        
        # Store encrypted key in environment variable or config
        # In production, you'd want to use a secure key management service
        os.environ["OPENAI_API_KEY_ENCRYPTED"] = base64.b64encode(encrypted_key).decode()
        
        return ApiKeyResponse(
            message="API key stored successfully",
            encrypted=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store API key: {str(e)}")

@router.get("/api-key/status")
async def get_api_key_status():
    """Check if API key is configured"""
    try:
        encrypted_key = os.environ.get("OPENAI_API_KEY_ENCRYPTED")
        if encrypted_key:
            return {"configured": True, "encrypted": True}
        else:
            return {"configured": False, "encrypted": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check API key status: {str(e)}")

@router.delete("/api-key")
async def clear_api_key():
    """Clear the stored API key"""
    try:
        if "OPENAI_API_KEY_ENCRYPTED" in os.environ:
            del os.environ["OPENAI_API_KEY_ENCRYPTED"]
        return {"message": "API key cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear API key: {str(e)}")

@router.get("/api-key/decrypt")
async def get_decrypted_api_key():
    """Get the decrypted API key for LLM use"""
    try:
        encrypted_key = os.environ.get("OPENAI_API_KEY_ENCRYPTED")
        if not encrypted_key:
            raise HTTPException(status_code=404, detail="No API key configured")
        
        fernet = get_fernet()
        decrypted_key = fernet.decrypt(base64.b64decode(encrypted_key)).decode()
        
        return {"api_key": decrypted_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decrypt API key: {str(e)}")

