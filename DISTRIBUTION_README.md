# ArgosOS Distribution Script

## 🚀 Quick Start

### Create Distribution Package
```bash
# Run the distribution script
./create-distribution.sh
```

This will:
1. Build the Electron app (if not already built)
2. Create a complete distribution package
3. Generate all necessary documentation
4. Create installation scripts
5. Package everything into a ZIP file

### What Gets Created

The script creates a complete distribution package in `distribution/ArgosOS-v1.0.0/`:

```
ArgosOS-v1.0.0/
├── ArgosOS-1.0.0-arm64.dmg          # Main application installer
├── README.md                        # User documentation
├── INSTALLATION.md                  # Installation guide
├── install.sh                       # Installation script
├── verify_installation.sh           # Verification script
├── uninstall.sh                     # Uninstaller script
├── PACKAGE_INFO.txt                 # Package information
├── ArgosOS-1.0.0-arm64.dmg.sha256   # File integrity checksum
└── ArgosOS-1.0.0-arm64.dmg.md5      # File integrity checksum
```

Plus a ZIP package: `distribution/ArgosOS-v1.0.0-macOS.zip`

## 📋 Prerequisites

- macOS system (for building)
- Node.js and npm installed
- Electron dependencies installed (`npm install` in frontend/)
- Python and Poetry (for backend)

## 🔧 Usage

### Basic Usage
```bash
# Make sure you're in the ArgosOS root directory
cd /path/to/ArgosOS

# Run the distribution script
./create-distribution.sh
```

### What the Script Does

1. **Checks Environment**: Verifies you're in the right directory
2. **Builds Electron App**: Runs `npm run electron:dist` if needed
3. **Creates Distribution Directory**: Sets up the package structure
4. **Copies DMG File**: Moves the built app to distribution folder
5. **Generates Documentation**: Creates README, installation guides, etc.
6. **Creates Scripts**: Generates install, verify, and uninstall scripts
7. **Adds Security**: Creates file integrity checksums
8. **Packages Everything**: Creates a ZIP file for easy distribution

### Output

After running the script, you'll have:
- **Distribution Directory**: `distribution/ArgosOS-v1.0.0/`
- **ZIP Package**: `distribution/ArgosOS-v1.0.0-macOS.zip`
- **Ready for Distribution**: Upload the ZIP file anywhere

## 📦 Distribution

### Upload to GitHub Releases
1. Create a new release on GitHub
2. Upload `ArgosOS-v1.0.0-macOS.zip` as a release asset
3. Tag the release as `v1.0.0`

### Upload to Website
1. Host the ZIP file on your website
2. Create a download page with instructions
3. Share the download link

### Direct Distribution
1. Share the ZIP file directly
2. Users can extract and run `./install.sh`

## 🎯 User Installation

Users who download the package can install ArgosOS by:

### Quick Installation
```bash
# Extract the ZIP file
unzip ArgosOS-v1.0.0-macOS.zip
cd ArgosOS-v1.0.0

# Run the installer
./install.sh

# Verify installation
./verify_installation.sh
```

### Manual Installation
1. Extract the ZIP file
2. Double-click `ArgosOS-1.0.0-arm64.dmg`
3. Drag ArgosOS.app to Applications folder
4. Launch from Applications or Launchpad

## 🔒 Security Features

- **File Integrity**: SHA256 and MD5 checksums included
- **Local Storage**: All documents stored locally
- **Encrypted API Keys**: Secure credential storage
- **No Data Collection**: Privacy-first approach

## 📚 Documentation

The distribution package includes comprehensive documentation:
- **README.md**: Complete user guide
- **INSTALLATION.md**: Detailed installation instructions
- **PACKAGE_INFO.txt**: Package information and checksums

## 🚨 Troubleshooting

### Script Issues
- **Permission Denied**: Run `chmod +x create-distribution.sh`
- **DMG Not Found**: Make sure Electron app is built first
- **Directory Error**: Run from ArgosOS root directory

### Build Issues
- **Electron Build Fails**: Check Node.js and npm installation
- **Missing Dependencies**: Run `npm install` in frontend/
- **Python Issues**: Ensure Poetry is installed and configured

## 🔄 Updates

To create a new distribution:
1. Update version numbers in the script
2. Run `./create-distribution.sh`
3. Upload the new ZIP file

## 📊 Package Contents

- **Main App**: ~100MB DMG file
- **Documentation**: ~50KB of guides
- **Scripts**: ~10KB of installation tools
- **Total Package**: ~100MB ZIP file

---

**Ready to distribute!** 🎉  
Run `./create-distribution.sh` to create your distribution package.




