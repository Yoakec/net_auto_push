import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

TASKS = {}

class WsManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    def register(self, task_id: str, ws: WebSocket):
        self.connections.setdefault(task_id, []).append(ws)

    def unregister(self, task_id: str, ws: WebSocket):
        if task_id in self.connections:
            self.connections[task_id].remove(ws)

    async def send(self, task_id: str, msg: dict):
        for ws in self.connections.get(task_id, []):
            try:
                await ws.send_json(msg)
            except Exception:
                pass

ws_manager = WsManager()

router = APIRouter()


@router.websocket("/ws/task/{task_id}")
async def ws_task(ws: WebSocket, task_id: str):
    await ws.accept()
    ws_manager.register(task_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.unregister(task_id, ws)
