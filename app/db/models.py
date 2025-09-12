import uuid
import time
from typing import List, Optional

from sqlalchemy import Column, String, Integer, ForeignKey, Table, Text, Index
from sqlalchemy.orm import declarative_base, Mapped, relationship

Base = declarative_base()

# Association table for many-to-many relationship between documents and tags
document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", String, ForeignKey("documents.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


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
    
    # Timestamps (epoch milliseconds)
    created_at: Mapped[int] = Column(Integer, nullable=False, default=lambda: int(time.time() * 1000))
    imported_at: Mapped[int] = Column(Integer, nullable=False, default=lambda: int(time.time() * 1000))
    
    # Relationships
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary=document_tags, back_populates="documents"
    )
    
    def __repr__(self):
        return f"<Document(id='{self.id[:8]}...', title='{self.title}', size={self.size_bytes})>"


class Tag(Base):
    """Tags table - stores document categories and labels"""
    __tablename__ = "tags"
    
    # Primary key - auto-increment integer
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tag name (stored in lowercase for consistency)
    name: Mapped[str] = Column(String, unique=True, nullable=False, index=True)
    
    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", secondary=document_tags, back_populates="tags"
    )
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"




# Create additional indexes for performance
Index('idx_documents_created_at', Document.created_at)
Index('idx_documents_imported_at', Document.imported_at)
Index('idx_documents_mime_type', Document.mime_type)
