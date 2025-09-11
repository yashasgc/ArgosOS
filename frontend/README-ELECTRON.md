# ArgosOS Electron Desktop App

This document explains how to run and build the ArgosOS desktop application using Electron.

## Prerequisites

1. **Node.js** (v18 or higher)
2. **Python** (v3.8 or higher) with the backend dependencies installed
3. **Backend running** on `http://localhost:8000`

## Installation

1. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Install backend dependencies (if not already done):
   ```bash
   cd ..
   pip install -r requirements.txt
   ```

## Development

### Start the Backend
```bash
# From the project root
python start.py
```

### Start the Electron App in Development Mode
```bash
# From the frontend directory
npm run electron:dev
```

This will:
- Start the Vite development server on `http://localhost:5173`
- Wait for the server to be ready
- Launch the Electron app pointing to the development server

### Alternative: Start Electron Only
```bash
# If the backend and frontend are already running
npm run electron
```

## Building for Production

### Build the Frontend
```bash
npm run build
```

### Build the Electron App
```bash
npm run electron:build
```

### Create Distribution Packages
```bash
npm run electron:dist
```

This creates platform-specific installers in the `dist-electron` directory:
- **macOS**: `.dmg` file
- **Windows**: `.exe` installer
- **Linux**: `.AppImage` file

## Features

### Electron-Specific Features
- **Native File Picker**: Use the OS file dialog for better UX
- **Menu Bar**: Native application menu with keyboard shortcuts
- **Auto-Updater**: Automatic updates (when configured)
- **Settings Storage**: Persistent settings using electron-store
- **Backend Integration**: Automatic Python backend startup

### Cross-Platform Support
- **macOS**: Native menu bar, dock integration
- **Windows**: Taskbar integration, native file dialogs
- **Linux**: AppImage support, desktop integration

## Configuration

### Environment Variables
- `NODE_ENV=development` - Enables development mode with hot reload
- `OPENAI_API_KEY` - Your OpenAI API key (can be set in the app settings)

### Build Configuration
The Electron build is configured in `package.json` under the `build` section:
- App ID: `com.argos.os`
- Product Name: `ArgosOS`
- Output Directory: `dist-electron`

## File Structure

```
frontend/
├── electron/
│   ├── main.js          # Main Electron process
│   └── preload.js       # Preload script for security
├── src/
│   ├── components/
│   │   └── ElectronFileUpload.tsx  # Electron-specific file upload
│   ├── hooks/
│   │   └── useElectron.ts          # Electron API hook
│   ├── types/
│   │   └── electron.d.ts           # TypeScript definitions
│   └── App.tsx                     # Main app with Electron integration
├── package.json                    # Dependencies and scripts
└── README-ELECTRON.md             # This file
```

## API Integration

The Electron app communicates with the Python backend through:
- **IPC (Inter-Process Communication)**: For file operations and dialogs
- **HTTP API**: For document processing and LLM operations
- **Electron Store**: For persistent settings

## Troubleshooting

### Common Issues

1. **Backend not starting**: Ensure Python dependencies are installed and port 8000 is available
2. **Electron not launching**: Check that Node.js and npm are properly installed
3. **File upload not working**: Ensure the backend is running and accessible
4. **Build failures**: Clear `node_modules` and reinstall dependencies

### Debug Mode
```bash
# Enable Electron debug logging
DEBUG=electron* npm run electron:dev
```

### Logs
- **Main Process**: Check the terminal where you started the app
- **Renderer Process**: Use DevTools (Cmd/Ctrl+Shift+I)
- **Backend**: Check the Python console output

## Development Tips

1. **Hot Reload**: The app automatically reloads when you make changes to the frontend code
2. **DevTools**: Press `Cmd/Ctrl+Shift+I` to open developer tools
3. **Menu Shortcuts**: Use `Cmd/Ctrl+N` for new document, `Cmd/Ctrl+O` for open file
4. **Settings**: Access via the Settings tab or `Cmd/Ctrl+,`

## Deployment

### Creating Installers
```bash
# Build for current platform
npm run electron:dist

# Build for specific platform (requires additional setup)
npm run electron:build -- --mac
npm run electron:build -- --win
npm run electron:build -- --linux
```

### Code Signing (Optional)
For production deployment, configure code signing in the `build` section of `package.json`.

## Security

- **Context Isolation**: Enabled for security
- **Node Integration**: Disabled in renderer process
- **Preload Script**: Secure API exposure
- **API Key Storage**: Encrypted on the backend server

## Performance

- **Memory Usage**: Electron apps typically use more memory than web apps
- **Startup Time**: First launch may be slower due to backend startup
- **File Processing**: Large files are processed asynchronously

## Support

For issues specific to the Electron app:
1. Check the troubleshooting section above
2. Review the console logs
3. Ensure all dependencies are properly installed
4. Verify the backend is running and accessible
