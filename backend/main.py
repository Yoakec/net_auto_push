import os
import sys
import logging
import webbrowser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Add project root to path for direct python execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import FRONTEND_DIST
from backend.routes.inventory import router as inventory_router, load_devices_on_startup
from backend.routes.snippets import router as snippets_router, load_snippets_on_startup
from backend.routes.execute import router as execute_router
from backend.routes.archives import router as archives_router
from backend.ws.task import router as ws_router

app = FastAPI(title="Net Auto Push")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory_router, prefix="/api")
app.include_router(snippets_router, prefix="/api")
app.include_router(execute_router, prefix="/api")
app.include_router(archives_router, prefix="/api")
app.include_router(ws_router)


@app.on_event("startup")
async def startup():
    load_devices_on_startup()
    load_snippets_on_startup()
    # Auto-open browser on startup (for PyInstaller deployment)
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
