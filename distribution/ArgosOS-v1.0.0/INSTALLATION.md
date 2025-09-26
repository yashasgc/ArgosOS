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



