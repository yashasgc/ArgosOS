#!/bin/bash

# ArgosOS Poetry-based Distribution Build Script

echo "🚀 Building ArgosOS with Poetry for Distribution..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install it first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf frontend/dist
rm -rf frontend/dist-electron
rm -rf standalone-build
rm -rf docker-distribution

# Install dependencies with Poetry
echo "📦 Installing Python dependencies with Poetry..."
poetry install

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    exit 1
fi

# Build Electron app
echo "🖥️  Building Electron app..."
npm run electron:dist

if [ $? -ne 0 ]; then
    echo "❌ Electron build failed"
    exit 1
fi

echo "✅ Build completed successfully!"
echo ""
echo "📁 Distribution files are in: frontend/dist-electron/"
echo ""
echo "Files created:"
ls -la dist-electron/

echo ""
echo "🎉 Ready for distribution!"
echo ""
echo "📋 What's included in the DMG:"
echo "  ✅ Frontend (React/Electron app)"
echo "  ✅ Python source code"
echo "  ✅ SQLite database"
echo "  ❌ Python runtime (users need Python installed)"
echo "  ❌ Python dependencies (users need to run 'poetry install')"
echo "  ❌ Tesseract OCR (users need to install separately)"
echo ""
echo "💡 For a complete standalone app, use:"
echo "  python3 create-docker-app.py      # Docker distribution"
echo "  python3 create-standalone-app.py  # Native executable"
