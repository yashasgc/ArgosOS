#!/usr/bin/env python3
"""
ArgosOS standalone backend starter.
Used by the packaged Electron app to launch the FastAPI backend
with the bundled Python environment.
"""

import sys
import os
from pathlib import Path


def main():
    script_dir = Path(__file__).parent.absolute()

    # Use ARGOS_DATA_DIR from Electron (points to writable user data dir).
    # Fall back to script_dir/data for development.
    argos_data_dir = os.environ.get("ARGOS_DATA_DIR")
    data_dir = Path(argos_data_dir) if argos_data_dir else script_dir / "data"
    blobs_dir = data_dir / "blobs"

    data_dir.mkdir(parents=True, exist_ok=True)
    blobs_dir.mkdir(parents=True, exist_ok=True)

    # Set pydantic-settings-compatible env vars (case-insensitive)
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{data_dir / 'argos.db'}")
    os.environ.setdefault("DATA_DIR", str(data_dir))
    os.environ.setdefault("BLOBS_DIR", str(blobs_dir))
    os.environ.setdefault("PORT", "8000")

    # Make the app package importable
    sys.path.insert(0, str(script_dir))

    os.chdir(str(script_dir))

    try:
        from app.main import app
        import uvicorn

        port = int(os.environ.get("PORT", "8000"))
        print(f"Starting ArgosOS backend on port {port}...")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error starting backend: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
