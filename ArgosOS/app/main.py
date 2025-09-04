from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
import base64
import os
import json
from pathlib import Path

app = FastAPI(
    title="ArgosOS Backend",
    description="Intelligent file analysis and document management backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration file paths
CONFIG_DIR = Path("./config")
ENCRYPTED_KEY_FILE = CONFIG_DIR / "api_keys.enc"
SECRET_KEY_FILE = CONFIG_DIR / "secret.key"

# Ensure config directory exists
CONFIG_DIR.mkdir(exist_ok=True)

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
    except Exception as e:
        return ApiKeyResponse(
            message=f"Failed to store API key: {str(e)}",
            encrypted=False
        )

@app.get("/v1/api-key/status")
async def get_api_key_status():
    """Check if API key is configured"""
    try:
        api_keys = load_encrypted_api_keys()
        openai_configured = "openai" in api_keys and api_keys["openai"]
        
        return {
            "configured": openai_configured,
            "encrypted": True,
            "services": list(api_keys.keys())
        }
    except Exception as e:
        return {"configured": False, "encrypted": False, "error": str(e)}

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

@app.get("/v1/api-key/decrypt")
async def get_decrypted_api_key():
    """Get the decrypted API key for LLM use"""
    try:
        api_keys = load_encrypted_api_keys()
        if "openai" not in api_keys or not api_keys["openai"]:
            return {"error": "No OpenAI API key configured"}
        
        return {"api_key": api_keys["openai"]}
    except Exception as e:
        return {"error": f"Failed to decrypt API key: {str(e)}"}

