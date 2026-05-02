# ArgosOS

An Electron desktop app for intelligent document management. Upload PDFs, DOCX, images, and text files — ArgosOS extracts content, generates AI summaries and tags, and lets you search your library with natural language.

Built with Python (FastAPI), React (TypeScript), and Electron.

---

## Download

Pre-built installers are on the [Releases](../../releases) page:

| Platform | File |
|---|---|
| macOS Apple Silicon | `ArgosOS-1.0.0-arm64.dmg` |
| macOS Intel | `ArgosOS-1.0.0.dmg` |
| Windows | built by CI (see below) |
| Linux | built by CI (see below) |

On macOS, open the DMG, drag ArgosOS to Applications, and launch it. macOS may warn about an unsigned app — go to **System Settings → Privacy & Security** and click **Open Anyway**.

Windows and Linux builds are produced by the GitHub Actions workflow on every version tag push.

---

## Features

- **Multi-format ingestion** — PDF, DOCX, TXT, MD, PNG, JPG, GIF, BMP, TIFF, WebP
- **Text extraction** — PyMuPDF for PDFs, python-docx for DOCX, pytesseract OCR for images
- **AI analysis** — OpenAI-powered summarisation, tag generation, and natural language search
- **Deduplication** — SHA-256 content hash prevents duplicate uploads
- **Encrypted key storage** — OpenAI API key is stored with Fernet symmetric encryption; never written in plaintext
- **Offline-first** — all document data is local (SQLite + `data/blobs/`)

---

## Development

### Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.11 |
| Node.js | 18 |
| Poetry | any recent |
| Tesseract OCR | any |

Install Tesseract:
```bash
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt-get install tesseract-ocr

# Windows — download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Run in development mode

```bash
git clone <repo-url>
cd ArgosOS

# Install Python dependencies
poetry install

# Install Node dependencies
cd frontend && npm install && cd ..

# Start everything (backend + Vite + Electron)
./dev.sh
```

`dev.sh` runs `npm run electron:dev` which starts the Vite dev server and Electron together. The Electron window shows a loading screen while the backend starts, then loads the React UI.

### Run the backend standalone

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs available at `http://localhost:8000/docs`.

---

## Build for distribution

```bash
./build.sh
```

This script:
1. Checks prerequisites (Node.js 18+, Python 3.11+)
2. Builds a fresh standalone Python virtual environment (`standalone-python-env/`) with all dependencies
3. Builds the React frontend with TypeScript + Vite
4. Packages with electron-builder into DMG (macOS)
5. Copies installers + SHA-256 checksums to `distribution/`

Windows EXE and Linux AppImage require building on those platforms. The GitHub Actions workflow (`.github/workflows/build.yml`) handles all three platforms — trigger it by pushing a `v*` tag:

```bash
git tag v1.0.1
git push --tags
```

---

## Project structure

```
ArgosOS/
├── app/                     # Python FastAPI backend
│   ├── agents/              # IngestAgent, RetrievalAgent, PostProcessorAgent
│   ├── db/                  # SQLAlchemy models, CRUD, Alembic migrations
│   ├── llm/                 # OpenAI provider
│   ├── utils/               # File validation, sanitisation
│   ├── config.py            # pydantic-settings configuration
│   ├── constants.py         # CORS origins, limits, HTTP codes
│   └── main.py              # FastAPI app, all endpoints
├── alembic/                 # Database migrations
├── frontend/
│   ├── src/                 # React + TypeScript UI
│   ├── electron/
│   │   ├── main.js          # Electron main process
│   │   └── preload.js       # Context bridge (renderer ↔ main)
│   └── package.json         # Build config + electron-builder settings
├── distribution/            # Built installers (committed for direct download)
├── data/                    # Runtime — gitignored
│   ├── argos.db             # SQLite database
│   └── blobs/               # Stored document files (content-addressed)
├── build.sh                 # Full build script
├── dev.sh                   # Development startup
└── start-standalone.py      # Backend entry point for packaged app
```

---

## Architecture

```
Electron (main process)
  └─ spawns Python backend (standalone-python-env or poetry in dev)
  └─ loads React UI (Vite dev server or built dist/)
  └─ IPC bridge (preload.js) — proxies API calls, file dialogs, key-value store

FastAPI backend  :8000
  ├─ POST /api/files/upload    → IngestAgent → extract + summarise + tag → SQLite
  ├─ GET  /api/search          → RetrievalAgent → tag match + text search → PostProcessorAgent
  ├─ GET  /api/documents       → list all documents
  ├─ GET  /api/documents/{id}/content   → return extracted text or base64
  ├─ GET  /api/documents/{id}/download  → stream raw file
  ├─ DELETE /api/documents/{id}
  ├─ POST /v1/api-key          → encrypt and store OpenAI key
  ├─ GET  /v1/api-key/status   → check if key is configured
  ├─ DELETE /v1/api-key
  └─ GET  /health

SQLite + blobs/
  ├─ documents  — metadata, summary, tags (JSON), storage_path
  └─ tags       — tag name, document_ids (JSON)
```

**Text extraction pipeline:**
- **PDF** — PyMuPDF direct extraction, falls back to pytesseract OCR on images
- **DOCX** — python-docx direct extraction
- **Images** — OpenAI Vision API if key is set, pytesseract OCR fallback
- **TXT / MD** — read directly

---

## Configuration

The backend reads configuration from environment variables (or a `.env` file). All have defaults so no configuration is required to run:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./argos.db` | SQLite connection string |
| `DATA_DIR` | `./data` | Directory for database and blobs |
| `BLOBS_DIR` | `./data/blobs` | Uploaded file storage |
| `PORT` | `8000` | Backend port |
| `DEBUG` | `false` | SQLAlchemy query logging |

The packaged Electron app sets `DATA_DIR` / `BLOBS_DIR` / `DATABASE_URL` to `app.getPath('userData')` so data is stored in the OS-standard user data directory, not the read-only app bundle.

---

## Security

- API keys are encrypted at rest with Fernet (symmetric encryption); the encryption key is stored separately in `config/secret.key` (gitignored)
- File paths from the database are validated to be inside `blobs_dir` before being read or served
- `Content-Disposition` filename is RFC 8187 encoded to prevent header injection
- The Electron subprocess receives a filtered environment — variables matching `API_KEY`, `SECRET`, `TOKEN`, `PASSWORD`, or `CREDENTIAL` are stripped before spawning Python
- CORS is restricted to localhost origins + `null` (required for Electron's `file://` origin in packaged mode)
- No authentication is required — the backend binds to `localhost:8000` only and is not reachable from the network

---

## Troubleshooting

**Backend won't start / "no such table" error**  
Delete `data/argos.db` and restart — the app recreates the schema automatically on startup.

**Port 8000 already in use**
```bash
pkill -f uvicorn
```

**Tesseract not found**  
Install it (see Prerequisites above) and ensure it's in `$PATH`. On macOS with Homebrew it's at `/opt/homebrew/bin/tesseract`.

**macOS "app is damaged" / quarantine warning**  
The DMG is unsigned. Run: `xattr -dr com.apple.quarantine /Applications/ArgosOS.app`

**Electron window shows blank / "Backend Failed to Start"**  
Check that Python and all dependencies are installed. In dev mode run `poetry run uvicorn app.main:app` manually to see the error.

---

## Contributing

1. Fork and create a branch
2. Make changes with tests where applicable
3. `poetry run pytest` — run the test suite
4. Open a PR

---

## License

MIT — see [LICENSE](LICENSE).
