#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'; BOLD='\033[1m'; NC='\033[0m'
log() { echo -e "${GREEN}▶ $*${NC}"; }

unset ELECTRON_RUN_AS_NODE

log "Starting ArgosOS in development mode…"
log "  Backend:  http://localhost:8000"
log "  Frontend: http://localhost:5173"
echo ""

cd frontend
exec npm run electron:dev
