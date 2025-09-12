# ArgosOS

A modern desktop application for intelligent document management with AI-powered analysis. Built with Python (FastAPI), React (TypeScript), and Electron.

## Features

- **Multi-format Support**: PDF, DOCX, TXT, MD, and image files (JPG, PNG, GIF, BMP, TIFF, WebP)
- **OCR Integration**: Tesseract for text extraction from images and scanned documents
- **AI Analysis**: OpenAI-powered summarization and tagging
- **Content Deduplication**: SHA-256 based deduplication
- **Native Desktop App**: Cross-platform Electron application
- **Smart Search**: Natural language document search
- **Security**: Encrypted API key storage, input validation, and SQL injection protection
- **Distribution**: Ready-to-distribute DMG, EXE, and AppImage packages

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Poetry
- Tesseract OCR

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ArgosOS
   ```

2. **Install dependencies**
   ```bash
   # Backend dependencies
   poetry install
   
   # Frontend dependencies
   cd frontend
   npm install
   cd ..
   ```

3. **Run the application**
   ```bash
   ./start-electron.sh
   ```

## Project Structure

```
ArgosOS/
├── app/                    # Python backend
│   ├── agents/            # AI agents (ingest, retrieval, postprocess)
│   ├── db/                # Database models and CRUD
│   ├── llm/               # LLM providers (OpenAI)
│   ├── config.py          # Configuration
│   └── main.py            # FastAPI application
├── frontend/              # React + Electron frontend
│   ├── src/               # React components
│   ├── electron/          # Electron main process
│   └── package.json       # Frontend dependencies
├── tests/                 # Test suite
├── data/                  # Database and file storage
├── pyproject.toml         # Python dependencies (Poetry)
└── start-electron.sh      # Startup script
```

## Usage

1. **Upload Documents**: Drag and drop files or use the native file picker
2. **Configure AI**: Add your OpenAI API key in Settings for AI features
3. **Search**: Use natural language to find documents
4. **Manage**: View, organize, and manage your document library

## Development

```bash
# Backend development
poetry run python start.py

# Frontend development
cd frontend
npm run dev

# Run tests
poetry run pytest

# Build for distribution
./build-with-poetry.sh
```

## Distribution

### Create Installers
```bash
# Build Electron app
./build-with-poetry.sh

# Create Docker distribution
python3 create-docker-app.py

# Create standalone executable
python3 create-standalone-app.py
```

### Security Features
- ✅ Encrypted API key storage
- ✅ Input validation and sanitization
- ✅ SQL injection protection
- ✅ CORS configuration
- ✅ File type and size validation
- ✅ Path traversal protection

## Architecture

- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: React with TypeScript and Tailwind CSS
- **Desktop**: Electron for cross-platform native apps
- **Database**: SQLite with Alembic migrations
- **AI**: OpenAI GPT for text analysis
- **OCR**: Tesseract for image text extraction

## License

MIT License - see [LICENSE](LICENSE) file for details.