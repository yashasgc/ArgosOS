#!/bin/bash

echo "🔧 ArgosOS Installation Script"
echo "=============================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This installer is for macOS only."
    exit 1
fi

# Check macOS version
macos_version=$(sw_vers -productVersion)
echo "📱 macOS Version: $macos_version"

# Check if DMG exists
if [ ! -f "ArgosOS-1.0.0-arm64.dmg" ]; then
    echo "❌ Error: DMG file not found."
    exit 1
fi

# Mount the DMG
echo "📦 Mounting DMG..."
hdiutil attach ArgosOS-1.0.0-arm64.dmg

# Copy to Applications
echo "📋 Installing to Applications..."
cp -R /Volumes/ArgosOS/ArgosOS.app /Applications/

# Unmount DMG
echo "🗑️ Cleaning up..."
hdiutil detach /Volumes/ArgosOS

# Fix permissions
echo "🔧 Setting permissions..."
chmod -R 755 /Applications/ArgosOS.app

echo "✅ Installation complete!"
echo "🎉 You can now launch ArgosOS from Applications or Launchpad."
echo ""
echo "📚 For help, see README.md or INSTALLATION.md"
