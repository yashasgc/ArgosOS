#!/usr/bin/env python3
"""
Simple test script to verify ArgosOS Backend installation
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"✗ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import alembic
        print("✓ Alembic imported successfully")
    except ImportError as e:
        print(f"✗ Alembic import failed: {e}")
        return False
    
    try:
        import pytesseract
        print("✓ pytesseract imported successfully")
    except ImportError as e:
        print(f"✗ pytesseract import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow imported successfully")
    except ImportError as e:
        print(f"✗ Pillow import failed: {e}")
        return False
    
    try:
        import pdfminer
        print("✓ pdfminer.six imported successfully")
    except ImportError as e:
        print(f"✗ pdfminer.six import failed: {e}")
        return False
    
    try:
        import docx
        print("✓ python-docx imported successfully")
    except ImportError as e:
        print(f"✗ python-docx import failed: {e}")
        return False
    
    try:
        import openai
        print("✓ OpenAI imported successfully")
    except ImportError as e:
        print(f"✗ OpenAI import failed: {e}")
        return False
    
    return True


def test_app_imports():
    """Test if the app modules can be imported"""
    print("\nTesting app imports...")
    
    try:
        from app.config import settings
        print("✓ App config imported successfully")
    except ImportError as e:
        print(f"✗ App config import failed: {e}")
        return False
    
    try:
        from app.db.models import Document, Tag
        print("✓ Database models imported successfully")
    except ImportError as e:
        print(f"✗ Database models import failed: {e}")
        return False
    
    try:
        from app.files.storage import FileStorage
        print("✓ File storage imported successfully")
    except ImportError as e:
        print(f"✗ File storage import failed: {e}")
        return False
    
    try:
        from app.llm.provider import LLMProvider, DisabledLLMProvider
        print("✓ LLM providers imported successfully")
    except ImportError as e:
        print(f"✗ LLM providers import failed: {e}")
        return False
    
    return True


def test_tesseract():
    """Test if Tesseract OCR is available"""
    print("\nTesting Tesseract OCR...")
    
    try:
        import pytesseract
        # Try to get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR available (version: {version})")
        return True
    except Exception as e:
        print(f"✗ Tesseract OCR not available: {e}")
        print("  Please install Tesseract OCR on your system")
        return False


def main():
    """Main test function"""
    print("ArgosOS Backend - Installation Test")
    print("=" * 40)
    
    success = True
    
    # Test package imports
    if not test_imports():
        success = False
    
    # Test app imports
    if not test_app_imports():
        success = False
    
    # Test Tesseract
    if not test_tesseract():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! ArgosOS Backend is ready to use.")
        print("\nTo start the server, run:")
        print("  python main.py")
        print("\nOr:")
        print("  uvicorn app.main:app --reload")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

