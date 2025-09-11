#!/usr/bin/env python3
"""
Demo script for the IngestAgent
This script demonstrates how to use the IngestAgent to ingest files into ArgosOS
"""
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from agents.ingest_agent import IngestAgent
from llm.openai_provider import OpenAIProvider
from llm.provider import DisabledLLMProvider
from db.engine import get_db
from config import settings


def main():
    """Main demo function"""
    print("ArgosOS IngestAgent Demo")
    print("=" * 30)
    
    # Initialize LLM provider
    if settings.llm_enabled and settings.openai_api_key:
        print("Using OpenAI provider")
        llm_provider = OpenAIProvider()
    else:
        print("Using disabled LLM provider (no API key)")
        llm_provider = DisabledLLMProvider()
    
    # Create IngestAgent
    agent = IngestAgent(llm_provider)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if any files were provided as command line arguments
        if len(sys.argv) > 1:
            file_paths = [Path(arg) for arg in sys.argv[1:]]
        else:
            # Use example files if no arguments provided
            file_paths = [
                Path("README.md"),
                Path("requirements.txt"),
                Path("config.env.example")
            ]
        
        # Filter to only existing files
        existing_files = [fp for fp in file_paths if fp.exists()]
        
        if not existing_files:
            print("No files found to ingest.")
            print("Usage: python ingest_demo.py [file1] [file2] ...")
            print("Or place some files in the current directory.")
            return
        
        print(f"Found {len(existing_files)} files to ingest:")
        for file_path in existing_files:
            print(f"  - {file_path}")
        
        # Check supported file types
        supported_files = [fp for fp in existing_files if agent.is_file_supported(fp)]
        unsupported_files = [fp for fp in existing_files if not agent.is_file_supported(fp)]
        
        if unsupported_files:
            print(f"\nUnsupported file types:")
            for file_path in unsupported_files:
                print(f"  - {file_path}")
        
        if not supported_files:
            print("No supported files found.")
            return
        
        print(f"\nIngesting {len(supported_files)} supported files...")
        
        # Ingest files
        documents, errors = agent.ingest_multiple_files(supported_files, db)
        
        # Display results
        print(f"\nSuccessfully ingested {len(documents)} documents:")
        for doc in documents:
            print(f"  - {doc.title} (ID: {doc.id})")
            if doc.summary:
                print(f"    Summary: {doc.summary[:100]}...")
            if doc.tags:
                print(f"    Tags: {[tag.name for tag in doc.tags]}")
        
        if errors:
            print(f"\nErrors encountered:")
            for error in errors:
                print(f"  - {error}")
        
        print(f"\nIngestion complete!")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()


