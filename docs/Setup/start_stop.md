## Install and start:

### Copy to LaunchAgents
cp /Users/rahulmishra/Desktop/Personal/wifi-tracking/com.officetracker.plist ~/Library/LaunchAgents/

### Load it (starts immediately + runs on every login)
launchctl load ~/Library/LaunchAgents/com.officetracker.plist

### Check if it's running:
launchctl list | grep officetracker

### Stop/unload (deprecated — do NOT use):
# launchctl unload ~/Library/LaunchAgents/com.officetracker.plist
# launchctl load ~/Library/LaunchAgents/com.officetracker.plist
# These don't fully kill the process — old config stays loaded.

### Stop (correct way):
launchctl bootout gui/$(id -u)/com.officetracker

### Start (correct way):
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.officetracker.plist

### Restart (e.g. after changing .env):
launchctl bootout gui/$(id -u)/com.officetracker 2>/dev/null; kill -9 $(lsof -ti :8787) 2>/dev/null; sleep 2; launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.officetracker.plist

# The kill -9 force-clears port 8787 in case the old process didn't die cleanly.
# Wait ~8 seconds after running before checking the browser.

### View logs:
tail -f /Users/rahulmishra/Desktop/Personal/wifi-tracking/logs/stdout.log
tail -f /Users/rahulmishra/Desktop/Personal/wifi-tracking/logs/stderr.log

The plist has RunAtLoad: true and KeepAlive: true — so it starts on login and auto-restarts if it crashes. Make sure the logs/ directory exists before loading:

mkdir -p /Users/rahulmishra/Desktop/Personal/wifi-tracking/logs