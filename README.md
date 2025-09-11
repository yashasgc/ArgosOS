# ArgosOS Backend

A FastAPI-based backend for intelligent file analysis and document management. The system ingests files, extracts text via OCR, generates tags and summaries using LLM providers, and stores everything in SQLite with content-addressed blob storage.

## Features

- **Multi-format Support**: PDF, DOCX, TXT, MD, and image files (PNG, JPEG, GIF, BMP)
- **Text Extraction**: OCR for images, PDF parsing, DOCX extraction
- **AI Analysis**: Pluggable LLM providers for summarization and tagging
- **Content Deduplication**: SHA-256 based deduplication
- **Search & Filtering**: Query documents by tags, title, content, and date ranges
- **RESTful API**: Clean FastAPI endpoints with automatic documentation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Install requirements (if not already done)
pip install -r requirements.txt
```

### 2. Run the Server
```bash
# Development mode
python start.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the API
```bash
# Health check
curl http://localhost:8000/v1/health

# API documentation
open http://localhost:8000/docs
```

## 🏗️ System Components

### FastAPI Application (`app/main.py`)
- **Purpose**: Main web application with CORS middleware
- **Features**: API routing, middleware configuration, health checks

### Database Layer (`app/db/`)
- **Models**: SQLAlchemy ORM for documents, tags, and audit logs
- **Engine**: SQLite connection management and session handling
- **CRUD**: Create, read, update, delete operations
- **Migrations**: Alembic for database schema management

### File Processing (`app/files/`)
- **Storage**: Content-addressed blob storage with SHA-256 hashing
- **Extractors**: OCR for images, PDF parsing, DOCX extraction
- **Deduplication**: Automatic duplicate detection and prevention

### LLM Integration (`app/llm/`)
- **Provider Interface**: Pluggable LLM provider system
- **OpenAI Provider**: GPT-based summarization and tagging
- **Fallback**: Disabled provider when no API key configured

## 📊 Data Model

### Documents Table
- `id` - UUID primary key
- `content_hash` - SHA-256 hash (unique)
- `title` - Filename or user-provided title
- `mime_type` - File MIME type
- `size_bytes` - File size in bytes
- `storage_path` - Blob storage path
- `summary` - LLM-generated summary
- `created_at` - Creation timestamp (epoch ms)
- `imported_at` - Import timestamp (epoch ms)

### Tags Table
- `id` - Auto-increment primary key
- `name` - Tag name (unique)

### Document Tags Table
- `document_id` - Foreign key to documents
- `tag_id` - Foreign key to tags
- Composite primary key

### Audit Log Table
- `id` - Auto-increment primary key
- `ts` - Timestamp (epoch ms)
- `actor` - Who performed the action
- `action` - What action was performed
- `details` - Additional details (JSON)

## 🔍 API Endpoints

### Health Check
- `GET /v1/health` - System health status

### File Management
- `POST /v1/files` - Upload and process files
- `GET /v1/documents/{id}` - Get specific document
- `GET /v1/documents` - List documents with filters

### Search
- `POST /v1/search` - Search documents by query

## 🔧 File Processing Pipeline

1. **Upload**: File is uploaded via multipart form
2. **Hash**: SHA-256 hash is computed for deduplication
3. **Storage**: File is stored in content-addressed blob storage
4. **Extraction**: Text is extracted based on file type
5. **Analysis**: LLM generates summary and tags (if enabled)
6. **Storage**: Document metadata is stored in SQLite

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_files.py
```

### Test Structure
- **`tests/test_files.py`** - File upload and processing tests
- **`tests/test_documents.py`** - Document retrieval and filtering tests
- **`tests/test_search.py`** - Search functionality tests
- **`tests/conftest.py`** - Test configuration and fixtures

## 🔧 Configuration

### Environment Variables
```bash
# Database path (default: ./data/argos.db)
DATABASE_URL=sqlite:///./data/argos.db

# LLM features (default: disabled)
LLM_ENABLED=false
OPENAI_API_KEY=your_key_here

# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### File Type Support

| Type | Extensions | Processing |
|------|------------|------------|
| **PDF** | `.pdf` | pdfminer.six text extraction |
| **DOCX** | `.docx` | python-docx text extraction |
| **Text** | `.txt`, `.md` | Direct file reading |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp` | Tesseract OCR |

## 🚫 Security & Safety

### File Upload Safety
- **File Type Validation**: Only supported formats allowed
- **Size Limits**: Configurable maximum file sizes
- **Content Scanning**: Basic malware detection (future)

### Database Security
- **SQL Injection Prevention**: Parameterized queries only
- **Input Validation**: Pydantic schema validation
- **Access Control**: Future user authentication support

### API Security
- **CORS Configuration**: Configurable cross-origin settings
- **Rate Limiting**: Future implementation
- **Input Sanitization**: Automatic request validation

## 📁 Project Structure

```
argos-backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── db/                  # Database layer
│   │   ├── engine.py        # Database connection
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── crud.py          # CRUD operations
│   │   └── schemas.py       # Pydantic schemas
│   ├── files/               # File processing
│   │   ├── storage.py       # Blob storage
│   │   └── extractors.py    # Text extraction
│   ├── llm/                 # LLM providers
│   │   ├── provider.py      # Abstract interface
│   │   └── openai_provider.py # OpenAI implementation
│   ├── api/                 # API routes
│   │   └── routes/          # Endpoint definitions
│   └── utils/               # Utility functions
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
└── start.py                 # Application entry point
```

## 🔮 Future Enhancements

### Cloud Integration
- **Storage Backends**: S3, GCS, Azure Blob support
- **CDN Integration**: Global content delivery
- **Backup & Sync**: Automated backup strategies

### Advanced Search
- **Vector Embeddings**: Semantic search capabilities
- **Full-Text Search**: Lucene/Solr integration
- **Fuzzy Matching**: Typo-tolerant search

### Workflow Automation
- **Batch Processing**: Bulk file operations
- **Webhook Notifications**: Event-driven updates
- **API Rate Limiting**: Usage control and monitoring

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone <repository>
cd ArgosOs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest

# Start development server
python start.py
```

### Code Standards
- **Type Hints**: Full type annotation support
- **Documentation**: Comprehensive docstrings
- **Testing**: Pytest-based test suite
- **Linting**: PEP 8 compliance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2024 ArgosOS

## 🆘 Troubleshooting

### Common Issues

**OCR Not Working**
- Ensure Tesseract is installed and in PATH
- Check image file format support

**LLM Features Disabled**
- Verify OpenAI API key is set
- Check `LLM_ENABLED` environment variable

**Database Errors**
- Run `alembic upgrade head` to apply migrations
- Check database file permissions

**File Upload Issues**
- Verify file type is supported
- Check file size limits
- Ensure data directory is writable

---

**Built with ❤️ for intelligent document management**
