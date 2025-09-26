import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import json

from app.db.models import Document, Tag
from app.db.schemas import DocumentCreate, TagCreate

logger = logging.getLogger(__name__)


class DocumentCRUD:
    @staticmethod
    def create(db: Session, document: DocumentCreate) -> Document:
        # Convert tags list to JSON string for storage
        doc_data = document.model_dump()
        if 'tags' in doc_data and isinstance(doc_data['tags'], list):
            doc_data['tags'] = json.dumps(doc_data['tags'])
        
        db_document = Document(**doc_data)
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
        title_like: Optional[str] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None
    ) -> List[Document]:
        query = db.query(Document)
        
        # Apply filters
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
        """Search by title, summary, or tags"""
        search_query = f"%{query.lower()}%"
        
        # Search by title, summary, or tags (JSON field) - case insensitive
        results = db.query(Document).filter(
            or_(
                func.lower(Document.title).contains(search_query),
                func.lower(Document.summary).contains(search_query),
                func.lower(Document.tags).contains(search_query)
            )
        ).all()
        
        return results[skip:skip + limit]
    
    @staticmethod
    def delete(db: Session, document_id: str) -> bool:
        """
        Delete a document and its associated file from disk.
        Also removes the document from all tags in the tags table.
        
        Args:
            db: Database session
            document_id: ID of the document to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Get the document
            document = DocumentCRUD.get_by_id(db, document_id)
            if not document:
                return False
            
            # Remove document from all tags before deleting the document
            if document.tags:
                try:
                    # Parse tags from JSON
                    document_tags = json.loads(document.tags) if isinstance(document.tags, str) else document.tags
                    if isinstance(document_tags, list):
                        # Remove document ID from each tag's document_ids list
                        for tag_name in document_tags:
                            TagCRUD.remove_document_from_tag(db, tag_name, document_id)
                        logger.info(f"Removed document {document_id} from {len(document_tags)} tags")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Could not parse document tags for cleanup: {e}")
            
            # Delete the file from disk if it exists
            if document.storage_path and not document.storage_path.startswith('memory://'):
                from pathlib import Path
                file_path = Path(document.storage_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file: {file_path}")
            
            # Delete the document from database
            db.delete(document)
            db.commit()
            
            logger.info(f"Deleted document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            db.rollback()
            return False


class TagCRUD:
    @staticmethod
    def create(db: Session, tag: TagCreate) -> Tag:
        # Convert document_ids list to JSON string for storage
        tag_data = tag.model_dump()
        if 'document_ids' in tag_data and isinstance(tag_data['document_ids'], list):
            tag_data['document_ids'] = json.dumps(tag_data['document_ids'])
        
        db_tag = Tag(**tag_data)
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return db_tag
    
    @staticmethod
    def get_by_tag(db: Session, tag: str) -> Optional[Tag]:
        return db.query(Tag).filter(Tag.tag == tag).first()
    
    @staticmethod
    def get_or_create(db: Session, tag: str) -> Tag:
        """Get existing tag or create new one"""
        db_tag = TagCRUD.get_by_tag(db, tag)
        if not db_tag:
            db_tag = TagCRUD.create(db, TagCreate(tag=tag, document_ids=[]))
        return db_tag
    
    @staticmethod
    def get_all(db: Session) -> List[Tag]:
        """Get all tags"""
        return db.query(Tag).all()
    
    @staticmethod
    def add_document_to_tag(db: Session, tag: str, document_id: str) -> bool:
        """Add a document ID to a tag's document_ids list"""
        try:
            db_tag = TagCRUD.get_by_tag(db, tag)
            if not db_tag:
                # Create new tag with this document
                TagCRUD.create(db, TagCreate(tag=tag, document_ids=[document_id]))
                return True
            
            # Parse existing document_ids
            try:
                doc_ids = json.loads(db_tag.document_ids) if db_tag.document_ids else []
            except (json.JSONDecodeError, TypeError):
                doc_ids = []
            
            # Add document_id if not already present
            if document_id not in doc_ids:
                doc_ids.append(document_id)
                db_tag.document_ids = json.dumps(doc_ids)
                db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error adding document {document_id} to tag {tag}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def remove_document_from_tag(db: Session, tag: str, document_id: str) -> bool:
        """Remove a document ID from a tag's document_ids list"""
        try:
            db_tag = TagCRUD.get_by_tag(db, tag)
            if not db_tag:
                return True  # Tag doesn't exist, nothing to remove
            
            # Parse existing document_ids
            try:
                doc_ids = json.loads(db_tag.document_ids) if db_tag.document_ids else []
            except (json.JSONDecodeError, TypeError):
                doc_ids = []
            
            # Remove document_id if present
            if document_id in doc_ids:
                doc_ids.remove(document_id)
                if doc_ids:
                    db_tag.document_ids = json.dumps(doc_ids)
                    db.commit()
                else:
                    # If no documents left, delete the tag
                    db.delete(db_tag)
                    db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error removing document {document_id} from tag {tag}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def delete(db: Session, tag_id: int) -> bool:
        try:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if tag:
                db.delete(tag)
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting tag {tag_id}: {e}")
            db.rollback()
            return False



