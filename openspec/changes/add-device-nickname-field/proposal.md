## Why

Devices are currently identified only by IP address everywhere in the UI — table, result cards, terminal log, and modal. Operators think in terms of device names/roles ("Core-SW-01", "Access-3F-East"), not IPs. Adding a human-readable nickname field makes device identification immediate and reduces operational errors (running commands on the wrong device because IPs all look similar).

## What Changes

- Add optional `nickname` column to `data/devices.csv` — empty if not set, no migration needed for existing CSVs
- Backend: include `nickname` in `GET /api/inventory` response and `POST /api/upload` parsing; password-stripping logic unchanged
- Backend: pass `nickname` in WebSocket messages (`device_start`, `device_done`, `device_error`) so frontend can use it
- Frontend DeviceTable: show `nickname` column (leftmost, before IP); keyword search also matches against nickname
- Frontend result cards: display nickname as primary label, IP as secondary subtitle; fall back to IP when nickname is empty
- Frontend terminal event log: show nickname in log lines (e.g., `[Core-SW-01] [OK] connected`) with IP fallback
- Frontend modal title: show nickname in modal header when viewing device output
- **BREAKING**: None — nickname is optional, all existing CSVs and API consumers continue to work

## Capabilities

### New Capabilities

None. This change modifies existing behavior without introducing new capability boundaries.

### Modified Capabilities

- `device-inventory`: CSV column schema gains optional `nickname` field; API response and upload flow include nickname; keyword search scope expands to nickname
- `live-terminal`: Result cards, terminal event log, and modal display use nickname as primary identifier with IP fallback

## Impact

- **Backend files**: `backend/config.py` (column list), `backend/routes/inventory.py` (load/parse/return), `backend/executor/engine.py` (WebSocket message payloads), `backend/models.py` (Device model), `backend/archiver.py` (archive device filenames)
- **Frontend files**: `frontend/src/components/DeviceTable.vue` (new column + search), `frontend/src/App.vue` (result card labels, terminal log format, modal title)
- **Data files**: Existing `data/devices.csv` files remain valid (nickname defaults to empty string)
- **No new dependencies**, no API breaking changes
