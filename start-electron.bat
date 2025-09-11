@echo off
REM ArgosOS Electron Development Startup Script

echo 🚀 Starting ArgosOS Electron App...

REM Check if we're in the right directory
if not exist "start.py" (
    echo ❌ Please run this script from the project root directory
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if npm is available
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed or not in PATH
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Install frontend dependencies if needed
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
)

REM Install backend dependencies if needed
if not exist "venv" if not exist ".venv" (
    echo 📦 Installing backend dependencies...
    pip install -r requirements.txt
)

REM Start the backend in the background
echo 🐍 Starting Python backend...
start /b python start.py

REM Wait for backend to start
echo ⏳ Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Check if backend is running
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend failed to start
    pause
    exit /b 1
)

echo ✅ Backend is running on http://localhost:8000

REM Start the Electron app
echo 🖥️  Starting Electron app...
cd frontend
npm run electron:dev

REM Cleanup
echo 🛑 Shutting down...
pause
