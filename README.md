# bt-web-ui

A web-based interface for managing Bluetooth device pairing and connections on a Raspberry Pi. Access your Pi's Bluetooth from any browser on the local network -- no monitor, keyboard, or SSH required.

Built for ham radio operators and hobbyists who need to pair Bluetooth serial devices (TNC radios, GPS units, etc.) to a headless Pi.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser (any device on LAN)                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│  │  HTMX      │  │  Alpine.js │  │  WebSocket │                 │
│  │  (partials) │  │  (theme,   │  │  (live     │                 │
│  │             │  │   toasts)  │  │   updates) │                 │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘                 │
└─────────┼───────────────┼───────────────┼────────────────────────┘
          │ HTTP          │ HTTP          │ ws://
          ▼               ▼               ▼
┌──────────────────────────────────────────────────────────────────┐
│  Raspberry Pi                                                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  FastAPI + Uvicorn (single process)                         │ │
│  │                                                             │ │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐ │ │
│  │  │ REST API │  │ HTML Pages   │  │ WebSocket Endpoint    │ │ │
│  │  │ /api/*   │  │ Jinja2       │  │ /ws                   │ │ │
│  │  └────┬─────┘  └──────┬───────┘  └───────────┬───────────┘ │ │
│  │       │               │                      │             │ │
│  │       ▼               ▼                      ▼             │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │                  Service Layer                       │  │ │
│  │  │  ┌─────────────┐  ┌────────────┐  ┌──────────────┐  │  │ │
│  │  │  │ BlueZManager│  │DeviceStore │  │  EventBus    │  │  │ │
│  │  │  │ (dbus-fast) │  │(aiosqlite) │  │  (pub/sub)   │  │  │ │
│  │  │  └──────┬──────┘  └─────┬──────┘  └──────────────┘  │  │ │
│  │  └─────────┼───────────────┼────────────────────────────┘  │ │
│  └────────────┼───────────────┼───────────────────────────────┘ │
│               │               │                                  │
│               ▼               ▼                                  │
│  ┌────────────────┐  ┌──────────────┐                            │
│  │   BlueZ 5.x    │  │   SQLite     │                            │
│  │   (bluetoothd)  │  │   (WAL mode) │                            │
│  │   via D-Bus     │  │              │                            │
│  └────────┬───────┘  └──────────────┘                            │
│           │                                                      │
│           ▼                                                      │
│  ┌────────────────┐                                              │
│  │  BT Adapter    │                                              │
│  │  (hci0)        │                                              │
│  └────────────────┘                                              │
└──────────────────────────────────────────────────────────────────┘
```

## Features

- **Adapter control** -- power on/off, view address and status
- **Device discovery** -- scan for nearby Bluetooth devices with configurable duration
- **Pairing & connecting** -- pair, connect, disconnect, trust/untrust from the browser
- **Device management** -- assign aliases, add notes, mark favorites
- **Persistent history** -- paired devices are remembered across restarts (SQLite)
- **Real-time updates** -- WebSocket pushes device state changes to the browser instantly
- **Theming** -- light, dark, and auto (follows OS preference) via CSS custom properties
- **Mobile-friendly** -- responsive layout works on phones, tablets, and desktops
- **No build toolchain** -- HTMX and Alpine.js are vendored; no Node.js needed
- **Graceful degradation** -- starts without Bluetooth if D-Bus/BlueZ is unavailable

## Screenshots

Access the UI at `http://<pi-ip>:8080`:

| Page | Description |
|------|-------------|
| `/` | Dashboard with adapter status, scan controls, and device overview |
| `/devices` | Device list with filter (all/paired/connected/favorites) and sort options |
| `/devices/{mac}` | Device detail with actions (pair, connect, trust) and editable alias/notes |
| `/settings` | Theme selector, scan duration slider, auto-connect toggle |

## Quick Start

### Prerequisites

- Raspberry Pi (or any Linux with BlueZ 5.x)
- Python 3.11+
- Bluetooth adapter (built-in on Pi 3/4/5, or USB dongle)
- `bluetoothd` service running

### Install & Run

```bash
# Clone
git clone https://github.com/hemna/bt-web-ui.git
cd bt-web-ui

# Create venv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Ensure your user can access Bluetooth
sudo usermod -aG bluetooth $USER
# (log out and back in for group change to take effect)

# Run
PYTHONPATH=backend/src uvicorn bt_web_ui.main:app --host 0.0.0.0 --port 8080
```

Open `http://<pi-ip>:8080` in any browser on your network.

### Pi Zero Notes

The Pi Zero (ARMv6l) is too slow to compile C/Rust extensions. Pre-built wheels for `dbus-fast` are included in `dist/wheels/`:

```bash
# On Pi Zero, install the pre-built wheel instead of compiling
pip install dist/wheels/dbus_fast-4.0.0-cp313-cp313-linux_armv6l.whl

# Install remaining deps from piwheels (fast, pre-compiled)
pip install --extra-index-url https://www.piwheels.org/simple \
    fastapi uvicorn aiosqlite jinja2 pydantic-settings python-multipart websockets
```

## Configuration

All settings are read from environment variables (prefix: `BT_WEB_UI_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `BT_WEB_UI_HOST` | `0.0.0.0` | Server bind address |
| `BT_WEB_UI_PORT` | `8080` | Server bind port |
| `BT_WEB_UI_DB_PATH` | `data/bt_web_ui.db` | SQLite database path |
| `BT_WEB_UI_ADAPTER` | auto-detect | Bluetooth adapter name (e.g., `hci0`) |
| `BT_WEB_UI_LOG_LEVEL` | `INFO` | Python logging level |

## API Reference

### Adapter

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/adapter` | Get adapter state (address, name, powered, discovering) |
| `POST` | `/api/adapter/power` | Toggle adapter power |

### Scanning

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scan/start` | Start discovery (auto-stops after configured duration) |
| `POST` | `/api/scan/stop` | Stop an active scan |

### Devices

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/devices` | List all devices (query: `filter`, `sort`) |
| `GET` | `/api/devices/{mac}` | Get single device |
| `PATCH` | `/api/devices/{mac}` | Update alias, notes, or favorite status |
| `DELETE` | `/api/devices/{mac}` | Remove from app history |
| `POST` | `/api/devices/{mac}/pair` | Pair with device |
| `POST` | `/api/devices/{mac}/connect` | Connect to paired device |
| `POST` | `/api/devices/{mac}/disconnect` | Disconnect device |
| `POST` | `/api/devices/{mac}/trust` | Trust device (allow auto-connect) |
| `POST` | `/api/devices/{mac}/untrust` | Remove trust |
| `POST` | `/api/devices/{mac}/remove` | Remove/unpair from BlueZ |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/settings` | Get current app settings |
| `PATCH` | `/api/settings` | Update settings (theme, scan_duration, auto_connect) |

### WebSocket

Connect to `ws://<host>:8080/ws` for real-time events:

| Event | Description |
|-------|-------------|
| `device_discovered` | New device found during scan |
| `device_updated` | Device property changed (RSSI, connection, etc.) |
| `device_removed` | Device removed from BlueZ |
| `scan_started` | Discovery began |
| `scan_stopped` | Discovery ended |
| `adapter_changed` | Adapter state changed |

All error responses follow the format:
```json
{"error": "error_code", "message": "Human-readable explanation."}
```

## Project Structure

```
bt-web-ui/
├── backend/
│   ├── pyproject.toml              # Metadata, deps, mypy/ruff config
│   ├── requirements.txt            # Runtime dependencies
│   ├── requirements-dev.txt        # Dev dependencies (pytest, mypy, ruff)
│   ├── src/bt_web_ui/
│   │   ├── main.py                 # FastAPI app, lifespan, error handlers
│   │   ├── config.py               # pydantic-settings configuration
│   │   ├── deps.py                 # Dependency injection (singletons)
│   │   ├── models/
│   │   │   ├── device.py           # Device, AdapterState, DeviceRuntimeState
│   │   │   └── settings.py         # AppSettings, ThemeChoice
│   │   ├── services/
│   │   │   ├── bluetooth.py        # BlueZManager (D-Bus via dbus-fast)
│   │   │   ├── device_store.py     # SQLite persistence (aiosqlite)
│   │   │   └── event_bus.py        # Async pub/sub for WebSocket events
│   │   ├── api/
│   │   │   ├── __init__.py         # Exception hierarchy (12 error types)
│   │   │   ├── adapter.py          # Adapter + scan endpoints
│   │   │   ├── devices.py          # Device CRUD + actions
│   │   │   ├── settings.py         # Settings endpoints
│   │   │   └── websocket.py        # WebSocket endpoint
│   │   └── templates/              # Jinja2 templates (base, pages, partials)
│   └── tests/
│       ├── unit/                   # Model, store, and service tests
│       ├── integration/            # WebSocket and device lifecycle tests
│       └── api/                    # HTTP endpoint tests
├── data/                           # SQLite database (runtime, gitignored)
├── dist/wheels/                    # Pre-built ARM wheels for Pi Zero
└── specs/                          # Design docs, API contracts, task tracking
```

## Development

### Run Tests

```bash
source .venv/bin/activate
pip install -r backend/requirements-dev.txt

# All tests (96 passing)
PYTHONPATH=backend/src pytest backend/tests/ -v

# With coverage
PYTHONPATH=backend/src pytest backend/tests/ --cov=bt_web_ui --cov-report=term-missing

# Subsets
PYTHONPATH=backend/src pytest backend/tests/unit/
PYTHONPATH=backend/src pytest backend/tests/api/
PYTHONPATH=backend/src pytest backend/tests/integration/
```

### Lint & Type Check

```bash
# Lint (ruff)
ruff check backend/src/

# Format
ruff format backend/src/

# Type check (strict mode)
PYTHONPATH=backend/src mypy backend/src/bt_web_ui/ --strict
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ (fully async) |
| Web framework | FastAPI + Uvicorn |
| Bluetooth | BlueZ 5.x via dbus-fast (D-Bus) |
| Database | SQLite via aiosqlite (WAL mode) |
| Templates | Jinja2 (server-rendered) |
| Interactivity | HTMX (HTML partials) + Alpine.js (client state) |
| Theming | CSS custom properties (light/dark/auto) |
| Testing | pytest + pytest-asyncio + httpx |
| Quality | mypy --strict, ruff |

## Deployment (systemd)

For persistent operation:

```bash
sudo tee /etc/systemd/system/bt-web-ui.service << 'EOF'
[Unit]
Description=Bluetooth Web UI
After=bluetooth.service network.target
Requires=bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bt-web-ui
Environment=PYTHONPATH=/home/pi/bt-web-ui/backend/src
Environment=PATH=/home/pi/bt-web-ui/.venv/bin:/usr/bin
ExecStart=/home/pi/bt-web-ui/.venv/bin/uvicorn \
    bt_web_ui.main:app \
    --host 0.0.0.0 --port 8080
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bt-web-ui
sudo systemctl start bt-web-ui

# Check status
sudo systemctl status bt-web-ui
journalctl -u bt-web-ui -f
```

## License

MIT
