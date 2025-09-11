#!/usr/bin/env python3
"""
Test script to verify Electron integration with the ArgosOS backend
"""
import os
import sys
import time
import subprocess
import requests
from pathlib import Path

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Python not found")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"✅ Node.js: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Node.js not found")
        return False
    
    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        print(f"✅ npm: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ npm not found")
        return False
    
    return True

def check_dependencies():
    """Check if dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    # Check frontend dependencies
    frontend_node_modules = Path("frontend/node_modules")
    if frontend_node_modules.exists():
        print("✅ Frontend dependencies installed")
    else:
        print("❌ Frontend dependencies not installed")
        print("   Run: cd frontend && npm install")
        return False
    
    # Check if Electron is installed
    electron_path = frontend_node_modules / "electron"
    if electron_path.exists():
        print("✅ Electron installed")
    else:
        print("❌ Electron not installed")
        return False
    
    # Check backend dependencies
    try:
        import fastapi
        import sqlalchemy
        import openai
        print("✅ Backend dependencies installed")
    except ImportError as e:
        print(f"❌ Backend dependencies missing: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def test_backend():
    """Test if backend starts and responds"""
    print("\n🐍 Testing backend...")
    
    try:
        # Start backend in background
        backend_process = subprocess.Popen(
            ['python', 'start.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for backend to start
        print("   Waiting for backend to start...")
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Backend is running and healthy")
                return backend_process
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                backend_process.terminate()
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Backend not responding: {e}")
            backend_process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def test_frontend_build():
    """Test if frontend builds successfully"""
    print("\n🏗️  Testing frontend build...")
    
    try:
        os.chdir("frontend")
        result = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Frontend builds successfully")
            os.chdir("..")
            return True
        else:
            print(f"❌ Frontend build failed:")
            print(result.stderr)
            os.chdir("..")
            return False
    except Exception as e:
        print(f"❌ Frontend build error: {e}")
        os.chdir("..")
        return False

def test_electron_files():
    """Test if Electron files exist and are valid"""
    print("\n🖥️  Testing Electron files...")
    
    electron_files = [
        "frontend/electron/main.js",
        "frontend/electron/preload.js",
        "frontend/src/hooks/useElectron.ts",
        "frontend/src/components/ElectronFileUpload.tsx",
        "frontend/src/types/electron.d.ts"
    ]
    
    all_exist = True
    for file_path in electron_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_package_json():
    """Test if package.json has Electron configuration"""
    print("\n📋 Testing package.json configuration...")
    
    try:
        import json
        with open("frontend/package.json", "r") as f:
            package_data = json.load(f)
        
        # Check for Electron scripts
        scripts = package_data.get("scripts", {})
        required_scripts = ["electron", "electron:dev", "electron:build", "electron:dist"]
        
        for script in required_scripts:
            if script in scripts:
                print(f"✅ Script '{script}' found")
            else:
                print(f"❌ Script '{script}' missing")
                return False
        
        # Check for Electron dependencies
        dev_deps = package_data.get("devDependencies", {})
        if "electron" in dev_deps:
            print("✅ Electron dependency found")
        else:
            print("❌ Electron dependency missing")
            return False
        
        # Check for build configuration
        if "build" in package_data:
            print("✅ Electron build configuration found")
        else:
            print("❌ Electron build configuration missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 ArgosOS Electron Integration Test")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("start.py").exists():
        print("❌ Please run this script from the project root directory")
        return False
    
    tests = [
        ("Prerequisites", check_prerequisites),
        ("Dependencies", check_dependencies),
        ("Electron Files", test_electron_files),
        ("Package.json", test_package_json),
        ("Frontend Build", test_frontend_build),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results.append((test_name, False))
    
    # Test backend (this will start it)
    backend_process = test_backend()
    if backend_process:
        results.append(("Backend", True))
    else:
        results.append(("Backend", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Electron integration is ready.")
        print("\nTo start the Electron app:")
        print("  ./start-electron.sh    # Linux/macOS")
        print("  start-electron.bat     # Windows")
        print("  cd frontend && npm run electron:dev")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix the issues above.")
    
    # Cleanup
    if backend_process:
        print("\n🛑 Stopping backend...")
        backend_process.terminate()
        backend_process.wait()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
