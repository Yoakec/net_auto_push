import csv
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging

from backend.models import Device, DeviceResponse
from backend.config import DATA_DIR
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()

devices: List[Device] = []


def load_devices_on_startup():
    os.makedirs(DATA_DIR, exist_ok=True)
    loaded = []
    for fname in os.listdir(DATA_DIR):
        if fname.lower().endswith('.csv'):
            fpath = os.path.join(DATA_DIR, fname)
            loaded.extend(_parse_csv(fpath))
    devices.clear()
    devices.extend(loaded)
    logger.info(f"Loaded {len(devices)} devices from /data/")


def _parse_csv(path: str) -> List[Device]:
    rows = []
    try:
        df = pd.read_csv(path)
        df = df.fillna('')
        for _, row in df.iterrows():
            if not str(row.get('ip', '')).strip():
                continue
            rows.append(Device(
                nickname=str(row.get('nickname', '')).strip(),
                ip=str(row['ip']).strip(),
                type=str(row.get('Type', row.get('type', ''))).strip(),
                username=str(row.get('username', '')).strip(),
                password=str(row.get('password', '')).strip(),
                protocol=str(row.get('Protocol', row.get('protocol', 'ssh'))).strip() or 'ssh',
                port=int(row.get('port', 22)) if str(row.get('port', '')).strip() else 22,
                area=str(row.get('Area', row.get('area', ''))).strip(),
                encode=str(row.get('encode', 'utf-8')).strip() or 'utf-8',
            ))
    except Exception as e:
        logger.error(f"Failed to parse CSV {path}: {e}")
    return rows


def _to_response(d: Device) -> dict:
    return {
        "nickname": d.nickname,
        "ip": d.ip,
        "type": d.type,
        "username": d.username,
        "protocol": d.protocol,
        "port": d.port,
        "area": d.area,
        "encode": d.encode,
    }


@router.get("/inventory")
async def get_inventory():
    return [_to_response(d) for d in devices]


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=422, detail="Only CSV files are accepted")
    content = await file.read()
    save_path = os.path.join(DATA_DIR, file.filename)
    with open(save_path, 'wb') as f:
        f.write(content)
    load_devices_on_startup()
    return {"status": "ok", "count": len(devices), "devices": [_to_response(d) for d in devices]}
