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

    # If task doesn't exist yet, send simulated logs (for testing the channel)
    if task_id not in TASKS or TASKS[task_id].get("status") == "pending":
        asyncio.create_task(_send_simulated_logs(ws, task_id))

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.unregister(task_id, ws)


async def _send_simulated_logs(ws: WebSocket, task_id: str):
    """Send simulated event stream for testing WebSocket channel."""
    try:
        for i in range(1, 6):
            await ws.send_json({"type": "task_progress", "total": 5, "completed": i, "running": 1, "failed": 0})
            await ws.send_json({
                "type": "device_output",
                "device_ip": f"10.0.0.{i}",
                "command": "show arp",
                "data": f"Simulated output line {i}\n",
                "stream": "stdout"
            })
            await asyncio.sleep(1)
        await ws.send_json({"type": "task_complete", "total": 5, "success": 5, "failed": 0})
    except Exception:
        pass
