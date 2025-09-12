# ArgosOS Distribution Guide

This guide explains how to create shareable installers for ArgosOS.

## 🚀 Distribution Options

### Option 1: Electron App (Recommended)
Creates native desktop apps for Windows, macOS, and Linux.

### Option 2: Docker Container
Creates a containerized version that runs anywhere Docker is installed.

### Option 3: Web App
Deploy as a web application (requires server setup).

---

## 📦 Option 1: Electron App Distribution

### Prerequisites
```bash
# Install dependencies
cd frontend
npm install

# Install Python dependencies
cd ..
poetry install
```

### Build Process

#### 1. Build Frontend
```bash
cd frontend
npm run build
```

#### 2. Create Distribution Packages
```bash
# For all platforms
npm run electron:dist

# For specific platforms
npm run electron:dist -- --mac
npm run electron:dist -- --win
npm run electron:dist -- --linux
```

#### 3. Output Files
The built apps will be in `frontend/dist-electron/`:
- **macOS**: `ArgosOS-1.0.0.dmg`
- **Windows**: `ArgosOS Setup 1.0.0.exe`
- **Linux**: `ArgosOS-1.0.0.AppImage`

### Distribution Methods

#### A. Direct Download
1. Upload files to cloud storage (Google Drive, Dropbox, etc.)
2. Share download links
3. Users download and install

#### B. GitHub Releases
1. Create a GitHub release
2. Upload the built files as assets
3. Users download from GitHub

#### C. App Stores
- **Mac App Store**: Requires Apple Developer account
- **Microsoft Store**: Requires Microsoft Developer account
- **Snap Store**: For Linux distribution

---

## 🐳 Option 2: Docker Distribution

### Create Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "start.py"]
```

### Build and Run
```bash
# Build Docker image
docker build -t argos-os .

# Run container
docker run -p 8000:8000 -v $(pwd)/data:/app/data argos-os
```

### Distribution
```bash
# Save image
docker save argos-os > argos-os.tar

# Load on another machine
docker load < argos-os.tar
```

---

## 🌐 Option 3: Web App Deployment

### Using Railway
1. Connect GitHub repository to Railway
2. Set environment variables
3. Deploy automatically

### Using Heroku
1. Create `Procfile`:
```
web: python start.py
```
2. Deploy to Heroku
3. Set environment variables

### Using DigitalOcean App Platform
1. Connect repository
2. Configure build settings
3. Deploy

---

## 📋 Pre-Distribution Checklist

### Code Quality
- [ ] All tests pass
- [ ] No console errors
- [ ] Code is documented
- [ ] README is updated

### Security
- [ ] No hardcoded secrets
- [ ] Environment variables configured
- [ ] Input validation in place
- [ ] Error handling implemented

### User Experience
- [ ] Installation instructions clear
- [ ] Error messages helpful
- [ ] UI is intuitive
- [ ] Performance is acceptable

### Distribution
- [ ] App icons created
- [ ] Version numbers updated
- [ ] Release notes written
- [ ] Download links tested

---

## 🎯 Recommended Distribution Strategy

### For Beta Testing
1. **GitHub Releases** - Easy for developers to test
2. **Direct Download** - Simple for non-technical users

### For Production
1. **Electron App** - Best user experience
2. **Docker** - For server deployments
3. **Web App** - For easy access

### Marketing
1. **GitHub Repository** - Source code and documentation
2. **Demo Video** - Show features in action
3. **Documentation** - Clear setup instructions
4. **Community** - Discord/Slack for support

---

## 🔧 Advanced Configuration

### Auto-Updates
Configure `electron-updater` for automatic updates:
```javascript
// In main process
const { autoUpdater } = require('electron-updater');
autoUpdater.checkForUpdatesAndNotify();
```

### Code Signing
For trusted installers:
- **macOS**: Apple Developer certificate
- **Windows**: Code signing certificate
- **Linux**: GPG signing

### Notarization (macOS)
Required for distribution outside App Store:
```bash
xcrun altool --notarize-app --file "ArgosOS.dmg" --username "your@email.com" --password "app-password"
```

---

## 📊 Distribution Metrics

Track your distribution success:
- Download counts
- Installation success rate
- User feedback
- Bug reports
- Feature requests

---

## 🆘 Support

For distribution issues:
1. Check build logs
2. Test on clean machines
3. Verify all dependencies
4. Check platform-specific requirements
