#!/bin/bash

# ArgosOS Multi-Platform Build Script
# This script builds ArgosOS for macOS, Windows, and Linux

echo "🚀 Building ArgosOS for All Platforms..."
echo "========================================"

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the ArgosOS root directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install it first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install it first."
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf frontend/dist
rm -rf frontend/dist-electron

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

if [ $? -ne 0 ]; then
    echo "❌ Frontend dependency installation failed"
    exit 1
fi

# Build frontend
echo "📦 Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    exit 1
fi

# Build for all platforms
echo "🖥️  Building Electron app for all platforms..."

# Build for all platforms explicitly
echo "🍎 Building for macOS (Intel and Apple Silicon)..."
npx electron-builder --mac --publish=never

echo "🪟 Building for Windows..."
npx electron-builder --win --publish=never

echo "🐧 Building for Linux..."
npx electron-builder --linux --publish=never

if [ $? -ne 0 ]; then
    echo "❌ Electron build failed"
    exit 1
fi

cd ..

# Create distribution directory
DIST_DIR="distribution/ArgosOS-v1.0.0"
echo "📁 Creating distribution directory: $DIST_DIR"
mkdir -p "$DIST_DIR"

# Copy all built files
echo "📋 Copying built files..."
cp frontend/dist-electron/*.dmg "$DIST_DIR/" 2>/dev/null || true
cp frontend/dist-electron/*.exe "$DIST_DIR/" 2>/dev/null || true
cp frontend/dist-electron/*.AppImage "$DIST_DIR/" 2>/dev/null || true
cp frontend/dist-electron/*.deb "$DIST_DIR/" 2>/dev/null || true
cp frontend/dist-electron/*.rpm "$DIST_DIR/" 2>/dev/null || true

# Create comprehensive documentation
echo "📚 Creating documentation..."

# README.md
cat > "$DIST_DIR/README.md" << 'EOF'
# ArgosOS v1.0.0 - Multi-Platform Distribution

## 🚀 Quick Start

### System Requirements
- **macOS**: 10.12+ (Sierra or later) - Intel x64 or Apple Silicon (ARM64)
- **Windows**: Windows 10+ (x64)
- **Linux**: Ubuntu 18.04+ or equivalent (x64)

### Installation

#### macOS
1. Download `ArgosOS-1.0.0-arm64.dmg` (Apple Silicon) or `ArgosOS-1.0.0-x64.dmg` (Intel)
2. Double-click the DMG file to mount it
3. Drag the ArgosOS app to your Applications folder
4. Launch from Applications or Launchpad

#### Windows
1. Download `ArgosOS-1.0.0.exe`
2. Run the installer as Administrator
3. Follow the installation wizard
4. Launch from Start Menu or Desktop shortcut

#### Linux
1. Download `ArgosOS-1.0.0.AppImage`
2. Make it executable: `chmod +x ArgosOS-1.0.0.AppImage`
3. Run: `./ArgosOS-1.0.0.AppImage`

### First Time Setup

1. **Launch ArgosOS**
2. **Configure OpenAI API Key** (optional but recommended):
   - Click on the "Settings" tab
   - Enter your OpenAI API key
   - Click "Save API Key"
3. **Start using**: Upload documents and search with AI!

## 📋 Features

### Core Features
- **Document Upload**: Support for PDF, TXT, DOC, DOCX, images, and more
- **AI-Powered Search**: Intelligent search through your documents
- **Smart Summarization**: Automatic document summarization
- **Tag Generation**: AI-generated tags for easy organization
- **Cross-Platform**: Works on macOS, Windows, and Linux

### Supported File Types
- **Documents**: PDF, TXT, DOC, DOCX, MD, RTF
- **Images**: JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP
- **Text Files**: Any text-based format

## 🔧 Configuration

### OpenAI API Setup (Recommended)
1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Open ArgosOS and go to Settings
3. Enter your API key and save
4. Enjoy full AI features!

### Without API Key
- Basic document upload and storage
- Limited search functionality
- No AI summarization or tagging

## 🚨 Troubleshooting

### Common Issues

**App won't open:**
- **macOS**: Right-click the app → "Open" (first time only)
- **Windows**: Run as Administrator
- **Linux**: Check file permissions and dependencies

**Search not working:**
- Check your internet connection
- Verify OpenAI API key in Settings
- Try uploading a document first

**File upload fails:**
- Check file format is supported
- Ensure file is not corrupted
- Try smaller files first

## 🔒 Security & Privacy

- **Local Storage**: All documents are stored locally on your device
- **Encrypted API Keys**: Your OpenAI API key is encrypted before storage
- **No Data Collection**: We don't collect or transmit your documents
- **Secure Communication**: All API calls use HTTPS encryption

---

**Version**: 1.0.0  
**Build Date**: $(date)  
**Platforms**: macOS (Intel/ARM64), Windows (x64), Linux (x64)  

Enjoy using ArgosOS! 🎉
EOF

# Create platform-specific installation guides
cat > "$DIST_DIR/INSTALLATION.md" << 'EOF'
# ArgosOS Installation Guide

## 📦 Installation Steps

### macOS Installation

#### Method 1: Standard Installation
1. **Download** the appropriate DMG file:
   - `ArgosOS-1.0.0-arm64.dmg` for Apple Silicon Macs (M1, M2, M3)
   - `ArgosOS-1.0.0-x64.dmg` for Intel Macs
2. **Double-click** the DMG file to mount it
3. **Drag** the ArgosOS application to your Applications folder
4. **Eject** the DMG by dragging it to Trash
5. **Launch** ArgosOS from Applications or Launchpad

#### Method 2: Command Line Installation
```bash
# Mount the DMG
hdiutil attach ArgosOS-1.0.0-arm64.dmg

# Copy to Applications
cp -R /Volumes/ArgosOS/ArgosOS.app /Applications/

# Unmount the DMG
hdiutil detach /Volumes/ArgosOS
```

### Windows Installation

1. **Download** `ArgosOS-1.0.0.exe`
2. **Right-click** the installer and select "Run as administrator"
3. **Follow** the installation wizard
4. **Choose** installation directory (default: C:\Program Files\ArgosOS)
5. **Create** desktop shortcut (optional)
6. **Launch** from Start Menu or Desktop shortcut

### Linux Installation

#### AppImage (Recommended)
1. **Download** `ArgosOS-1.0.0.AppImage`
2. **Make executable**:
   ```bash
   chmod +x ArgosOS-1.0.0.AppImage
   ```
3. **Run**:
   ```bash
   ./ArgosOS-1.0.0.AppImage
   ```

#### Optional: Install to System
```bash
# Extract AppImage
./ArgosOS-1.0.0.AppImage --appimage-extract

# Move to system directory
sudo mv squashfs-root /opt/ArgosOS

# Create desktop entry
sudo ln -s /opt/ArgosOS/AppRun /usr/local/bin/argos-os
```

## 🔧 System Requirements

### Minimum Requirements
- **macOS**: 10.12 (Sierra) or later
- **Windows**: Windows 10 (version 1903) or later
- **Linux**: Ubuntu 18.04+ or equivalent
- **RAM**: 4GB
- **Storage**: 500MB free space
- **Internet**: Required for AI features

### Recommended Requirements
- **macOS**: 11.0 (Big Sur) or later
- **Windows**: Windows 11
- **Linux**: Ubuntu 20.04+ or equivalent
- **RAM**: 8GB or more
- **Storage**: 2GB free space
- **Internet**: Stable broadband connection

## 🚨 Troubleshooting Installation

### macOS Issues

#### "App is damaged and can't be opened"
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine /Applications/ArgosOS.app
```

#### "App can't be opened because it is from an unidentified developer"
1. Right-click the app → "Open"
2. Or go to System Preferences → Security & Privacy → "Open Anyway"

### Windows Issues

#### "Windows protected your PC"
1. Click "More info"
2. Click "Run anyway"

#### Installation fails
1. Run as Administrator
2. Check available disk space
3. Disable antivirus temporarily

### Linux Issues

#### "Permission denied"
```bash
chmod +x ArgosOS-1.0.0.AppImage
```

#### AppImage won't run
```bash
# Install FUSE if needed
sudo apt install fuse libfuse2

# Run with --appimage-extract-and-run
./ArgosOS-1.0.0.AppImage --appimage-extract-and-run
```

---

**Installation completed successfully?** 🎉  
Enjoy using ArgosOS for your document management needs!
EOF

# Create checksums for all files
echo "📋 Creating file checksums..."
cd "$DIST_DIR"
for file in *.dmg *.exe *.AppImage *.deb *.rpm; do
    if [ -f "$file" ]; then
        echo "Creating checksums for $file"
        sha256sum "$file" > "$file.sha256"
        md5sum "$file" > "$file.md5"
    fi
done
cd ../..

# Create package info
cat > "$DIST_DIR/PACKAGE_INFO.txt" << EOF
ArgosOS v1.0.0 Multi-Platform Distribution Package
=================================================

Package Contents:
EOF

# List all files in the distribution
ls -la "$DIST_DIR" | grep -E '\.(dmg|exe|AppImage|deb|rpm)$' | while read line; do
    filename=$(echo "$line" | awk '{print $NF}')
    if [ -f "$DIST_DIR/$filename" ]; then
        echo "- $filename (Main application)" >> "$DIST_DIR/PACKAGE_INFO.txt"
    fi
done

cat >> "$DIST_DIR/PACKAGE_INFO.txt" << 'EOF'
- README.md (User documentation)
- INSTALLATION.md (Installation guide)
- PACKAGE_INFO.txt (This file)

System Requirements:
- macOS 10.12+ (Intel x64 or Apple Silicon ARM64)
- Windows 10+ (x64)
- Linux Ubuntu 18.04+ or equivalent (x64)
- 4GB RAM minimum, 8GB recommended
- 500MB free storage space
- Internet connection for AI features

Installation:
- macOS: Double-click DMG, drag to Applications
- Windows: Run EXE installer as Administrator
- Linux: Make AppImage executable and run

Support:
- Documentation: README.md
- Installation Help: INSTALLATION.md

Created: $(date)
Version: 1.0.0
Platforms: macOS (Intel/ARM64), Windows (x64), Linux (x64)
EOF

# Create ZIP package
echo "📦 Creating ZIP package..."
cd distribution
zip -r ArgosOS-v1.0.0-multi-platform.zip ArgosOS-v1.0.0/
cd ..

echo "✅ Multi-platform distribution package created successfully!"
echo ""
echo "📦 Package Contents:"
ls -la "$DIST_DIR"
echo ""
echo "🚀 Distribution package ready:"
echo "   - Directory: $DIST_DIR"
echo "   - ZIP file: distribution/ArgosOS-v1.0.0-multi-platform.zip"
echo ""
echo "📋 Files created:"
echo "   - macOS: $(ls "$DIST_DIR"/*.dmg 2>/dev/null | wc -l) DMG file(s)"
echo "   - Windows: $(ls "$DIST_DIR"/*.exe 2>/dev/null | wc -l) EXE file(s)"
echo "   - Linux: $(ls "$DIST_DIR"/*.AppImage 2>/dev/null | wc -l) AppImage file(s)"
echo ""
echo "🎉 Multi-platform distribution package ready!"
