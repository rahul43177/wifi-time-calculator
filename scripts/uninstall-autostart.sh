#!/bin/bash
set -e

# Office Wi-Fi Tracker - Auto-start Uninstallation Script
# This script removes the launchd service

PLIST_FILE="com.officetracker.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
DEST_PLIST="$LAUNCH_AGENTS_DIR/$PLIST_FILE"

echo "🗑️  Uninstalling Office Wi-Fi Tracker auto-start service..."
echo ""

# 1. Unload service if running (using modern bootout command)
if launchctl list | grep -q "com.officetracker"; then
    echo "⚠️  Stopping service..."
    if launchctl bootout "gui/$(id -u)/com.officetracker" 2>/dev/null; then
        echo "✅ Service stopped"
    else
        echo "⚠️  Service stop failed (may not be loaded)"
    fi
else
    echo "ℹ️  Service is not running"
fi

# 2. Remove plist file
if [ -f "$DEST_PLIST" ]; then
    echo "🗑️  Removing service configuration..."
    rm "$DEST_PLIST"
    echo "✅ Removed $DEST_PLIST"
else
    echo "ℹ️  Service configuration already removed"
fi

# 3. Verify removal (wait longer for launchd to fully unregister)
sleep 2
if launchctl list | grep -q "com.officetracker"; then
    echo "⚠️  Warning: Service still appears in launchctl list"
    echo "   You may need to restart your computer for complete removal"
else
    echo "✅ Service completely removed"
fi

echo ""
echo "✅ Uninstallation complete!"
echo ""
echo "The Office Wi-Fi Tracker will no longer start automatically."
echo "You can still run it manually with: uvicorn app.main:app --host 127.0.0.1 --port 8787"
