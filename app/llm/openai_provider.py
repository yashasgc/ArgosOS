from typing import List
import logging
import json
import re
from openai import OpenAI
from .provider import LLMProvider
from app.constants import (
    VISION_MAX_TOKENS, SQL_MAX_TOKENS
)

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """OpenAI GPT-based LLM provider"""
    
    def __init__(self):
        try:
            from app.config import settings
            self.api_key = getattr(settings, 'openai_api_key', None)
            self.model = getattr(settings, 'openai_model', 'gpt-3.5-turbo')
        except ImportError:
            self.api_key = None
            self.model = 'gpt-3.5-turbo'
        
        # Initialize OpenAI client
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        return bool(self.api_key and self.api_key.strip() and self.client)
    
    def summarize(self, text: str) -> str:
        """Generate a summary using OpenAI"""
        if not self.is_available() or not self.client:
            return ""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates comprehensive summaries of documents. Provide a detailed, informative summary focusing on the main topics and key information. Return only the summary text, no additional formatting or explanations."},
                    {"role": "user", "content": f"Please summarize the following document content:\n\n{text}"}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {e}")
            # Fallback to simple truncation
            words = text.split()
            if len(words) <= 50:
                return text
            else:
                return " ".join(words[:50]) + "..."
    
    def extract_text_from_image(self, image_data: bytes, filename: str) -> str:
        """Extract text from image using OpenAI Vision API"""
        if not self.is_available() or not self.client:
            return ""
        
        try:
            import base64
            import mimetypes
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = 'image/jpeg'  # Default fallback
            
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            data_url = f"data:{mime_type};base64,{base64_image}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o for vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image. Return only the extracted text, preserving line breaks and formatting. Do not add any explanations or comments."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=VISION_MAX_TOKENS,
                temperature=0.1
            )
            
            extracted_text = response.choices[0].message.content.strip()
            logger.info(f"Vision API extracted {len(extracted_text)} characters from image")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Vision API extraction failed: {e}")
            return ""

    def generate_tags(self, text: str) -> List[str]:
        """Generate tags using OpenAI"""
        if not self.is_available() or not self.client:
            return []
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates comprehensive and relevant tags for documents. Return ONLY a valid JSON array of relevant tags (lowercase, no spaces, use hyphens for multi-word tags). Focus on the main topics, document type, key concepts, and any important details. Generate as many relevant tags as needed for thorough categorization. Do not include any other text or explanation."},
                    {"role": "user", "content": f"Generate relevant tags for this document content:\n\n{text}"}
                ],
                temperature=0.3
            )
            
            # Parse JSON response with robust error handling
            content = response.choices[0].message.content.strip()
            
            try:
                # First try to parse the entire response as JSON
                tags = json.loads(content)
                if isinstance(tags, list):
                    return [str(tag).lower().strip() for tag in tags if tag][:7]
                else:
                    raise ValueError("Response is not a list")
                    
            except (json.JSONDecodeError, ValueError):
                try:
                    # Try to extract JSON array from response using regex
                    json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                    if json_match:
                        tags = json.loads(json_match.group())
                        if isinstance(tags, list):
                            return [str(tag).lower().strip() for tag in tags if tag][:7]
                except (json.JSONDecodeError, AttributeError):
                    pass
                
                # Fallback: split by common delimiters and clean up
                logger.warning(f"JSON parsing failed, using fallback for content: {content}")
                tags = re.split(r'[,;\n]', content)
                tags = [tag.strip().lower().strip('"\'[]') for tag in tags if tag.strip()]
                return [tag for tag in tags if tag][:7]
            
        except Exception as e:
            logger.error(f"Error generating tags with OpenAI: {e}")
            # Fallback to simple keyword-based tagging
            tags = []
            text_lower = text.lower()
            
            if "pdf" in text_lower or "document" in text_lower:
                tags.append("document")
            if "report" in text_lower:
                tags.append("report")
            if "contract" in text_lower or "agreement" in text_lower:
                tags.append("legal")
            if "invoice" in text_lower or "bill" in text_lower:
                tags.append("financial")
            if "manual" in text_lower or "guide" in text_lower:
                tags.append("manual")
            
            return tags[:5]
    
    def generate_sql_query(self, query: str, schema_info: str = "") -> str:
        """Generate SQL query from natural language using OpenAI"""
        if not self.is_available() or not self.client:
            return ""
        
        try:
            # Default schema information for the documents database
            default_schema = """
            Database Schema:
            - documents table: id (TEXT), title (TEXT), summary (TEXT), mime_type (TEXT), 
              size_bytes (INTEGER), created_at (INTEGER), imported_at (INTEGER)
            - tags table: id (INTEGER), name (TEXT)
            - document_tags table: document_id (TEXT), tag_id (INTEGER)
            
            Common queries:
            - Find documents by title: SELECT * FROM documents WHERE title LIKE '%keyword%'
            - Find documents by tags: SELECT d.* FROM documents d JOIN document_tags dt ON d.id = dt.document_id JOIN tags t ON dt.tag_id = t.id WHERE t.tag = 'tag_name'
            - Find documents by date range: SELECT * FROM documents WHERE imported_at BETWEEN start_timestamp AND end_timestamp
            - Find documents by MIME type: SELECT * FROM documents WHERE mime_type = 'application/pdf'
            """
            
            schema = schema_info if schema_info else default_schema
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a SQL expert. Generate SQL queries based on natural language requests. Use the following database schema:\n\n{schema}\n\nReturn only the SQL query, no explanations. Use proper SQL syntax and parameterized queries where appropriate."},
                    {"role": "user", "content": f"Generate a SQL query for: {query}"}
                ],
                max_tokens=SQL_MAX_TOKENS,
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the response (remove markdown formatting if present)
            sql_query = re.sub(r'^```sql\s*', '', sql_query)
            sql_query = re.sub(r'\s*```$', '', sql_query)
            
            return sql_query
                
        except Exception as e:
            logger.error(f"Error generating SQL query with OpenAI: {e}")
            # Fallback to simple keyword-based SQL generation
            query_lower = query.lower()
            
            if "find" in query_lower or "search" in query_lower or "get" in query_lower:
                if "pdf" in query_lower:
                    return "SELECT * FROM documents WHERE mime_type = 'application/pdf'"
                elif "recent" in query_lower or "latest" in query_lower:
                    return "SELECT * FROM documents ORDER BY imported_at DESC LIMIT 10"
                elif "large" in query_lower or "big" in query_lower:
                    return "SELECT * FROM documents ORDER BY size_bytes DESC LIMIT 10"
                else:
                    return "SELECT * FROM documents WHERE title LIKE '%{}%' OR summary LIKE '%{}%'".format(query, query)
            elif "count" in query_lower:
                return "SELECT COUNT(*) as total_documents FROM documents"
            elif "tags" in query_lower:
                return "SELECT t.tag, COUNT(dt.document_id) as document_count FROM tags t LEFT JOIN document_tags dt ON t.id = dt.tag_id GROUP BY t.id, t.tag ORDER BY document_count DESC"
            else:
                return "SELECT * FROM documents WHERE title LIKE '%{}%' OR summary LIKE '%{}%'".format(query, query)