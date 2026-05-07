import uuid
import logging
from fastapi import APIRouter
from backend.models import ExecuteRequest

logger = logging.getLogger(__name__)
router = APIRouter()

# Global reference to the WebSocket manager (set by ws/task.py)
ws_manager = None


@router.post("/execute")
async def execute(req: ExecuteRequest):
    from backend.ws.task import ws_manager as wsm, TASKS
    task_id = str(uuid.uuid4())[:8]
    TASKS[task_id] = {
        "device_ips": req.device_ips,
        "commands": req.commands,
        "max_concurrent": req.max_concurrent,
        "status": "pending",
    }
    # Trigger background execution
    from backend.executor.engine import run_task
    import asyncio
    asyncio.create_task(run_task(task_id, req.device_ips, req.commands, req.max_concurrent))
    return {"task_id": task_id}
