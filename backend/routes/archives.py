from fastapi import APIRouter
from backend.archiver import list_archives

router = APIRouter()


@router.get("/archives")
async def get_archives():
    return list_archives()
