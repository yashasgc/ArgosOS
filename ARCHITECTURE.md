# ArgosOS Architecture Documentation

## 🏗️ System Overview

ArgosOS is an intelligent document management system that combines modern web technologies with AI-powered analysis and agentic architecture. The system consists of a FastAPI backend with specialized AI agents for document processing, a SQLite database for metadata storage, and a React frontend for user interaction.

### **Agentic Architecture Philosophy**

ArgosOS implements an agentic architecture where specialized AI agents work together to process, analyze, and manage documents. Each agent has a specific role and can communicate with other agents to accomplish complex tasks. This approach provides:

- **Modularity**: Each agent handles a specific aspect of document processing
- **Scalability**: Agents can be independently optimized and scaled
- **Flexibility**: New agents can be added without affecting existing functionality
- **Intelligence**: Each agent can make decisions and adapt to different document types

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    ARGOSOS                                                │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   Frontend      │    │    Backend      │    │  AI Agents      │    │      Storage     │ │
│  │   (React)       │◄──►│   (FastAPI)     │◄──►│   System        │◄──►│   (SQLite +      │ │
│  │                 │    │                 │    │                 │    │    Blobs)        │ │
│  │ • File Upload   │    │ • API Endpoints │    │ • Ingest Agent  │    │ • Document       │ │
│  │ • Document View │    │ • Request       │    │ • Retrieval     │    │   Metadata      │ │
│  │ • AI Search     │    │   Routing       │    │   Agent         │    │ • Content Blobs │ │
│  │ • Settings      │    │ • Response      │    │ • Postprocessor │    │ • Search Index  │ │
│  │ • Electron      │    │   Handling      │    │   Agent         │    │ • File Storage  │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### **Agentic System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              AI AGENTS ECOSYSTEM                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  Ingest Agent   │    │ Retrieval Agent │    │Postprocessor    │    │   LLM Provider  │ │
│  │                 │    │                 │    │    Agent        │    │                 │ │
│  │ • File Upload   │    │ • Document      │    │ • Content       │    │ • OpenAI API    │ │
│  │ • Text Extract  │    │   Search        │    │   Analysis      │    │ • Vision API    │ │
│  │ • Content       │    │ • Tag-based     │    │ • Direct        │    │ • OCR Fallback  │ │
│  │   Processing    │    │   Filtering     │    │   Answers       │    │ • Text          │ │
│  │ • Format        │    │ • Relevance     │    │ • Additional    │    │   Processing    │ │
│  │   Detection     │    │   Scoring       │    │   Processing    │    │                 │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │                       │         │
│           └───────────────────────┼───────────────────────┼───────────────────────┘         │
│                                   │                       │                                 │
│  ┌─────────────────────────────────┴───────────────────────┴─────────────────────────────┐ │
│  │                        SQLite Database Layer                                        │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │ │
│  │  │   Documents     │  │      Tags       │  │ Document_Tags   │  │   Audit_Log     │ │ │
│  │  │     Table       │  │     Table       │  │   Junction      │  │     Table       │ │ │
│  │  │                 │  │                 │  │     Table       │  │                 │ │ │
│  │  │ • id (UUID)     │  │ • id (INT)      │  │ • document_id   │  │ • id (INT)      │ │ │
│  │  │ • content_hash  │  │ • name (TEXT)   │  │ • tag_id        │  │ • timestamp     │ │ │
│  │  │ • title         │  │ • created_at    │  │ • created_at    │  │ • action        │ │ │
│  │  │ • mime_type     │  │                 │  │                 │  │ • details       │ │ │
│  │  │ • size_bytes    │  │                 │  │                 │  │                 │ │ │
│  │  │ • storage_path  │  │                 │  │                 │  │                 │ │ │
│  │  │ • summary       │  │                 │  │                 │  │                 │ │ │
│  │  │ • created_at    │  │                 │  │                 │  │                 │ │ │
│  │  │ • imported_at   │  │                 │  │                 │  │                 │ │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 🤖 AI Agents System

### **Agent Architecture Overview**

ArgosOS implements a multi-agent system where specialized AI agents collaborate to process and analyze documents. Each agent has specific responsibilities and can communicate with other agents to accomplish complex tasks.

### **1. Ingest Agent**

**Purpose**: Handles document ingestion, text extraction, and initial processing.

**Responsibilities**:
- File upload and validation
- Text extraction from various formats (PDF, DOCX, images)
- Content deduplication using SHA-256 hashing
- Initial document metadata creation
- Format detection and MIME type identification

**Key Methods**:
```python
class IngestAgent:
    def ingest_file(self, file_data: bytes, filename: str, mime_type: str) -> Document
    def extract_text_from_file(self, file_data: bytes, mime_type: str) -> str
    def compute_content_hash(self, file_data: bytes) -> str
    def detect_file_format(self, file_data: bytes, filename: str) -> str
```

**Text Extraction Pipeline**:
- **PDFs**: Uses PyMuPDF (fitz) for direct text extraction, falls back to OCR if needed
- **DOCX**: Uses python-docx for direct text extraction
- **Images**: Uses ChatGPT Vision API with OCR fallback (pytesseract)
- **Text Files**: Direct UTF-8 decoding

### **2. Retrieval Agent**

**Purpose**: Handles document search and retrieval based on user queries.

**Responsibilities**:
- Query analysis and tag generation
- Document search using multiple strategies
- Relevance scoring and ranking
- Search result optimization

**Key Methods**:
```python
class RetrievalAgent:
    def search_documents(self, query: str, db: Session, limit: int = 20) -> Dict
    def generate_search_tags(self, query: str) -> List[str]
    def find_documents_by_tags(self, tags: List[str], db: Session) -> List[Document]
    def score_document_relevance(self, doc: Document, query: str) -> float
```

**Search Strategies**:
1. **Tag-based Search**: Find documents with matching AI-generated tags
2. **Content Search**: Full-text search through document content
3. **Title Search**: Search through document titles
4. **Hybrid Approach**: Combines multiple strategies with relevance scoring

### **3. Postprocessor Agent**

**Purpose**: Processes retrieved documents and generates intelligent responses.

**Responsibilities**:
- Content analysis and summarization
- Direct answer generation
- Additional processing decisions
- Response formatting and optimization

**Key Methods**:
```python
class PostProcessorAgent:
    def process_documents(self, query: str, document_ids: List[str], db: Session) -> Dict
    def _answer_or_do_further_processing(self, query: str, extracted_contents: Dict) -> Dict
    def _perform_additional_processing(self, content: str, instructions: str) -> str
    def _extract_text_from_file(self, file_data: bytes, mime_type: str) -> str
```

**Processing Workflow**:
1. **Content Extraction**: Extract text from retrieved documents
2. **AI Analysis**: Use LLM to analyze content and generate direct answers
3. **Processing Decision**: Determine if additional processing is needed
4. **Response Generation**: Format final response with relevant content

### **4. LLM Provider**

**Purpose**: Provides a unified interface for Large Language Model interactions.

**Responsibilities**:
- OpenAI API integration
- Text summarization
- Tag generation
- Vision API for image processing
- Fallback mechanisms when API is unavailable

**Key Methods**:
```python
class LLMProvider(ABC):
    def is_available(self) -> bool
    def summarize(self, text: str) -> str
    def generate_tags(self, text: str) -> List[str]
    def extract_text_from_image(self, image_data: bytes) -> str
    def answer_question(self, question: str, context: str) -> str
```

**Supported Models**:
- **GPT-4**: For text analysis and generation
- **GPT-4 Vision**: For image analysis and OCR
- **Fallback**: Local processing when API unavailable

## 🔄 System Dataflow

### **1. File Upload & Processing Flow (Agentic)**

```mermaid
graph TD
    A[User Uploads File] --> B[Frontend Validation]
    B --> C[FastAPI Backend]
    C --> D[Ingest Agent]
    D --> E[Compute SHA-256 Hash]
    E --> F{File Exists?}
    F -->|Yes| G[Return Existing Document]
    F -->|No| H[Store in Blob Storage]
    H --> I[Extract Text Content]
    I --> J[LLM Provider]
    J --> K{LLM Available?}
    K -->|Yes| L[Generate Summary & Tags]
    K -->|No| M[Skip AI Analysis]
    L --> N[Store in SQLite Database]
    M --> N
    N --> O[Return Document Response]
    G --> P[Update Frontend]
    O --> P
```

### **2. AI-Powered Search Flow (Agentic)**

```mermaid
graph TD
    A[User Search Query] --> B[Frontend API Call]
    B --> C[FastAPI Backend]
    C --> D[Retrieval Agent]
    D --> E[Generate Search Tags]
    E --> F[Query SQLite Database]
    F --> G[Tag-based Search]
    F --> H[Content Search]
    F --> I[Title Search]
    G --> J[Combine Results]
    H --> J
    I --> J
    J --> K[Relevance Scoring]
    K --> L[Postprocessor Agent]
    L --> M[Extract Document Content]
    M --> N[LLM Analysis]
    N --> O[Generate Direct Answer]
    O --> P[Format Response]
    P --> Q[Return to Frontend]
    Q --> R[Display Results]
```

### **3. Document Management Flow (Agentic)**

```mermaid
graph TD
    A[Document Operations] --> B{Operation Type}
    B -->|List| C[Fetch All Documents]
    B -->|Get| D[Fetch by ID]
    B -->|Update| E[Modify Document]
    B -->|Delete| F[Remove Document]
    
    C --> G[Apply Filters]
    G --> H[Return Document List]
    
    D --> I[Check Existence]
    I --> J[Return Document]
    
    E --> K[Validate Changes]
    K --> L[Update Database]
    
    F --> M[Remove from Storage]
    M --> N[Update Database]
    
    H --> O[Frontend Display]
    J --> O
    L --> O
    N --> O
```

## 🗄️ Database Architecture

### **SQLite Database Design**

ArgosOS uses SQLite as its primary database for metadata storage, providing a lightweight, serverless solution that's perfect for desktop applications. The database stores document metadata, tags, and relationships while the actual file content is stored in a content-addressed blob storage system.

### **Database Schema**

```sql
-- Documents Table - Core document metadata
CREATE TABLE documents (
    id TEXT PRIMARY KEY,                    -- UUID string (v4)
    content_hash TEXT UNIQUE NOT NULL,      -- SHA-256 hash for deduplication
    title TEXT NOT NULL,                    -- File name/title
    mime_type TEXT NOT NULL,                -- MIME type (e.g., application/pdf)
    size_bytes INTEGER NOT NULL,            -- File size in bytes
    storage_path TEXT NOT NULL,             -- Blob storage path
    summary TEXT,                           -- AI-generated summary (nullable)
    created_at INTEGER NOT NULL,            -- Creation timestamp (epoch ms)
    imported_at INTEGER NOT NULL            -- Import timestamp (epoch ms)
);

-- Tags Table - AI-generated and user tags
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Auto-increment ID
    name TEXT UNIQUE NOT NULL,              -- Tag name (lowercase, normalized)
    created_at INTEGER NOT NULL             -- Creation timestamp
);

-- Document-Tags Junction Table - Many-to-many relationship
CREATE TABLE document_tags (
    document_id TEXT NOT NULL,              -- Foreign key to documents
    tag_id INTEGER NOT NULL,                -- Foreign key to tags
    created_at INTEGER NOT NULL,            -- Association timestamp
    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Audit Log Table - System activity tracking
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Auto-increment ID
    timestamp INTEGER NOT NULL,             -- Event timestamp (epoch ms)
    action TEXT NOT NULL,                   -- Action performed
    document_id TEXT,                       -- Related document (nullable)
    details TEXT,                           -- Additional details (JSON)
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);
```

### **Database Relationships**

```
Documents (1) ──────── (M) Document_Tags (M) ──────── (1) Tags
    │                                                      │
    │                                                      │
    └─── (1) ──────── (M) Audit_Log                       │
                                                          │
                    ┌─────────────────────────────────────┘
                    │
                    ▼
                Tag Usage
            (Document Count)
```

### **Content-Addressed Storage**

The database works in conjunction with a content-addressed blob storage system:

```
data/
├── argos.db              # SQLite database (metadata)
└── blobs/                # Content-addressed storage
    ├── 02/               # First 2 chars of SHA-256
    │   └── [hash].bin    # Actual file content
    ├── 5f/
    │   └── 5f986fa4c0eda169d89c588f3d08942edf6e49d07174a7036b1cfb30784db807
    ├── 72/
    │   └── 726df8bcc21cb319dde031e10a3ab40ee5ce4979cef01451a9be341fec8e8153
    └── ...
```

**Benefits of Content-Addressed Storage**:
- **Deduplication**: Identical files share the same storage location
- **Integrity**: SHA-256 hash ensures file integrity
- **Efficiency**: No duplicate storage of identical content
- **Scalability**: Easy to add new storage backends

### **How the System Works**

#### **1. Document Ingestion Process**

When a user uploads a document, the following process occurs:

1. **Frontend Validation**: React frontend validates file type and size
2. **API Request**: File sent to FastAPI backend via multipart/form-data
3. **Ingest Agent Activation**: IngestAgent processes the uploaded file
4. **Content Hashing**: SHA-256 hash computed for deduplication
5. **Duplicate Check**: Database queried for existing content
6. **Text Extraction**: Appropriate extraction method based on file type
7. **AI Processing**: LLM Provider generates summary and tags (if available)
8. **Database Storage**: Document metadata stored in SQLite
9. **Blob Storage**: File content stored in content-addressed storage
10. **Response**: Document metadata returned to frontend

#### **2. Search and Retrieval Process**

When a user performs a search:

1. **Query Input**: User enters search query in React frontend
2. **API Call**: Query sent to FastAPI backend
3. **Retrieval Agent**: RetrievalAgent analyzes the query
4. **Tag Generation**: AI generates relevant search tags
5. **Database Query**: Multiple search strategies executed:
   - Tag-based search using generated tags
   - Content search through document summaries
   - Title search for exact matches
6. **Relevance Scoring**: Documents ranked by relevance
7. **Postprocessor Agent**: Retrieved documents processed
8. **Content Analysis**: LLM analyzes document content
9. **Answer Generation**: Direct answers generated when possible
10. **Response Formatting**: Results formatted and returned

#### **3. Agent Communication Flow**

```
User Query → FastAPI → Retrieval Agent → SQLite Database
                ↓
            Postprocessor Agent ← LLM Provider
                ↓
            Response Generation → Frontend Display
```

#### **4. Error Handling and Fallbacks**

The system includes multiple fallback mechanisms:

- **LLM Unavailable**: System continues with basic functionality
- **Text Extraction Fails**: OCR fallback for images
- **Database Errors**: Graceful degradation with error messages
- **File Processing Errors**: Detailed error reporting to user

### **Database Indexes**

```sql
-- Performance optimization indexes
CREATE INDEX idx_documents_content_hash ON documents(content_hash);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_imported_at ON documents(imported_at);
CREATE INDEX idx_documents_mime_type ON documents(mime_type);
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_audit_log_ts_action ON audit_log(ts, action);
```

### **Storage Architecture**

```
data/
├── argos.db              # SQLite database
└── blobs/                # Content-addressed storage
    ├── 02/               # First 2 chars of SHA-256
    │   └── [hash].bin    # Actual file content
    ├── 5f/
    │   └── 5f986fa4c0eda169d89c588f3d08942edf6e49d07174a7036b1cfb30784db807
    ├── 72/
    │   └── 726df8bcc21cb319dde031e10a3ab40ee5ce4979cef01451a9be341fec8e8153
    └── ...
```

## 🔌 API Specifications

### **Base URL**
```
http://localhost:8000/v1
```

### **Authentication**
Currently, the API is open (no authentication required). Future versions will include JWT-based authentication.

### **Response Format**
All API responses follow this structure:
```json
{
  "data": <response_data>,
  "message": "Success message",
  "status": "success"
}
```

### **Error Format**
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### **1. Health Check**

#### **GET /health**
Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### **2. File Upload**

#### **POST /files**
Upload and process a file.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:** File upload with `file` field

**Response:**
```json
{
  "id": "uuid-string",
  "title": "document.pdf",
  "tags": ["document", "pdf"],
  "summary": "AI-generated summary of the document content...",
  "mime_type": "application/pdf",
  "size_bytes": 1024000,
  "created_at": 1704067200000
}
```

**Supported File Types:**
- **PDF:** `application/pdf`
- **DOCX:** `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Text:** `text/plain`, `text/markdown`
- **Images:** `image/png`, `image/jpeg`, `image/gif`, `image/bmp`

### **3. Document Management**

#### **GET /documents**
Retrieve all documents with optional filtering.

**Query Parameters:**
- `skip` (int): Number of documents to skip (pagination)
- `limit` (int): Maximum number of documents to return
- `tags_any` (string[]): Documents with any of these tags
- `tags_all` (string[]): Documents with all of these tags
- `title_like` (string): Documents with title containing this string
- `date_from` (int): Documents imported after this timestamp
- `date_to` (int): Documents imported before this timestamp

**Response:**
```json
[
  {
    "id": "uuid-string",
    "title": "document.pdf",
    "tags": ["document", "pdf"],
    "summary": "AI-generated summary...",
    "mime_type": "application/pdf",
    "size_bytes": 1024000,
    "created_at": 1704067200000
  }
]
```

#### **GET /documents/{document_id}**
Retrieve a specific document by ID.

**Response:**
```json
{
  "id": "uuid-string",
  "title": "document.pdf",
  "tags": ["document", "pdf"],
  "summary": "AI-generated summary...",
  "mime_type": "application/pdf",
  "size_bytes": 1024000,
  "storage_path": "./data/blobs/5f/5f986fa4c0eda169d89c588f3d08942edf6e49d07174a7036b1cfb30784db807",
  "created_at": 1704067200000,
  "imported_at": 1704067200000
}
```

### **4. Search**

#### **POST /search**
Search documents by query string.

**Request:**
```json
{
  "query": "search term or question"
}
```

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid-string",
      "title": "document.pdf",
      "tags": ["document", "pdf"],
      "summary": "AI-generated summary...",
      "mime_type": "application/pdf",
      "size_bytes": 1024000,
      "created_at": 1704067200000
    }
  ]
}
```

### **5. Tags**

#### **GET /tags**
Retrieve all available tags.

**Response:**
```json
[
  {
    "id": 1,
    "name": "document"
  },
  {
    "id": 2,
    "name": "pdf"
  }
]
```

#### **POST /tags**
Create a new tag.

**Request:**
```json
{
  "name": "new-tag-name"
}
```

**Response:**
```json
{
  "id": 3,
  "name": "new-tag-name"
}
```

## 🧠 LLM Integration Architecture

### **Provider Interface**

```python
class LLMProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        pass
    
    @abstractmethod
    def summarize(self, text: str) -> str:
        """Generate a summary of the given text"""
        pass
    
    @abstractmethod
    def generate_tags(self, text: str) -> List[str]:
        """Generate tags for the given text"""
        pass
```

### **OpenAI Provider**

```python
class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
    
    def summarize(self, text: str) -> str:
        # Generate concise summary using GPT
        # Current implementation: Simple word limit
        # Future: OpenAI API integration
    
    def generate_tags(self, text: str) -> List[str]:
        # Generate relevant tags using GPT
        # Current implementation: Keyword-based
        # Future: OpenAI API integration
```

### **Disabled Provider**

```python
class DisabledLLMProvider(LLMProvider):
    """Fallback when LLM is not configured"""
    def is_available(self) -> bool:
        return False
    
    def summarize(self, text: str) -> str:
        return ""
    
    def generate_tags(self, text: str) -> List[str]:
        return []
```

## 🔧 File Processing Pipeline

### **Text Extraction**

```mermaid
graph TD
    A[File Upload] --> B{File Type}
    B -->|PDF| C[PDF Text Extraction]
    B -->|DOCX| D[DOCX Text Extraction]
    B -->|Text| E[Direct File Read]
    B -->|Image| F[Tesseract OCR]
    
    C --> G[Extracted Text]
    D --> G
    E --> G
    F --> G
    
    G --> H[Text Processing]
    H --> I[LLM Analysis]
    I --> J[Store Results]
```

### **Content Deduplication**

```python
def compute_bytes_hash(file_data: bytes) -> str:
    """Compute SHA-256 hash of file content"""
    return hashlib.sha256(file_data).hexdigest()

def check_duplicate(content_hash: str) -> Optional[Document]:
    """Check if file with same content already exists"""
    return DocumentCRUD.get_by_hash(db, content_hash)
```

## 🎨 Frontend Architecture

### **Component Structure**

```
src/
├── components/           # Reusable UI components
│   ├── FileCard.tsx     # Document display card
│   ├── FileUpload.tsx   # File upload component
│   ├── SearchResultCard.tsx # Search result display
│   └── Sidebar.tsx      # Navigation sidebar
├── pages/               # Page components
│   ├── Home.tsx         # Landing page with upload
│   ├── Documents.tsx    # Document management
│   ├── Search.tsx       # AI-powered search
│   └── Settings.tsx     # Configuration settings
├── store/               # State management
│   └── useConfigStore.ts # Configuration store
├── lib/                 # Utility libraries
│   ├── api.ts          # API client wrapper
│   └── utils.ts        # Utility functions
└── App.tsx             # Main app component
```

### **State Management**

```typescript
// Zustand store for configuration
interface ConfigStore {
  apiBaseUrl: string;
  openaiApiKey: string;
  setApiBaseUrl: (url: string) => void;
  setOpenaiApiKey: (key: string) => void;
  testConnection: () => Promise<boolean>;
}

// Persistent storage with localStorage
export const useConfigStore = create<ConfigStore>()(
  persist(
    (set, get) => ({
      apiBaseUrl: 'http://localhost:8000',
      openaiApiKey: '',
      setApiBaseUrl: (url) => set({ apiBaseUrl: url }),
      setOpenaiApiKey: (key) => set({ openaiApiKey: key }),
      testConnection: async () => {
        // Test API connection
      }
    }),
    {
      name: 'argos-config',
    }
  )
);
```

### **API Client**

```typescript
// Axios-based API client
export const apiClient = {
  health: () => api.get('/health'),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/files', formData);
  },
  getDocuments: () => api.get('/documents'),
  search: (query: string) => api.post('/search', { query }),
  getTags: () => api.get('/tags'),
  createTag: (name: string) => api.post('/tags', { name })
};
```

## 🚀 Deployment Architecture

### **Development Environment**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (Vite Dev)    │    │   (Uvicorn)     │    │   (SQLite)      │
│   Port: 5173    │◄──►│   Port: 8000    │◄──►│   Local File    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Production Environment**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (Static Host) │    │   (Uvicorn)     │    │   (SQLite/      │
│   (Nginx/CDN)   │◄──►│   (Gunicorn)    │◄──►│    PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Container Deployment**

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# Docker Compose
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///./data/argos.db
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

## 🔒 Security Considerations

### **File Upload Security**
- **File Type Validation**: Whitelist of allowed MIME types
- **Size Limits**: Configurable maximum file sizes
- **Content Scanning**: Future malware detection integration
- **Path Traversal Prevention**: Secure file path handling

### **API Security**
- **Input Validation**: Pydantic schema validation
- **SQL Injection Prevention**: Parameterized queries only
- **CORS Configuration**: Configurable cross-origin settings
- **Rate Limiting**: Future implementation

### **Data Security**
- **Content Hashing**: SHA-256 for integrity verification
- **Secure Storage**: Content-addressed blob storage
- **Audit Logging**: Complete action tracking
- **Access Control**: Future user authentication

## 📊 Performance Characteristics

### **Database Performance**
- **Indexing Strategy**: Optimized for common query patterns
- **Connection Pooling**: SQLAlchemy session management
- **Query Optimization**: Efficient JOIN operations

### **File Processing**
- **Asynchronous Processing**: Non-blocking file operations
- **Content Deduplication**: Prevents storage waste
- **Streaming Uploads**: Memory-efficient file handling

### **Search Performance**
- **Text Indexing**: Full-text search capabilities
- **Tag-based Filtering**: Fast document categorization
- **Result Caching**: Future Redis integration

## 🔮 Future Enhancements

### **Short Term (1-3 months)**
- [ ] User authentication and authorization
- [ ] Advanced search with vector embeddings
- [ ] Document versioning and history
- [ ] Batch file processing
- [ ] API rate limiting

### **Medium Term (3-6 months)**
- [ ] Multi-tenant architecture
- [ ] Advanced OCR with layout analysis
- [ ] Document collaboration features
- [ ] Mobile application
- [ ] Integration with cloud storage

### **Long Term (6+ months)**
- [ ] Machine learning model training
- [ ] Advanced document analytics
- [ ] Workflow automation
- [ ] Enterprise features
- [ ] Global deployment

## 🧪 Testing Strategy

### **Backend Testing**
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# API tests
pytest tests/api/

# Coverage report
pytest --cov=app --cov-report=html
```

### **Frontend Testing**
```bash
# Component tests
npm run test:components

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e
```

### **Performance Testing**
```bash
# Load testing
locust -f tests/load/locustfile.py

# Stress testing
artillery run tests/performance/stress.yml
```

## 📚 Additional Resources

### **Documentation**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### **Development Tools**
- **Backend**: PyCharm, VS Code, Vim
- **Frontend**: VS Code, WebStorm, Chrome DevTools
- **Database**: SQLite Browser, DBeaver
- **API Testing**: Postman, Insomnia, curl

### **Monitoring & Logging**
- **Application Logs**: Python logging, console output
- **Performance Monitoring**: Future Prometheus integration
- **Error Tracking**: Future Sentry integration
- **Health Checks**: Built-in health endpoint

---

*This architecture document provides a comprehensive overview of the ArgosOS system. For specific implementation details, refer to the individual component documentation and source code.*


