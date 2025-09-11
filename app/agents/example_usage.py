"""
Example usage of the IngestAgent and RetrievalAgent
"""
from pathlib import Path
from sqlalchemy.orm import Session

from app.agents.ingest_agent import IngestAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.postprocessor_agent import PostProcessorAgent
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider import DisabledLLMProvider
from app.db.engine import get_db


def example_ingest_single_file():
    """Example of ingesting a single file"""
    # Initialize LLM provider (use DisabledLLMProvider if no API key)
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        print("OpenAI not available, using disabled provider")
        llm_provider = DisabledLLMProvider()
    
    # Create IngestAgent
    agent = IngestAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Example file path (replace with actual file)
        file_path = Path("example_document.pdf")
        
        if not file_path.exists():
            print(f"Example file {file_path} not found. Please provide a real file path.")
            return
        
        # Check if file is supported
        if not agent.is_file_supported(file_path):
            print(f"File type not supported: {file_path}")
            return
        
        # Ingest the file
        document, errors = agent.ingest_file(file_path, db)
        
        if document:
            print(f"Successfully ingested: {document.title}")
            print(f"Document ID: {document.id}")
            print(f"Summary: {document.summary}")
            print(f"Tags: {[tag.name for tag in document.tags]}")
        else:
            print("Failed to ingest file")
            for error in errors:
                print(f"Error: {error}")
    
    finally:
        db.close()


def example_ingest_multiple_files():
    """Example of ingesting multiple files"""
    # Initialize LLM provider
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        llm_provider = DisabledLLMProvider()
    
    # Create IngestAgent
    agent = IngestAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Example file paths (replace with actual files)
        file_paths = [
            Path("document1.pdf"),
            Path("document2.docx"),
            Path("document3.txt")
        ]
        
        # Filter to only existing files
        existing_files = [fp for fp in file_paths if fp.exists()]
        
        if not existing_files:
            print("No example files found. Please provide real file paths.")
            return
        
        # Ingest all files
        documents, errors = agent.ingest_multiple_files(existing_files, db)
        
        print(f"Successfully ingested {len(documents)} documents")
        for doc in documents:
            print(f"- {doc.title} (ID: {doc.id})")
        
        if errors:
            print(f"\nErrors encountered:")
            for error in errors:
                print(f"- {error}")
    
    finally:
        db.close()


def example_reprocess_document():
    """Example of reprocessing an existing document"""
    # Initialize LLM provider
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        llm_provider = DisabledLLMProvider()
    
    # Create IngestAgent
    agent = IngestAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Example document ID (replace with actual ID)
        document_id = "your-document-id-here"
        
        # Reprocess the document
        success, errors = agent.reprocess_document(document_id, db)
        
        if success:
            print(f"Successfully reprocessed document {document_id}")
        else:
            print(f"Failed to reprocess document {document_id}")
            for error in errors:
                print(f"Error: {error}")
    
    finally:
        db.close()


def example_search_documents():
    """Example of searching documents using LLM-generated SQL"""
    # Initialize LLM provider
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        llm_provider = DisabledLLMProvider()
    
    # Create RetrievalAgent
    agent = RetrievalAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Example search queries
        queries = [
            "find all PDF documents",
            "show me recent documents",
            "find large files",
            "count total documents",
            "show documents with machine learning tags"
        ]
        
        for query in queries:
            print(f"\nQuery: '{query}'")
            
            # Search documents using LLM-generated SQL
            results = agent.search_documents(query, db, limit=5)
            
            print(f"Generated SQL: {results['sql_query']}")
            print(f"Found {results['total_found']} documents")
            
            if results['errors']:
                print(f"Errors: {results['errors']}")
            else:
                for i, doc in enumerate(results['documents'], 1):
                    print(f"  {i}. {doc['title']} ({doc['mime_type']})")
    
    finally:
        db.close()


def example_get_document_content():
    """Example of retrieving document content"""
    # Initialize LLM provider
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        llm_provider = DisabledLLMProvider()
    
    # Create RetrievalAgent
    agent = RetrievalAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Example document ID (replace with actual ID)
        document_id = "your-document-id-here"
        
        print(f"Retrieving content for document: {document_id}")
        
        # Get document content
        content = agent.get_document_content(document_id, db)
        
        if content and 'error' not in content:
            print(f"Title: {content['title']}")
            print(f"Summary: {content['summary']}")
            print(f"Tags: {content['tags']}")
            print(f"Content preview: {content['content'][:200]}...")
        else:
            print(f"Error: {content.get('error', 'Unknown error')}")
    
    finally:
        db.close()


def example_find_related_documents():
    """Example of finding related documents"""
    # Initialize LLM provider
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        llm_provider = DisabledLLMProvider()
    
    # Create RetrievalAgent
    agent = RetrievalAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Example document ID (replace with actual ID)
        document_id = "your-document-id-here"
        
        print(f"Finding documents related to: {document_id}")
        
        # Find related documents
        related = agent.get_related_documents(document_id, db, limit=5)
        
        if related:
            print(f"Found {len(related)} related documents:")
            for i, doc in enumerate(related, 1):
                print(f"\n{i}. {doc['title']}")
                print(f"   Similarity: {doc['overlap_score']:.2f}")
                print(f"   Shared tags: {doc['shared_tags']}")
        else:
            print("No related documents found")
    
    finally:
        db.close()


def example_advanced_search():
    """Example of advanced filter search using LLM-generated SQL"""
    # Initialize LLM provider
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        llm_provider = DisabledLLMProvider()
    
    # Create RetrievalAgent
    agent = RetrievalAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        print("Advanced filter search using LLM-generated SQL:")
        
        # Search with natural language filter descriptions
        filter_descriptions = [
            "find PDF documents with machine learning or AI tags",
            "show documents imported in the last 30 days",
            "find large files over 1MB",
            "show documents with 'algorithm' in the title"
        ]
        
        for description in filter_descriptions:
            print(f"\nFilter: '{description}'")
            
            results = agent.search_by_filters(
                db,
                filters_description=description,
                limit=5
            )
            
            print(f"Generated SQL: {results['sql_query']}")
            print(f"Found {results['total_found']} documents")
            
            if results.get('error'):
                print(f"Error: {results['error']}")
            else:
                for i, doc in enumerate(results['documents'], 1):
                    print(f"  {i}. {doc['title']} ({doc['mime_type']})")
    
    finally:
        db.close()


def example_get_tag_statistics():
    """Example of getting tag statistics"""
    # Initialize LLM provider
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        llm_provider = DisabledLLMProvider()
    
    # Create RetrievalAgent
    agent = RetrievalAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        print("Tag statistics:")
        
        # Get all tags with statistics
        tags = agent.get_all_tags(db)
        
        if tags:
            print(f"Total tags: {len(tags)}")
            print("\nTop 10 most used tags:")
            for i, tag in enumerate(tags[:10], 1):
                print(f"{i:2d}. {tag['name']}: {tag['document_count']} documents")
        else:
            print("No tags found")
    
    finally:
        db.close()


def example_process_documents():
    """Example of processing documents with PostProcessorAgent"""
    # Initialize LLM provider
    llm_provider = OpenAIProvider()
    if not llm_provider.is_available():
        llm_provider = DisabledLLMProvider()
    
    # Create agents
    retrieval_agent = RetrievalAgent(llm_provider)
    postprocessor_agent = PostProcessorAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Step 1: Search for documents using RetrievalAgent
        print("Step 1: Searching for documents...")
        search_results = retrieval_agent.search_documents(
            query="find all PDF documents",
            db=db,
            limit=3
        )
        
        print(f"Found {search_results['total_found']} documents")
        print(f"Generated SQL: {search_results['sql_query']}")
        
        if not search_results['documents']:
            print("No documents found to process")
            return
        
        # Step 2: Process documents with PostProcessorAgent
        print("\nStep 2: Processing documents with OCR and LLM...")
        processing_results = postprocessor_agent.process_documents(
            retrieval_results=search_results,
            db=db,
            extraction_query="extract amounts, dates, and items"
        )
        
        print(f"Processed {processing_results['total_processed']} documents")
        
        # Step 3: Show results
        for i, doc_result in enumerate(processing_results['processed_documents'], 1):
            print(f"\n--- Document {i}: {doc_result['document_title']} ---")
            
            if doc_result['errors']:
                print(f"Errors: {doc_result['errors']}")
            else:
                print(f"Extracted text length: {len(doc_result['extracted_text'])} characters")
                print(f"Extracted fields: {doc_result['extracted_fields']}")
                print(f"Calculations: {doc_result['calculations']}")
        
        # Step 4: Get processing summary
        summary = postprocessor_agent.get_processing_summary(processing_results)
        print(f"\n--- Processing Summary ---")
        print(f"Total documents: {summary['total_documents']}")
        print(f"Successful extractions: {summary['successful_extractions']}")
        print(f"Failed extractions: {summary['failed_extractions']}")
        print(f"Common fields found: {summary['common_fields_found']}")
    
    finally:
        db.close()




if __name__ == "__main__":
    print("Agents Example Usage")
    print("=" * 30)
    
    print("\n=== IngestAgent Examples ===")
    print("\n1. Single file ingestion:")
    example_ingest_single_file()
    
    print("\n2. Multiple files ingestion:")
    example_ingest_multiple_files()
    
    print("\n3. Document reprocessing:")
    example_reprocess_document()
    
    print("\n=== RetrievalAgent Examples ===")
    print("\n4. Search documents:")
    example_search_documents()
    
    print("\n5. Get document content:")
    example_get_document_content()
    
    print("\n6. Find related documents:")
    example_find_related_documents()
    
    print("\n7. Advanced filter search:")
    example_advanced_search()
    
    print("\n8. Tag statistics:")
    example_get_tag_statistics()
    
    print("\n=== PostProcessorAgent Examples ===")
    print("\n9. Process documents with OCR and LLM:")
    example_process_documents()
