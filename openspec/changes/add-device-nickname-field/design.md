## Context

Devices are identified by IP everywhere: device table, result cards, terminal event log, modal, and archive filenames. IPs are hard for operators to map mentally to physical devices. The proposal adds an optional `nickname` CSV column to solve this. The implementation spans backend model/parsing/WS and frontend table/cards/terminal/modal.

Current state:
- `Device` Pydantic model has no `nickname` field
- CSV parser (`inventory.py`) reads fixed columns; unknown columns are ignored by pandas silently
- `DeviceResponse` / `_to_response()` explicitly enumerates fields returned to frontend
- WebSocket messages carry `device_ip` as the primary identifier; `device_start` also includes `device_type` and `area`
- Frontend `deviceStates` is keyed by IP (`reactive({})`) and result cards iterate `Object.keys` / `Object.entries`
- DeviceTable filtering searches only `d.ip`; columns are IP, Type, Area, Proto
- Modal title shows IP (`currentModalIp`); export download filename uses IP
- Archive device files named `{ip}_{type}.md`, summary JSON entries keyed by IP

## Goals / Non-Goals

**Goals:**
- Add `nickname` to CSV parsing, Pydantic model, API response, and WebSocket payloads
- Show nickname as the primary label in DeviceTable (leftmost column), result cards, terminal log, and modal title
- Fallback to IP everywhere when nickname is empty/missing — no regressions for existing data
- Keyword search in DeviceTable also matches nickname text

**Non-Goals:**
- Nickname uniqueness enforcement — duplicates are harmless, just confusing for operators (can add later)
- Nickname editing in the UI — CSV upload is the only mutation path
- Nickname in archive filenames (keep `{ip}_{type}.md` for filesystem safety; include nickname in the Markdown content and summary JSON)
- Frontend backup restoration or any new UI chrome

## Decisions

### 1. Nickname as optional string, empty default

All existing CSVs lack a `nickname` column. `df.fillna('')` already handles missing columns → empty string. No migration, no schema versioning. The field is `str = ""` in Pydantic, `nickname || ip` fallback is a frontend-only display concern.

**Alternative considered**: Make nickname required → breaks existing CSVs, requires migration scripts, adds friction for zero benefit since IP is always a valid fallback identifier.

### 2. Nickname passed in WebSocket messages, not looked up on frontend

Backend already has the `dev` object when sending `device_start`. Add `device_nickname` to `device_start`, `device_done`, `device_error` messages. Frontend stores it in `deviceStates[ip].nickname` and uses it for display.

**Alternative considered**: Frontend looks up nickname from `devices[]` by IP → fragile when inventory reloads mid-task, and requires frontend-side join logic in multiple places (cards, terminal, modal).

### 3. DeviceStates stays keyed by IP

`deviceStates` remains `reactive({})` keyed by IP. IP is the stable unique key (nickname can duplicate, be empty, or change across uploads). Nickname is just a display attribute stored per-entry: `deviceStates[ip].nickname`.

**Alternative considered**: Key by nickname → breaks when nickname is empty or duplicates exist. Non-starter.

### 4. Display helper pattern: `displayName(nickname, ip)` → `nickname || ip`

A single pure function used everywhere: result cards, terminal log lines, modal title. Avoids scattered `||` checks that could diverge.

**Alternative considered**: Compute `displayName` once at store time → ip-only entries (early `device_output`) would show IP initially then never update to nickname once `device_start` arrives later. Computing at display time handles out-of-order message arrival correctly.

### 5. DeviceTable column order: Nickname → IP (was: IP first)

Nickname is the human-facing identifier, so it goes leftmost. IP stays as the second column for technical reference.

## Risks / Trade-offs

- **[Risk] Frontend display name computed from `deviceStates[ip].nickname`, but `device_output` can arrive before `device_start`** → `device_output` handler already creates a stub entry; the stub won't have `nickname` until `device_start` arrives. Mitigation: display helper falls back to IP when nickname is undefined/empty, so cards show IP briefly then update to nickname when `device_start` fires. Vue reactivity handles this automatically since we mutate the existing key.

- **[Risk] Nickname changes between task runs** → If user uploads a new CSV mid-session with different nicknames, the `deviceStates` from a prior task will show stale nicknames. Mitigation: Acceptable — task results reflect the state at execution time. Clearing `deviceStates` on each new execute (already done) ensures the next task picks up current nicknames via new WS messages.

- **[Trade-off] Archive filenames stay `{ip}_{type}.md` not `{nickname}_{type}.md`** → Nicknames may contain spaces, special chars, or be empty. Using IP for filenames avoids filesystem escaping complexity and ensures stable paths.
