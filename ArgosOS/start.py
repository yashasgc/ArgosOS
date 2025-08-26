#!/usr/bin/env python3
"""
ArgosOS Backend Startup Script
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import fastapi
        import sqlalchemy
        import alembic
        import pytesseract
        from PIL import Image
        import pdfminer
        import docx
        import openai
        print("✓ All dependencies are available")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install all requirements: pip install -r requirements.txt")
        return False

def check_tesseract():
    """Check if Tesseract OCR is available"""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✓ Tesseract OCR is available")
        return True
    except Exception as e:
        print(f"✗ Tesseract OCR not available: {e}")
        print("Please install Tesseract OCR on your system")
        return False

def setup_database():
    """Set up the database and run migrations"""
    try:
        from app.db.engine import create_tables
        create_tables()
        print("✓ Database tables created")
        
        # Try to run Alembic migrations
        try:
            import subprocess
            result = subprocess.run(["alembic", "upgrade", "head"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Database migrations applied")
            else:
                print("⚠ Database migrations failed (this is okay for first run)")
        except FileNotFoundError:
            print("⚠ Alembic not found (this is okay for first run)")
        
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    try:
        import uvicorn
        from app.config import settings
        
        print(f"🚀 Starting ArgosOS Backend on {settings.host}:{settings.port}")
        print(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")
        print(f"🔍 Health Check: http://{settings.host}:{settings.port}/v1/health")
        print("\nPress Ctrl+C to stop the server")
        
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug
        )
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        return False

def main():
    """Main startup function"""
    print("ArgosOS Backend - Starting up...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Tesseract
    if not check_tesseract():
        print("⚠ Continuing without OCR support...")
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    print("=" * 50)
    print("✓ All checks passed! Starting server...")
    print()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()

