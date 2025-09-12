#!/bin/bash

# ArgosOS Distribution Build Script

echo "🚀 Building ArgosOS for Distribution..."

# Check if we're in the right directory
if [ ! -f "start.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf frontend/dist
rm -rf frontend/dist-electron

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
echo "Next steps:"
echo "1. Test the built app on a clean machine"
echo "2. Upload to GitHub Releases or cloud storage"
echo "3. Share download links with users"
