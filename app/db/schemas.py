from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class Tag(TagBase):
    id: int
    
    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    title: str
    mime_type: str
    size_bytes: int
    summary: Optional[str] = None


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
    tags: List[Tag] = []
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    mime_type: str
    size_bytes: int
    created_at: int
    tags: List[Tag] = []
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    q: str


class SearchResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

