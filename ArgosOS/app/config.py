import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./argos.db"
    
    # File storage
    data_dir: Path = Path("./data")
    blobs_dir: Path = Path("./data/blobs")
    
    # LLM settings
    llm_enabled: bool = False
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    # OCR settings
    tesseract_cmd: Optional[str] = None
    
    # API settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()

# Ensure data directories exist
settings.data_dir.mkdir(exist_ok=True)
settings.blobs_dir.mkdir(exist_ok=True)
