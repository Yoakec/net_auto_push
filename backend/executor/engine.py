import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from backend.ws.task import ws_manager, TASKS

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=20)


async def run_task(task_id: str, device_ips: list[str], commands: list[str], max_concurrent: int):
    from backend.executor.device import run_device_commands
    from backend.routes.inventory import devices

    sem = asyncio.Semaphore(max_concurrent)
    total = len(device_ips)
    completed = 0
    failed = 0
    device_results = []

    TASKS[task_id] = {"status": "running"}

    async def run_one(ip: str):
        nonlocal completed, failed
        async with sem:
            dev = next((d for d in devices if d.ip == ip), None)
            await ws_manager.send(task_id, {
                "type": "device_start",
                "device_ip": ip,
                "device_nickname": dev.nickname if dev else "",
                "device_type": dev.type if dev else "unknown",
                "area": dev.area if dev else "",
            })

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(_executor, run_device_commands, ip, commands)
            result["ip"] = ip

            if result["status"] == "success":
                for cmd, output in result["outputs"].items():
                    await ws_manager.send(task_id, {
                        "type": "device_output",
                        "device_ip": ip,
                        "command": cmd,
                        "data": output,
                        "stream": "stdout",
                    })
                await ws_manager.send(task_id, {
                    "type": "device_done",
                    "device_ip": ip,
                    "device_nickname": dev.nickname if dev else "",
                    "status": "success",
                    "duration_ms": result["duration_ms"],
                })
            else:
                await ws_manager.send(task_id, {
                    "type": "device_error",
                    "device_ip": ip,
                    "device_nickname": dev.nickname if dev else "",
                    "error": result["error"],
                })
                failed += 1

            completed += 1
            device_results.append(result)
            await ws_manager.send(task_id, {
                "type": "task_progress",
                "total": total,
                "completed": completed,
                "running": total - completed,
                "failed": failed,
            })

    await asyncio.gather(*[run_one(ip) for ip in device_ips])

    await ws_manager.send(task_id, {
        "type": "task_complete",
        "total": total,
        "success": total - failed,
        "failed": failed,
    })

    # Archive results
    from backend.archiver import archive_task
    try:
        archive_task(task_id, commands, device_results)
    except Exception as e:
        logger.error(f"Failed to archive task {task_id}: {e}")

    TASKS[task_id]["status"] = "complete"
