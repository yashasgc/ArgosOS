"""
File hashing utilities for content deduplication
"""
import hashlib
from pathlib import Path
from typing import Union


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of file content for deduplication.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    # Read file in chunks to handle large files efficiently
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    """
    Compute SHA-256 hash of byte data.
    
    Args:
        data: Byte data to hash
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    return hashlib.sha256(data).hexdigest()
