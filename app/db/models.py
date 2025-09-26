import uuid
import time
from typing import Optional

from sqlalchemy import Column, String, Integer, Text, Index
from sqlalchemy.orm import declarative_base, Mapped

Base = declarative_base()



class Document(Base):
    """Documents table - stores file metadata and content information"""
    __tablename__ = "documents"
    
    # Primary key - UUID as TEXT
    id: Mapped[str] = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content hash for deduplication (SHA-256)
    content_hash: Mapped[str] = Column(String, unique=True, nullable=False, index=True)
    
    # File metadata
    title: Mapped[str] = Column(String, nullable=False)
    mime_type: Mapped[str] = Column(String, nullable=False)
    size_bytes: Mapped[int] = Column(Integer, nullable=False)
    storage_path: Mapped[str] = Column(String, nullable=False)
    
    # AI-generated content
    summary: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # Tags stored as JSON string
    tags: Mapped[str] = Column(Text, nullable=False, default="[]")
    
    # Timestamps (epoch milliseconds)
    created_at: Mapped[int] = Column(Integer, nullable=False, default=lambda: int(time.time() * 1000))
    imported_at: Mapped[int] = Column(Integer, nullable=False, default=lambda: int(time.time() * 1000))
    
    
    def __repr__(self):
        return f"<Document(id='{self.id[:8]}...', title='{self.title}', size={self.size_bytes})>"


class Tag(Base):
    """Tags table - stores unique tag names with associated document IDs"""
    __tablename__ = "tags"
    
    # Primary key - auto-increment integer
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tag name (stored in lowercase for consistency)
    tag: Mapped[str] = Column(String, unique=True, nullable=False, index=True)
    
    # Document IDs as JSON string
    document_ids: Mapped[str] = Column(Text, nullable=False, default="[]")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, tag='{self.tag}', document_ids='{self.document_ids}')>"






# Create additional indexes for performance
Index('idx_documents_created_at', Document.created_at)
Index('idx_documents_imported_at', Document.imported_at)
Index('idx_documents_mime_type', Document.mime_type)
