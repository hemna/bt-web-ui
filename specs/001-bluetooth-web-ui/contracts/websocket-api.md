# WebSocket Contract: Bluetooth Web UI

**Feature**: 001-bluetooth-web-ui
**Date**: 2026-03-10
**Endpoint**: `ws://<host>:8080/ws`

## Connection

The client connects to `/ws` to receive real-time Bluetooth event
notifications. The WebSocket is unidirectional: the server pushes
events, the client does not send messages (all actions go through
REST endpoints).

## Message Format

All messages are JSON with a consistent envelope:

```json
{
  "event": "event_type",
  "timestamp": "2026-03-10T14:30:00Z",
  "data": { ... }
}
```

## Events

### device_discovered

A new device was found during a scan.

```json
{
  "event": "device_discovered",
  "timestamp": "2026-03-10T14:30:01Z",
  "data": {
    "mac_address": "11:22:33:44:55:66",
    "name": "JBL Speaker",
    "device_type": "audio",
    "rssi": -45,
    "paired": false,
    "connected": false
  }
}
```

### device_updated

A device property changed (connection state, name, RSSI, etc.).

```json
{
  "event": "device_updated",
  "timestamp": "2026-03-10T14:30:05Z",
  "data": {
    "mac_address": "11:22:33:44:55:66",
    "changed_properties": {
      "connected": true,
      "connection_state": "connected"
    }
  }
}
```

### device_removed

A device was removed from BlueZ (e.g., went out of range during
scan, or explicitly removed).

```json
{
  "event": "device_removed",
  "timestamp": "2026-03-10T14:30:10Z",
  "data": {
    "mac_address": "11:22:33:44:55:66"
  }
}
```

### scan_started

Device discovery has begun.

```json
{
  "event": "scan_started",
  "timestamp": "2026-03-10T14:30:00Z",
  "data": {
    "duration_seconds": 10
  }
}
```

### scan_stopped

Device discovery has ended (timeout or manual stop).

```json
{
  "event": "scan_stopped",
  "timestamp": "2026-03-10T14:30:10Z",
  "data": {
    "reason": "timeout"
  }
}
```

`reason` values: `timeout`, `manual`, `error`

### adapter_changed

Bluetooth adapter state changed (powered on/off, etc.).

```json
{
  "event": "adapter_changed",
  "timestamp": "2026-03-10T14:30:00Z",
  "data": {
    "address": "AA:BB:CC:DD:EE:FF",
    "powered": true,
    "discovering": false,
    "discoverable": false
  }
}
```

### pairing_request

A pairing operation requires user interaction (e.g., PIN
confirmation). The UI MUST display the appropriate dialog.

```json
{
  "event": "pairing_request",
  "timestamp": "2026-03-10T14:30:05Z",
  "data": {
    "mac_address": "11:22:33:44:55:66",
    "name": "Keyboard",
    "request_type": "confirm_passkey",
    "passkey": "123456"
  }
}
```

`request_type` values:
- `confirm_passkey` — display passkey and ask user to confirm
- `enter_pin` — prompt user to enter a PIN
- `confirm_pairing` — simple yes/no pairing confirmation

### error

An asynchronous error occurred (e.g., connection dropped
unexpectedly).

```json
{
  "event": "error",
  "timestamp": "2026-03-10T14:30:15Z",
  "data": {
    "mac_address": "11:22:33:44:55:66",
    "error": "connection_lost",
    "message": "Connection to JBL Speaker was lost unexpectedly."
  }
}
```

## HTMX Integration

The WebSocket is consumed via HTMX's `hx-ws` extension. Events
trigger partial HTML updates via server-sent HTML fragments:

```html
<!-- In base.html -->
<div hx-ws="connect:/ws" hx-ws-send="">
  <div id="device-list">
    <!-- Swapped by device_discovered/device_updated events -->
  </div>
  <div id="toast-container">
    <!-- Swapped by error events -->
  </div>
</div>
```

The server formats WebSocket messages as HTML partials (not raw
JSON) when the client connects with an `Accept: text/html` header
or via HTMX. Raw JSON is sent for programmatic clients.

## Reconnection

If the WebSocket disconnects, the client MUST reconnect
automatically. HTMX handles this natively with `hx-ws`. On
reconnect, the client SHOULD refresh the device list via
`GET /api/devices` to catch any missed events.
