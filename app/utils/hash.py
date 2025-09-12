"""
File hashing utilities for content deduplication
"""
import hashlib
from pathlib import Path
from typing import Union




def compute_bytes_hash(data: bytes) -> str:
    """
    Compute SHA-256 hash of byte data.
    
    Args:
        data: Byte data to hash
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    return hashlib.sha256(data).hexdigest()
