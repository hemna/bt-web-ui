# Data Model: Bluetooth Web UI

**Feature**: 001-bluetooth-web-ui
**Date**: 2026-03-10

## Entities

### Device

Represents a Bluetooth device — either currently visible, previously
paired, or stored in the app's history.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| mac_address | TEXT | PRIMARY KEY, format `XX:XX:XX:XX:XX:XX` | Unique hardware address |
| name | TEXT | nullable | Device-reported name from BlueZ |
| alias | TEXT | nullable | User-assigned friendly name |
| device_type | TEXT | nullable, one of: `audio`, `input`, `phone`, `computer`, `network`, `other` | Device class category derived from BlueZ `Icon` property |
| first_seen | DATETIME | NOT NULL, ISO 8601 | Timestamp when device was first discovered |
| last_seen | DATETIME | NOT NULL, ISO 8601 | Timestamp of most recent discovery or connection |
| last_connected | DATETIME | nullable, ISO 8601 | Timestamp of most recent successful connection |
| is_favorite | BOOLEAN | NOT NULL, default `false` | User-marked favorite for quick access |
| notes | TEXT | nullable | Free-text user notes about the device |

**Validation Rules**:
- `mac_address` MUST match pattern `^([0-9A-F]{2}:){5}[0-9A-F]{2}$`
  (uppercase hex, colon-separated)
- `alias` MUST be 1-64 characters if provided
- `device_type` MUST be from the enumerated set or null
- `notes` MUST be <= 500 characters if provided

### AdapterState

Represents the current state of the local Bluetooth adapter. This is
**not persisted** — it is a runtime-only model populated from BlueZ
D-Bus properties.

| Field | Type | Description |
|-------|------|-------------|
| address | TEXT | Adapter MAC address |
| name | TEXT | Adapter name (e.g., "hci0") |
| powered | BOOLEAN | Whether adapter is powered on |
| discovering | BOOLEAN | Whether a scan is in progress |
| discoverable | BOOLEAN | Whether adapter is visible to other devices |

### DeviceRuntimeState

Runtime-only model combining persisted Device data with live BlueZ
state. Used in API responses and templates. **Not persisted.**

| Field | Type | Description |
|-------|------|-------------|
| (all Device fields) | — | From SQLite |
| paired | BOOLEAN | Live: is device paired in BlueZ |
| connected | BOOLEAN | Live: is device currently connected |
| trusted | BOOLEAN | Live: is device trusted in BlueZ |
| rssi | INTEGER | Live: signal strength (during scan only, nullable) |
| connection_state | ENUM | Derived: `disconnected`, `connecting`, `connected`, `pairing`, `error` |

### AppSettings

Application configuration. Single row in SQLite.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, always 1 | Singleton row |
| theme | TEXT | NOT NULL, one of: `light`, `dark`, `auto` | Active color theme |
| auto_connect_favorites | BOOLEAN | NOT NULL, default `false` | Auto-connect favorite devices on startup |
| scan_duration_seconds | INTEGER | NOT NULL, default `10`, range 5-60 | How long to scan when user triggers discovery |
| adapter_name | TEXT | nullable | Preferred Bluetooth adapter (null = first available) |

**Validation Rules**:
- `theme` MUST be one of `light`, `dark`, `auto`
- `scan_duration_seconds` MUST be between 5 and 60 inclusive
- `adapter_name` MUST match an available adapter or be null

## State Transitions

### Device Connection Lifecycle

```
                ┌──────────────┐
                │ disconnected │◄────────────────────────┐
                └──────┬───────┘                         │
                       │ user: connect()                 │
                       ▼                                 │
                ┌──────────────┐     timeout/error  ┌────┴─────┐
                │  connecting  │───────────────────►│  error   │
                └──────┬───────┘                    └────┬─────┘
                       │ BlueZ: Connected=true           │
                       ▼                                 │
                ┌──────────────┐     user: retry()       │
                │  connected   │◄────────────────────────┘
                └──────┬───────┘
                       │ user: disconnect()
                       │ or BlueZ: Connected=false
                       ▼
                ┌──────────────┐
                │ disconnected │
                └──────────────┘
```

### Device Pairing Lifecycle

```
                ┌────────────┐
                │  unknown   │  (discovered but not paired)
                └─────┬──────┘
                      │ user: pair()
                      ▼
                ┌────────────┐     error/rejected  ┌─────────┐
                │  pairing   │────────────────────►│  error  │
                └─────┬──────┘                     └────┬────┘
                      │ BlueZ: Paired=true              │
                      ▼                                 │
                ┌────────────┐     user: retry()        │
                │   paired   │◄─────────────────────────┘
                └─────┬──────┘
                      │ user: remove()
                      ▼
                ┌────────────┐
                │  removed   │  (kept in DB, removed from BlueZ)
                └────────────┘
```

## Relationships

```
AdapterState (1) ──── manages ────► (many) DeviceRuntimeState
Device (persisted) ──── extends to ──► DeviceRuntimeState (runtime)
AppSettings (1) ──── configures ────► Application behavior
```

## SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS devices (
    mac_address TEXT PRIMARY KEY,
    name TEXT,
    alias TEXT,
    device_type TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    last_connected TEXT,
    is_favorite INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    theme TEXT NOT NULL DEFAULT 'light',
    auto_connect_favorites INTEGER NOT NULL DEFAULT 0,
    scan_duration_seconds INTEGER NOT NULL DEFAULT 10,
    adapter_name TEXT
);

CREATE INDEX idx_devices_last_seen ON devices(last_seen DESC);
CREATE INDEX idx_devices_is_favorite ON devices(is_favorite)
    WHERE is_favorite = 1;
```
