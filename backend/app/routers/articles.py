from fastapi import APIRouter, HTTPException, Query

from app.schemas import ArticleRead
from app.services import article_service

router = APIRouter()


@router.get("", response_model=list[ArticleRead])
def list_articles(
    feed_id: int | None = None,
    tag_id: int | None = None,
    unread: bool | None = Query(default=None),
    starred: bool | None = Query(default=None),
):
    return article_service.list_articles(feed_id=feed_id, tag_id=tag_id, unread=unread, starred=starred)


@router.get("/{article_id}", response_model=ArticleRead)
def get_article(article_id: int):
    try:
        return article_service.get_article(article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{article_id}/refresh-content", response_model=ArticleRead)
def refresh_article_content(article_id: int):
    try:
        return article_service.refresh_article_content(article_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{article_id}/read", response_model=ArticleRead)
def mark_read(article_id: int, is_read: bool = True):
    return article_service.mark_read(article_id, is_read)


@router.patch("/{article_id}/star", response_model=ArticleRead)
def mark_starred(article_id: int, is_starred: bool = True):
    return article_service.mark_starred(article_id, is_starred)
