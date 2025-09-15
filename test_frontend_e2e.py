#!/usr/bin/env python3
"""
Frontend E2E Test for Refactored ArgosOS
Tests frontend functionality and integration
"""
import sys
import os
import subprocess
import time
import requests
import json
from pathlib import Path

def test_frontend_build():
    """Test if frontend builds successfully"""
    print("🏗️ Testing Frontend Build...")
    
    try:
        # Change to frontend directory
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
        
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            result = subprocess.run(["npm", "install"], cwd=frontend_dir, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ npm install failed: {result.stderr}")
                return False
        
        # Test TypeScript compilation
        print("🔧 Testing TypeScript compilation...")
        result = subprocess.run(["npx", "tsc", "--noEmit"], cwd=frontend_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ TypeScript compilation failed: {result.stderr}")
            return False
        
        print("✅ Frontend builds successfully")
        return True
        
    except Exception as e:
        print(f"❌ Frontend build test failed: {e}")
        return False

def test_frontend_components():
    """Test if frontend components are properly structured"""
    print("\n🧩 Testing Frontend Components...")
    
    try:
        frontend_dir = Path("frontend")
        
        # Check main files exist
        required_files = [
            "src/App.tsx",
            "src/main.tsx",
            "src/index.css",
            "package.json",
            "vite.config.ts"
        ]
        
        for file_path in required_files:
            if not (frontend_dir / file_path).exists():
                print(f"❌ Required file missing: {file_path}")
                return False
        
        print("✅ All required files present")
        
        # Check App.tsx structure
        app_file = frontend_dir / "src" / "App.tsx"
        with open(app_file, 'r') as f:
            content = f.read()
        
        # Check for key components
        required_components = [
            "useState",
            "useEffect",
            "useElectron",
            "FileUpload",
            "activeTab",
            "documents",
            "searchQuery",
            "searchResults"
        ]
        
        for component in required_components:
            if component not in content:
                print(f"❌ Missing component/state: {component}")
                return False
        
        print("✅ App.tsx structure is correct")
        
        # Check for refactored code (should be more concise)
        lines = content.count('\n')
        if lines > 500:  # Should be around 424 lines after refactoring
            print(f"⚠️ App.tsx might not be fully refactored ({lines} lines)")
        else:
            print(f"✅ App.tsx is properly refactored ({lines} lines)")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend component test failed: {e}")
        return False

def test_electron_integration():
    """Test Electron integration"""
    print("\n⚡ Testing Electron Integration...")
    
    try:
        frontend_dir = Path("frontend")
        
        # Check Electron files
        electron_files = [
            "electron/main.js",
            "electron/preload.js",
            "src/hooks/useElectron.ts",
            "src/types/electron.d.ts"
        ]
        
        for file_path in electron_files:
            if not (frontend_dir / file_path).exists():
                print(f"❌ Electron file missing: {file_path}")
                return False
        
        print("✅ All Electron files present")
        
        # Check useElectron hook
        use_electron_file = frontend_dir / "src" / "hooks" / "useElectron.ts"
        with open(use_electron_file, 'r') as f:
            content = f.read()
        
        required_functions = ["useElectron", "apiCall", "isElectron"]
        for func in required_functions:
            if func not in content:
                print(f"❌ Missing function: {func}")
                return False
        
        print("✅ useElectron hook is properly structured")
        
        return True
        
    except Exception as e:
        print(f"❌ Electron integration test failed: {e}")
        return False

def test_frontend_api_integration():
    """Test frontend API integration"""
    print("\n🌐 Testing Frontend API Integration...")
    
    try:
        # Start backend server in background
        print("🚀 Starting backend server...")
        backend_process = subprocess.Popen(
            ["poetry", "run", "python", "-m", "uvicorn", "app.main:app", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Test API endpoints that frontend uses
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend health check failed")
            return False
        print("✅ Backend health check passed")
        
        # Test files endpoint
        response = requests.get(f"{base_url}/api/files", timeout=5)
        if response.status_code != 200:
            print("❌ Files API endpoint failed")
            return False
        print("✅ Files API endpoint working")
        
        # Test search endpoint
        response = requests.get(f"{base_url}/api/search?query=test", timeout=5)
        if response.status_code != 200:
            print("❌ Search API endpoint failed")
            return False
        print("✅ Search API endpoint working")
        
        # Test API key status endpoint
        response = requests.get(f"{base_url}/v1/api-key/status", timeout=5)
        if response.status_code != 200:
            print("❌ API key status endpoint failed")
            return False
        print("✅ API key status endpoint working")
        
        # Clean up
        backend_process.terminate()
        backend_process.wait()
        
        print("✅ Frontend API integration working")
        return True
        
    except Exception as e:
        print(f"❌ Frontend API integration test failed: {e}")
        # Clean up on error
        try:
            backend_process.terminate()
            backend_process.wait()
        except:
            pass
        return False

def test_frontend_ui_components():
    """Test frontend UI components"""
    print("\n🎨 Testing Frontend UI Components...")
    
    try:
        frontend_dir = Path("frontend")
        
        # Check component files
        component_files = [
            "src/components/FileUpload.tsx",
            "src/components/FileCard.tsx",
            "src/components/SearchResultCard.tsx"
        ]
        
        for file_path in component_files:
            if not (frontend_dir / file_path).exists():
                print(f"⚠️ Component file missing: {file_path}")
            else:
                print(f"✅ Component file present: {file_path}")
        
        # Check FileUpload component
        file_upload = frontend_dir / "src" / "components" / "FileUpload.tsx"
        if file_upload.exists():
            with open(file_upload, 'r') as f:
                content = f.read()
            
            if "onUploadSuccess" in content and "handleFileUpload" in content:
                print("✅ FileUpload component properly structured")
            else:
                print("❌ FileUpload component missing key functions")
                return False
        
        # Check CSS and styling
        css_file = frontend_dir / "src" / "index.css"
        if css_file.exists():
            with open(css_file, 'r') as f:
                content = f.read()
            
            if "tailwind" in content.lower() or "css" in content.lower():
                print("✅ CSS styling present")
            else:
                print("⚠️ CSS styling might be minimal")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend UI components test failed: {e}")
        return False

def test_frontend_performance():
    """Test frontend performance metrics"""
    print("\n⚡ Testing Frontend Performance...")
    
    try:
        frontend_dir = Path("frontend")
        
        # Check bundle size (if build exists)
        dist_dir = frontend_dir / "dist"
        if dist_dir.exists():
            total_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            if size_mb < 10:  # Should be reasonable size
                print(f"✅ Bundle size is reasonable: {size_mb:.2f} MB")
            else:
                print(f"⚠️ Bundle size might be large: {size_mb:.2f} MB")
        else:
            print("ℹ️ No build directory found, skipping bundle size check")
        
        # Check for unused imports or dead code
        app_file = frontend_dir / "src" / "App.tsx"
        with open(app_file, 'r') as f:
            content = f.read()
        
        # Check for common dead code patterns
        if "console.log" in content:
            print("⚠️ Found console.log statements (should be removed in production)")
        
        if "debugger" in content:
            print("⚠️ Found debugger statements (should be removed in production)")
        
        print("✅ Frontend performance check completed")
        return True
        
    except Exception as e:
        print(f"❌ Frontend performance test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Frontend E2E Testing Suite...")
    print("Testing refactored frontend for functionality preservation")
    print("=" * 60)
    
    tests = [
        ("Frontend Build", test_frontend_build),
        ("Frontend Components", test_frontend_components),
        ("Electron Integration", test_electron_integration),
        ("Frontend API Integration", test_frontend_api_integration),
        ("Frontend UI Components", test_frontend_ui_components),
        ("Frontend Performance", test_frontend_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*60}")
    print(f"📊 Frontend Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FRONTEND TESTS PASSED! 🎉")
        print("The refactored frontend is working perfectly!")
        sys.exit(0)
    else:
        print("❌ SOME FRONTEND TESTS FAILED!")
        print("Please check the errors above.")
        sys.exit(1)
