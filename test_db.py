#!/usr/bin/env python3
"""
Simple test script for ArgosOS MVP database layer
"""

import hashlib
from db.engine import init_database, get_db_session
from db.models import Document, Tag, AuditLog


def test_basic_operations():
    """Test basic database operations"""
    print("🧪 Testing basic database operations...")
    
    # Initialize database
    init_database()
    
    # Get session
    session = get_db_session()
    
    try:
        # Test 1: Create a tag
        tag = Tag(name="test_tag")
        session.add(tag)
        session.commit()
        print(f"✓ Created tag: {tag.name} (ID: {tag.id})")
        
        # Test 2: Create a document
        content = "Test document content"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        document = Document(
            title="test.txt",
            content_hash=content_hash,
            mime_type="text/plain",
            size_bytes=len(content),
            storage_path=f"./test/{content_hash}",
            summary="A test document"
        )
        
        # Associate tag with document
        document.tags = [tag]
        
        session.add(document)
        session.commit()
        print(f"✓ Created document: {document.title} (ID: {document.id})")
        
        # Test 3: Query document with tags
        retrieved_doc = session.query(Document).filter(Document.id == document.id).first()
        if retrieved_doc:
            print(f"✓ Retrieved document: {retrieved_doc.title}")
            print(f"  Tags: {[tag.name for tag in retrieved_doc.tags]}")
        
        # Test 4: Create audit log
        audit_entry = AuditLog(
            action="test_completed",
            details='{"test": "success"}'
        )
        session.add(audit_entry)
        session.commit()
        print(f"✓ Created audit log entry: {audit_entry.action}")
        
        # Test 5: Count records
        doc_count = session.query(Document).count()
        tag_count = session.query(Tag).count()
        audit_count = session.query(AuditLog).count()
        
        print(f"\n📊 Final counts:")
        print(f"  Documents: {doc_count}")
        print(f"  Tags: {tag_count}")
        print(f"  Audit Logs: {audit_count}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    test_basic_operations()



