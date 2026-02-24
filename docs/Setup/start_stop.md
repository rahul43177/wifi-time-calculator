## Install and start:

### Copy to LaunchAgents
cp /Users/rahulmishra/Desktop/Personal/wifi-tracking/com.officetracker.plist ~/Library/LaunchAgents/

### Load it (starts immediately + runs on every login)
launchctl load ~/Library/LaunchAgents/com.officetracker.plist

### Check if it's running:
launchctl list | grep officetracker

### Stop/unload:
launchctl unload ~/Library/LaunchAgents/com.officetracker.plist

### View logs:
tail -f /Users/rahulmishra/Desktop/Personal/wifi-tracking/logs/stdout.log
tail -f /Users/rahulmishra/Desktop/Personal/wifi-tracking/logs/stderr.log

The plist has RunAtLoad: true and KeepAlive: true — so it starts on login and auto-restarts if it crashes. Make sure the logs/ directory exists before loading:

mkdir -p /Users/rahulmishra/Desktop/Personal/wifi-tracking/logs