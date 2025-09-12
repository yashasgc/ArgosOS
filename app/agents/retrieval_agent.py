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
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for documents with tags based on query.
        
        Workflow:
        1. Read the query
        2. Create a query to search for documents with tags based on tag metadata from SQLite
        3. Return the files retrieved and pass the path to postprocessor_agent
        
        Args:
            query: Natural language search query
            db: Database session
            limit: Maximum number of documents to return
            
        Returns:
            Dictionary containing search results and file paths for postprocessor
        """
        # Input validation
        if not query or not query.strip():
            return {
                'query': query,
                'documents': [],
                'file_paths': [],
                'total_found': 0,
                'errors': ['Query cannot be empty']
            }
        
        if limit <= 0 or limit > 1000:
            limit = 10  # Default safe limit
        
        results = {
            'query': query.strip(),
            'documents': [],
            'file_paths': [],
            'total_found': 0,
            'errors': []
        }
        
        try:
            # Step 1: Read the query (already done)
            search_query = query.strip()
            
            # Step 2: Create a query to search for documents with tags
            documents = self._search_documents_with_tags(db, search_query, limit)
            
            # Step 3: Return files and prepare paths for postprocessor
            file_paths = []
            for doc in documents:
                # Get file path from document metadata
                file_path = self._get_document_file_path(doc)
                if file_path:
                    file_paths.append(file_path)
            
            # Format results
            formatted_docs = self._format_documents(documents)
            
            results['documents'] = formatted_docs
            results['file_paths'] = file_paths
            results['total_found'] = len(formatted_docs)
            
            # Pass file paths to postprocessor agent
            if file_paths and self.llm_provider.is_available():
                self._pass_to_postprocessor(search_query, file_paths)
            
        except Exception as e:
            results['errors'].append(f"Search failed: {str(e)}")
        
        return results
    
    def _search_documents_with_tags(self, db: Session, query: str, limit: int) -> List[Document]:
        """
        Search for documents with tags based on query using SQLite.
        
        Args:
            db: Database session
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of Document objects with matching tags
        """
        try:
            from app.db.crud import DocumentCRUD
            
            # Search by tags, title, and summary
            documents = DocumentCRUD.search(db, query, 0, limit)
            
            # If no results, try searching by individual words
            if not documents:
                words = query.split()
                for word in words:
                    if len(word) > 2:  # Only search words longer than 2 characters
                        word_docs = DocumentCRUD.search(db, word, 0, limit)
                        documents.extend(word_docs)
                
                # Remove duplicates
                seen_ids = set()
                unique_docs = []
                for doc in documents:
                    if doc.id not in seen_ids:
                        unique_docs.append(doc)
                        seen_ids.add(doc.id)
                documents = unique_docs[:limit]
            
            return documents
            
        except Exception as e:
            print(f"Error searching documents with tags: {e}")
            return []
    
    def _get_document_file_path(self, document: Document) -> Optional[str]:
        """
        Get the file path for a document.
        
        Args:
            document: Document object
            
        Returns:
            File path if available, None otherwise
        """
        try:
            # Check if the document has a storage_path field
            if hasattr(document, 'storage_path') and document.storage_path:
                # Check if it's a real file path (not memory://)
                if not document.storage_path.startswith('memory://'):
                    from pathlib import Path
                    file_path = Path(document.storage_path)
                    if file_path.exists():
                        return str(file_path)
                    else:
                        print(f"File not found: {document.storage_path}")
                        return None
                else:
                    print(f"Document stored in memory only: {document.storage_path}")
                    return None
            
            return None
            
        except Exception as e:
            print(f"Error getting file path for document {document.id}: {e}")
            return None
    
    def _pass_to_postprocessor(self, query: str, file_paths: List[str]):
        """
        Pass file paths to postprocessor agent for further processing.
        
        Args:
            query: Original search query
            file_paths: List of file paths to process
        """
        try:
            from app.agents.postprocessor_agent import PostProcessorAgent
            
            # Create postprocessor agent
            postprocessor = PostProcessorAgent(self.llm_provider)
            
            # Process the files with the postprocessor
            for file_path in file_paths:
                result = postprocessor.process_file(file_path, query)
                print(f"Postprocessor result for {file_path}: {result}")
                
        except Exception as e:
            print(f"Error passing to postprocessor: {e}")
    
    
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
            
            # Extract text content directly
            content = self._extract_text_from_file(file_path, row.mime_type)
            
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
    
    def _extract_text_from_file(self, file_path: str, mime_type: str) -> str:
        """
        Extract text content from a file based on its MIME type.
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            
        Returns:
            Extracted text content
        """
        try:
            from pathlib import Path
            file_path = Path(file_path)
            
            if not file_path.exists():
                return f"File not found: {file_path}"
            
            # Read file based on MIME type
            if mime_type.startswith('text/'):
                return file_path.read_text(encoding='utf-8')
            elif mime_type == 'application/pdf':
                # For PDF files, we'll return a placeholder since we don't have PDF extraction here
                return f"PDF content from {file_path.name} (text extraction not available in retrieval agent)"
            else:
                return f"Content from {file_path.name} (MIME type: {mime_type})"
                
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
    
