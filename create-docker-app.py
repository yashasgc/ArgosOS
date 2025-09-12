#!/usr/bin/env python3
"""
Create a Docker-based ArgosOS app that can be easily distributed.
This creates a single Docker image that contains everything needed.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def create_docker_app():
    """Create a Docker-based app that bundles everything"""
    
    print("🐳 Creating Docker-based ArgosOS App...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("start.py"):
        print("❌ Please run this script from the project root directory")
        return False
    
    print("📦 Step 1: Building frontend...")
    
    # Build frontend
    if not run_command("cd frontend && npm run build"):
        return False
    
    print("📦 Step 2: Creating Docker image...")
    
    # Create a comprehensive Dockerfile
    dockerfile_content = """
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    tesseract-ocr \\
    tesseract-ocr-eng \\
    curl \\
    wget \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Copy built frontend
COPY frontend/dist /app/frontend/dist

# Install Node.js for serving frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \\
    && apt-get install -y nodejs

# Install a simple HTTP server for frontend
RUN npm install -g serve

# Create startup script
RUN echo '#!/bin/bash\\n\\
# Start Python backend in background\\n\\
poetry run python start.py &\\n\\
BACKEND_PID=$!\\n\\
\\n\\
# Wait for backend to be ready\\n\\
echo "Waiting for backend to start..."\\n\\
for i in {1..30}; do\\n\\
  if curl -f http://localhost:8000/health > /dev/null 2>&1; then\\n\\
    echo "Backend is ready!"\\n\\
    break\\n\\
  fi\\n\\
  sleep 2\\n\\
done\\n\\
\\n\\
# Start frontend server\\n\\
echo "Starting frontend server..."\\n\\
serve -s frontend/dist -l 3000\\n\\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["/app/start.sh"]
"""
    
    with open("Dockerfile.standalone", "w") as f:
        f.write(dockerfile_content)
    
    # Build Docker image
    if not run_command("docker build -f Dockerfile.standalone -t argos-os:standalone ."):
        return False
    
    print("📦 Step 3: Creating distribution package...")
    
    # Create distribution directory
    dist_dir = Path("docker-distribution")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Create docker-compose file
    compose_content = """
version: '3.8'

services:
  argos-os:
    image: argos-os:standalone
    ports:
      - "8000:8000"  # Backend API
      - "3000:3000"  # Frontend
    volumes:
      - ./data:/app/data
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
"""
    
    with open(dist_dir / "docker-compose.yml", "w") as f:
        f.write(compose_content)
    
    # Create README
    readme_content = """
# ArgosOS Docker Distribution

This package contains everything needed to run ArgosOS in a Docker container.

## Quick Start

1. **Prerequisites**: Install Docker and Docker Compose
   - Windows: Download Docker Desktop
   - macOS: Download Docker Desktop  
   - Linux: Install docker and docker-compose

2. **Run the application**:
   ```bash
   docker-compose up
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## What's Included

- ✅ Python Backend (FastAPI)
- ✅ Frontend (React)
- ✅ SQLite Database
- ✅ Tesseract OCR
- ✅ All Dependencies

## Data Persistence

Your documents and data are stored in the `./data` directory and will persist between container restarts.

## Stopping the Application

Press `Ctrl+C` or run:
```bash
docker-compose down
```

## Troubleshooting

If you encounter issues:
1. Make sure Docker is running
2. Check if ports 3000 and 8000 are available
3. View logs: `docker-compose logs`

## Support

For issues and questions, please check the main repository.
"""
    
    with open(dist_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    # Create start script
    start_script = """#!/bin/bash
echo "🚀 Starting ArgosOS..."
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo ""
docker-compose up
"""
    
    with open(dist_dir / "start.sh", "w") as f:
        f.write(start_script)
    
    # Make start script executable
    os.chmod(dist_dir / "start.sh", 0o755)
    
    # Create Windows batch file
    start_bat = """@echo off
echo 🚀 Starting ArgosOS...
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
echo.
docker-compose up
pause
"""
    
    with open(dist_dir / "start.bat", "w") as f:
        f.write(start_bat)
    
    print("✅ Docker-based app created successfully!")
    print(f"📁 Distribution directory: {dist_dir}")
    print("")
    print("🎉 The distribution includes:")
    print("  ✅ Docker image with everything bundled")
    print("  ✅ Docker Compose configuration")
    print("  ✅ Start scripts for Windows and Linux/macOS")
    print("  ✅ Complete documentation")
    print("")
    print("📦 To distribute:")
    print("  1. Zip the 'docker-distribution' folder")
    print("  2. Share with users")
    print("  3. Users just need Docker installed")
    print("")
    print("🚀 To test locally:")
    print(f"  cd {dist_dir}")
    print("  ./start.sh  # Linux/macOS")
    print("  start.bat   # Windows")
    
    return True

if __name__ == "__main__":
    success = create_docker_app()
    sys.exit(0 if success else 1)
