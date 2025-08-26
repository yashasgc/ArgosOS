from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import Document, Tag, document_tags
from app.db.schemas import DocumentCreate, TagCreate


class DocumentCRUD:
    @staticmethod
    def create(db: Session, document: DocumentCreate) -> Document:
        db_document = Document(**document.dict())
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document
    
    @staticmethod
    def get_by_id(db: Session, document_id: str) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id).first()
    
    @staticmethod
    def get_by_hash(db: Session, content_hash: str) -> Optional[Document]:
        return db.query(Document).filter(Document.content_hash == content_hash).first()
    
    @staticmethod
    def get_all(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        tags_any: Optional[List[str]] = None,
        tags_all: Optional[List[str]] = None,
        title_like: Optional[str] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None
    ) -> List[Document]:
        query = db.query(Document)
        
        # Apply filters
        if tags_any:
            query = query.join(Document.tags).filter(Tag.name.in_(tags_any))
        
        if tags_all:
            for tag_name in tags_all:
                query = query.join(Document.tags).filter(Tag.name == tag_name)
        
        if title_like:
            query = query.filter(Document.title.contains(title_like))
        
        if date_from:
            query = query.filter(Document.imported_at >= date_from)
        
        if date_to:
            query = query.filter(Document.imported_at <= date_to)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def search(
        db: Session, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """Simple search by tags, title, or summary"""
        search_query = f"%{query}%"
        
        # Search by tag names
        tag_results = db.query(Document).join(Document.tags).filter(
            Tag.name.contains(query)
        ).all()
        
        # Search by title or summary
        text_results = db.query(Document).filter(
            or_(
                Document.title.contains(search_query),
                Document.summary.contains(search_query)
            )
        ).all()
        
        # Combine and deduplicate results
        all_results = list({doc.id: doc for doc in tag_results + text_results}.values())
        
        return all_results[skip:skip + limit]


class TagCRUD:
    @staticmethod
    def create(db: Session, tag: TagCreate) -> Tag:
        db_tag = Tag(**tag.dict())
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return db_tag
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Tag]:
        return db.query(Tag).filter(Tag.name == name).first()
    
    @staticmethod
    def get_or_create(db: Session, name: str) -> Tag:
        """Get existing tag or create new one"""
        tag = TagCRUD.get_by_name(db, name)
        if not tag:
            tag = TagCRUD.create(db, TagCreate(name=name))
        return tag
    
    @staticmethod
    def add_to_document(db: Session, document_id: str, tag_names: List[str]):
        """Add tags to a document"""
        document = DocumentCRUD.get_by_id(db, document_id)
        if not document:
            return
        
        for tag_name in tag_names:
            tag = TagCRUD.get_or_create(db, tag_name)
            if tag not in document.tags:
                document.tags.append(tag)
        
        db.commit()

