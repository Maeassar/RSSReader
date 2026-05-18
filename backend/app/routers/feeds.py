from fastapi import APIRouter, HTTPException

from app.schemas import FeedCreate, FeedRead, FeedUpdate, OperationResult
from app.services import feed_service

router = APIRouter()


@router.get("", response_model=list[FeedRead])
def list_feeds():
    return feed_service.list_feeds()


@router.post("", response_model=FeedRead)
def create_feed(payload: FeedCreate):
    return feed_service.create_feed(payload)


@router.put("/{feed_id}", response_model=FeedRead)
def update_feed(feed_id: int, payload: FeedUpdate):
    try:
        return feed_service.update_feed(feed_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{feed_id}", response_model=OperationResult)
def delete_feed(feed_id: int):
    feed_service.delete_feed(feed_id)
    return OperationResult(message="Feed deleted from mock repository.")


@router.post("/{feed_id}/sync", response_model=FeedRead)
def sync_feed(feed_id: int):
    try:
        return feed_service.sync_feed(feed_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sync-all", response_model=list[FeedRead])
def sync_all_feeds():
    return feed_service.sync_all_feeds()

