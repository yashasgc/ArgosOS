#!/bin/bash

# ArgosOS Electron Development Startup Script

# Unset ELECTRON_RUN_AS_NODE to ensure Electron runs properly
unset ELECTRON_RUN_AS_NODE

echo "🚀 Starting ArgosOS Electron App..."

# Check if we're in the right directory
if [ ! -f "start.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed or not in PATH"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed or not in PATH"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Install backend dependencies if needed
if [ ! -f "poetry.lock" ]; then
    echo "📦 Installing backend dependencies with Poetry..."
    poetry install
else
    echo "📦 Backend dependencies already installed"
fi

# Start the backend in the background
echo "🐍 Starting Python backend..."
poetry run python start.py &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
echo "🔍 Checking backend health..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend is running on http://localhost:8000"

# Start the Electron app
echo "🖥️  Starting Electron app..."
echo "📁 Current directory: $(pwd)"
echo "📁 Changing to frontend directory..."
cd frontend
echo "📁 Now in directory: $(pwd)"
echo "🚀 Running npm run electron:dev..."
npm run electron:dev

# Cleanup function
cleanup() {
    echo "🛑 Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop the app
wait
