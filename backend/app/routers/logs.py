from fastapi import APIRouter, Query

from app.schemas import SyncLogRead
from app.repositories import repository

router = APIRouter()


@router.get("/sync", response_model=list[SyncLogRead])
def sync_logs(range: str | None = Query(None)):
    return repository.list_logs(range)

