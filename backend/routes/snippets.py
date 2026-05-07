import csv
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging

from backend.models import SnippetItem
from backend.config import DATA_DIR

logger = logging.getLogger(__name__)
router = APIRouter()

snippets: List[SnippetItem] = []


def load_snippets_on_startup():
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "commands.csv")
    if not os.path.exists(path):
        logger.info("No commands.csv found, snippet library empty")
        return
    try:
        loaded = []
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cmd = row.get('command', '').strip()
                if not cmd:
                    continue
                loaded.append(SnippetItem(
                    command=cmd,
                    category=row.get('category', '').strip(),
                ))
        snippets.clear()
        snippets.extend(loaded)
        logger.info(f"Loaded {len(snippets)} snippets from commands.csv")
    except Exception as e:
        logger.error(f"Failed to load commands.csv: {e}")


@router.get("/snippets")
async def get_snippets():
    return [s.model_dump() for s in snippets]


@router.post("/upload/snippets")
async def upload_snippets(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=422, detail="Only CSV files are accepted")
    content = await file.read()
    save_path = os.path.join(DATA_DIR, "commands.csv")
    with open(save_path, 'wb') as f:
        f.write(content)
    load_snippets_on_startup()
    return {"status": "ok", "count": len(snippets), "snippets": [s.model_dump() for s in snippets]}
