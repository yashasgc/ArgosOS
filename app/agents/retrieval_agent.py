"""
RetrievalAgent - Handles query processing and document retrieval using LLM-generated SQL
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import Document
from app.llm.provider import LLMProvider


class RetrievalAgent:
    """
    Agent responsible for processing queries and retrieving documents using LLM-generated SQL.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the RetrievalAgent with an LLM provider.
        
        Args:
            llm_provider: LLM provider for generating SQL queries
        """
        self.llm_provider = llm_provider
    
    def search_documents(
        self, 
        query: str, 
        db: Session,
        limit: int = 10,
        schema_info: str = ""
    ) -> Dict[str, Any]:
        """
        Search for documents using LLM-generated SQL queries.
        
        Args:
            query: Natural language search query
            db: Database session
            limit: Maximum number of documents to return
            schema_info: Optional database schema information for the LLM
            
        Returns:
            Dictionary containing search results and metadata
        """
        # Input validation
        if not query or not query.strip():
            return {
                'query': query,
                'sql_query': '',
                'documents': [],
                'total_found': 0,
                'errors': ['Query cannot be empty']
            }
        
        if limit <= 0 or limit > 1000:
            limit = 10  # Default safe limit
        
        results = {
            'query': query.strip(),
            'sql_query': '',
            'documents': [],
            'total_found': 0,
            'errors': []
        }
        
        try:
            # Generate SQL query using LLM
            if not self.llm_provider.is_available():
                results['errors'].append("LLM provider not available")
                return results
            
            sql_query = self.llm_provider.generate_sql_query(query, schema_info)
            if not sql_query:
                results['errors'].append("Failed to generate SQL query")
                return results
            
            results['sql_query'] = sql_query
            
            # Execute the SQL query
            documents = self._execute_sql_query(db, sql_query, limit)
            
            # Format results
            formatted_docs = self._format_documents(documents)
            
            results['documents'] = formatted_docs
            results['total_found'] = len(formatted_docs)
            
        except Exception as e:
            results['errors'].append(f"Search failed: {str(e)}")
        
        return results
    
    def _execute_sql_query(self, db: Session, sql_query: str, limit: int) -> List[Document]:
        """Execute SQL query and return Document objects - DISABLED FOR SECURITY"""
        # SECURITY: Raw SQL execution disabled to prevent SQL injection
        # LLM-generated SQL queries are not safe to execute directly
        print("WARNING: Raw SQL execution disabled for security reasons")
        return []
    
    def get_document_content(self, document_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Retrieve full document content and metadata.
        
        Args:
            document_id: ID of the document to retrieve
            db: Database session
            
        Returns:
            Dictionary containing document content and metadata, or None if not found
        """
        # Input validation
        if not document_id or not document_id.strip():
            return {
                'error': 'Document ID cannot be empty',
                'document_id': document_id
            }
        
        # Sanitize document_id (basic validation)
        document_id = document_id.strip()
        if len(document_id) > 255:  # Reasonable limit
            return {
                'error': 'Document ID too long',
                'document_id': document_id
            }
        
        try:
            # Get document from database using parameterized query
            from sqlalchemy import text
            sql_query = text("SELECT * FROM documents WHERE id = :document_id")
            result = db.execute(sql_query, {"document_id": document_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            # Read the actual file content
            file_path = Path(row.storage_path)
            if not file_path.exists():
                return {
                    'error': 'File not found on disk',
                    'document': {
                        'id': row.id,
                        'title': row.title,
                        'summary': row.summary,
                        'mime_type': row.mime_type,
                        'size_bytes': row.size_bytes,
                        'created_at': row.created_at,
                        'imported_at': row.imported_at
                    }
                }
            
            # Extract text content
            from app.files.extractors import TextExtractor
            extractor = TextExtractor()
            content = extractor.extract_text(file_path, row.mime_type)
            
            return {
                'id': row.id,
                'title': row.title,
                'summary': row.summary,
                'mime_type': row.mime_type,
                'size_bytes': row.size_bytes,
                'created_at': row.created_at,
                'imported_at': row.imported_at,
                'content': content,
                'file_path': str(file_path)
            }
            
        except Exception as e:
            return {
                'error': f'Failed to retrieve document content: {str(e)}',
                'document_id': document_id
            }
    
    def _format_documents(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Format Document objects into dictionaries for API responses."""
        formatted_docs = []
        for doc in documents:
            formatted_doc = {
                'id': doc.id,
                'title': doc.title,
                'summary': doc.summary,
                'tags': [],  # Tags not available in raw SQL results
                'mime_type': doc.mime_type,
                'size_bytes': doc.size_bytes,
                'created_at': doc.created_at,
                'imported_at': doc.imported_at
            }
            formatted_docs.append(formatted_doc)
        return formatted_docs
    
