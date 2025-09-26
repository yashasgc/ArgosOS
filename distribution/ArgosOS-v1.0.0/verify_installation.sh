#!/bin/bash

echo "🔍 Verifying ArgosOS Installation"
echo "================================="

# Check if app exists
if [ -d "/Applications/ArgosOS.app" ]; then
    echo "✅ ArgosOS.app found in Applications"
else
    echo "❌ ArgosOS.app not found in Applications"
    exit 1
fi

# Check app permissions
if [ -x "/Applications/ArgosOS.app/Contents/MacOS/ArgosOS" ]; then
    echo "✅ App executable has proper permissions"
else
    echo "❌ App executable permission issue"
    exit 1
fi

# Check app bundle
if [ -f "/Applications/ArgosOS.app/Contents/Info.plist" ]; then
    echo "✅ App bundle structure is correct"
else
    echo "❌ App bundle structure issue"
    exit 1
fi

# Get app version
version=$(defaults read /Applications/ArgosOS.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo "Unknown")
echo "📱 App Version: $version"

echo "✅ Installation verification complete!"
echo "🚀 You can now launch ArgosOS from Applications or Launchpad."
