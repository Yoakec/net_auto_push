# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
# Backend (Python virtualenv required — project root)
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Frontend dev server (hot reload, proxies /api and /ws to :8000)
cd frontend && npm run dev        # → localhost:5173

# Frontend production build → frontend/dist/
cd frontend && npm run build

# PyInstaller .exe (requires frontend/dist/ built first)
pyinstaller build.spec
```

`npm run build` must run before uvicorn serves the frontend — the backend mounts `frontend/dist/` as static files only if the directory exists.

## Architecture

**Purpose**: Single-user Windows tool for batch SSH command execution against network switches (Huawei/Cisco). CSV device inventory, multi-device concurrent execution via netmiko, WebSocket real-time output, Xterm.js terminal, Markdown result archiving. No database.

### Backend (FastAPI)

```
backend/
├── main.py              # App entry: CORS, route registration, static mount, browser auto-open
├── config.py            # Paths (DATA_DIR, ARCHIVES_DIR), SSH_TIMEOUT=15, DEFAULT_MAX_CONCURRENT=5
├── models.py            # Pydantic: Device, ExecuteRequest, SnippetItem
├── archiver.py          # Task completion → /archives/<timestamp>_Task/<ip>_<type>.md + task_summary.json
├── routes/
│   ├── inventory.py     # CSV→in-memory devices list, GET /api/inventory (no password), POST /api/upload
│   ├── execute.py       # POST /api/execute → asyncio.create_task(run_task(...)), returns task_id
│   ├── snippets.py      # commands.csv→snippets list, GET /api/snippets, POST /api/upload/snippets
│   └── archives.py      # GET /api/archives
├── executor/
│   ├── engine.py        # asyncio.Semaphore + ThreadPoolExecutor(20) → gather per-device coroutines
│   └── device.py        # netmiko ConnectHandler, "screen-length 0 disable", fail-fast per device
└── ws/
    └── task.py           # WebSocket /ws/task/{task_id}, WsManager broadcasts to registered clients
```

**Route prefix convention**: REST routes use `/api` prefix via `app.include_router(router, prefix="/api")`. WebSocket route has no prefix (`/ws/task/{task_id}`).

**Device CSV columns**: `ip`, `Type`, `username`, `password`, `Protocol` (ssh/telnet), `port`, `Area`, `encode`. The `password` field is stripped in all API responses.

**Execution flow**:
1. `POST /api/execute` creates task entry, spawns `run_task` as background coroutine, returns `task_id`
2. `run_task` sends `device_start` → runs netmiko in thread pool → streams `device_output` per command → sends `device_done` or `device_error` → sends `task_progress` → `task_complete`
3. On `task_complete`, `archiver.archive_task` writes Markdown files

**WebSocket message protocol** (6 types, JSON):
- `device_start` — connection established, card created on frontend
- `device_output` — raw command output (NOT displayed in main terminal, routed to result store)
- `device_done` / `device_error` — per-device completion/failure
- `task_progress` / `task_complete` — aggregate progress

**Module-level list pattern**: `inventory.py` and `snippets.py` hold data in module-level lists. Startup functions MUST mutate in-place with `list.clear()` + `list.extend()` — reassigning the name silently breaks imports in other modules that hold a reference to the original list object.

### Frontend (Vue 3 + Vite + Tailwind + Xterm.js)

```
frontend/src/
├── App.vue              # ALL core logic: Xterm.js terminal init, WebSocket handler, result cards (inline)
└── components/
    ├── DeviceTable.vue  # Filterable device table (Area/Type dropdowns, IP search, checkboxes)
    ├── CommandInput.vue # Multi-line textarea, snippet dropdown (grouped by category), execute button
    ├── OutputModal.vue  # Modal with Xterm.js instance for per-device pure command output, tab switching
    └── ProgressBar.vue  # Header progress bar
```

**Layout**: 30/70 flex split. Left: DeviceTable + CommandInput. Right: Xterm.js main terminal (event log) + result cards strip at bottom.

**Key architectural decisions**:
- Terminal and result cards are **inline in App.vue**, not separate components. This was done intentionally after reactivity issues with prop-passing across component boundaries.
- Only **one WebSocket connection** exists (managed by App.vue). Never open a second WS inside a child component — it causes message duplication and state mismatches.
- `deviceResults` uses `ref([])` (array ref), mutated with `.push()` and direct property assignment (`r.status = 'success'`). Do NOT use `reactive({})` with dynamic keys for result storage.

**Vite dev proxy** (vite.config.js): `/api` → `http://localhost:8000`, `/ws` → `ws://localhost:8000`.

## Data Files

- `data/devices.csv` — device inventory (loaded on startup, survives across restarts)
- `data/commands.csv` — snippet library with optional `category` column
- `archives/<timestamp>_Task/` — per-task result archive (auto-generated on completion)
