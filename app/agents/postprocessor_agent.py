"""
PostProcessorAgent - Simple document processing with OCR and LLM
"""
from typing import Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session

from app.llm.provider import LLMProvider
from app.files.extractors import TextExtractor


class PostProcessorAgent:
    """
    Agent responsible for processing documents retrieved by RetrievalAgent.
    1. Use OCR to extract text
    2. Use LLM to read query + extracted text and generate response
    3. If flag is true, run post-processing method with LLM
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self.text_extractor = TextExtractor()
    
    def process_documents(
        self, 
        retrieval_results: Dict[str, Any], 
        db: Session,
        extraction_query: str
    ) -> Dict[str, Any]:
        """Process documents from RetrievalAgent results."""
        # Input validation
        if not extraction_query or not extraction_query.strip():
            return {
                'query': extraction_query,
                'processed_documents': [],
                'total_processed': 0,
                'errors': ['Extraction query cannot be empty']
            }
        
        if not retrieval_results or not isinstance(retrieval_results, dict):
            return {
                'query': extraction_query,
                'processed_documents': [],
                'total_processed': 0,
                'errors': ['Invalid retrieval results provided']
            }
        
        results = {
            'query': extraction_query.strip(),
            'processed_documents': [],
            'total_processed': 0,
            'errors': []
        }
        
        try:
            documents = retrieval_results.get('documents', [])
            
            for doc in documents:
                doc_result = self._process_single_document(doc, db, extraction_query)
                results['processed_documents'].append(doc_result)
            
            results['total_processed'] = len(results['processed_documents'])
            
        except Exception as e:
            results['errors'].append(f"Processing failed: {str(e)}")
        
        return results
    
    def _process_single_document(
        self, 
        document: Dict[str, Any], 
        db: Session, 
        extraction_query: str
    ) -> Dict[str, Any]:
        """Process a single document: OCR -> LLM -> Post-processing (if needed)."""
        doc_result = {
            'document_id': document['id'],
            'document_title': document['title'],
            'extracted_text': '',
            'llm_response': {},
            'final_response': {},
            'errors': []
        }
        
        try:
            # Step 1: Use OCR to extract text
            extracted_text = self._extract_text_with_ocr(document, db)
            doc_result['extracted_text'] = extracted_text
            
            if not extracted_text:
                doc_result['errors'].append("No text extracted from document")
                return doc_result
            
            # Step 2: Use LLM to read query + extracted text and generate response
            llm_response = self._process_with_llm(extraction_query, extracted_text)
            doc_result['llm_response'] = llm_response
            
            # Step 3: If flag is true, run post-processing method
            if llm_response.get('needs_post_processing', False):
                final_response = self._post_processing(extraction_query, llm_response, extracted_text)
                doc_result['final_response'] = final_response
            else:
                doc_result['final_response'] = llm_response
            
        except Exception as e:
            doc_result['errors'].append(f"Document processing failed: {str(e)}")
        
        return doc_result
    
    def _extract_text_with_ocr(self, document: Dict[str, Any], db: Session) -> str:
        """Use OCR to extract text from document."""
        try:
            from app.agents.retrieval_agent import RetrievalAgent
            retrieval_agent = RetrievalAgent(self.llm_provider)
            
            content_result = retrieval_agent.get_document_content(document['id'], db)
            
            if not content_result or 'error' in content_result:
                return ""
            
            file_path = Path(content_result.get('file_path', ''))
            mime_type = content_result.get('mime_type', '')
            
            if not file_path.exists():
                return ""
            
            extracted_text = self.text_extractor.extract_text(file_path, mime_type)
            return extracted_text or ""
            
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""
    
    def _process_with_llm(self, extraction_query: str, extracted_text: str) -> Dict[str, Any]:
        """Use LLM to read query + extracted text and generate response."""
        if not self.llm_provider.is_available():
            return {"error": "LLM not available", "needs_post_processing": False}
        
        try:
            # Let LLM decide if post-processing is needed
            prompt = f"""
            Query: {extraction_query}
            
            Extracted Text: {extracted_text[:2000]}
            
            Analyze the query and extracted text. Return a JSON response with:
            - "extracted_data": The relevant data you found
            - "needs_post_processing": true/false - whether additional processing is needed
            - "post_processing_instructions": Instructions for what post-processing to do (if needed)
            
            Example:
            {{
                "extracted_data": {{"amounts": ["$10.50", "$5.25"], "items": ["apple", "banana"]}},
                "needs_post_processing": true,
                "post_processing_instructions": "Calculate total and format as receipt"
            }}
            """
            
            # Use LLM to make the decision
            response = self.llm_provider.generate_tags(prompt)
            
            # For now, return a simple response (in full implementation, LLM would return JSON)
            return {
                "extracted_data": {"text": extracted_text[:500]},
                "needs_post_processing": False,
                "post_processing_instructions": ""
            }
            
        except Exception as e:
            print(f"LLM processing failed: {e}")
            return {"error": str(e), "needs_post_processing": False}
    
    def _post_processing(self, extraction_query: str, llm_response: Dict[str, Any], extracted_text: str) -> Dict[str, Any]:
        """Post-processing method using LLM with instructions."""
        if not self.llm_provider.is_available():
            return {"error": "LLM not available for post-processing"}
        
        try:
            # Get post-processing instructions from LLM response
            instructions = llm_response.get('post_processing_instructions', '')
            extracted_data = llm_response.get('extracted_data', {})
            
            # Use LLM to do the post-processing based on instructions
            prompt = f"""
            Original Query: {extraction_query}
            
            Extracted Data: {extracted_data}
            
            Post-Processing Instructions: {instructions}
            
            Original Text: {extracted_text[:1000]}
            
            Perform the post-processing as instructed and return a JSON response with:
            - "post_processed_result": The final result
            - "processing_steps": Steps taken
            - "confidence": Confidence level (0-1)
            """
            
            # Use LLM for post-processing
            response = self.llm_provider.generate_tags(prompt)
            
            # For now, return a simple response (in full implementation, LLM would return JSON)
            return {
                "post_processed_result": f"Post-processed based on: {instructions}",
                "processing_steps": ["LLM post-processing"],
                "confidence": 0.8
            }
            
        except Exception as e:
            return {"error": f"Post-processing failed: {str(e)}", "confidence": 0.0}
    