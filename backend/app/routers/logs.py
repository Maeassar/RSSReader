from fastapi import APIRouter

from app.schemas import SyncLogRead
from app.repositories import repository

router = APIRouter()


@router.get("/sync", response_model=list[SyncLogRead])
def sync_logs():
    return repository.list_logs()

