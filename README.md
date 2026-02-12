# Office Wi-Fi 4-Hour Tracker

A fully automatic local application that tracks your office presence by detecting office Wi-Fi connection and running a 4-hour work timer. No database required - uses local file logging only.

## 🎯 Purpose

- Detects when laptop connects to office Wi-Fi
- Automatically starts 4-hour work timer
- Shows live remaining time in web dashboard
- Sends alert when 4 hours complete
- Stores daily proof logs locally for HR reference
- Runs automatically in background (no manual intervention)

## 📋 Requirements

- Python 3.11 or higher
- macOS (launchd for auto-start)
- No database required (file-based storage only)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to project directory
cd /Users/rahulmishra/Desktop/Personal/wifi-tracking

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your office Wi-Fi name:

```bash
cp .env.example .env
```

Edit `.env` and set your office Wi-Fi SSID:

```
OFFICE_WIFI_NAME=YourActualOfficeWiFiName
```

### 3. Run Development Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
uvicorn app.main:app --reload
```

Visit http://localhost:8000 in your browser.

## 📁 Project Structure

```
office-wifi-tracker/
├── app/                    # Application code
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Configuration settings
│   ├── wifi_detector.py   # Wi-Fi SSID detection
│   ├── session_manager.py # Session state machine
│   ├── timer_engine.py    # Timer calculations
│   ├── notifier.py        # Notification system
│   └── file_store.py      # File-based storage
├── data/                  # Session log files
│   └── archive/           # Archived logs
├── templates/             # HTML templates
├── static/                # CSS, JavaScript
├── logs/                  # Application logs
├── docs/                  # Documentation
│   ├── requirements.md    # Requirements specification
│   └── action-plan.md     # Development action plan
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (create this)
└── README.md             # This file
```

## 🛠️ Development Status

Currently in **Pre-Development Phase** (Phase 0) - Setup Complete! ✅

### Development Phases

- [x] **Phase 0:** Pre-Development Setup
- [ ] **Phase 1:** Wi-Fi Detection System
- [ ] **Phase 2:** File-Based Session Storage
- [ ] **Phase 3:** Timer Engine & Notifications
- [ ] **Phase 4:** Local Web UI Dashboard
- [ ] **Phase 5:** Auto-Start on Boot

See [docs/action-plan.md](docs/action-plan.md) for detailed development phases.

## 📊 How It Works

1. **Wi-Fi Detection:** Checks every 30 seconds if connected to office Wi-Fi
2. **Session Tracking:** Starts timer when office Wi-Fi detected
3. **Time Calculation:** Tracks elapsed and remaining time (target: 4 hours)
4. **Notification:** Alerts when 4 hours completed
5. **Logging:** Saves sessions to daily log files (`data/sessions_YYYY-MM-DD.log`)

## 📝 Session Log Format

Sessions are stored as JSON Lines (one JSON object per line):

```json
{"date": "2026-02-12", "ssid": "OfficeWifi", "start_time": "09:42:10", "end_time": "13:48:55", "duration_minutes": 246, "completed_4h": true}
```

## 🔧 Configuration Options

Edit `.env` to customize:

```
OFFICE_WIFI_NAME=YourOfficeWiFiName    # Your office Wi-Fi SSID
WORK_DURATION_HOURS=4                  # Target work hours
WIFI_CHECK_INTERVAL_SECONDS=30         # Wi-Fi check frequency
TIMER_CHECK_INTERVAL_SECONDS=60        # Timer check frequency
TEST_MODE=false                        # Enable for 2-minute testing
TEST_DURATION_MINUTES=2                # Duration when in test mode
```

## 🧪 Testing

Enable test mode for quick testing (2-minute duration instead of 4 hours):

```
TEST_MODE=true
TEST_DURATION_MINUTES=2
```

## 🤝 Contributing

This is a personal productivity tool. Development follows the phased approach outlined in [docs/action-plan.md](docs/action-plan.md).

## 📄 License

Personal use project.

## 🙋 Support

For issues or questions, refer to:
- [Requirements Specification](docs/requirements.md)
- [Action Plan](docs/action-plan.md)

---

**Status:** Pre-Development Phase Complete ✅ | Ready for Phase 1: Wi-Fi Detection
