# Research: Bluetooth Web UI

**Feature**: 001-bluetooth-web-ui
**Date**: 2026-03-10

## 1. Python Web Framework

**Decision**: FastAPI (with Uvicorn ASGI server)

**Rationale**: Native async/await support is essential since D-Bus
interactions with BlueZ are inherently asynchronous (device discovery,
pairing callbacks, connection state changes). FastAPI provides
first-class WebSocket support via Starlette for real-time BT status
push. Built-in Jinja2 template rendering and static file serving
means a single process handles both API and UI. Pydantic models
provide automatic validation for structured BT device data. Low
memory footprint suitable for Raspberry Pi.

**Alternatives Considered**:

| Framework | Why Not |
|-----------|---------|
| Flask | WSGI (synchronous) by default. WebSocket requires flask-socketio + eventlet/gevent. Async support in Flask 2.x is bolted on, not native. |
| Litestar | Comparable ASGI framework but smaller community and fewer examples for embedded/Pi deployments. |
| Bottle | No async, no WebSocket. Too minimal for real-time updates. |

## 2. Bluetooth Management on Linux

**Decision**: `dbus-fast` — async D-Bus client talking directly to
BlueZ D-Bus interfaces

**Rationale**: BlueZ exposes its full API over D-Bus:
`org.bluez.Adapter1` (power, discovery), `org.bluez.Device1` (pair,
connect, disconnect, trust), `org.freedesktop.DBus.ObjectManager`
(enumerate adapters/devices), and `org.freedesktop.DBus.Properties`
(watch `PropertiesChanged` for real-time status). `dbus-fast` is a
maintained fork of the abandoned `dbus-next`, provides pure async
`asyncio` integration, has an optional Cython extension for ARM
performance, and is battle-tested in Home Assistant on Raspberry Pi.

**Alternatives Considered**:

| Library | Why Not |
|---------|---------|
| `dbus-next` | Abandoned since July 2021. No Python 3.11+ testing. `dbus-fast` is its direct successor. |
| `pydbus` | Uses GLib main loop, not asyncio. Last release 2016. Threading hacks required for FastAPI integration. |
| `bluezero` | BLE only (GATT). Does not cover Classic Bluetooth pairing (A2DP, HID). Uses GLib internally. |
| `bleak` | BLE GATT client only. Cannot pair Classic BT devices or manage adapters. |
| `bluetoothctl` subprocess | Fragile text parsing. No structured errors. No real-time event subscription. Race conditions. Hard to test. |

**Key BlueZ D-Bus Interfaces Used**:

- `org.bluez.Adapter1`: `StartDiscovery()`, `StopDiscovery()`,
  `RemoveDevice()`, properties `Powered`, `Discovering`, `Address`
- `org.bluez.Device1`: `Pair()`, `Connect()`, `Disconnect()`,
  `Trust()`, properties `Name`, `Address`, `Paired`, `Connected`,
  `Trusted`, `Icon`
- `org.freedesktop.DBus.ObjectManager`: `GetManagedObjects()` for
  enumerating all adapters and devices
- `org.freedesktop.DBus.Properties`: `PropertiesChanged` signal for
  real-time state updates

## 3. Frontend Approach

**Decision**: Jinja2 server-rendered HTML + HTMX + Alpine.js + CSS
custom properties

**Rationale**: Zero build step — no Node.js, webpack, or npm required
on the Pi. HTMX (~16KB gzipped) handles AJAX partial updates and
WebSocket connections from HTML attributes. Alpine.js (~17KB gzipped)
handles client-side state for theme switching, toast notifications,
and modal dialogs. CSS custom properties provide native theming with
no runtime cost. Total frontend payload: ~33KB gzipped. FastAPI
serves everything from a single process.

**Theming via CSS custom properties**:
```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --text-primary: #1a1a1a;
  --accent: #2563eb;
}
[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --text-primary: #e5e5e5;
  --accent: #3b82f6;
}
```

Theme preference stored in `localStorage`, applied via Alpine.js
`$store.theme.toggle()`.

**Alternatives Considered**:

| Approach | Why Not |
|----------|---------|
| HTMX only (no Alpine) | Lacks client-side state management for theme toggle, modals, toasts. Would need ad-hoc vanilla JS. |
| Preact + CSS custom properties | Requires JSX transpilation and build toolchain. Unnecessary complexity for 4-5 views. |
| React/Vue SPA | 40-100KB+ gzipped. Requires Node.js build chain. Overkill for this scope. |
| Svelte | Still needs build step. Unnecessary complexity. |

## 4. Persistent Storage for Paired Devices

**Decision**: SQLite via `aiosqlite`

**Rationale**: Single file, zero configuration, built into Python's
stdlib. `aiosqlite` provides async access compatible with FastAPI's
event loop. Handles concurrent reads well; writes are serialized
(fine for single-user Pi app). Survives power loss better than JSON
files (WAL mode). Supports structured queries (filter by device type,
sort by last seen). BlueZ's own storage
(`/var/lib/bluetooth/<adapter>/<device>/info`) is read on startup to
sync known-paired devices, but SQLite is the primary store because
BlueZ removes device directories on `remove-device` and stores no
app-level metadata.

**Alternatives Considered**:

| Storage | Why Not |
|---------|---------|
| JSON file | No atomic writes (corruption on power loss). No querying. Must load entire file. |
| BlueZ storage only | Loses data on `remove-device`. No custom metadata (aliases, favorites, categories). |
| TinyDB | Adds dependency for no benefit over SQLite. Slower queries. |

## 5. Testing Strategy

**Decision**: `python-dbusmock` + pytest + FastAPI TestClient +
dependency injection

**Rationale**: Three-layer testing strategy that requires no
Bluetooth hardware:

1. **D-Bus layer**: `python-dbusmock` creates mock D-Bus objects
   responding to method calls and emitting signals. Private bus per
   test — no root needed, no real BlueZ needed.
2. **Application layer**: FastAPI dependency injection swaps real
   `BlueZManager` for `MockBlueZManager` in tests.
3. **API layer**: FastAPI `TestClient` (httpx) tests REST and
   WebSocket endpoints without starting a real server.

All tests run in standard CI (GitHub Actions Linux) without
Bluetooth hardware.

**Test Matrix**:

| Layer | Tool | Scope |
|-------|------|-------|
| Unit | pytest + unittest.mock | Business logic, state machine, storage |
| D-Bus Integration | python-dbusmock + pytest | BlueZ adapter/device interactions, signals |
| API Integration | FastAPI TestClient | REST endpoints, WebSocket, error handling |
| Storage | pytest tmp_path + SQLite in-memory | Schema, queries, migrations |

**Alternatives Considered**:

| Approach | Why Not |
|----------|---------|
| `unittest.mock.patch` on dbus-fast | Fragile, coupled to dbus-fast internals. Doesn't test D-Bus serialization. |
| Docker with BlueZ | Complex setup. Still no real hardware. Overkill for unit tests. |
| Hardware-in-the-loop | Not CI-friendly. Flaky. Manual acceptance only. |
