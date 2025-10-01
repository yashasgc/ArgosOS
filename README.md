# ArgosOS

A modern desktop application for intelligent document management with AI-powered analysis. Built with Python (FastAPI), React (TypeScript), and Electron.

## Features

- **Multi-format Support**: PDF, DOCX, TXT, MD, and image files (JPG, PNG, GIF, BMP, TIFF, WebP)
- **Advanced Text Extraction**: 
  - **PDFs**: OCR-based extraction using pdf2image + Tesseract
  - **DOCX**: Direct text extraction using python-docx
  - **Images**: ChatGPT Vision API with OCR fallback
- **AI Analysis**: OpenAI-powered summarization and tagging
- **Persistent Storage**: Files saved to disk with content-addressed storage
- **Content Deduplication**: SHA-256 based deduplication
- **Native Desktop App**: Cross-platform Electron application
- **Smart Search**: Natural language document search with AI-powered postprocessing
- **Complete CRUD**: Upload, view, search, and delete documents
- **Security**: Encrypted API key storage, input validation, and SQL injection protection
- **Distribution**: Ready-to-distribute DMG, EXE, and AppImage packages

## Recent Updates

### v1.1.0 - Complete File Management
- ✅ **Persistent File Storage**: Files now saved to `data/blobs/` directory
- ✅ **Complete Delete**: Delete removes both file and database record
- ✅ **Real File Paths**: Database stores actual file locations
- ✅ **Code Cleanup**: Removed dead code and unused functions
- ✅ **Improved Search**: Search returns real file paths for postprocessor integration
- ✅ **Better Error Handling**: Enhanced validation and error messages

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

### Create Multi-Platform Installers
```bash
# Build for all platforms (macOS, Windows, Linux)
./build-all-platforms.sh

# Build specific platforms only
cd frontend
npm run electron:dist  # All platforms
npx electron-builder --win --publish=never  # Windows only
npx electron-builder --linux --publish=never  # Linux only
npx electron-builder --mac --publish=never  # macOS only
```

### Alternative Distribution Methods
```bash
# Create Docker distribution
python3 create-docker-app.py

# Create standalone executable
python3 create-standalone-app.py

# Build with Poetry (development)
./build-with-poetry.sh
```

### Security Features
- ✅ Encrypted API key storage
- ✅ Input validation and sanitization
- ✅ SQL injection protection
- ✅ CORS configuration
- ✅ File type and size validation
- ✅ Path traversal protection

## Architecture

### System Overview
ArgosOS is a three-tier desktop application with AI-powered document processing:

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Desktop App                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   React UI      │  │   File Upload   │  │   Search    │  │
│  │   (TypeScript)  │  │   Management    │  │   Results   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Ingest      │  │ Retrieval   │  │ PostProcessor       │  │
│  │ Agent       │  │ Agent       │  │ Agent               │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Text        │  │ LLM         │  │ Database            │  │
│  │ Extractor   │  │ Provider    │  │ (SQLite)            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ OpenAI      │  │ Tesseract   │  │ File System         │  │
│  │ (GPT-4)     │  │ (OCR)       │  │ (data/blobs/)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Frontend (Electron + React)**
- **Technology**: React 18 + TypeScript + Tailwind CSS
- **Desktop**: Electron for native desktop experience
- **Features**: File upload, document management, search interface
- **State Management**: React hooks and context

#### 2. **Backend (FastAPI)**
- **Technology**: Python 3.11+ with FastAPI
- **Architecture**: RESTful API with async support
- **Security**: CORS, input validation, encrypted storage
- **Port**: 8000 (configurable)

#### 3. **AI Agents**
- **IngestAgent**: File processing, text extraction, AI analysis
- **RetrievalAgent**: Document search and tag-based filtering
- **PostProcessorAgent**: Advanced query processing and result enhancement

#### 4. **Text Extraction Pipeline**
```
PDF Files:
  PDF → pdf2image → Images → Tesseract OCR → Text → ChatGPT LLM → Processed Text

DOCX Files:
  DOCX → python-docx → Direct Text Extraction → ChatGPT LLM → Processed Text

Image Files:
  Image → ChatGPT Vision API → Text (with OCR fallback)
```

#### 5. **Database (SQLite)**
- **Tables**: Documents, Tags
- **Features**: Content deduplication, full-text search
- **Migrations**: Alembic for schema management
- **Storage**: `data/argos.db`

#### 6. **File Storage**
- **Location**: `data/blobs/` directory
- **Naming**: Content-addressed (SHA-256 hash)
- **Deduplication**: Automatic duplicate detection
- **Persistence**: Files survive app restarts

### Data Flow

1. **Upload**: User uploads file → Electron → FastAPI → IngestAgent
2. **Processing**: File → TextExtractor → AI Analysis → Database Storage
3. **Search**: Query → RetrievalAgent → PostProcessorAgent → Results
4. **Display**: Results → React UI → User Interface

## How to Download

### Option 1: Pre-built Releases (Recommended)
1. Go to [Releases](https://github.com/yashasgc/ArgosOS/releases)
2. Download the appropriate package for your OS:
   - **macOS**: `ArgosOS-1.0.0-arm64.dmg` (Apple Silicon) or `ArgosOS-1.0.0-x64.dmg` (Intel)
   - **Windows**: `ArgosOS-1.0.0.exe`
   - **Linux**: `ArgosOS-1.0.0.AppImage`
3. Install and run the application

### Option 2: Clone from Source
```bash
git clone https://github.com/yashasgc/ArgosOS.git
cd ArgosOS
```

## How to Deploy

### Local Development
```bash
# 1. Install dependencies
poetry install
cd frontend && npm install && cd ..

# 2. Run the application
./start-electron.sh
```

### Production Build
```bash
# 1. Build multi-platform Electron apps
./build-all-platforms.sh

# 2. Create alternative distribution packages
python3 create-docker-app.py      # Docker container
python3 create-standalone-app.py  # Standalone executable
```

### Docker Deployment
```bash
# 1. Build Docker image
docker build -t argos-os .

# 2. Run container
docker run -p 8000:8000 -v $(pwd)/data:/app/data argos-os
```

### System Requirements

#### Minimum Requirements
- **OS**: Windows 10+, macOS 10.12+, Ubuntu 18.04+
- **Architecture**: x64 (Intel/AMD) or ARM64 (Apple Silicon)
- **RAM**: 4GB
- **Storage**: 1GB free space
- **Python**: 3.11+ (for development only)
- **Node.js**: 18+ (for development only)

#### Recommended Requirements
- **OS**: Latest version of Windows/macOS/Linux
- **RAM**: 8GB+
- **Storage**: 5GB+ free space
- **CPU**: Multi-core processor
- **Internet**: For AI features (OpenAI API)

### Dependencies

#### System Dependencies
```bash
# macOS
brew install tesseract poppler

# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

#### Python Dependencies (Managed by Poetry)
- FastAPI, SQLAlchemy, Pydantic
- OpenAI, Tesseract, PyMuPDF
- pdf2image, python-docx
- See `pyproject.toml` for complete list

#### Node.js Dependencies (Managed by npm)
- React, TypeScript, Tailwind CSS
- Electron, Vite
- See `frontend/package.json` for complete list

## Troubleshooting

### Common Issues

#### 1. **Port Already in Use**
```bash
# Kill processes using port 8000
pkill -f uvicorn
# Or use a different port
export PORT=8001
```

#### 2. **Tesseract Not Found**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

#### 3. **Poetry Not Found**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

#### 4. **Node.js Version Issues**
```bash
# Use Node Version Manager
nvm install 18
nvm use 18
```

#### 5. **Database Issues**
```bash
# Reset database
rm data/argos.db
# Restart application
./start-electron.sh
```

#### 6. **File Upload Issues**
- Check file size limits (default: 100MB)
- Verify file type is supported
- Ensure sufficient disk space

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./start-electron.sh
```

### Performance Optimization

1. **Increase OCR Performance**:
   - Use SSD storage
   - Increase RAM allocation
   - Adjust Tesseract PSM modes

2. **Reduce Memory Usage**:
   - Process files in smaller batches
   - Clear cache regularly
   - Monitor file sizes

3. **Improve Search Speed**:
   - Index frequently searched terms
   - Use database optimization
   - Implement result caching

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write tests for new features
- Update documentation
- Test on multiple platforms

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yashasgc/ArgosOS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yashasgc/ArgosOS/discussions)
- **Documentation**: [Wiki](https://github.com/yashasgc/ArgosOS/wiki)

## Changelog

### v1.2.0 - Advanced Text Processing
- ✅ **OCR for PDFs**: PDF files now use OCR for better text extraction
- ✅ **Direct DOCX Processing**: DOCX files use direct text extraction
- ✅ **Vision API for Images**: Images use ChatGPT Vision API with OCR fallback
- ✅ **Comprehensive Documentation**: Added detailed architecture and deployment guides
- ✅ **Enhanced README**: Complete setup, troubleshooting, and contribution guidelines

### v1.1.0 - Complete File Management
- ✅ **Persistent File Storage**: Files now saved to `data/blobs/` directory
- ✅ **Complete Delete**: Delete removes both file and database record
- ✅ **Real File Paths**: Database stores actual file locations
- ✅ **Code Cleanup**: Removed dead code and unused functions
- ✅ **Improved Search**: Search returns real file paths for postprocessor integration
- ✅ **Better Error Handling**: Enhanced validation and error messages