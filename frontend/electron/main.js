'use strict';

const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const Store = require('electron-store');

const store = new Store();
const BACKEND_PORT = 8000;

let mainWindow = null;
let backendProcess = null;

function checkBackend() {
  return new Promise((resolve) => {
    const req = http.get(`http://localhost:${BACKEND_PORT}/health`, (res) => {
      resolve(res.statusCode < 400);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function waitForBackend(timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await checkBackend()) return true;
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

async function startBackend() {
  const alreadyRunning = await checkBackend();
  if (alreadyRunning) {
    console.log('Backend already running, skipping startup');
    return;
  }

  // Store data in writable user data dir, not the app bundle
  const userDataDir = app.getPath('userData');
  const dataDir = path.join(userDataDir, 'data');
  const blobsDir = path.join(dataDir, 'blobs');
  fs.mkdirSync(blobsDir, { recursive: true });

  let pythonPath, args, cwd;

  if (app.isPackaged) {
    const pythonBin = process.platform === 'win32' ? 'Scripts\\python.exe' : 'bin/python';
    pythonPath = path.join(process.resourcesPath, 'standalone-python-env', pythonBin);
    const startScript = path.join(process.resourcesPath, 'start-standalone.py');
    args = [startScript];
    cwd = process.resourcesPath;
  } else {
    pythonPath = 'poetry';
    args = ['run', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT)];
    cwd = path.join(__dirname, '..', '..');
  }

  console.log('Starting backend:', pythonPath, args.join(' '));

  // Filter parent env: pass system vars needed by Python, drop any credentials
  // that happen to be set in the user's shell (AWS keys, tokens, etc.)
  const SECRET_PATTERN = /API[_-]?KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL|PRIVATE[_-]?KEY/i;
  const safeEnv = Object.fromEntries(
    Object.entries(process.env).filter(([k]) => !SECRET_PATTERN.test(k))
  );

  backendProcess = spawn(pythonPath, args, {
    cwd,
    env: {
      ...safeEnv,
      ARGOS_DATA_DIR: dataDir,
      DATABASE_URL: `sqlite:///${path.join(dataDir, 'argos.db')}`,
      DATA_DIR: dataDir,
      BLOBS_DIR: blobsDir,
      PORT: String(BACKEND_PORT),
    },
    stdio: 'pipe',
  });

  backendProcess.stdout.on('data', (d) => process.stdout.write(`[backend] ${d}`));
  backendProcess.stderr.on('data', (d) => process.stderr.write(`[backend] ${d}`));
  backendProcess.on('error', (err) => console.error('Backend failed to start:', err.message));
  backendProcess.on('close', (code) => console.log(`Backend exited with code ${code}`));
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    titleBarStyle: 'default',
    show: false,
    backgroundColor: '#0f172a',
  });

  // Show branded loading screen while backend starts
  mainWindow.loadURL(
    "data:text/html,<!DOCTYPE html><html><head><style>*{margin:0;padding:0;box-sizing:border-box}body{background:%230f172a;display:flex;align-items:center;justify-content:center;height:100vh;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.c{text-align:center;color:%23e2e8f0}.icon{width:80px;height:80px;background:linear-gradient(135deg,%233b82f6,%236366f1);border-radius:20px;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;font-size:40px;font-weight:700;color:%23fff}h1{font-size:32px;font-weight:700;margin-bottom:8px;color:%23f8fafc}p{color:%2394a3b8;font-size:16px}.dots::after{content:'...';animation:d 1.5s steps(3,end) infinite}@keyframes d{0%,33%{content:'.'}34%,66%{content:'..'}67%,100%{content:'...'}}</style></head><body><div class=c><div class=icon>A</div><h1>ArgosOS</h1><p>Starting<span class=dots></span></p></div></body></html>"
  );

  mainWindow.once('ready-to-show', () => mainWindow && mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

async function loadApp() {
  if (!mainWindow) return;

  const ready = await waitForBackend(30000);

  if (!mainWindow) return; // window might have been closed during the wait

  if (!ready) {
    mainWindow.loadURL(
      "data:text/html,<!DOCTYPE html><html><head><style>*{margin:0;padding:0;box-sizing:border-box}body{background:%230f172a;display:flex;align-items:center;justify-content:center;height:100vh;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.c{text-align:center;color:%23e2e8f0;max-width:480px;padding:24px}h1{font-size:24px;font-weight:700;color:%23ef4444;margin-bottom:12px}p{color:%2394a3b8;line-height:1.6}button{margin-top:20px;padding:10px 24px;background:%233b82f6;color:%23fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}button:hover{background:%232563eb}</style></head><body><div class=c><h1>Backend Failed to Start</h1><p>ArgosOS could not start the Python backend. Ensure Python and all dependencies are installed.</p><button onclick=location.reload()>Retry</button></div></body></html>"
    );
    return;
  }

  if (!app.isPackaged) {
    mainWindow.loadURL(`http://localhost:5173`);
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }
}

function createMenu() {
  const fileSubmenu = [
    {
      label: 'Upload Document',
      accelerator: 'CmdOrCtrl+N',
      click: () => mainWindow && mainWindow.webContents.send('menu-new-document'),
    },
    {
      label: 'Open File...',
      accelerator: 'CmdOrCtrl+O',
      click: async () => {
        if (!mainWindow) return;
        const result = await dialog.showOpenDialog(mainWindow, {
          properties: ['openFile'],
          filters: [
            { name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md'] },
            { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'] },
          ],
        });
        if (!result.canceled) {
          mainWindow.webContents.send('menu-open-document', result.filePaths[0]);
        }
      },
    },
    { type: 'separator' },
    {
      label: 'Settings',
      accelerator: 'CmdOrCtrl+,',
      click: () => mainWindow && mainWindow.webContents.send('menu-settings'),
    },
  ];

  if (process.platform !== 'darwin') {
    fileSubmenu.push({ type: 'separator' });
    fileSubmenu.push({
      label: 'Quit',
      accelerator: 'Ctrl+Q',
      click: () => app.quit(),
    });
  }

  const template = [
    { label: 'File', submenu: fileSubmenu },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
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
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Window',
      submenu:
        process.platform === 'darwin'
          ? [{ role: 'minimize' }, { role: 'zoom' }, { type: 'separator' }, { role: 'front' }]
          : [{ role: 'minimize' }, { role: 'close' }],
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
              message: 'ArgosOS',
              detail: `Version ${app.getVersion()}\n\nIntelligent document management with AI-powered analysis.`,
            });
          },
        },
      ],
    },
  ];

  if (process.platform === 'darwin') {
    template.unshift({
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    });
  }

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// App lifecycle
app.whenReady().then(async () => {
  createWindow();
  createMenu();
  await startBackend();
  loadApp(); // intentionally not awaited — loading screen shows while polling
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', stopBackend);

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
    loadApp();
  }
});

// IPC: File dialogs
ipcMain.handle('select-file', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md'] },
      { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('show-message-box', async (_, options) => {
  return dialog.showMessageBox(mainWindow, options);
});

ipcMain.handle('get-app-version', () => app.getVersion());

// IPC: Persistent key-value store
ipcMain.handle('get-store-value', (_, key) => store.get(key));
ipcMain.handle('set-store-value', (_, key, value) => store.set(key, value));
ipcMain.handle('get-store-all', () => store.store);
ipcMain.handle('clear-store', () => store.clear());

// IPC: Open files with system default application
ipcMain.handle('open-file', async (_, fileUrl) => {
  try {
    if (fileUrl.startsWith('http://') || fileUrl.startsWith('https://')) {
      await shell.openExternal(fileUrl);
    } else {
      await shell.openPath(fileUrl);
    }
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('open-file-data', async (_, fileData, filename) => {
  try {
    const tempPath = path.join(app.getPath('temp'), `argos-${Date.now()}-${filename}`);
    fs.writeFileSync(tempPath, Buffer.from(fileData));
    await shell.openPath(tempPath);
    setTimeout(() => { try { fs.unlinkSync(tempPath); } catch (_) {} }, 30000);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC: Proxy API calls to backend from main process (avoids CORS in renderer)
ipcMain.handle('api-call', async (_, { method, endpoint, data }) => {
  try {
    const axios = require('axios');
    const response = await axios({
      method,
      url: `http://localhost:${BACKEND_PORT}${endpoint}`,
      data,
      headers: { 'Content-Type': 'application/json' },
      timeout: 60000,
    });
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message,
    };
  }
});
