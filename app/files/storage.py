import os
import shutil
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils.hash import compute_bytes_hash


class FileStorage:
    def __init__(self):
        self.blobs_dir = settings.blobs_dir
        self.blobs_dir.mkdir(parents=True, exist_ok=True)
    
    def store_file(self, file_data: bytes, content_hash: str) -> str:
        """Store file data and return storage path"""
        # Create directory structure: /data/blobs/<first_2_chars>/<full_hash>
        hash_dir = self.blobs_dir / content_hash[:2]
        hash_dir.mkdir(exist_ok=True)
        
        storage_path = hash_dir / content_hash
        
        # Write file data
        with open(storage_path, 'wb') as f:
            f.write(file_data)
        
        return str(storage_path)
    
    def get_file_path(self, content_hash: str) -> Optional[Path]:
        """Get file path for a given content hash"""
        file_path = self.blobs_dir / content_hash[:2] / content_hash
        
        if file_path.exists():
            return file_path
        
        return None
    
    def file_exists(self, content_hash: str) -> bool:
        """Check if file exists by content hash"""
        file_path = self.get_file_path(content_hash)
        return file_path is not None
    
    def delete_file(self, content_hash: str) -> bool:
        """Delete file by content hash"""
        file_path = self.get_file_path(content_hash)
        if file_path and file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def get_file_size(self, content_hash: str) -> Optional[int]:
        """Get file size by content hash"""
        file_path = self.get_file_path(content_hash)
        if file_path and file_path.exists():
            return file_path.stat().st_size
        return None

