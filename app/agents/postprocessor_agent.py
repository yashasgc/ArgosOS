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
            
            # Step 3: Generate a direct answer to the query
            direct_answer = self._generate_direct_answer(query, extracted_contents)
            
            # Step 4: Use LLM to find relevant content based on query
            relevant_content = self._find_relevant_content(query, extracted_contents)
            
            # Step 5: Check if additional processing is needed
            processing_decision = self._decide_additional_processing(query, relevant_content)
            
            # Step 6: Perform additional processing if needed
            if processing_decision['needs_processing']:
                final_result = self._perform_additional_processing(
                    query, 
                    relevant_content, 
                    processing_decision['instructions']
                )
            else:
                final_result = relevant_content
            
            # Format results with direct answer
            results['direct_answer'] = direct_answer
            results['processed_documents'] = [{
                'document_id': doc.id,
                'title': doc.title,
                'relevant_content': final_result,
                'processing_applied': processing_decision['needs_processing']
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
    
    def _generate_direct_answer(self, query: str, extracted_contents: Dict[str, str]) -> str:
        """Generate a direct answer to the query based on document contents."""
        if not self.llm_provider.is_available():
            return "LLM not available for generating direct answer"
        
        try:
            # Combine all content
            all_content = "\n\n".join([
                f"Document {doc_id}:\n{content}" 
                for doc_id, content in extracted_contents.items()
            ])
            
            prompt = f"""
Based on the following documents, provide a direct and concise answer to the question.

Question: "{query}"

Documents:
{all_content}

Instructions:
- Answer the question directly and concisely
- If the information is not available in the documents, say "Information not found in the documents"
- If you find partial information, provide what you can find
- Be specific and factual
- Use bullet points or numbered lists if appropriate
- Keep the answer under 200 words

Answer:"""

            response = self.llm_provider.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating direct answer: {e}")
            return "Error generating answer"
    
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
    
    def _find_relevant_content(self, query: str, extracted_contents: Dict[str, str]) -> str:
        """Use LLM to find relevant content based on query."""
        if not self.llm_provider.is_available():
            # Fallback: simple text matching
            relevant_parts = []
            for doc_id, content in extracted_contents.items():
                if query.lower() in content.lower():
                    relevant_parts.append(f"Document {doc_id}: {content[:500]}...")
            return "\n\n".join(relevant_parts)
        
        try:
            # Combine all content
            all_content = "\n\n".join([
                f"Document {doc_id}:\n{content}" 
                for doc_id, content in extracted_contents.items()
            ])
            
            prompt = f"""
Given the following search query and document contents, extract only the most relevant information that directly answers or relates to the query.

Search Query: "{query}"

Document Contents:
{all_content}

Please extract and return only the relevant information that directly relates to the query. Be concise and focused.

Relevant Information:"""

            response = self.llm_provider.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error finding relevant content: {e}")
            return "Error processing content with LLM"
    
    def _decide_additional_processing(self, query: str, relevant_content: str) -> Dict[str, Any]:
        """Decide if additional processing is needed and what instructions to use."""
        if not self.llm_provider.is_available():
            return {
                'needs_processing': False,
                'instructions': None
            }
        
        try:
            prompt = f"""
Based on the search query and relevant content, determine if additional processing is needed.

Search Query: "{query}"

Relevant Content: "{relevant_content}"

Consider if the content needs:
- Summarization
- Analysis
- Comparison
- Formatting
- Translation
- Or any other specific processing

Respond with valid JSON format only:
{{
    "needs_processing": true,
    "instructions": "specific instructions for processing if needed"
}}

or

{{
    "needs_processing": false,
    "instructions": null
}}

Decision:"""

            response = self.llm_provider.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse JSON response with better error handling
            import json
            content = response.choices[0].message.content.strip()
            
            try:
                # Try to parse as JSON
                decision = json.loads(content)
                
                # Validate required fields
                if not isinstance(decision, dict):
                    raise ValueError("Response is not a JSON object")
                
                if "needs_processing" not in decision:
                    raise ValueError("Missing 'needs_processing' field")
                
                if "instructions" not in decision:
                    raise ValueError("Missing 'instructions' field")
                
                # Ensure needs_processing is boolean
                if not isinstance(decision["needs_processing"], bool):
                    decision["needs_processing"] = bool(decision["needs_processing"])
                
                return decision
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response content: {content}")
                
                # Fallback: return safe default
                return {
                    'needs_processing': False,
                    'instructions': None
                }
            
        except Exception as e:
            logger.error(f"Error deciding additional processing: {e}")
            return {
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
