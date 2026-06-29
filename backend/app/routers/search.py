from fastapi import APIRouter, HTTPException, Query

from app.schemas import SearchResultRead
from app.repositories.sqlite_repository import repository

router = APIRouter()


@router.get("", response_model=list[SearchResultRead])
def search_articles(
    q: str = Query(min_length=1, description="搜索关键词"),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return repository.search_articles(q, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
