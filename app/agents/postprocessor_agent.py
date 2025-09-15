"""
PostProcessorAgent - Advanced document processing with OCR and multi-step LLM processing
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session
import json

from app.db.models import Document
from app.db.crud import DocumentCRUD
from app.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class PostProcessorAgent:
    """
    Agent responsible for processing documents retrieved by RetrievalAgent.
    
    Workflow:
    1. Takes all the document IDs and finds the docs
    2. Uses OCR on the docs to extract all the content
    3. Uses the query to find relevant info from the docs for extracting relevant content only
    4. Calls another method if there is additional processing requiring
    5. The LLM decides if additional processing is required and the instructions to process
    6. The new method would make another LLM call with relevant info, query and processing instructions
    7. Finally returns the result
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    def process_documents(
        self, 
        query: str,
        document_ids: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Process documents using the new workflow.
        
        Args:
            query: Search query
            document_ids: List of document IDs to process
            db: Database session
            
        Returns:
            Dictionary containing processed results
        """
        # Input validation
        if not query or not query.strip():
            return {
                'query': query,
                'processed_documents': [],
                'total_processed': 0,
                'errors': ['Query cannot be empty']
            }
        
        if not document_ids:
            return {
                'query': query,
                'processed_documents': [],
                'total_processed': 0,
                'errors': ['No document IDs provided']
            }
        
        results = {
            'query': query.strip(),
            'processed_documents': [],
            'total_processed': 0,
            'errors': []
        }
        
        try:
            # Step 1: Get documents by IDs
            documents = self._get_documents_by_ids(db, document_ids)
            
            if not documents:
                results['errors'].append('No documents found for the provided IDs')
                return results
            
            # Step 2: Extract content using OCR for all documents
            extracted_contents = self._extract_document_contents(documents)
            
            # Step 3: One API call to answer the question or decide if further processing is needed
            processing_result = self._answer_or_do_further_processing(query, extracted_contents)
            
            # Step 4: Perform additional processing if needed
            if processing_result['needs_processing']:
                final_result = self._perform_additional_processing(
                    query, 
                    processing_result['relevant_content'], 
                    processing_result['instructions']
                )
            else:
                final_result = processing_result['direct_answer']
            
            # Format results with direct answer
            results['direct_answer'] = processing_result['direct_answer']
            results['processed_documents'] = [{
                'document_id': doc.id,
                'title': doc.title,
                'relevant_content': final_result,
                'processing_applied': processing_result['needs_processing']
            } for doc in documents]
            
            results['total_processed'] = len(documents)
            
        except Exception as e:
            results['errors'].append(f"Processing failed: {str(e)}")
        
        return results
    
    def _get_documents_by_ids(self, db: Session, document_ids: List[str]) -> List[Document]:
        """Get documents by their IDs from the database."""
        try:
            documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
            return documents
        except Exception as e:
            logger.error(f"Error getting documents by IDs: {e}")
            return []
    
    def _extract_document_contents(self, documents: List[Document]) -> Dict[str, str]:
        """Extract content from documents, using summary for images."""
        extracted_contents = {}
        
        for doc in documents:
            try:
                # For images, use the summary instead of OCR extraction
                if doc.mime_type and doc.mime_type.startswith('image/'):
                    if doc.summary:
                        extracted_contents[doc.id] = doc.summary
                        logger.info(f"Using summary for image document {doc.id}")
                    else:
                        extracted_contents[doc.id] = f"Image: {doc.title} (no summary available)"
                        logger.warning(f"No summary available for image document {doc.id}")
                else:
                    # For non-images, read the file content
                    if doc.storage_path and Path(doc.storage_path).exists():
                        with open(doc.storage_path, 'rb') as f:
                            file_data = f.read()
                        
                        # Extract text based on MIME type
                        content = self._extract_text_from_file(file_data, doc.mime_type)
                        extracted_contents[doc.id] = content
                    else:
                        # Fallback to summary if available
                        if doc.summary:
                            extracted_contents[doc.id] = doc.summary
                        else:
                            extracted_contents[doc.id] = f"Document: {doc.title} (no content available)"
                        logger.warning(f"File not found for document {doc.id}: {doc.storage_path}")
                    
            except Exception as e:
                logger.error(f"Error extracting content from document {doc.id}: {e}")
                # Fallback to summary if available
                if doc.summary:
                    extracted_contents[doc.id] = doc.summary
                else:
                    extracted_contents[doc.id] = f"Document: {doc.title} (error extracting content)"
        
        return extracted_contents
    
    
    def _extract_text_from_file(self, file_data: bytes, mime_type: str) -> str:
        """Extract text from file data based on MIME type."""
        try:
            if mime_type.startswith('text/'):
                return file_data.decode('utf-8', errors='ignore')
            elif mime_type == 'application/pdf':
                import fitz  # PyMuPDF
                doc = fitz.open(stream=file_data, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            elif mime_type in ['image/jpeg', 'image/png', 'image/tiff']:
                import pytesseract
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(file_data))
                return pytesseract.image_to_string(image)
            else:
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from file: {e}")
            return ""
    
    def _answer_or_do_further_processing(self, query: str, extracted_contents: Dict[str, str]) -> Dict[str, Any]:
        """One API call to answer the question directly or decide if further processing is needed."""
        if not self.llm_provider.is_available():
            # Fallback: simple text matching
            relevant_parts = []
            for doc_id, content in extracted_contents.items():
                if query.lower() in content.lower():
                    relevant_parts.append(f"Document {doc_id}: {content[:500]}...")
            return {
                'direct_answer': "\n\n".join(relevant_parts),
                'relevant_content': "\n\n".join(relevant_parts),
                'needs_processing': False,
                'instructions': None
            }
        
        try:
            # Combine all content
            all_content = "\n\n".join([
                f"Document {doc_id}:\n{content}" 
                for doc_id, content in extracted_contents.items()
            ])
            
            prompt = f"""
Given the following search query and document contents, provide a direct answer to the question and determine if additional processing is needed.

Search Query: "{query}"

Document Contents:
{all_content}

Your task:
1. Provide a direct, concise answer to the question based on the document contents
2. Extract the most relevant information that supports your answer
3. Determine if the answer needs additional processing to be more complete or accurate
4. If processing is needed, provide specific instructions for what type of processing would be most helpful

Additional processing could include any operation that would improve the answer to the query. Be specific about what processing is needed based on the query and content.

Instructions for the direct answer:
- Answer the question directly and concisely
- If the information is not available in the documents, say "Information not found in the documents"
- If you find partial information, provide what you can find
- Be specific and factual
- Use bullet points or numbered lists if appropriate
- Keep the answer under 200 words

Respond with valid JSON format only:
{{
    "direct_answer": "direct answer to the question",
    "relevant_content": "extracted relevant information that supports the answer",
    "needs_processing": true/false,
    "instructions": "specific processing instructions if needed, or null if not needed"
}}

Response:"""

            response = self.llm_provider.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.1
            )
            
            # Parse JSON response
            import json
            content = response.choices[0].message.content.strip()
            
            try:
                result = json.loads(content)
                
                # Validate required fields
                if not isinstance(result, dict):
                    raise ValueError("Response is not a JSON object")
                
                required_fields = ['direct_answer', 'relevant_content', 'needs_processing', 'instructions']
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing '{field}' field")
                
                # Ensure needs_processing is boolean
                if not isinstance(result["needs_processing"], bool):
                    result["needs_processing"] = bool(result["needs_processing"])
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response content: {content}")
                
                # Fallback: return safe default
                return {
                    'direct_answer': "Error processing content with LLM",
                    'relevant_content': "Error processing content with LLM",
                    'needs_processing': False,
                    'instructions': None
                }
            
        except Exception as e:
            logger.error(f"Error answering question and deciding processing: {e}")
            return {
                'direct_answer': "Error processing content with LLM",
                'relevant_content': "Error processing content with LLM",
                'needs_processing': False,
                'instructions': None
            }
    
    
    def _perform_additional_processing(
        self, 
        query: str, 
        relevant_content: str, 
        instructions: str
    ) -> str:
        """Perform additional processing based on LLM instructions."""
        if not self.llm_provider.is_available():
            return relevant_content
        
        try:
            prompt = f"""
Process the following content according to the specific instructions.

Search Query: "{query}"

Content to Process: "{relevant_content}"

Processing Instructions: "{instructions}"

Please process the content according to the instructions and return the final result.

Processed Result:"""

            response = self.llm_provider.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.2
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error performing additional processing: {e}")
            return relevant_content
