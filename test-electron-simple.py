#!/usr/bin/env python3
"""
Simple test script to verify Electron integration files exist
"""
import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and print status"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (missing)")
        return False

def check_command_exists(command, description):
    """Check if a command exists and print status"""
    try:
        result = subprocess.run([command, '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description}: Command failed")
            return False
    except FileNotFoundError:
        print(f"❌ {description}: Not found")
        return False

def main():
    """Run simple tests"""
    print("🚀 ArgosOS Electron Integration - Simple Test")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("start.py").exists():
        print("❌ Please run this script from the project root directory")
        return False
    
    print("\n📁 Checking Electron files...")
    electron_files = [
        ("frontend/electron/main.js", "Electron main process"),
        ("frontend/electron/preload.js", "Electron preload script"),
        ("frontend/src/hooks/useElectron.ts", "Electron React hook"),
        ("frontend/src/components/ElectronFileUpload.tsx", "Electron file upload component"),
        ("frontend/src/types/electron.d.ts", "Electron TypeScript definitions"),
        ("frontend/README-ELECTRON.md", "Electron documentation"),
        ("start-electron.sh", "Linux/macOS startup script"),
        ("start-electron.bat", "Windows startup script"),
    ]
    
    file_results = []
    for file_path, description in electron_files:
        result = check_file_exists(file_path, description)
        file_results.append(result)
    
    print("\n🔧 Checking prerequisites...")
    prereq_results = []
    
    # Check Node.js
    node_result = check_command_exists("node", "Node.js")
    prereq_results.append(node_result)
    
    # Check npm
    npm_result = check_command_exists("npm", "npm")
    prereq_results.append(npm_result)
    
    # Check Python
    python_result = check_command_exists("python3", "Python 3")
    prereq_results.append(python_result)
    
    print("\n📦 Checking frontend dependencies...")
    frontend_deps = [
        ("frontend/node_modules", "Node modules directory"),
        ("frontend/node_modules/electron", "Electron package"),
        ("frontend/node_modules/concurrently", "Concurrently package"),
        ("frontend/node_modules/wait-on", "Wait-on package"),
    ]
    
    dep_results = []
    for dep_path, description in frontend_deps:
        result = check_file_exists(dep_path, description)
        dep_results.append(result)
    
    print("\n📋 Checking package.json configuration...")
    package_json_path = "frontend/package.json"
    if Path(package_json_path).exists():
        try:
            import json
            with open(package_json_path, "r") as f:
                package_data = json.load(f)
            
            # Check for Electron scripts
            scripts = package_data.get("scripts", {})
            required_scripts = ["electron", "electron:dev", "electron:build", "electron:dist"]
            
            script_results = []
            for script in required_scripts:
                if script in scripts:
                    print(f"✅ Script '{script}' found")
                    script_results.append(True)
                else:
                    print(f"❌ Script '{script}' missing")
                    script_results.append(False)
            
            # Check for Electron dependency
            dev_deps = package_data.get("devDependencies", {})
            if "electron" in dev_deps:
                print("✅ Electron dependency found")
                script_results.append(True)
            else:
                print("❌ Electron dependency missing")
                script_results.append(False)
            
            # Check for build configuration
            if "build" in package_data:
                print("✅ Electron build configuration found")
                script_results.append(True)
            else:
                print("❌ Electron build configuration missing")
                script_results.append(False)
                
        except Exception as e:
            print(f"❌ Error reading package.json: {e}")
            script_results = [False] * (len(required_scripts) + 2)
    else:
        print("❌ package.json not found")
        script_results = [False] * 7
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    total_tests = len(file_results) + len(prereq_results) + len(dep_results) + len(script_results)
    passed_tests = sum(file_results) + sum(prereq_results) + sum(dep_results) + sum(script_results)
    
    print(f"Files: {sum(file_results)}/{len(file_results)}")
    print(f"Prerequisites: {sum(prereq_results)}/{len(prereq_results)}")
    print(f"Dependencies: {sum(dep_results)}/{len(dep_results)}")
    print(f"Configuration: {sum(script_results)}/{len(script_results)}")
    print("=" * 60)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Electron integration is ready.")
        print("\n📖 Next steps:")
        print("1. Install frontend dependencies: cd frontend && npm install")
        print("2. Start the Electron app:")
        print("   - Linux/macOS: ./start-electron.sh")
        print("   - Windows: start-electron.bat")
        print("   - Manual: cd frontend && npm run electron:dev")
        print("\n📚 Documentation: frontend/README-ELECTRON.md")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed.")
        print("Please install missing dependencies and fix configuration issues.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
