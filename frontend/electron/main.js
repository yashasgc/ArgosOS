const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');

// Initialize electron-store
const store = new Store();

// Keep a global reference of the window object
let mainWindow;
let backendProcess;

// Enable live reload for development
if (process.env.NODE_ENV === 'development') {
  try {
    require('electron-reload')(__dirname, {
      electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron'),
      hardResetMethod: 'exit'
    });
  } catch (err) {
    console.log('electron-reload not available in production');
  }
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    titleBarStyle: 'default',
    show: false
  });

  // Load the app
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  if (isDev) {
    // In development, load from Vite dev server
    console.log('Loading from Vite dev server...');
    
    // Wait for Vite to be ready, then load
    const loadViteApp = () => {
      const ports = [5173, 5174, 5175, 5176, 3000, 8080];
      let loaded = false;
      
      const tryLoad = (port) => {
        if (loaded || !mainWindow) return; // Check if mainWindow still exists
        console.log(`Trying to load from http://localhost:${port}`);
        
        mainWindow.loadURL(`http://localhost:${port}`).then(() => {
          console.log(`Successfully loaded from port ${port}`);
          loaded = true;
        }).catch((error) => {
          console.log(`Failed to load from port ${port}:`, error.message);
          const nextPort = ports[ports.indexOf(port) + 1];
          if (nextPort && mainWindow) { // Check if mainWindow still exists
            setTimeout(() => tryLoad(nextPort), 1000);
          } else {
            console.error('Could not connect to any Vite server');
            // Fallback to a simple HTML page
            if (mainWindow) {
              mainWindow.loadURL('data:text/html,<h1>Loading...</h1><p>Waiting for Vite server...</p>');
            }
          }
        });
      };
      
      // Start trying to load after a short delay
      setTimeout(() => tryLoad(5173), 2000);
    };
    
    loadViteApp();
  } else {
    // In production, load from built files
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    console.log('Window ready to show');
    mainWindow.show();
    
    // Open DevTools in development
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Show window immediately for debugging
  if (isDev) {
    mainWindow.show();
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

function startBackend() {
  // Check if backend is already running
  const http = require('http');
  const checkBackend = () => {
    return new Promise((resolve) => {
      const req = http.get('http://localhost:8000', (res) => {
        resolve(true);
      });
      req.on('error', () => resolve(false));
      req.setTimeout(1000, () => {
        req.destroy();
        resolve(false);
      });
    });
  };

  checkBackend().then((isRunning) => {
    if (isRunning) {
      console.log('Backend is already running');
      return;
    }

    // Start the Python backend
    const backendPath = path.join(__dirname, '..', '..', 'start.py');
    backendProcess = spawn('python3', [backendPath], {
      cwd: path.join(__dirname, '..', '..'),
      stdio: 'pipe'
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

// App event handlers
app.whenReady().then(() => {
  createWindow();
  startBackend();
  
  // Create application menu
  createMenu();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

// IPC handlers
ipcMain.handle('select-file', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md'] },
      { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });
  
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-store-value', (event, key) => {
  return store.get(key);
});

ipcMain.handle('set-store-value', (event, key, value) => {
  store.set(key, value);
});

ipcMain.handle('get-store-all', () => {
  return store.store;
});

ipcMain.handle('clear-store', () => {
  store.clear();
});

// Handle file opening with system default application
ipcMain.handle('open-file', async (event, fileUrl) => {
  try {
    console.log('Opening file:', fileUrl);
    
    if (fileUrl.startsWith('http://localhost:') || fileUrl.startsWith('https://')) {
      // For local server URLs, open in default browser
      await shell.openExternal(fileUrl);
    } else {
      // For local file paths, open with default application
      await shell.openPath(fileUrl);
    }
    return { success: true };
  } catch (error) {
    console.error('File open error:', error);
    return { success: false, error: error.message };
  }
});

// Handle file opening with file data
ipcMain.handle('open-file-data', async (event, fileData, filename) => {
  try {
    console.log('Opening file data:', filename);
    
    const { app } = require('electron');
    const path = require('path');
    const fs = require('fs');
    
    // Create a temporary file path
    const tempDir = app.getPath('temp');
    const tempFilePath = path.join(tempDir, `argos-temp-${Date.now()}-${filename}`);
    
    // Write the file data to temp file
    fs.writeFileSync(tempFilePath, Buffer.from(fileData));
    
    // Open the temporary file with system default application
    await shell.openPath(tempFilePath);
    
    // Clean up the temp file after a delay
    setTimeout(() => {
      try {
        fs.unlinkSync(tempFilePath);
      } catch (err) {
        console.log('Could not delete temp file:', err.message);
      }
    }, 30000); // 30 seconds delay
    
    return { success: true };
  } catch (error) {
    console.error('File open error:', error);
    return { success: false, error: error.message };
  }
});

// Backend API calls
ipcMain.handle('api-call', async (event, { method, endpoint, data }) => {
  try {
    const axios = require('axios');
    
    // Configure axios based on data type
    const config = {
      method,
      url: `http://localhost:8000${endpoint}`,
      timeout: 30000
    };
    
    if (data instanceof FormData) {
      // For FormData, let axios handle the headers automatically
      config.data = data;
      config.headers = {
        'Content-Type': 'multipart/form-data'
      };
    } else {
      // For JSON data
      config.data = data;
      config.headers = {
        'Content-Type': 'application/json'
      };
    }
    
    const response = await axios(config);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('API call failed:', error.message);
    console.error('Error response:', error.response?.data);
    return { 
      success: false, 
      error: error.response?.data?.detail || error.message 
    };
  }
});

// Auto-updater (disabled for now)
// autoUpdater.checkForUpdatesAndNotify();

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Document',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('menu-new-document');
          }
        },
        {
          label: 'Open Document',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const filePath = await dialog.showOpenDialog(mainWindow, {
              properties: ['openFile'],
              filters: [
                { name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md'] },
                { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'] }
              ]
            });
            
            if (!filePath.canceled) {
              mainWindow.webContents.send('menu-open-document', filePath.filePaths[0]);
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Settings',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            mainWindow.webContents.send('menu-settings');
          }
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectall' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'close' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About ArgosOS',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About ArgosOS',
              message: 'ArgosOS Document Processing',
              detail: `Version ${app.getVersion()}\n\nA powerful document processing application with OCR and LLM capabilities.`
            });
          }
        },
        {
          label: 'Check for Updates',
          click: () => {
            autoUpdater.checkForUpdatesAndNotify();
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}
