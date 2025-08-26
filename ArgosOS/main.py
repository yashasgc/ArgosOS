#!/usr/bin/env python3
"""
ArgosOS MVP - Database Example Runner

This script demonstrates the SQLite database layer for ArgosOS MVP.
It initializes the database, creates sample data, and shows basic operations.

Usage:
    python main.py
"""

import hashlib
import json
import time
from pathlib import Path

from db.engine import init_database, get_db_session
from db.models import Document, Tag, AuditLog


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def log_action(session, action: str, details: dict = None, actor: str = "system"):
    """Helper function to log actions to audit log"""
    log_entry = AuditLog(
        action=action,
        actor=actor,
        details=json.dumps(details) if details else None
    )
    session.add(log_entry)
    session.commit()
    return log_entry


def create_sample_data(session):
    """Create sample documents and tags"""
    print("📝 Creating sample data...")
    
    # Sample document content
    sample_content = """
    ArgosOS Backend MVP
    
    This is a sample document for testing the ArgosOS backend system.
    It demonstrates file processing, text extraction, and database storage.
    
    Key features:
    - File upload and processing
    - OCR text extraction
    - AI-powered summarization
    - Tag-based organization
    - Search and retrieval
    """
    
    # Create sample document
    content_hash = compute_content_hash(sample_content)
    storage_path = f"./data/blobs/{content_hash[:2]}/{content_hash}"
    
    # Ensure storage directory exists
    storage_dir = Path(storage_path).parent
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Write content to storage
    with open(storage_path, 'w') as f:
        f.write(sample_content)
    
    document = Document(
        title="argos_sample_document.txt",
        content_hash=content_hash,
        mime_type="text/plain",
        size_bytes=len(sample_content.encode('utf-8')),
        storage_path=storage_path,
        summary="A sample document demonstrating ArgosOS backend capabilities and features."
    )
    
    # Create sample tags
    tags_data = [
        "documentation",
        "sample",
        "argos",
        "backend",
        "testing"
    ]
    
    tags = []
    for tag_name in tags_data:
        # Check if tag already exists
        existing_tag = session.query(Tag).filter(Tag.name == tag_name.lower()).first()
        if existing_tag:
            tags.append(existing_tag)
        else:
            tag = Tag(name=tag_name.lower())
            session.add(tag)
            tags.append(tag)
    
    # Associate tags with document
    document.tags = tags
    
    # Add document to session
    session.add(document)
    session.commit()
    
    # Log the document creation
    log_action(session, "document_created", {
        "document_id": document.id,
        "title": document.title,
        "content_hash": document.content_hash,
        "tags": [tag.name for tag in document.tags]
    })
    
    print(f"✓ Created document: {document.title}")
    print(f"  - ID: {document.id}")
    print(f"  - Hash: {document.content_hash[:16]}...")
    print(f"  - Size: {document.size_bytes} bytes")
    print(f"  - Tags: {', '.join([tag.name for tag in document.tags])}")
    
    return document


def demonstrate_queries(session):
    """Demonstrate various database queries"""
    print("\n🔍 Demonstrating database queries...")
    
    # 1. Get all documents
    documents = session.query(Document).all()
    print(f"\n📄 Total documents in database: {len(documents)}")
    
    # 2. Find documents by tag
    backend_docs = session.query(Document).join(Document.tags).filter(Tag.name == "backend").all()
    print(f"📊 Documents tagged 'backend': {len(backend_docs)}")
    
    # 3. Get document with its tags
    for doc in documents:
        print(f"\n📋 Document: {doc.title}")
        print(f"   Summary: {doc.summary}")
        print(f"   Tags: {', '.join([tag.name for tag in doc.tags])}")
        print(f"   Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(doc.created_at / 1000))}")
    
    # 4. Show tag usage statistics
    print(f"\n🏷️  Tag statistics:")
    for tag in session.query(Tag).all():
        doc_count = len(tag.documents)
        print(f"   - {tag.name}: {doc_count} document(s)")
    
    # 5. Show recent audit log entries
    recent_logs = session.query(AuditLog).order_by(AuditLog.ts.desc()).limit(5).all()
    print(f"\n📝 Recent audit log entries:")
    for log in recent_logs:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(log.ts / 1000))
        print(f"   - [{timestamp}] {log.actor}: {log.action}")
        if log.details:
            details = json.loads(log.details)
            print(f"     Details: {details}")


def demonstrate_search(session):
    """Demonstrate search functionality"""
    print("\n🔎 Demonstrating search functionality...")
    
    # Search by title
    search_term = "argos"
    docs_by_title = session.query(Document).filter(
        Document.title.contains(search_term)
    ).all()
    print(f"📝 Documents with '{search_term}' in title: {len(docs_by_title)}")
    
    # Search by content hash
    if docs_by_title:
        doc = docs_by_title[0]
        doc_by_hash = session.query(Document).filter(
            Document.content_hash == doc.content_hash
        ).first()
        print(f"🔍 Found document by hash: {doc_by_hash.title if doc_by_hash else 'None'}")
    
    # Search by tag
    tag_search = "testing"
    docs_by_tag = session.query(Document).join(Document.tags).filter(
        Tag.name == tag_search
    ).all()
    print(f"🏷️  Documents tagged '{tag_search}': {len(docs_by_tag)}")


def cleanup_demo_data(session):
    """Clean up demo data (optional)"""
    print("\n🧹 Cleaning up demo data...")
    
    # Remove all documents (this will also remove tag associations)
    documents = session.query(Document).all()
    for doc in documents:
        # Remove the storage file
        storage_path = Path(doc.storage_path)
        if storage_path.exists():
            storage_path.unlink()
            print(f"   Removed file: {storage_path}")
        
        session.delete(doc)
    
    # Remove unused tags
    tags = session.query(Tag).all()
    for tag in tags:
        if not tag.documents:  # No associated documents
            session.delete(tag)
            print(f"   Removed unused tag: {tag.name}")
    
    session.commit()
    
    # Log cleanup action
    log_action(session, "demo_cleanup", {"removed_documents": len(documents)})
    
    print(f"✓ Cleaned up {len(documents)} documents and unused tags")


def main():
    """Main function - demonstrates the complete database layer"""
    print("🚀 ArgosOS MVP - Database Layer Demo")
    print("=" * 50)
    
    try:
        # Initialize database
        print("📦 Initializing database...")
        init_database()
        
        # Get database session
        session = get_db_session()
        
        # Log demo start
        log_action(session, "demo_started", {"timestamp": int(time.time() * 1000)})
        
        # Create sample data
        document = create_sample_data(session)
        
        # Demonstrate queries
        demonstrate_queries(session)
        
        # Demonstrate search
        demonstrate_search(session)
        
        # Show database statistics
        print(f"\n📊 Database Statistics:")
        doc_count = session.query(Document).count()
        tag_count = session.query(Tag).count()
        log_count = session.query(AuditLog).count()
        
        print(f"   Documents: {doc_count}")
        print(f"   Tags: {tag_count}")
        print(f"   Audit Logs: {log_count}")
        
        # Optional: Clean up demo data
        cleanup_choice = input("\n❓ Would you like to clean up demo data? (y/N): ").lower()
        if cleanup_choice == 'y':
            cleanup_demo_data(session)
        else:
            print("📝 Demo data preserved for inspection")
        
        # Log demo completion
        log_action(session, "demo_completed", {"success": True})
        
        print("\n✅ Database demo completed successfully!")
        print(f"📍 Database location: {Path('./data/argos.db').absolute()}")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        if 'session' in locals():
            log_action(session, "demo_failed", {"error": str(e)})
        raise
    
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    main()
