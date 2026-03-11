# REST API Contract: Bluetooth Web UI

**Feature**: 001-bluetooth-web-ui
**Date**: 2026-03-10
**Base URL**: `http://<host>:8080`

## Adapter Endpoints

### GET /api/adapter

Returns the current Bluetooth adapter state.

**Response 200**:
```json
{
  "address": "AA:BB:CC:DD:EE:FF",
  "name": "hci0",
  "powered": true,
  "discovering": false,
  "discoverable": false
}
```

**Response 503** (no adapter found):
```json
{
  "error": "no_adapter",
  "message": "No Bluetooth adapter found. Check that a Bluetooth adapter is connected and BlueZ is running."
}
```

### POST /api/adapter/power

Toggle adapter power state.

**Request**:
```json
{
  "powered": true
}
```

**Response 200**:
```json
{
  "address": "AA:BB:CC:DD:EE:FF",
  "name": "hci0",
  "powered": true,
  "discovering": false,
  "discoverable": false
}
```

**Response 503**: Adapter unavailable.

## Discovery Endpoints

### POST /api/scan/start

Start Bluetooth device discovery. Runs for the configured scan
duration (default 10 seconds) then stops automatically.

**Response 200**:
```json
{
  "status": "scanning",
  "duration_seconds": 10
}
```

**Response 409** (already scanning):
```json
{
  "error": "already_scanning",
  "message": "A scan is already in progress."
}
```

**Response 503**: Adapter unavailable or powered off.

### POST /api/scan/stop

Stop an in-progress scan.

**Response 200**:
```json
{
  "status": "stopped"
}
```

## Device Endpoints

### GET /api/devices

List all known devices (from SQLite store + live BlueZ state).

**Query Parameters**:
- `filter` (optional): `all` (default), `paired`, `connected`,
  `favorites`
- `sort` (optional): `last_seen` (default), `name`, `last_connected`

**Response 200**:
```json
{
  "devices": [
    {
      "mac_address": "11:22:33:44:55:66",
      "name": "JBL Speaker",
      "alias": "Living Room Speaker",
      "device_type": "audio",
      "first_seen": "2026-03-01T10:00:00Z",
      "last_seen": "2026-03-10T14:30:00Z",
      "last_connected": "2026-03-10T14:25:00Z",
      "is_favorite": true,
      "notes": null,
      "paired": true,
      "connected": true,
      "trusted": true,
      "rssi": null,
      "connection_state": "connected"
    }
  ],
  "count": 1
}
```

### GET /api/devices/{mac_address}

Get a single device by MAC address.

**Path Parameter**: `mac_address` — URL-encoded MAC (e.g.,
`11:22:33:44:55:66` or `11%3A22%3A33%3A44%3A55%3A66`)

**Response 200**: Single device object (same shape as list item).

**Response 404**:
```json
{
  "error": "device_not_found",
  "message": "No device found with address 11:22:33:44:55:66."
}
```

### PATCH /api/devices/{mac_address}

Update user-editable device fields.

**Request** (all fields optional):
```json
{
  "alias": "Kitchen Speaker",
  "is_favorite": true,
  "notes": "Bluetooth 5.0, supports aptX"
}
```

**Response 200**: Updated device object.

**Response 404**: Device not found.

**Response 422**: Validation error (alias too long, etc.).

### DELETE /api/devices/{mac_address}

Remove a device from the app's stored history. Does NOT unpair from
BlueZ — use POST /api/devices/{mac_address}/remove for that.

**Response 200**:
```json
{
  "status": "deleted",
  "mac_address": "11:22:33:44:55:66"
}
```

**Response 404**: Device not found.

## Device Action Endpoints

### POST /api/devices/{mac_address}/pair

Initiate pairing with a device.

**Response 200**:
```json
{
  "mac_address": "11:22:33:44:55:66",
  "status": "pairing"
}
```

**Response 409** (already paired):
```json
{
  "error": "already_paired",
  "message": "Device is already paired."
}
```

**Response 504** (pairing timeout/failure):
```json
{
  "error": "pairing_failed",
  "message": "Pairing with 11:22:33:44:55:66 failed: device rejected the pairing request."
}
```

### POST /api/devices/{mac_address}/connect

Connect to a paired device.

**Response 200**:
```json
{
  "mac_address": "11:22:33:44:55:66",
  "status": "connecting"
}
```

**Response 409**: Already connected.

**Response 412** (not paired):
```json
{
  "error": "not_paired",
  "message": "Device must be paired before connecting."
}
```

**Response 504**: Connection timeout/failure.

### POST /api/devices/{mac_address}/disconnect

Disconnect a connected device.

**Response 200**:
```json
{
  "mac_address": "11:22:33:44:55:66",
  "status": "disconnected"
}
```

**Response 409**: Already disconnected.

### POST /api/devices/{mac_address}/trust

Trust a device (allow auto-connect).

**Response 200**: Updated device object with `trusted: true`.

### POST /api/devices/{mac_address}/untrust

Remove trust from a device.

**Response 200**: Updated device object with `trusted: false`.

### POST /api/devices/{mac_address}/remove

Remove/unpair a device from BlueZ. The device remains in the app's
history (SQLite) with `paired: false`.

**Response 200**:
```json
{
  "mac_address": "11:22:33:44:55:66",
  "status": "removed"
}
```

## Settings Endpoints

### GET /api/settings

Get current application settings.

**Response 200**:
```json
{
  "theme": "dark",
  "auto_connect_favorites": false,
  "scan_duration_seconds": 10,
  "adapter_name": null
}
```

### PATCH /api/settings

Update application settings.

**Request** (all fields optional):
```json
{
  "theme": "dark",
  "auto_connect_favorites": true,
  "scan_duration_seconds": 15
}
```

**Response 200**: Updated settings object.

**Response 422**: Validation error.

## Page Endpoints (HTML)

These serve server-rendered HTML pages via Jinja2 templates.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard — adapter status, quick actions |
| GET | `/devices` | Device list with filters |
| GET | `/devices/{mac_address}` | Device detail page |
| GET | `/settings` | Application settings page |

## Error Response Format

All error responses use a consistent structure:

```json
{
  "error": "error_code_snake_case",
  "message": "Human-readable explanation of what happened and what to do."
}
```

HTTP status codes used:
- `200` — Success
- `404` — Resource not found
- `409` — Conflict (action not applicable in current state)
- `412` — Precondition failed (e.g., not paired before connect)
- `422` — Validation error
- `503` — Bluetooth adapter unavailable
- `504` — Bluetooth operation timed out
