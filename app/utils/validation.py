"""
Validation utilities for ArgosOS
"""
import re
from typing import List, Optional, Tuple
from pathlib import Path

class ValidationError(Exception):
    """Custom validation error"""
    pass

class FileValidator:
    """File validation utilities"""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.pdf', '.txt', '.docx', '.doc', '.md', '.csv',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
    }
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/bmp', 'image/tiff', 'image/webp',
        'application/pdf', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain', 'text/markdown', 'text/csv'
    }
    
    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Maximum filename length
    MAX_FILENAME_LENGTH = 255
    
    @classmethod
    def validate_file_size(cls, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate file size"""
        if len(content) > cls.MAX_FILE_SIZE:
            return False, f"File too large: {len(content)} bytes (max: {cls.MAX_FILE_SIZE} bytes)"
        return True, None
    
    @classmethod
    def validate_filename(cls, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate filename for security"""
        if not filename:
            return False, "No filename provided"
        
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            return False, f"Filename too long: {len(filename)} characters (max: {cls.MAX_FILENAME_LENGTH})"
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Filename contains path traversal characters"
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in filename:
                return False, f"Filename contains dangerous character: {char}"
        
        # Check file extension
        file_path = Path(filename)
        if file_path.suffix.lower() not in cls.ALLOWED_EXTENSIONS:
            return False, f"File extension not allowed: {file_path.suffix}"
        
        return True, None
    
    @classmethod
    def validate_mime_type(cls, mime_type: str) -> Tuple[bool, Optional[str]]:
        """Validate MIME type"""
        if mime_type not in cls.ALLOWED_MIME_TYPES:
            return False, f"MIME type not allowed: {mime_type}"
        return True, None
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe storage"""
        if not filename:
            return f"file_{hash(filename) % 100000000:08d}"
        
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple consecutive underscores
        filename = re.sub(r'_+', '_', filename)
        # Remove leading/trailing underscores and dots
        filename = filename.strip('_.')
        # Ensure filename is not empty
        if not filename:
            filename = f"file_{hash(filename) % 100000000:08d}"
        
        return filename

class ContentValidator:
    """Content validation utilities"""
    
    @staticmethod
    def validate_text_content(text: str, max_length: int = 1000000) -> Tuple[bool, Optional[str]]:
        """Validate text content"""
        if not text or not text.strip():
            return False, "Empty text content"
        
        if len(text) > max_length:
            return False, f"Text content too long: {len(text)} characters (max: {max_length})"
        
        return True, None
    
    @staticmethod
    def validate_search_query(query: str) -> Tuple[bool, Optional[str]]:
        """Validate search query"""
        if not query or not query.strip():
            return False, "Empty search query"
        
        if len(query) > 1000:
            return False, "Search query too long"
        
        # Check for SQL injection attempts
        sql_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'EXEC', 'UNION']
        query_upper = query.upper()
        for keyword in sql_keywords:
            if keyword in query_upper:
                return False, f"Search query contains potentially dangerous keyword: {keyword}"
        
        return True, None

class APIKeyValidator:
    """API key validation utilities"""
    
    @staticmethod
    def validate_openai_key(api_key: str) -> Tuple[bool, Optional[str]]:
        """Validate OpenAI API key format"""
        if not api_key or not api_key.strip():
            return False, "API key cannot be empty"
        
        if not api_key.startswith('sk-'):
            return False, "Invalid OpenAI API key format"
        
        if len(api_key) < 20:
            return False, "API key too short"
        
        if len(api_key) > 200:
            return False, "API key too long"
        
        return True, None
