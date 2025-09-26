#!/bin/bash

# ArgosOS Distribution Creation Script
# This script creates a complete distribution package for ArgosOS

set -e

echo "🚀 ArgosOS Distribution Creation Script"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the ArgosOS root directory"
    exit 1
fi

# Check if Electron app is built
if [ ! -f "frontend/dist-electron/ArgosOS-1.0.0-arm64.dmg" ]; then
    echo "📦 Building Electron app first..."
    cd frontend
    npm run electron:dist
    cd ..
fi

# Create distribution directory
DIST_DIR="distribution/ArgosOS-v1.0.0"
echo "📁 Creating distribution directory: $DIST_DIR"
mkdir -p "$DIST_DIR"

# Copy the DMG file
echo "📋 Copying DMG file..."
cp frontend/dist-electron/ArgosOS-1.0.0-arm64.dmg "$DIST_DIR/"

# Create documentation files
echo "📚 Creating documentation..."

# README.md
cat > "$DIST_DIR/README.md" << 'EOF'
# ArgosOS v1.0.0 - Desktop Distribution

## 🚀 Quick Start

### System Requirements
- **macOS**: 10.12+ (macOS Sierra or later)
- **Architecture**: Apple Silicon (ARM64) or Intel x64
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Internet**: Required for AI features (OpenAI API)

### Installation

1. **Download the DMG file**: `ArgosOS-1.0.0-arm64.dmg`
2. **Mount the DMG**: Double-click the downloaded file
3. **Drag to Applications**: Drag the ArgosOS app to your Applications folder
4. **Launch**: Open ArgosOS from Applications or Launchpad

### First Time Setup

1. **Launch ArgosOS** from your Applications folder
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

**App won't open on macOS:**
- Right-click the app → "Open" (first time only)
- Go to System Preferences → Security & Privacy → Allow

**Search not working:**
- Check your internet connection
- Verify OpenAI API key in Settings
- Try uploading a document first

**File upload fails:**
- Check file format is supported
- Ensure file is not corrupted
- Try smaller files first

**Performance issues:**
- Close other applications
- Check available RAM
- Restart the application

### Getting Help

1. **Check the logs**: Look for error messages in the app
2. **Restart the app**: Close and reopen ArgosOS
3. **Check system requirements**: Ensure your Mac meets minimum specs
4. **Update macOS**: Make sure you're running a supported version

## 🔒 Security & Privacy

- **Local Storage**: All documents are stored locally on your device
- **Encrypted API Keys**: Your OpenAI API key is encrypted before storage
- **No Data Collection**: We don't collect or transmit your documents
- **Secure Communication**: All API calls use HTTPS encryption

---

**Version**: 1.0.0  
**Build Date**: September 2024  
**Platform**: macOS (ARM64)  
**Size**: ~100MB

Enjoy using ArgosOS! 🎉
EOF

# INSTALLATION.md
cat > "$DIST_DIR/INSTALLATION.md" << 'EOF'
# ArgosOS Installation Guide

## 📦 Installation Steps

### Step 1: Download
1. Download `ArgosOS-1.0.0-arm64.dmg` from the distribution package
2. Verify the file size is approximately 100MB
3. Check the file integrity if provided

### Step 2: Install on macOS

#### Method 1: Standard Installation
1. **Double-click** the DMG file to mount it
2. **Drag** the ArgosOS application to your Applications folder
3. **Eject** the DMG by dragging it to Trash
4. **Launch** ArgosOS from Applications or Launchpad

#### Method 2: Command Line Installation
```bash
# Mount the DMG
hdiutil attach ArgosOS-1.0.0-arm64.dmg

# Copy to Applications
cp -R /Volumes/ArgosOS/ArgosOS.app /Applications/

# Unmount the DMG
hdiutil detach /Volumes/ArgosOS
```

### Step 3: First Launch
1. **Open** ArgosOS from Applications
2. If prompted about security, click **"Open"**
3. If blocked by macOS, go to:
   - System Preferences → Security & Privacy
   - Click **"Open Anyway"** under General tab

### Step 4: Initial Setup
1. **Configure API Key** (optional):
   - Click "Settings" tab
   - Enter your OpenAI API key
   - Click "Save API Key"
2. **Upload a test document** to verify functionality
3. **Try a search** to test AI features

## 🔧 System Requirements

### Minimum Requirements
- **macOS**: 10.12 (Sierra) or later
- **RAM**: 4GB
- **Storage**: 500MB free space
- **Internet**: Required for AI features

### Recommended Requirements
- **macOS**: 11.0 (Big Sur) or later
- **RAM**: 8GB or more
- **Storage**: 2GB free space
- **Internet**: Stable broadband connection

### Supported Architectures
- **Apple Silicon**: M1, M2, M3 Macs (ARM64)
- **Intel**: x64 Macs (Intel processors)

## 🚨 Troubleshooting Installation

### Common Issues

#### "App is damaged and can't be opened"
**Solution:**
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine /Applications/ArgosOS.app
```

#### "App can't be opened because it is from an unidentified developer"
**Solution:**
1. Right-click the app → "Open"
2. Or go to System Preferences → Security & Privacy → "Open Anyway"

#### "App won't launch"
**Solutions:**
1. Check system requirements
2. Restart your Mac
3. Try running from Terminal:
   ```bash
   /Applications/ArgosOS.app/Contents/MacOS/ArgosOS
   ```

#### "Insufficient permissions"
**Solution:**
```bash
# Fix permissions
sudo chmod -R 755 /Applications/ArgosOS.app
```

---

**Installation completed successfully?** 🎉  
Enjoy using ArgosOS for your document management needs!
EOF

# Create installation script
cat > "$DIST_DIR/install.sh" << 'EOF'
#!/bin/bash

echo "🔧 ArgosOS Installation Script"
echo "=============================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This installer is for macOS only."
    exit 1
fi

# Check macOS version
macos_version=$(sw_vers -productVersion)
echo "📱 macOS Version: $macos_version"

# Check if DMG exists
if [ ! -f "ArgosOS-1.0.0-arm64.dmg" ]; then
    echo "❌ Error: DMG file not found."
    exit 1
fi

# Mount the DMG
echo "📦 Mounting DMG..."
hdiutil attach ArgosOS-1.0.0-arm64.dmg

# Copy to Applications
echo "📋 Installing to Applications..."
cp -R /Volumes/ArgosOS/ArgosOS.app /Applications/

# Unmount DMG
echo "🗑️ Cleaning up..."
hdiutil detach /Volumes/ArgosOS

# Fix permissions
echo "🔧 Setting permissions..."
chmod -R 755 /Applications/ArgosOS.app

echo "✅ Installation complete!"
echo "🎉 You can now launch ArgosOS from Applications or Launchpad."
echo ""
echo "📚 For help, see README.md or INSTALLATION.md"
EOF

chmod +x "$DIST_DIR/install.sh"

# Create verification script
cat > "$DIST_DIR/verify_installation.sh" << 'EOF'
#!/bin/bash

echo "🔍 Verifying ArgosOS Installation"
echo "================================="

# Check if app exists
if [ -d "/Applications/ArgosOS.app" ]; then
    echo "✅ ArgosOS.app found in Applications"
else
    echo "❌ ArgosOS.app not found in Applications"
    exit 1
fi

# Check app permissions
if [ -x "/Applications/ArgosOS.app/Contents/MacOS/ArgosOS" ]; then
    echo "✅ App executable has proper permissions"
else
    echo "❌ App executable permission issue"
    exit 1
fi

# Check app bundle
if [ -f "/Applications/ArgosOS.app/Contents/Info.plist" ]; then
    echo "✅ App bundle structure is correct"
else
    echo "❌ App bundle structure issue"
    exit 1
fi

# Get app version
version=$(defaults read /Applications/ArgosOS.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo "Unknown")
echo "📱 App Version: $version"

echo "✅ Installation verification complete!"
echo "🚀 You can now launch ArgosOS from Applications or Launchpad."
EOF

chmod +x "$DIST_DIR/verify_installation.sh"

# Create uninstaller
cat > "$DIST_DIR/uninstall.sh" << 'EOF'
#!/bin/bash

echo "🗑️ ArgosOS Uninstaller"
echo "======================"

# Check if app exists
if [ -d "/Applications/ArgosOS.app" ]; then
    echo "📱 Found ArgosOS.app in Applications"
    
    # Ask for confirmation
    read -p "Are you sure you want to uninstall ArgosOS? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️ Removing ArgosOS.app..."
        rm -rf /Applications/ArgosOS.app
        
        echo "🗑️ Removing user data..."
        rm -rf ~/Library/Application\ Support/ArgosOS
        rm -rf ~/Library/Preferences/com.argosos.app.plist
        rm -rf ~/Library/Caches/com.argosos.app
        
        echo "✅ ArgosOS has been uninstalled."
    else
        echo "❌ Uninstall cancelled."
    fi
else
    echo "❌ ArgosOS.app not found in Applications"
fi
EOF

chmod +x "$DIST_DIR/uninstall.sh"

# Create checksums
echo "📋 Creating file checksums..."
cd "$DIST_DIR"
sha256sum ArgosOS-1.0.0-arm64.dmg > ArgosOS-1.0.0-arm64.dmg.sha256
md5sum ArgosOS-1.0.0-arm64.dmg > ArgosOS-1.0.0-arm64.dmg.md5
cd ../..

# Create package info
cat > "$DIST_DIR/PACKAGE_INFO.txt" << EOF
ArgosOS v1.0.0 Distribution Package
==================================

Package Contents:
- ArgosOS-1.0.0-arm64.dmg (Main application)
- README.md (User documentation)
- INSTALLATION.md (Installation guide)
- install.sh (Installation script)
- verify_installation.sh (Verification script)
- uninstall.sh (Uninstaller script)
- PACKAGE_INFO.txt (This file)

File Integrity:
- SHA256: $(cat "$DIST_DIR/ArgosOS-1.0.0-arm64.dmg.sha256")
- MD5: $(cat "$DIST_DIR/ArgosOS-1.0.0-arm64.dmg.md5")

System Requirements:
- macOS 10.12+ (Sierra or later)
- Apple Silicon (ARM64) or Intel x64
- 4GB RAM minimum, 8GB recommended
- 500MB free storage space
- Internet connection for AI features

Installation:
1. Run: ./install.sh
2. Verify: ./verify_installation.sh
3. Launch from Applications

Support:
- Documentation: README.md
- Installation Help: INSTALLATION.md

Created: $(date)
Version: 1.0.0
Platform: macOS (ARM64)
EOF

# Create ZIP package
echo "📦 Creating ZIP package..."
cd distribution
zip -r ArgosOS-v1.0.0-macOS.zip ArgosOS-v1.0.0/
cd ..

echo "✅ Distribution package created successfully!"
echo ""
echo "📦 Package Contents:"
ls -la "$DIST_DIR"
echo ""
echo "🚀 Distribution package ready:"
echo "   - Directory: $DIST_DIR"
echo "   - ZIP file: distribution/ArgosOS-v1.0.0-macOS.zip"
echo ""
echo "📋 Users can install by running: ./install.sh"
echo "🔍 Users can verify by running: ./verify_installation.sh"
echo ""
echo "🎉 Distribution package ready!"



