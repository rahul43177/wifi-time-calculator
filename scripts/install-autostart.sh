#!/bin/bash
set -e

# Office Wi-Fi Tracker - Auto-start Installation Script
# This script installs the launchd service for automatic startup

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_FILE="com.officetracker.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
DEST_PLIST="$LAUNCH_AGENTS_DIR/$PLIST_FILE"

echo "🚀 Installing Office Wi-Fi Tracker auto-start service..."
echo ""

# 1. Verify plist file exists
if [ ! -f "$PROJECT_DIR/$PLIST_FILE" ]; then
    echo "❌ Error: $PLIST_FILE not found in project directory"
    exit 1
fi

# 2. Validate plist syntax
echo "📝 Validating plist syntax..."
if ! plutil -lint "$PROJECT_DIR/$PLIST_FILE" > /dev/null 2>&1; then
    echo "❌ Error: Invalid plist syntax"
    exit 1
fi
echo "✅ Plist syntax valid"

# 3. Verify Python virtual environment exists
if [ ! -f "$PROJECT_DIR/venv/bin/python" ]; then
    echo "❌ Error: Python virtual environment not found at $PROJECT_DIR/venv/"
    echo "   Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
echo "✅ Virtual environment found"

# 4. Verify dependencies installed
if ! "$PROJECT_DIR/venv/bin/python" -c "import uvicorn" 2>/dev/null; then
    echo "❌ Error: uvicorn not installed in virtual environment"
    echo "   Please run: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
echo "✅ Dependencies installed"

# 5. Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# 6. Unload existing service if running (using modern bootout command)
if launchctl list | grep -q "com.officetracker"; then
    echo "⚠️  Unloading existing service..."
    launchctl bootout "gui/$(id -u)/com.officetracker" 2>/dev/null || true
    sleep 1
fi

# 7. Copy plist to LaunchAgents
echo "📋 Installing service configuration..."
if ! cp "$PROJECT_DIR/$PLIST_FILE" "$DEST_PLIST" 2>/dev/null; then
    echo "❌ Error: Failed to copy plist (permission denied or disk full)"
    exit 1
fi
echo "✅ Copied plist to $DEST_PLIST"

# 8. Load the service (using modern bootstrap command)
echo "🔄 Loading service..."
if launchctl bootstrap "gui/$(id -u)" "$DEST_PLIST" 2>/dev/null; then
    echo "✅ Service loaded successfully"
else
    # Service might already be loaded, try to enable it
    if launchctl enable "gui/$(id -u)/com.officetracker" 2>/dev/null; then
        echo "✅ Service enabled successfully"
    else
        echo "❌ Failed to load service"
        echo "   Check logs: tail -f $PROJECT_DIR/logs/stderr.log"
        exit 1
    fi
fi

# 9. Verify service is running
sleep 2
if launchctl list | grep -q "com.officetracker"; then
    echo "✅ Service is running"
else
    echo "⚠️  Service loaded but not running yet (will start on next login)"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "The Office Wi-Fi Tracker will now start automatically when you log in."
echo ""
echo "Useful commands:"
echo "  - Check status:   launchctl list | grep officetracker"
echo "  - View logs:      tail -f $PROJECT_DIR/logs/stdout.log"
echo "  - View errors:    tail -f $PROJECT_DIR/logs/stderr.log"
echo "  - Uninstall:      $PROJECT_DIR/scripts/uninstall-autostart.sh"
echo ""
echo "Dashboard: http://127.0.0.1:8787/"
