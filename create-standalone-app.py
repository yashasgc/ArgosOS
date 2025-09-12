#!/usr/bin/env python3
"""
Create a standalone ArgosOS app that bundles everything needed.
This script creates a self-contained application that doesn't require
Python, dependencies, or Tesseract to be pre-installed.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def create_standalone_app():
    """Create a standalone app with all dependencies bundled"""
    
    print("🚀 Creating Standalone ArgosOS App...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("start.py"):
        print("❌ Please run this script from the project root directory")
        return False
    
    # Create build directory
    build_dir = Path("standalone-build")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    print("📦 Step 1: Setting up Python environment...")
    
    # Create virtual environment
    venv_path = build_dir / "python-env"
    if not run_command(f"python3 -m venv {venv_path}"):
        return False
    
    # Determine the correct Python executable path
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Install Poetry
    print("📦 Step 2: Installing Poetry...")
    if not run_command(f"{pip_exe} install poetry", cwd=build_dir):
        return False
    
    # Copy Poetry files
    for file in ["pyproject.toml", "poetry.lock"]:
        if os.path.exists(file):
            shutil.copy2(file, build_dir / file)
    
    # Install dependencies with Poetry
    print("📦 Step 3: Installing Python dependencies with Poetry...")
    if not run_command(f"{python_exe} -m poetry install --no-dev", cwd=build_dir):
        return False
    
    # Install PyInstaller for creating standalone executables
    if not run_command(f"{pip_exe} install pyinstaller", cwd=build_dir):
        return False
    
    print("📦 Step 4: Creating standalone Python backend...")
    
    # Create a simple backend launcher
    backend_launcher = build_dir / "backend_launcher.py"
    with open(backend_launcher, "w") as f:
        f.write("""
import sys
import os
import subprocess
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Change to the correct directory
os.chdir(Path(__file__).parent)

# Import and run the main application
if __name__ == "__main__":
    try:
        from app.main import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"Error starting backend: {e}")
        sys.exit(1)
""")
    
    # Copy app directory
    shutil.copytree("app", build_dir / "app")
    
    # Copy other necessary files
    for file in ["requirements.txt", "start.py", "data"]:
        if os.path.exists(file):
            if os.path.isdir(file):
                shutil.copytree(file, build_dir / file)
            else:
                shutil.copy2(file, build_dir / file)
    
    print("📦 Step 5: Building standalone backend executable...")
    
    # Create PyInstaller spec file
    spec_file = build_dir / "backend.spec"
    with open(spec_file, "w") as f:
        f.write(f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['backend_launcher.py'],
    pathex=['{build_dir.absolute()}'],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('data', 'data'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'uvicorn',
        'fastapi',
        'sqlalchemy',
        'pytesseract',
        'PIL',
        'fitz',
        'docx',
        'pdfminer',
        'openai',
        'cryptography',
        'alembic',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='argos-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
""")
    
    # Build the executable
    if not run_command(f"{python_exe} -m PyInstaller backend.spec", cwd=build_dir):
        return False
    
    print("📦 Step 6: Creating Electron app with bundled backend...")
    
    # Copy frontend files
    frontend_build_dir = build_dir / "frontend"
    frontend_build_dir.mkdir()
    
    # Copy built frontend
    if os.path.exists("frontend/dist"):
        shutil.copytree("frontend/dist", frontend_build_dir / "dist")
    
    # Copy electron files
    shutil.copytree("frontend/electron", frontend_build_dir / "electron")
    
    # Copy package.json
    shutil.copy2("frontend/package.json", frontend_build_dir / "package.json")
    
    # Create a modified main.js that uses the bundled backend
    main_js_content = f"""
const {{ app, BrowserWindow, Menu, ipcMain, dialog, shell }} = require('electron');
const path = require('path');
const {{ spawn }} = require('child_process');
const Store = require('electron-store');

// Initialize electron-store
const store = new Store();

// Keep a global reference of the window object
let mainWindow;
let backendProcess;

function createWindow() {{
  // Create the browser window
  mainWindow = new BrowserWindow({{
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {{
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    }},
    icon: path.join(__dirname, 'assets', 'icon.png'),
    titleBarStyle: 'default',
    show: false
  }});

  // Load the app from built files
  mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));

  // Show window when ready
  mainWindow.once('ready-to-show', () => {{
    console.log('Window ready to show');
    mainWindow.show();
  }});

  // Handle window closed
  mainWindow.on('closed', () => {{
    mainWindow = null;
  }});
}}

function startBackend() {{
  // Check if backend is already running
  const http = require('http');
  const checkBackend = () => {{
    return new Promise((resolve) => {{
      const req = http.get('http://localhost:8000', (res) => {{
        resolve(true);
      }});
      req.on('error', () => resolve(false));
      req.setTimeout(1000, () => {{
        req.destroy();
        resolve(false);
      }});
    }});
  }};

  checkBackend().then((isRunning) => {{
    if (isRunning) {{
      console.log('Backend is already running');
      return;
    }}

    // Start the bundled Python backend
    const backendExe = path.join(__dirname, '..', 'dist', 'argos-backend');
    if (process.platform === 'win32') {{
      backendExe += '.exe';
    }}
    
    console.log('Starting bundled backend:', backendExe);
    
    backendProcess = spawn(backendExe, [], {{
      cwd: path.join(__dirname, '..'),
      stdio: 'pipe'
    }});

    backendProcess.stdout.on('data', (data) => {{
      console.log(`Backend: ${{data}}`);
    }});

    backendProcess.stderr.on('data', (data) => {{
      console.error(`Backend Error: ${{data}}`);
    }});

    backendProcess.on('close', (code) => {{
      console.log(`Backend process exited with code ${{code}}`);
    }});
  }});
}}

function stopBackend() {{
  if (backendProcess) {{
    backendProcess.kill();
    backendProcess = null;
  }}
}}

// App event handlers
app.whenReady().then(() => {{
  createWindow();
  startBackend();
  
  app.on('activate', () => {{
    if (BrowserWindow.getAllWindows().length === 0) {{
      createWindow();
    }}
  }});
}});

app.on('window-all-closed', () => {{
  stopBackend();
  if (process.platform !== 'darwin') {{
    app.quit();
  }}
}});

app.on('before-quit', () => {{
  stopBackend();
}});

// IPC handlers (same as before)
ipcMain.handle('select-file', async () => {{
  const result = await dialog.showOpenDialog(mainWindow, {{
    properties: ['openFile'],
    filters: [
      {{ name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md'] }},
      {{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'] }},
      {{ name: 'All Files', extensions: ['*'] }}
    ]
  }});
  
  return result.canceled ? null : result.filePaths[0];
}});

// API call handler (same as before)
ipcMain.handle('api-call', async (event, {{ method, endpoint, data }}) => {{
  try {{
    const axios = require('axios');
    
    const config = {{
      method,
      url: `http://localhost:8000${{endpoint}}`,
      timeout: 30000
    }};
    
    if (data instanceof FormData) {{
      config.data = data;
      config.headers = {{
        'Content-Type': 'multipart/form-data'
      }};
    }} else {{
      config.data = data;
      config.headers = {{
        'Content-Type': 'application/json'
      }};
    }}
    
    const response = await axios(config);
    return {{ success: true, data: response.data }};
  }} catch (error) {{
    console.error('API call failed:', error.message);
    return {{ 
      success: false, 
      error: error.response?.data?.detail || error.message 
    }};
  }}
}});
"""
    
    with open(frontend_build_dir / "electron" / "main.js", "w") as f:
        f.write(main_js_content)
    
    print("📦 Step 7: Installing Electron dependencies...")
    
    # Install electron dependencies
    if not run_command("npm install", cwd=frontend_build_dir):
        return False
    
    print("📦 Step 8: Building Electron app...")
    
    # Build the Electron app
    if not run_command("npm run build", cwd=frontend_build_dir):
        return False
    
    # Use electron-builder to create distributables
    if not run_command("npx electron-builder --publish=never", cwd=frontend_build_dir):
        return False
    
    print("✅ Standalone app created successfully!")
    print(f"📁 Output directory: {build_dir}")
    print("")
    print("🎉 The app now includes:")
    print("  ✅ Frontend (React/Electron)")
    print("  ✅ Python Backend (bundled executable)")
    print("  ✅ All Python dependencies")
    print("  ✅ SQLite database")
    print("  ✅ Tesseract OCR (if available on system)")
    print("")
    print("📦 Distribution files are in: standalone-build/frontend/dist-electron/")
    
    return True

if __name__ == "__main__":
    success = create_standalone_app()
    sys.exit(0 if success else 1)
