# Agents Package

This package contains the agentic architecture components for ArgosOS. Agents are responsible for specific tasks in the document processing pipeline.

## IngestAgent

The `IngestAgent` is responsible for ingesting files, extracting text, generating tags and summaries using LLM APIs, and storing everything in the SQLite database.

### Features

- **File Processing**: Supports PDF, DOCX, TXT, Markdown, and image files (JPEG, PNG, TIFF, BMP)
- **Text Extraction**: Uses appropriate extractors for different file types
- **AI Processing**: Generates tags and summaries using LLM providers
- **Database Storage**: Stores documents, text, tags, and summaries in SQLite
- **Deduplication**: Prevents duplicate documents using content hashing
- **Batch Processing**: Can process multiple files at once
- **Reprocessing**: Can update existing documents with new AI-generated content

### Usage

#### Basic Setup

```python
from app.agents.ingest_agent import IngestAgent
from app.llm.openai_provider import OpenAIProvider
from app.db.engine import get_db

# Initialize LLM provider
llm_provider = OpenAIProvider()

# Create IngestAgent
agent = IngestAgent(llm_provider)

# Get database session
db = next(get_db())
```

#### Ingest a Single File

```python
from pathlib import Path

file_path = Path("document.pdf")
document, errors = agent.ingest_file(file_path, db)

if document:
    print(f"Successfully ingested: {document.title}")
    print(f"Summary: {document.summary}")
    print(f"Tags: {[tag.name for tag in document.tags]}")
else:
    print("Failed to ingest file")
    for error in errors:
        print(f"Error: {error}")
```

#### Ingest Multiple Files

```python
file_paths = [
    Path("document1.pdf"),
    Path("document2.docx"),
    Path("document3.txt")
]

documents, errors = agent.ingest_multiple_files(file_paths, db)
print(f"Successfully ingested {len(documents)} documents")
```

#### Reprocess an Existing Document

```python
document_id = "your-document-id"
success, errors = agent.reprocess_document(document_id, db)

if success:
    print("Document reprocessed successfully")
```

### Supported File Types

- **PDF**: `application/pdf`
- **Word Documents**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Text Files**: `text/plain`, `text/markdown`
- **Images**: `image/jpeg`, `image/png`, `image/tiff`, `image/bmp`

### Error Handling

The IngestAgent returns detailed error messages for various failure scenarios:

- File not found
- Unsupported file type
- Text extraction failure
- LLM processing errors
- Database errors

### Database Schema

The IngestAgent works with the following database tables:

- **documents**: Stores file metadata, content hash, and AI-generated summary
- **tags**: Stores tag names
- **document_tags**: Many-to-many relationship between documents and tags

### LLM Integration

The IngestAgent uses the LLM provider interface to:

1. **Generate Summaries**: Create concise summaries of document content
2. **Generate Tags**: Extract relevant keywords and categories
3. **Error Handling**: Gracefully handle LLM API failures

### Example

See `example_usage.py` for complete working examples of how to use the IngestAgent.

### Dependencies

- `sqlalchemy`: Database ORM
- `pydantic`: Data validation
- `pathlib`: File path handling
- `mimetypes`: MIME type detection
- `hashlib`: Content hashing
- `app.files.extractors`: Text extraction
- `app.llm.provider`: LLM integration
- `app.db.crud`: Database operations

## RetrievalAgent

The `RetrievalAgent` is responsible for processing search queries using LLM-generated SQL and retrieving relevant documents from the SQLite database.

### Features

- **LLM-Generated SQL**: Uses LLM to generate SQL queries from natural language
- **Secure Query Execution**: Uses parameterized queries to prevent SQL injection
- **Content Retrieval**: Retrieves full document content and metadata
- **Input Validation**: Validates all inputs for security and data integrity
- **Error Handling**: Comprehensive error handling with detailed error messages

### Usage

#### Basic Setup

```python
from app.agents.retrieval_agent import RetrievalAgent
from app.llm.openai_provider import OpenAIProvider
from app.db.engine import get_db

# Initialize LLM provider
llm_provider = OpenAIProvider()

# Create RetrievalAgent
agent = RetrievalAgent(llm_provider)

# Get database session
db = next(get_db())
```

#### Search Documents

```python
# Basic search using LLM-generated SQL
results = agent.search_documents("machine learning algorithms", db)

print(f"Found {results['total_found']} documents")
print(f"SQL Query: {results['sql_query']}")
for doc in results['documents']:
    print(f"- {doc['title']}: {doc['summary']}")
```

#### Get Document Content

```python
# Get full document content with security validation
content = agent.get_document_content("document-id", db)

if content and 'error' not in content:
    print(f"Title: {content['title']}")
    print(f"Content: {content['content'][:200]}...")
else:
    print(f"Error: {content.get('error', 'Unknown error')}")
```

#### Search with Custom Schema

```python
# Provide custom database schema for better SQL generation
custom_schema = """
Database Schema:
- documents table: id, title, summary, mime_type, size_bytes, created_at, imported_at
- tags table: id, name
- document_tags table: document_id, tag_id
"""

results = agent.search_documents(
    "find PDF documents about AI", 
    db, 
    limit=5,
    schema_info=custom_schema
)
```

### Search Process

The RetrievalAgent uses LLM-generated SQL for document retrieval:

1. **Input Validation**: Validates query and parameters for security
2. **LLM SQL Generation**: Uses LLM to generate SQL query from natural language
3. **Secure Execution**: Executes parameterized SQL query safely
4. **Result Formatting**: Formats results for consistent API responses

### Security Features

- **SQL Injection Prevention**: Uses parameterized queries
- **Input Validation**: Validates all inputs before processing
- **Query Limits**: Enforces reasonable limits on result sets
- **Error Handling**: Secure error messages without information leakage

### Error Handling

The RetrievalAgent provides comprehensive error handling:

- **LLM Failures**: Gracefully handles LLM API unavailability
- **SQL Errors**: Catches and reports SQL execution errors
- **Input Validation**: Returns clear error messages for invalid inputs
- **File System Errors**: Handles missing or inaccessible files
- **Database Errors**: Secure error reporting without information leakage

### Performance Features

- **Query Limits**: Configurable result limits (max 1000) to prevent resource exhaustion
- **Efficient SQL**: Uses optimized database queries
- **Input Sanitization**: Prevents malicious input processing
- **Resource Management**: Handles large result sets efficiently

### Example

```python
# Complete search workflow
def search_and_retrieve(query: str, db: Session):
    agent = RetrievalAgent(OpenAIProvider())
    
    # Search for documents
    results = agent.search_documents(query, db, limit=5)
    
    if not results['documents']:
        print("No documents found")
        return
    
    # Get content for the first result
    first_doc = results['documents'][0]
    content = agent.get_document_content(first_doc['id'], db)
    
    if content and 'content' in content:
        print(f"Found: {content['title']}")
        print(f"Content preview: {content['content'][:300]}...")
        
        # Find related documents
        related = agent.get_related_documents(first_doc['id'], db)
        if related:
            print(f"\nRelated documents:")
            for doc in related[:3]:
                print(f"- {doc['title']}")
```

### Dependencies

- `sqlalchemy`: Database ORM and query building
- `app.llm.provider`: LLM integration for query processing
- `app.db.crud`: Database operations
- `app.files.extractors`: Text extraction for content retrieval

## PostProcessorAgent

The `PostProcessorAgent` is responsible for processing documents retrieved by RetrievalAgent using OCR and LLM-based analysis. It follows a simple 3-step process: OCR extraction, LLM processing, and conditional post-processing.

### Features

- **OCR Text Extraction**: Extracts text from documents using appropriate extractors
- **LLM-Based Analysis**: Uses LLM to analyze query + extracted text and determine processing needs
- **Intelligent Post-Processing**: LLM decides if and what type of post-processing is needed
- **Input Validation**: Validates all inputs for security and data integrity
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Batch Processing**: Process multiple documents from RetrievalAgent results

### Usage

#### Basic Setup

```python
from app.agents.postprocessor_agent import PostProcessorAgent
from app.llm.openai_provider import OpenAIProvider
from app.db.engine import get_db

# Initialize LLM provider
llm_provider = OpenAIProvider()

# Create PostProcessorAgent
agent = PostProcessorAgent(llm_provider)

# Get database session
db = next(get_db())
```

#### Process Documents from RetrievalAgent

```python
# First, get documents from RetrievalAgent
retrieval_agent = RetrievalAgent(llm_provider)
search_results = retrieval_agent.search_documents("find receipts", db, limit=5)

# Then process them with PostProcessorAgent
postprocessor_agent = PostProcessorAgent(llm_provider)
results = postprocessor_agent.process_documents(
    retrieval_results=search_results,
    db=db,
    extraction_query="extract amounts and items"
)

print(f"Processed {results['total_processed']} documents")
for doc_result in results['processed_documents']:
    print(f"Document: {doc_result['document_title']}")
    print(f"LLM Response: {doc_result['llm_response']}")
    print(f"Final Response: {doc_result['final_response']}")
```

#### Complete Workflow

```python
def analyze_documents(query: str, db: Session):
    """Complete document analysis workflow"""
    # Step 1: Search for documents
    retrieval_agent = RetrievalAgent(OpenAIProvider())
    search_results = retrieval_agent.search_documents(query, db, limit=10)
    
    if not search_results['documents']:
        print("No documents found")
        return
    
    # Step 2: Process documents
    postprocessor_agent = PostProcessorAgent(OpenAIProvider())
    results = postprocessor_agent.process_documents(
        search_results, 
        db, 
        "extract key information"
    )
    
    # Step 3: Display results
    for doc_result in results['processed_documents']:
        print(f"\nDocument: {doc_result['document_title']}")
        if doc_result['errors']:
            print(f"Errors: {doc_result['errors']}")
        else:
            print(f"Extracted: {doc_result['extracted_text'][:200]}...")
            print(f"LLM Analysis: {doc_result['llm_response']}")
            if doc_result['final_response']:
                print(f"Post-Processed: {doc_result['final_response']}")
```

### Processing Flow

The PostProcessorAgent follows a simple 3-step process:

#### 1. OCR Text Extraction
- Uses appropriate text extractors based on file type
- Handles PDF, DOCX, images, and other supported formats
- Returns extracted text or empty string if extraction fails

#### 2. LLM Analysis
- LLM analyzes the query + extracted text
- Determines if post-processing is needed
- Returns structured response with extracted data and instructions

#### 3. Conditional Post-Processing
- If LLM determines post-processing is needed, runs additional LLM processing
- Uses LLM's own instructions for what type of post-processing to perform
- Returns final processed result

### LLM Decision Making

The LLM makes intelligent decisions about:
- **Data Extraction**: What relevant data to extract from the text
- **Post-Processing Need**: Whether additional processing is required
- **Processing Instructions**: What type of post-processing to perform
- **Result Formatting**: How to format the final response

### Use Cases

#### Receipt Analysis
```python
# Find and analyze receipts
retrieval_agent = RetrievalAgent(OpenAIProvider())
search_results = retrieval_agent.search_documents("receipts and invoices", db)

postprocessor_agent = PostProcessorAgent(OpenAIProvider())
results = postprocessor_agent.process_documents(
    search_results, 
    db, 
    "extract items, amounts, and calculate totals"
)

# LLM will decide if post-processing (like totaling) is needed
for doc_result in results['processed_documents']:
    if doc_result['final_response'].get('needs_post_processing'):
        print(f"Processed: {doc_result['final_response']['post_processed_result']}")
```

#### Document Summarization
```python
# Find and summarize documents
search_results = retrieval_agent.search_documents("research papers", db)
results = postprocessor_agent.process_documents(
    search_results, 
    db, 
    "summarize key findings and extract important data points"
)
```

#### Data Extraction
```python
# Extract specific data from documents
search_results = retrieval_agent.search_documents("financial reports", db)
results = postprocessor_agent.process_documents(
    search_results, 
    db, 
    "extract revenue, profit, and expense figures"
)
```

### Error Handling

The PostProcessorAgent provides comprehensive error handling:

- **Input Validation**: Validates all inputs before processing
- **OCR Failures**: Handles text extraction errors gracefully
- **LLM Failures**: Manages LLM API unavailability
- **Document Retrieval**: Handles missing or inaccessible documents
- **Processing Errors**: Catches and reports processing failures

### Security Features

- **Input Validation**: Validates all inputs for security
- **File Size Limits**: Prevents processing of extremely large files
- **Error Sanitization**: Secure error messages without information leakage
- **Resource Management**: Prevents resource exhaustion

### Performance Features

- **Efficient Processing**: Streamlined 3-step process
- **LLM Optimization**: Uses LLM efficiently for decision making
- **Batch Processing**: Handles multiple documents efficiently
- **Memory Management**: Processes documents without excessive memory usage

### Dependencies

- `pathlib`: File path handling
- `sqlalchemy.orm`: Database session management
- `app.llm.provider`: LLM integration for analysis and decision making
- `app.files.extractors`: Text extraction from various file types
- `app.agents.retrieval_agent`: Document content retrieval
