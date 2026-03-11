# Tasks: Bluetooth Web UI

**Input**: Design documents from `/specs/001-bluetooth-web-ui/`
**Prerequisites**: plan.md (required), data-model.md, contracts/, research.md, quickstart.md
**Note**: spec.md was not generated; user stories are derived from the plan and user description.

**Tests**: Included per Constitution Principle II (Testing Standards).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single Python project**: `backend/src/`, `backend/tests/` per plan.md

## User Stories (derived from plan.md and user description)

- **US1 (P1)**: Scan and discover Bluetooth devices — view adapter status, trigger scans, see discovered devices in real time
- **US2 (P2)**: Pair and connect to devices — pair, connect, disconnect, trust, remove devices via the web UI
- **US3 (P3)**: Remember past paired devices — persist device history in SQLite, display previously seen devices, allow reconnection
- **US4 (P4)**: Themeable interface — light/dark/auto themes, settings page, responsive layout

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency configuration, and basic structure

- [x] T001 Create project directory structure per plan.md at backend/src/bt_web_ui/ with subdirectories models/, services/, api/, templates/, templates/partials/ and backend/tests/ with subdirectories unit/, integration/, api/
- [x] T002 Create pyproject.toml at backend/pyproject.toml with Python 3.11+ requirement, project metadata, pytest configuration, mypy strict mode, and ruff configuration
- [x] T003 [P] Create requirements.txt at backend/requirements.txt with fastapi, uvicorn[standard], dbus-fast, aiosqlite, jinja2, python-multipart
- [x] T004 [P] Create requirements-dev.txt at backend/requirements-dev.txt with pytest, pytest-asyncio, pytest-cov, python-dbusmock, httpx, mypy, ruff
- [x] T005 [P] Create .gitignore at repository root with entries for data/*.db, __pycache__/, .venv/, *.pyc, .mypy_cache/, .pytest_cache/, .ruff_cache/
- [x] T006 [P] Vendor HTMX library to backend/src/static/js/htmx.min.js
- [x] T007 [P] Vendor Alpine.js library to backend/src/static/js/alpine.min.js

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Implement application configuration in backend/src/bt_web_ui/config.py — define Settings class using pydantic-settings with BT_WEB_UI_HOST, BT_WEB_UI_PORT, BT_WEB_UI_DB_PATH, BT_WEB_UI_ADAPTER, BT_WEB_UI_LOG_LEVEL environment variables per quickstart.md
- [x] T009 Create package __init__.py files at backend/src/bt_web_ui/__init__.py, backend/src/bt_web_ui/models/__init__.py, backend/src/bt_web_ui/services/__init__.py, backend/src/bt_web_ui/api/__init__.py
- [x] T010 Implement Device and DeviceRuntimeState Pydantic models in backend/src/bt_web_ui/models/device.py per data-model.md — include MacAddress validated type, DeviceType enum (audio, input, phone, computer, network, other), ConnectionState enum (disconnected, connecting, connected, pairing, error), Device base model with all fields, DeviceRuntimeState extending Device with live state fields
- [x] T011 [P] Implement AdapterState Pydantic model in backend/src/bt_web_ui/models/device.py — address, name, powered, discovering, discoverable fields per data-model.md
- [x] T012 [P] Implement AppSettings Pydantic model and ThemeChoice enum in backend/src/bt_web_ui/models/settings.py per data-model.md — theme (light/dark/auto), auto_connect_favorites, scan_duration_seconds (5-60), adapter_name
- [x] T013 Implement SQLite device store in backend/src/bt_web_ui/services/device_store.py — async init_db() to create tables per data-model.md schema, get_all_devices(), get_device(mac), upsert_device(), update_device(), delete_device() methods using aiosqlite
- [x] T014 Implement internal event bus in backend/src/bt_web_ui/services/event_bus.py — async pub/sub using asyncio.Queue for broadcasting BlueZ events to WebSocket clients, subscribe()/unsubscribe()/publish() methods
- [x] T015 Implement error response models and exception handlers in backend/src/bt_web_ui/api/__init__.py — define BluetoothError, DeviceNotFoundError, AdapterUnavailableError exceptions with error code and human-readable message per contracts/rest-api.md error format
- [x] T016 Implement FastAPI application entry point in backend/src/bt_web_ui/main.py — create FastAPI app, configure Jinja2 templates directory, mount static files at /static, register startup/shutdown lifecycle hooks for D-Bus connection and SQLite init, include API routers, configure structured logging
- [x] T017 Create shared test fixtures in backend/tests/conftest.py — pytest fixtures for: async test client (httpx.AsyncClient), in-memory SQLite device store, mock BlueZ manager using FastAPI dependency_overrides, mock event bus
- [x] T018 [P] Create unit tests for Device and DeviceRuntimeState models in backend/tests/unit/test_device_models.py — test MacAddress validation (valid, invalid, lowercase normalization), DeviceType enum values, ConnectionState transitions, Device creation with all fields, DeviceRuntimeState merging persisted and live state
- [x] T019 [P] Create unit tests for device store in backend/tests/unit/test_device_store.py — test init_db creates tables, upsert_device inserts new and updates existing, get_all_devices with filters, get_device by mac, update_device partial fields, delete_device, last_seen/first_seen timestamp handling

**Checkpoint**: Foundation ready — all models defined, storage operational, app boots, test infrastructure in place

---

## Phase 3: User Story 1 — Scan and Discover Devices (Priority: P1) MVP

**Goal**: User can view Bluetooth adapter status, trigger a device scan, and see discovered devices appearing in real time via the web UI.

**Independent Test**: Open the web UI, verify adapter status is displayed, click Scan, verify discovered devices appear in the device list within the scan duration.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T020 [P] [US1] Create unit tests for BlueZ bluetooth service in backend/tests/unit/test_bluetooth_service.py — test get_adapter_state returns AdapterState, test start_discovery calls D-Bus StartDiscovery, test stop_discovery calls StopDiscovery, test device_discovered callback creates DeviceRuntimeState from D-Bus properties
- [x] T021 [P] [US1] Create API tests for adapter endpoints in backend/tests/api/test_adapter_api.py — test GET /api/adapter returns adapter state (200), test GET /api/adapter returns 503 when no adapter, test POST /api/adapter/power toggles power state per contracts/rest-api.md
- [x] T022 [P] [US1] Create API tests for scan endpoints in backend/tests/api/test_adapter_api.py — test POST /api/scan/start returns 200 with scanning status, test POST /api/scan/start returns 409 when already scanning, test POST /api/scan/stop returns 200 per contracts/rest-api.md
- [x] T023 [P] [US1] Create integration tests for WebSocket events in backend/tests/integration/test_websocket_events.py — test client receives device_discovered event during scan, test client receives scan_started and scan_stopped events, test client receives adapter_changed event per contracts/websocket-api.md

### Implementation for User Story 1

- [x] T024 [US1] Implement BlueZ bluetooth service in backend/src/bt_web_ui/services/bluetooth.py — async BlueZManager class: connect to system D-Bus via dbus-fast MessageBus, get_adapter_state() reading org.bluez.Adapter1 properties, start_discovery()/stop_discovery() calling Adapter1 methods, subscribe to ObjectManager InterfacesAdded signal for device discovery, subscribe to Properties.PropertiesChanged on Adapter1 for state changes, publish events to event_bus
- [x] T025 [US1] Implement adapter API endpoints in backend/src/bt_web_ui/api/adapter.py — GET /api/adapter returning AdapterState, POST /api/adapter/power setting Powered property, POST /api/scan/start and /api/scan/stop with scan duration from AppSettings, error handling for 503 (no adapter) and 409 (already scanning) per contracts/rest-api.md
- [x] T026 [US1] Implement WebSocket endpoint in backend/src/bt_web_ui/api/websocket.py — accept WebSocket at /ws, subscribe to event_bus, format events as JSON (per contracts/websocket-api.md envelope format) or HTML partials (for HTMX clients based on Accept header), handle client disconnect gracefully
- [x] T027 [US1] Create base HTML template in backend/src/bt_web_ui/templates/base.html — HTML5 document with meta viewport, link to theme.css and main.css, script tags for htmx.min.js and alpine.min.js, Alpine.js x-data for theme store with localStorage persistence, navigation bar with links to /, /devices, /settings, HTMX WebSocket connection to /ws, toast container div, content block for child templates
- [x] T028 [P] [US1] Create CSS theme file in backend/src/static/css/theme.css — define CSS custom properties for light theme in :root (--bg-primary, --bg-secondary, --text-primary, --text-secondary, --accent, --success, --warning, --error, --border-radius, --shadow), dark theme in [data-theme="dark"], auto theme using prefers-color-scheme media query per research.md
- [x] T029 [P] [US1] Create main CSS file in backend/src/static/css/main.css — layout styles using CSS custom properties: body, nav bar, main content area, card component, button styles, badge/status indicator styles, responsive grid for device cards, toast notification styles, loading spinner/indicator, responsive breakpoints (320px-2560px per constitution)
- [x] T030 [US1] Create dashboard page template in backend/src/bt_web_ui/templates/index.html — extends base.html, display adapter status (address, powered, discovering) with status badges, Scan button triggering POST /api/scan/start via HTMX, scan progress indicator, quick stats (paired count, connected count), recently seen devices section
- [x] T031 [US1] Create device list page template in backend/src/bt_web_ui/templates/devices.html — extends base.html, device cards/rows with name, type icon, connection state badge, filter buttons (all, paired, connected, favorites) using HTMX to GET /api/devices with query params, sort dropdown, empty state message
- [x] T032 [P] [US1] Create device card partial in backend/src/bt_web_ui/templates/partials/device_card.html — device name (or alias), MAC address, device type icon, connection state badge using status_badge.html, action buttons (pair/connect/disconnect based on state), favorite toggle star
- [x] T033 [P] [US1] Create status badge partial in backend/src/bt_web_ui/templates/partials/status_badge.html — colored badge showing connection_state (disconnected=gray, connecting=yellow, connected=green, pairing=blue, error=red) with text label
- [x] T034 [P] [US1] Create toast notification partial in backend/src/bt_web_ui/templates/partials/toast.html — dismissable notification with type (success, error, info, warning), message text, auto-dismiss timer via Alpine.js
- [x] T035 [US1] Create scan results partial in backend/src/bt_web_ui/templates/scan.html — live-updating list of discovered devices during scan, HTMX swap target for device_discovered WebSocket events, scan progress bar, device count
- [x] T036 [US1] Implement HTML page route for dashboard in backend/src/bt_web_ui/api/adapter.py — GET / serving index.html template with adapter state and device summary data
- [x] T037 [US1] Implement HTML page route for device list in backend/src/bt_web_ui/api/devices.py — GET /devices serving devices.html template with device list, support HTMX partial responses for filter/sort changes

**Checkpoint**: User can open the web UI, see adapter status, trigger a scan, and watch devices appear in real time. This is the MVP.

---

## Phase 4: User Story 2 — Pair and Connect to Devices (Priority: P2)

**Goal**: User can pair with a discovered device, connect to paired devices, disconnect, trust/untrust, and remove devices — all through the web UI with real-time status feedback.

**Independent Test**: Discover a device via scan, click Pair, verify pairing succeeds and device shows as paired, click Connect, verify connection state changes to connected, click Disconnect, verify state returns to disconnected.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T038 [P] [US2] Create unit tests for BlueZ device operations in backend/tests/unit/test_bluetooth_service.py — test pair_device calls Device1.Pair(), test connect_device calls Device1.Connect(), test disconnect_device calls Device1.Disconnect(), test trust_device sets Trusted property, test remove_device calls Adapter1.RemoveDevice(), test pairing failure raises appropriate error, test connection to unpaired device raises error
- [x] T039 [P] [US2] Create API tests for device action endpoints in backend/tests/api/test_devices_api.py — test POST /api/devices/{mac}/pair returns 200 (pairing), test POST /api/devices/{mac}/pair returns 409 (already paired), test POST /api/devices/{mac}/connect returns 200, test POST /api/devices/{mac}/connect returns 412 (not paired), test POST /api/devices/{mac}/disconnect returns 200, test POST /api/devices/{mac}/trust and /untrust, test POST /api/devices/{mac}/remove per contracts/rest-api.md
- [x] T040 [P] [US2] Create integration tests for device lifecycle in backend/tests/integration/test_device_lifecycle.py — test full lifecycle: discover → pair → connect → disconnect → remove, test pairing_request WebSocket event triggers for passkey confirmation, test device_updated WebSocket events during connection state changes, test error WebSocket event on connection failure

### Implementation for User Story 2

- [x] T041 [US2] Extend BlueZ bluetooth service with device operations in backend/src/bt_web_ui/services/bluetooth.py — add pair_device(mac) calling Device1.Pair() with timeout, connect_device(mac) calling Device1.Connect(), disconnect_device(mac), trust_device(mac)/untrust_device(mac) setting Trusted property, remove_device(mac) calling Adapter1.RemoveDevice(), subscribe to Device1 PropertiesChanged for paired/connected/trusted state changes, publish device_updated events to event_bus
- [x] T042 [US2] Implement device action API endpoints in backend/src/bt_web_ui/api/devices.py — POST /api/devices/{mac}/pair, /connect, /disconnect, /trust, /untrust, /remove per contracts/rest-api.md with proper status codes (200, 409, 412, 504), error handling for pairing failures and timeouts
- [x] T043 [US2] Implement GET /api/devices and GET /api/devices/{mac} endpoints in backend/src/bt_web_ui/api/devices.py — list devices merging SQLite stored data with live BlueZ state into DeviceRuntimeState, support filter (all/paired/connected/favorites) and sort (last_seen/name/last_connected) query params, single device detail endpoint returning 404 if not found per contracts/rest-api.md
- [x] T044 [US2] Create device detail page template in backend/src/bt_web_ui/templates/device.html — extends base.html, display full device info (name, alias, MAC, type, first_seen, last_seen, last_connected), connection state with status badge, action buttons (pair/connect/disconnect/trust/untrust/remove) with HTMX POST to action endpoints, real-time state updates via WebSocket
- [x] T045 [US2] Create device row partial in backend/src/bt_web_ui/templates/partials/device_row.html — compact device row for list view with name, type, state badge, quick-action buttons (connect/disconnect), link to device detail page, HTMX swap target for device_updated events
- [x] T046 [US2] Implement HTML page route for device detail in backend/src/bt_web_ui/api/devices.py — GET /devices/{mac} serving device.html template with merged device data, return 404 page if device not found

**Checkpoint**: User can pair, connect, disconnect, and manage devices through the web UI with real-time feedback. Combined with US1, this delivers the core Bluetooth management experience.

---

## Phase 5: User Story 3 — Remember Past Paired Devices (Priority: P3)

**Goal**: The application persists all discovered/paired devices in SQLite so they appear on future visits even after BlueZ forgets them. Users can edit device aliases, mark favorites, add notes, and delete from history.

**Independent Test**: Pair a device, restart the application, verify the device still appears in the device list with correct metadata. Edit its alias, verify the alias persists. Mark as favorite, verify it appears in the favorites filter.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T047 [P] [US3] Create unit tests for device persistence sync in backend/tests/unit/test_device_store.py — test upsert_device on discovery updates last_seen, test upsert_device on first discovery sets first_seen, test device survives after BlueZ removal (bluez_paired=false but still in DB), test get_all_devices returns stored devices merged with live state
- [x] T048 [P] [US3] Create API tests for device CRUD in backend/tests/api/test_devices_api.py — test PATCH /api/devices/{mac} updates alias and is_favorite and notes, test PATCH /api/devices/{mac} returns 422 for alias >64 chars, test DELETE /api/devices/{mac} removes from store, test GET /api/devices?filter=favorites returns only favorites per contracts/rest-api.md

### Implementation for User Story 3

- [x] T049 [US3] Implement device sync on BlueZ events in backend/src/bt_web_ui/services/bluetooth.py — on device_discovered: upsert device into SQLite with current timestamp as last_seen, on connect success: update last_connected timestamp, on startup: sync existing BlueZ paired devices into SQLite store
- [x] T050 [US3] Implement PATCH /api/devices/{mac} endpoint in backend/src/bt_web_ui/api/devices.py — accept optional alias (1-64 chars), is_favorite (bool), notes (<=500 chars) fields, validate with Pydantic, update SQLite via device_store, return updated DeviceRuntimeState, 404 if not found, 422 on validation error per contracts/rest-api.md
- [x] T051 [US3] Implement DELETE /api/devices/{mac} endpoint in backend/src/bt_web_ui/api/devices.py — remove device from SQLite store only (not from BlueZ), return 200 with status deleted, 404 if not found per contracts/rest-api.md
- [x] T052 [US3] Update device detail template in backend/src/bt_web_ui/templates/device.html — add editable alias field with HTMX PATCH on blur/enter, favorite toggle star with HTMX PATCH, notes textarea with save button via HTMX PATCH, delete from history button with confirmation dialog (Alpine.js), display first_seen and last_connected timestamps

**Checkpoint**: Devices persist across restarts. Users can customize device metadata. Combined with US1+US2, this delivers the complete device management experience with memory.

---

## Phase 6: User Story 4 — Themeable Interface (Priority: P4)

**Goal**: User can switch between light, dark, and auto themes from a settings page. Theme preference persists across sessions. The settings page also exposes scan duration and auto-connect configuration.

**Independent Test**: Open settings, switch from light to dark theme, verify the UI immediately changes colors, refresh the page, verify the dark theme is still active. Change scan duration, verify next scan uses the new duration.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T053 [P] [US4] Create API tests for settings endpoints in backend/tests/api/test_settings_api.py — test GET /api/settings returns current settings, test PATCH /api/settings updates theme to dark, test PATCH /api/settings validates scan_duration_seconds range (5-60), test PATCH /api/settings returns 422 for invalid theme value per contracts/rest-api.md
- [x] T054 [P] [US4] Create unit tests for AppSettings store in backend/tests/unit/test_device_store.py — test get_settings returns defaults on fresh DB, test update_settings persists theme change, test update_settings validates scan_duration_seconds range

### Implementation for User Story 4

- [x] T055 [US4] Extend device store with settings methods in backend/src/bt_web_ui/services/device_store.py — add get_settings() returning AppSettings with defaults, update_settings(partial) updating only provided fields, ensure singleton row (id=1) per data-model.md schema
- [x] T056 [US4] Implement settings API endpoints in backend/src/bt_web_ui/api/settings.py — GET /api/settings returning AppSettings, PATCH /api/settings accepting partial updates, validation for theme enum and scan_duration range, 422 on validation error per contracts/rest-api.md
- [x] T057 [US4] Create settings page template in backend/src/bt_web_ui/templates/settings.html — extends base.html, theme selector (light/dark/auto) with immediate preview via Alpine.js $store.theme, scan duration slider/input (5-60 seconds), auto-connect favorites toggle, save button with HTMX PATCH to /api/settings, success toast on save
- [x] T058 [US4] Implement theme switching in base.html and theme.css — Alpine.js theme store reading from /api/settings on load, writing to localStorage for instant application, data-theme attribute on html element, auto theme respecting prefers-color-scheme, theme toggle in nav bar for quick switching without visiting settings
- [x] T059 [US4] Implement HTML page route for settings in backend/src/bt_web_ui/api/settings.py — GET /settings serving settings.html template with current AppSettings data
- [x] T060 [US4] Wire scan duration setting into scan endpoints in backend/src/bt_web_ui/api/adapter.py — read scan_duration_seconds from AppSettings when starting scan instead of hardcoded default

**Checkpoint**: Full theming support with persistent preferences. Settings page controls application behavior. The interface is complete and customizable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T061 [P] Create D-Bus integration tests using python-dbusmock in backend/tests/integration/test_dbus_bluetooth.py — mock org.bluez service with Adapter1 and Device1 interfaces, test full discovery → pair → connect flow against mock D-Bus, test PropertiesChanged signal handling, test error scenarios (adapter removed, permission denied)
- [ ] T062 [P] Add structured logging throughout backend/src/bt_web_ui/ — configure Python logging with JSON format in main.py, add log statements to BlueZManager (adapter state, discovery events, pairing, connection), device_store (DB operations), API endpoints (request/response), WebSocket (connect/disconnect/events)
- [ ] T063 Run mypy type checking across entire backend/src/bt_web_ui/ in strict mode — fix any type errors, ensure all function signatures are fully annotated, verify Pydantic model types are correct
- [ ] T064 Run ruff linter and formatter across entire backend/ — fix any style violations, ensure consistent formatting, verify no unused imports or dead code per Constitution Principle I
- [ ] T065 [P] Create data/ directory with .gitkeep, add data/*.db to .gitignore, ensure SQLite database path is created automatically on first run in device_store.init_db()
- [ ] T066 Run quickstart.md validation — follow quickstart.md steps to verify installation works, app starts, tests pass, and all documented commands produce expected output
- [ ] T067 [P] Review all error responses across API endpoints for consistent format per contracts/rest-api.md — verify every endpoint returns {error, message} on failure with correct HTTP status codes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase — delivers MVP
- **User Story 2 (Phase 4)**: Depends on Foundational phase — can run in parallel with US1 but logically extends it (US1 provides scan, US2 adds device actions)
- **User Story 3 (Phase 5)**: Depends on Foundational phase — requires US1/US2 device operations to persist
- **User Story 4 (Phase 6)**: Depends on Foundational phase — can start in parallel (mostly independent UI/settings work)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. Delivers scan + discovery.
- **US2 (P2)**: Can start after Foundational (Phase 2) — Uses adapter/scan from US1 but is independently testable. Delivers pair + connect.
- **US3 (P3)**: Can start after Foundational (Phase 2) — Integrates with US1/US2 device events for persistence triggers. Independently testable via direct store operations.
- **US4 (P4)**: Can start after Foundational (Phase 2) — Fully independent (settings and theme only). No dependencies on other stories.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before API endpoints
- API endpoints before templates
- Templates before page routes

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005, T006, T007)
- Foundational models can run in parallel (T010 + T011 + T012 after T009)
- Foundational tests can run in parallel (T018, T019)
- All test tasks within a user story can run in parallel
- US4 can be developed entirely in parallel with US1/US2/US3
- CSS files (T028, T029) can be developed in parallel with backend tasks
- Template partials (T032, T033, T034) can be developed in parallel

---

## Parallel Examples

### Phase 1: Setup (all independent)

```bash
Task: "Create requirements.txt at backend/requirements.txt"
Task: "Create requirements-dev.txt at backend/requirements-dev.txt"
Task: "Create .gitignore at repository root"
Task: "Vendor HTMX library to backend/src/static/js/htmx.min.js"
Task: "Vendor Alpine.js library to backend/src/static/js/alpine.min.js"
```

### Phase 2: Foundational models (after T009)

```bash
Task: "Implement Device and DeviceRuntimeState models in backend/src/bt_web_ui/models/device.py"
Task: "Implement AdapterState model in backend/src/bt_web_ui/models/device.py"
Task: "Implement AppSettings model in backend/src/bt_web_ui/models/settings.py"
```

### Phase 3: US1 tests (all independent)

```bash
Task: "Create unit tests for BlueZ bluetooth service"
Task: "Create API tests for adapter endpoints"
Task: "Create API tests for scan endpoints"
Task: "Create integration tests for WebSocket events"
```

### Phase 3: US1 CSS + partials (independent of backend)

```bash
Task: "Create CSS theme file in backend/src/static/css/theme.css"
Task: "Create main CSS file in backend/src/static/css/main.css"
Task: "Create device card partial"
Task: "Create status badge partial"
Task: "Create toast notification partial"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Open web UI, verify adapter status, scan, see devices
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP: scan + discover)
3. Add User Story 2 → Test independently → Deploy/Demo (pair + connect)
4. Add User Story 3 → Test independently → Deploy/Demo (device memory)
5. Add User Story 4 → Test independently → Deploy/Demo (theming + settings)
6. Each story adds value without breaking previous stories

### Recommended Sequential Path

For a single developer:

1. Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (US4) → Phase 7

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests MUST fail before implementing (Constitution Principle II)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
