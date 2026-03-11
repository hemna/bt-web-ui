# Implementation Plan: Bluetooth Web UI

**Branch**: `001-bluetooth-web-ui` | **Date**: 2026-03-10 | **Spec**: [specs/001-bluetooth-web-ui/spec.md](spec.md)
**Input**: User description — Python web-based themeable interface for managing Bluetooth pairing and device connections on Raspberry Pi (Debian).

## Summary

Build a Python-powered web interface for managing Bluetooth device
pairing and connections on a Raspberry Pi. The backend uses FastAPI
with async D-Bus access to BlueZ for all Bluetooth operations. The
frontend uses server-rendered Jinja2 templates with HTMX for
real-time updates and Alpine.js for client-side interactions, themed
via CSS custom properties. Paired device history persists in SQLite
so devices are remembered even after BlueZ forgets them.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Uvicorn, dbus-fast, aiosqlite,
Jinja2, HTMX (CDN/static), Alpine.js (CDN/static)
**Storage**: SQLite (via aiosqlite) for device history and settings
**Testing**: pytest, python-dbusmock, FastAPI TestClient, httpx
**Target Platform**: Raspberry Pi (Debian/Raspberry Pi OS, ARM64),
any Linux with BlueZ 5.x and systemd
**Project Type**: Web service (single-process Python server)
**Performance Goals**: <3s time to interactive on Pi,
<200ms UI feedback on every action, <50ms overhead on BT API calls
**Constraints**: Single-user local network app, <100MB total memory,
no Node.js build toolchain, must work headless (no display required
on the Pi itself — accessed via browser from another device)
**Scale/Scope**: 1 user, ~50 remembered devices max, 4-5 views
(dashboard, device list, device detail, settings, scan results)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality | PASS | Python with strict mypy type checking. Ruff for linting/formatting. Single-responsibility modules. |
| II. Testing Standards | PASS | pytest + python-dbusmock for D-Bus isolation. FastAPI TestClient for API. Dependency injection for mock boundaries. Test-first workflow enforced. |
| III. UX Consistency | PASS | CSS custom properties for theming. HTMX for immediate feedback. Alpine.js for toast notifications and state visibility. Responsive layout via CSS. |
| IV. Performance | PASS | Lightweight stack (~33KB frontend). Async throughout (FastAPI + dbus-fast + aiosqlite). No build step. SQLite for fast local storage. |
| Technical Constraints | DIVERGENCE | Constitution references Web Bluetooth API (client-side browser API). This implementation uses server-side BlueZ D-Bus instead, which is the correct approach for Raspberry Pi. The Web Bluetooth API does not support Classic Bluetooth and has limited browser support. The constitution's Technical Constraints section should be amended to reflect the actual architecture. Core principles (I-IV) are fully satisfied. |

**Gate result**: PASS with noted divergence on Technical Constraints.
The divergence is justified: Web Bluetooth API cannot manage Classic
Bluetooth pairing and is not suitable for a headless Raspberry Pi
deployment. A constitution amendment PR should follow to update the
Technical Constraints section.

## Project Structure

### Documentation (this feature)

```text
specs/001-bluetooth-web-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (REST + WebSocket API)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── bt_web_ui/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings and configuration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── device.py        # Device Pydantic models
│   │   │   └── settings.py      # App settings models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── bluetooth.py     # BlueZ D-Bus abstraction layer
│   │   │   ├── device_store.py  # SQLite device persistence
│   │   │   └── event_bus.py     # Internal event dispatch
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── devices.py       # REST endpoints for devices
│   │   │   ├── adapter.py       # REST endpoints for BT adapter
│   │   │   ├── settings.py      # REST endpoints for app settings
│   │   │   └── websocket.py     # WebSocket for real-time updates
│   │   └── templates/
│   │       ├── base.html        # Base layout with theme support
│   │       ├── index.html       # Dashboard
│   │       ├── devices.html     # Device list
│   │       ├── device.html      # Device detail
│   │       ├── scan.html        # Scan results partial
│   │       ├── settings.html    # App settings (theme, etc.)
│   │       └── partials/
│   │           ├── device_card.html
│   │           ├── device_row.html
│   │           ├── toast.html
│   │           └── status_badge.html
│   └── static/
│       ├── css/
│       │   ├── theme.css        # CSS custom properties (themes)
│       │   └── main.css         # Layout and components
│       └── js/
│           ├── htmx.min.js      # HTMX (vendored)
│           └── alpine.min.js    # Alpine.js (vendored)
├── tests/
│   ├── conftest.py              # Shared fixtures (mock bus, client)
│   ├── unit/
│   │   ├── test_device_models.py
│   │   ├── test_device_store.py
│   │   └── test_bluetooth_service.py
│   ├── integration/
│   │   ├── test_dbus_bluetooth.py   # python-dbusmock tests
│   │   ├── test_device_lifecycle.py
│   │   └── test_websocket_events.py
│   └── api/
│       ├── test_devices_api.py
│       ├── test_adapter_api.py
│       └── test_settings_api.py
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt

data/
└── bt_web_ui.db             # SQLite database (runtime, gitignored)
```

**Structure Decision**: Single Python project (no separate frontend
build). The backend serves both the API and the rendered HTML/CSS/JS.
This eliminates the need for Node.js on the Raspberry Pi and keeps
deployment simple (single `pip install` + `uvicorn`).

## Complexity Tracking

| Divergence | Why Needed | Constitution Update Required |
|-----------|------------|------------------------------|
| Server-side BlueZ D-Bus instead of Web Bluetooth API | Web Bluetooth API cannot pair Classic BT devices; not available in headless Pi scenarios; limited to Chromium-only | Yes — Technical Constraints section should be updated to reflect server-side BT architecture |
