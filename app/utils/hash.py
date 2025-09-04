import hashlib
from pathlib import Path
from typing import Union


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    """Compute SHA-256 hash of bytes data"""
    return hashlib.sha256(data).hexdigest()

