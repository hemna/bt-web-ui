# Quickstart: Bluetooth Web UI

**Feature**: 001-bluetooth-web-ui
**Date**: 2026-03-10

## Prerequisites

- Raspberry Pi (or any Linux system) running Debian/Raspberry Pi OS
- Python 3.11+
- BlueZ 5.x installed and running (`bluetoothd` service active)
- A Bluetooth adapter (built-in on Pi 3/4/5, or USB dongle)
- A web browser on any device on the same network

## Installation

```bash
# Clone the repository
git clone <repo-url> bt-web-ui
cd bt-web-ui

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Verify Bluetooth is Available

```bash
# Check BlueZ is running
systemctl status bluetooth

# Check adapter is detected
bluetoothctl show
# Should display adapter address and properties

# If adapter is powered off:
bluetoothctl power on
```

## Run the Application

```bash
# From the repository root, with venv activated
uvicorn backend.src.bt_web_ui.main:app --host 0.0.0.0 --port 8080

# The app is now accessible at http://<pi-ip-address>:8080
```

**Note**: The app needs access to the system D-Bus to communicate
with BlueZ. If you get permission errors, either:
- Add your user to the `bluetooth` group: `sudo usermod -aG bluetooth $USER`
- Or run with appropriate D-Bus permissions (see Deployment section)

## First Use

1. Open `http://<pi-ip-address>:8080` in a browser
2. The dashboard shows the Bluetooth adapter status
3. Click **Scan** to discover nearby devices
4. Discovered devices appear in the device list
5. Click a device to see details, then **Pair** and **Connect**
6. Paired devices are saved and appear on future visits
7. Switch themes from **Settings** (light/dark/auto)

## Run Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=backend/src/bt_web_ui --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests (includes D-Bus mocking)
pytest tests/integration/

# Run only API tests
pytest tests/api/
```

## Project Structure (Key Files)

```
backend/
├── src/bt_web_ui/
│   ├── main.py              # FastAPI app, startup/shutdown
│   ├── config.py            # Settings from env/file
│   ├── models/              # Pydantic models
│   ├── services/
│   │   ├── bluetooth.py     # BlueZ D-Bus abstraction
│   │   ├── device_store.py  # SQLite persistence
│   │   └── event_bus.py     # Internal pub/sub for WS
│   ├── api/                 # REST + WebSocket endpoints
│   └── templates/           # Jinja2 HTML templates
├── tests/                   # pytest test suite
├── pyproject.toml
└── requirements.txt
```

## Configuration

The app reads configuration from environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BT_WEB_UI_HOST` | `0.0.0.0` | Bind address |
| `BT_WEB_UI_PORT` | `8080` | Bind port |
| `BT_WEB_UI_DB_PATH` | `data/bt_web_ui.db` | SQLite database path |
| `BT_WEB_UI_ADAPTER` | (auto-detect) | Bluetooth adapter name (e.g., `hci0`) |
| `BT_WEB_UI_LOG_LEVEL` | `INFO` | Logging level |

## Deployment (systemd)

For persistent operation on the Pi:

```bash
# Create systemd service file
sudo tee /etc/systemd/system/bt-web-ui.service << 'EOF'
[Unit]
Description=Bluetooth Web UI
After=bluetooth.service network.target
Requires=bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bt-web-ui
Environment=PATH=/home/pi/bt-web-ui/.venv/bin:/usr/bin
ExecStart=/home/pi/bt-web-ui/.venv/bin/uvicorn \
    backend.src.bt_web_ui.main:app \
    --host 0.0.0.0 --port 8080
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bt-web-ui
sudo systemctl start bt-web-ui
```
