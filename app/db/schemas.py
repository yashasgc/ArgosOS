from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import json




class DocumentBase(BaseModel):
    title: str
    mime_type: str
    size_bytes: int
    summary: Optional[str] = None
    tags: List[str] = []


class DocumentCreate(DocumentBase):
    content_hash: str
    storage_path: str
    created_at: int
    imported_at: int


class Document(DocumentBase):
    id: str
    content_hash: str
    storage_path: str
    created_at: int
    imported_at: int
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle JSON tags field"""
        data = obj.__dict__.copy()
        if 'tags' in data and isinstance(data['tags'], str):
            try:
                data['tags'] = json.loads(data['tags'])
            except (json.JSONDecodeError, TypeError):
                data['tags'] = []
        return cls(**data)


class DocumentResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    mime_type: str
    size_bytes: int
    created_at: int
    tags: List[str] = []
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    q: str


class SearchResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

