"""
RetrievalAgent - Handles query processing and document retrieval using LLM-generated SQL
"""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import Document, Tag
from app.db.crud import TagCRUD
from app.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


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
        1. Get a list of tags from tags table
        2. Pass the tags table and the query to LLM to generate the tags
        3. Search for documents with those generated tags
        4. Return the files retrieved and pass the path to postprocessor_agent
        
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
            'document_ids': [],
            'total_found': 0,
            'errors': []
        }
        
        try:
            # Step 1: Get a list of tags from tags table
            available_tags = self._get_available_tags(db)
            
            # Step 2: Pass the tags table and the query to LLM to generate the tags
            relevant_tags = self._generate_relevant_tags(query, available_tags, db, limit)
            
            # Step 3: Search for documents with those generated tags
            documents = self._search_documents_with_generated_tags(db, relevant_tags, limit)
            
            # If no documents found with tags, try direct text search
            if not documents:
                logger.info("No documents found with generated tags, trying direct text search")
                from app.db.crud import DocumentCRUD
                documents = DocumentCRUD.search(db, query, 0, limit)
            
            # Step 4: Return document IDs for postprocessor
            document_ids = [doc.id for doc in documents]
            
            # Format results
            formatted_docs = self._format_documents(documents)
            
            results['documents'] = formatted_docs
            results['document_ids'] = document_ids
            results['total_found'] = len(formatted_docs)
            
        except Exception as e:
            results['errors'].append(f"Search failed: {str(e)}")
        
        return results
    
    def _get_available_tags(self, db: Session) -> List[str]:
        """
        Get a list of all available tags from the tags table.
        
        Args:
            db: Database session
            
        Returns:
            List of tag names
        """
        try:
            tags = TagCRUD.get_all(db)
            return [tag.name for tag in tags]
        except Exception as e:
            logger.error(f"Error getting available tags: {e}")
            return []
    
    def _generate_relevant_tags(self, query: str, available_tags: List[str], db: Session, limit: int = 10) -> List[str]:
        """
        Use LLM to generate relevant tags from the query based on available tags.
        
        Args:
            query: Natural language search query
            available_tags: List of available tags from the database
            db: Database session
            limit: Maximum number of documents to search
            
        Returns:
            List of relevant tag names
        """
        if not self.llm_provider.is_available():
            logger.warning("LLM not available, falling back to simple text matching")
            # Fallback: simple text matching in tags, titles, and summaries
            from app.db.crud import DocumentCRUD
            try:
                # Use the general search which looks in titles, summaries, and tags
                documents = DocumentCRUD.search(db, query, 0, limit)
                # Extract unique tags from matching documents
                relevant_tags = set()
                for doc in documents:
                    if doc.tags:
                        try:
                            import json
                            doc_tags = json.loads(doc.tags)
                            for tag in doc_tags:
                                relevant_tags.add(tag)
                        except:
                            pass
                
                # If we found documents, return their tags
                if relevant_tags:
                    return list(relevant_tags)
                
                # If no documents found, try partial matching on available tags
                query_lower = query.lower()
                matching_tags = []
                for tag in available_tags:
                    if query_lower in tag.lower() or tag.lower() in query_lower:
                        matching_tags.append(tag)
                
                return matching_tags
            except Exception as e:
                logger.error(f"Error in fallback search: {e}")
                return []
        
        try:
            # Create a prompt for the LLM to select relevant tags
            prompt = f"""
Given the following search query and available tags, select the most relevant tags that match the query.

Search Query: "{query}"

Available Tags: {', '.join(available_tags)}

Return your response as a JSON array of tag names. If no tags are relevant, return an empty array.

Format: ["tag1", "tag2", "tag3"]

Relevant tags:"""

            response = self.llm_provider.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse the JSON response
            relevant_tags_text = response.choices[0].message.content.strip()
            if not relevant_tags_text:
                return []
            
            try:
                import json
                # Try to parse as JSON array
                relevant_tags = json.loads(relevant_tags_text)
                if not isinstance(relevant_tags, list):
                    raise ValueError("Response is not a list")
                
                # Filter to only include tags that actually exist in our database
                valid_tags = [tag for tag in relevant_tags if tag in available_tags]
                
                logger.info(f"Generated relevant tags: {valid_tags}")
                return valid_tags
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {e}, falling back to comma parsing")
                # Fallback: split by comma and clean up
                relevant_tags = [tag.strip().strip('"\'') for tag in relevant_tags_text.split(',')]
                valid_tags = [tag for tag in relevant_tags if tag in available_tags]
                return valid_tags
            
        except Exception as e:
            logger.error(f"Error generating relevant tags: {e}")
            # Fallback: simple text matching
            relevant_tags = []
            query_lower = query.lower()
            for tag in available_tags:
                if tag.lower() in query_lower:
                    relevant_tags.append(tag)
            return relevant_tags
    
    def _search_documents_with_generated_tags(self, db: Session, relevant_tags: List[str], limit: int) -> List[Document]:
        """
        Search for documents that have any of the relevant tags.
        
        Args:
            db: Database session
            relevant_tags: List of relevant tag names
            limit: Maximum number of results
            
        Returns:
            List of Document objects with matching tags
        """
        try:
            from app.db.crud import DocumentCRUD
            
            if not relevant_tags:
                # If no relevant tags, return empty results instead of all documents
                logger.warning("No relevant tags found, returning empty results")
                return []
            
            # Search for documents that contain any of the relevant tags
            documents = []
            for tag in relevant_tags:
                # Search for documents containing this tag in their JSON tags field
                tag_docs = db.query(Document).filter(
                    Document.tags.contains(f'"{tag}"')
                ).limit(limit).all()
                documents.extend(tag_docs)
            
            # Remove duplicates
            seen_ids = set()
            unique_docs = []
            for doc in documents:
                if doc.id not in seen_ids:
                    unique_docs.append(doc)
                    seen_ids.add(doc.id)
            
            return unique_docs[:limit]
            
        except Exception as e:
            logger.error(f"Error searching documents with generated tags: {e}")
            return []
    
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
            logger.error(f"Error searching documents with tags: {e}")
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
                        logger.warning(f"File not found: {document.storage_path}")
                        return None
                else:
                    logger.debug(f"Document stored in memory only: {document.storage_path}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file path for document {document.id}: {e}")
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
                logger.debug(f"Postprocessor result for {file_path}: {result}")
                
        except Exception as e:
            logger.error(f"Error passing to postprocessor: {e}")
    
    
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
        import json
        formatted_docs = []
        for doc in documents:
            # Parse tags from JSON string
            try:
                tags = json.loads(doc.tags) if doc.tags else []
            except (json.JSONDecodeError, TypeError):
                tags = []
            
            formatted_doc = {
                'id': doc.id,
                'title': doc.title,
                'summary': doc.summary,
                'tags': tags,
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
    
