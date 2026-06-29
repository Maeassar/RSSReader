from fastapi import APIRouter, HTTPException

from app.schemas import (
    ArticleRead,
    FeedBatchDeleteReport,
    FeedBatchDeleteRequest,
    FeedCreate,
    FeedCreateResult,
    FeedRead,
    FeedSyncReport,
    FeedUpdate,
    OperationResult,
)
from app.services import article_service
from app.services import feed_service

router = APIRouter()


@router.get("", response_model=list[FeedRead])
def list_feeds():
    return feed_service.list_feeds()


@router.post("", response_model=FeedCreateResult)
def create_feed(payload: FeedCreate):
    try:
        return feed_service.create_feed(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sync-all", response_model=FeedSyncReport)
def sync_all_feeds():
    return feed_service.sync_all_feeds()


@router.post("/batch-delete", response_model=FeedBatchDeleteReport)
def batch_delete_feeds(payload: FeedBatchDeleteRequest):
    return feed_service.delete_feeds(payload.feed_ids)


@router.get("/{feed_id}", response_model=FeedRead)
def get_feed(feed_id: int):
    try:
        return feed_service.get_feed(feed_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{feed_id}", response_model=FeedRead)
def update_feed(feed_id: int, payload: FeedUpdate):
    try:
        return feed_service.update_feed(feed_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{feed_id}", response_model=OperationResult)
def delete_feed(feed_id: int):
    try:
        feed_service.delete_feed(feed_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OperationResult(message="Feed deleted.")


@router.post("/{feed_id}/sync", response_model=FeedRead)
def sync_feed(feed_id: int):
    try:
        return feed_service.sync_feed(feed_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{feed_id}/entries", response_model=list[ArticleRead])
def list_feed_entries(feed_id: int):
    try:
        feed_service.get_feed(feed_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return article_service.list_full_articles(feed_id=feed_id)

