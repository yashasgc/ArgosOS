#!/bin/bash

echo "🗑️ ArgosOS Uninstaller"
echo "======================"

# Check if app exists
if [ -d "/Applications/ArgosOS.app" ]; then
    echo "📱 Found ArgosOS.app in Applications"
    
    # Ask for confirmation
    read -p "Are you sure you want to uninstall ArgosOS? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️ Removing ArgosOS.app..."
        rm -rf /Applications/ArgosOS.app
        
        echo "🗑️ Removing user data..."
        rm -rf ~/Library/Application\ Support/ArgosOS
        rm -rf ~/Library/Preferences/com.argosos.app.plist
        rm -rf ~/Library/Caches/com.argosos.app
        
        echo "✅ ArgosOS has been uninstalled."
    else
        echo "❌ Uninstall cancelled."
    fi
else
    echo "❌ ArgosOS.app not found in Applications"
fi
