#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
log()   { echo -e "${GREEN}▶ $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠ $*${NC}"; }
error() { echo -e "${RED}✗ $*${NC}"; exit 1; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

# ── guards ────────────────────────────────────────────────────────────────────
# If ELECTRON_RUN_AS_NODE is set Electron runs as plain Node.js with no APIs.
unset ELECTRON_RUN_AS_NODE

# Strip any stale standalone-python-env from PATH so we always use the system Python
PATH=$(echo "$PATH" | tr ':' '\n' | grep -v "standalone-python-env" | tr '\n' ':' | sed 's/:$//')
export PATH

echo -e "${BOLD}"
echo "  ╔══════════════════════════════╗"
echo "  ║   ArgosOS — Build & Package  ║"
echo "  ╚══════════════════════════════╝"
echo -e "${NC}"

# ── 1. prerequisite checks ────────────────────────────────────────────────────
step "Checking prerequisites"

command -v node   >/dev/null || error "Node.js not found  →  https://nodejs.org"
command -v npm    >/dev/null || error "npm not found"
command -v python3 >/dev/null || error "python3 not found"

NODE_VER=$(node -e "process.stdout.write(process.versions.node)")
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

python3 -c "import sys; assert sys.version_info >= (3,11), 'need 3.11+'" \
  || error "Python 3.11+ required (found $PY_VER)"

log "Node.js $NODE_VER ✓"
log "Python  $PY_VER  ✓"

# ── 2. standalone Python environment ─────────────────────────────────────────
step "Building standalone Python environment"

log "Creating fresh virtual environment…"
rm -rf standalone-python-env
python3 -m venv standalone-python-env

log "Installing Python dependencies (this may take a minute)…"
standalone-python-env/bin/pip install --upgrade pip wheel --quiet

standalone-python-env/bin/pip install --quiet \
  "fastapi>=0.104.0" \
  "uvicorn[standard]>=0.24.0" \
  "sqlalchemy>=2.0.23" \
  "alembic>=1.12.1" \
  "pydantic>=2.5.0" \
  "pydantic-settings>=2.1.0" \
  "python-multipart>=0.0.6" \
  "pytesseract>=0.3.10" \
  "Pillow>=10.0.0" \
  "pdfminer-six>=20221105" \
  "python-docx>=1.1.0" \
  "openai>=1.3.7" \
  "python-dotenv>=1.0.0" \
  "cryptography>=41.0.0" \
  "PyMuPDF>=1.26.4"

log "Python environment ready ✓"

# ── 3. frontend dependencies ──────────────────────────────────────────────────
step "Installing frontend dependencies"
cd frontend
npm install
log "Frontend dependencies ready ✓"

# ── 4. build frontend (TypeScript + Vite) ────────────────────────────────────
step "Building frontend"
npm run build
log "Frontend built ✓"

# ── 5. package with electron-builder ─────────────────────────────────────────
# Note: Windows (.exe) and Linux (.AppImage) builds require running on those
# platforms or using the GitHub Actions workflow at .github/workflows/build.yml
step "Packaging with electron-builder (macOS only on this platform)"
env -u ELECTRON_RUN_AS_NODE npx electron-builder --publish=never
log "Packaging complete ✓"

cd ..

# ── 6. collect artifacts → distribution/ ─────────────────────────────────────
step "Collecting distribution artifacts"
mkdir -p distribution

FOUND=0
while IFS= read -r -d '' f; do
  NAME=$(basename "$f")
  cp "$f" "distribution/$NAME"
  HASH=$(shasum -a 256 "distribution/$NAME" | awk '{print $1}')
  echo "$HASH  $NAME" > "distribution/$NAME.sha256"
  SIZE=$(du -sh "distribution/$NAME" | awk '{print $1}')
  log "  $NAME  ($SIZE)"
  FOUND=$((FOUND + 1))
done < <(find frontend/dist-electron -maxdepth 1 \
  \( -name "*.dmg" -o -name "*.exe" -o -name "*.AppImage" -o -name "*.zip" \) \
  -not -name "*blockmap*" -print0 2>/dev/null)

if [ "$FOUND" -eq 0 ]; then
  warn "No installer files found in frontend/dist-electron — check electron-builder output above."
else
  echo ""
  echo -e "${GREEN}${BOLD}✓ Done! $FOUND installer(s) saved to distribution/${NC}"
  echo -e "${YELLOW}  Upload these to a GitHub Release — they exceed GitHub's 100 MB file limit${NC}"
  echo ""
  ls -lh distribution/*.dmg distribution/*.exe distribution/*.AppImage 2>/dev/null || true
fi
