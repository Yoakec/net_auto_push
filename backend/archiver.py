import os
import json
import logging
from datetime import datetime

from backend.config import ARCHIVES_DIR
from backend.routes.inventory import devices

logger = logging.getLogger(__name__)


def archive_task(task_id: str, commands: list[str], device_results: list[dict]):
    """Generate archive directory with device Markdown files and task_summary.json."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dirname = f"{timestamp}_Task"
    archive_dir = os.path.join(ARCHIVES_DIR, dirname)

    # Handle naming collision
    counter = 1
    while os.path.exists(archive_dir):
        counter += 1
        archive_dir = os.path.join(ARCHIVES_DIR, f"{timestamp}_Task_{counter}")

    os.makedirs(archive_dir, exist_ok=True)

    success_count = 0
    failed_count = 0
    device_entries = []

    for result in device_results:
        ip = result["ip"]
        dev = next((d for d in devices if d.ip == ip), None)
        dev_type = dev.type if dev else "unknown"
        area = dev.area if dev else ""
        status = result.get("status", "unknown")
        duration_ms = result.get("duration_ms", 0)

        if status == "success":
            success_count += 1
        elif status == "failed":
            failed_count += 1

        device_entries.append({
            "ip": ip,
            "type": dev_type,
            "area": area,
            "status": status,
            "duration_ms": duration_ms,
        })

        # Generate device Markdown file
        md_path = os.path.join(archive_dir, f"{ip}_{dev_type}.md")
        _write_device_md(md_path, ip, dev_type, area, result, commands)

    # Generate task_summary.json
    summary = {
        "task_id": task_id,
        "started_at": datetime.now().isoformat(),
        "finished_at": datetime.now().isoformat(),
        "commands": commands,
        "devices": device_entries,
        "summary": {
            "total": len(device_results),
            "success": success_count,
            "failed": failed_count,
        },
    }
    summary_path = os.path.join(archive_dir, "task_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Archived task {task_id} to {archive_dir}")
    return archive_dir


def _write_device_md(path: str, ip: str, dev_type: str, area: str, result: dict, commands: list[str]):
    """Write a per-device Markdown file organized by command."""
    lines = []
    lines.append(f"# {ip} ({dev_type})")
    lines.append("")
    lines.append(f"- **Area**: {area}")
    lines.append(f"- **Status**: {result.get('status', 'unknown')}")
    lines.append(f"- **Duration**: {result.get('duration_ms', 0)}ms")
    lines.append("")

    outputs = result.get("outputs", {})
    for cmd in commands:
        lines.append(f"## {cmd}")
        lines.append("")
        if cmd in outputs:
            lines.append("```")
            lines.append(outputs[cmd])
            lines.append("```")
        else:
            lines.append("_(no output)_")
        lines.append("")

    if result.get("status") == "failed" and result.get("error"):
        lines.append("## Error")
        lines.append("")
        lines.append(f"```")
        lines.append(result["error"])
        lines.append(f"```")
        lines.append("")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def list_archives() -> list[dict]:
    """Return list of archive summaries."""
    os.makedirs(ARCHIVES_DIR, exist_ok=True)
    archives = []
    for dirname in sorted(os.listdir(ARCHIVES_DIR), reverse=True):
        dirpath = os.path.join(ARCHIVES_DIR, dirname)
        if not os.path.isdir(dirpath):
            continue
        summary_path = os.path.join(dirpath, "task_summary.json")
        if os.path.exists(summary_path):
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                archives.append({
                    "task_id": data.get("task_id", ""),
                    "started_at": data.get("started_at", ""),
                    "finished_at": data.get("finished_at", ""),
                    "total": data.get("summary", {}).get("total", 0),
                    "success": data.get("summary", {}).get("success", 0),
                    "failed": data.get("summary", {}).get("failed", 0),
                    "device_count": len(data.get("devices", [])),
                })
            except Exception as e:
                logger.warning(f"Failed to read archive summary from {summary_path}: {e}")
    return archives
