## 1. Backend: Model and data layer

- [x] 1.1 Add `nickname: str = ""` field to `Device` and `DeviceResponse` Pydantic models in `backend/models.py`
- [x] 1.2 Parse `nickname` column in `backend/routes/inventory.py` `_parse_csv()` function with `str(row.get('nickname', '')).strip()`
- [x] 1.3 Include `nickname` in `_to_response()` dict for `GET /api/inventory` and `POST /api/upload` responses

## 2. Backend: WebSocket and archiver

- [x] 2.1 Pass `device_nickname` in `device_start` WebSocket message from `backend/executor/engine.py`
- [x] 2.2 Pass `device_nickname` in `device_done` and `device_error` WebSocket messages from `backend/executor/engine.py`
- [x] 2.3 Include nickname in archive Markdown files (`_write_device_md` header and metadata) and `task_summary.json` device entries in `backend/archiver.py`

## 3. Frontend: Device table

- [x] 3.1 Add `nickname` column (leftmost, before IP) to `frontend/src/components/DeviceTable.vue` table header and body
- [x] 3.2 Update search logic so keyword matches against both `d.nickname` and `d.ip`
- [x] 3.3 Update search placeholder text from "Search IP..." to "Search..."

## 4. Frontend: Result cards, terminal, and modal

- [x] 4.1 Store `nickname` from WebSocket messages in `deviceStates[ip]` (in `device_start`, `device_done`, `device_error` handlers)
- [x] 4.2 Add `displayLabel(ip)` helper that returns `nickname || ip` and use it in result card primary label, showing IP as subtitle when nickname is non-empty
- [x] 4.3 Update terminal log lines (`device_start`, `device_done`, `device_error`) to use `displayLabel` instead of raw IP
- [x] 4.4 Update modal title (`currentModalIp` display) to show nickname as primary title with IP subtitle, and update export filename to use nickname with IP fallback

## 5. Verification

- [x] 5.1 Verify existing CSV without nickname column still loads correctly (backward compatibility)
- [x] 5.2 Verify CSV with nickname column loads and nicknames appear in API response, table, cards, terminal, and modal
- [x] 5.3 Verify `npm run build` succeeds with no regressions
