from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json

from app.db.models import Document
from app.db.schemas import DocumentCreate


class DocumentCRUD:
    @staticmethod
    def create(db: Session, document: DocumentCreate) -> Document:
        # Convert tags list to JSON string for storage
        doc_data = document.dict()
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
        search_query = f"%{query}%"
        
        # Search by title, summary, or tags (JSON field)
        results = db.query(Document).filter(
            or_(
                Document.title.contains(search_query),
                Document.summary.contains(search_query),
                Document.tags.contains(search_query)
            )
        ).all()
        
        return results[skip:skip + limit]
    
    @staticmethod
    def delete(db: Session, document_id: str) -> bool:
        """
        Delete a document and its associated file from disk.
        
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
            
            # Delete the file from disk if it exists
            if document.storage_path and not document.storage_path.startswith('memory://'):
                from pathlib import Path
                file_path = Path(document.storage_path)
                if file_path.exists():
                    file_path.unlink()
                    print(f"Deleted file: {file_path}")
            
            
            # Delete the document from database
            db.delete(document)
            db.commit()
            
            print(f"Deleted document: {document_id}")
            return True
            
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            db.rollback()
            return False



