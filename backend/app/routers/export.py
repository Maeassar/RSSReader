from fastapi import APIRouter, Response

from app.schemas import ExportRequest
from app.services import export_service

router = APIRouter()


@router.get("/articles/{article_id}/markdown")
def export_article(article_id: int):
    return Response(content=export_service.article_markdown(article_id), media_type="text/markdown")


@router.post("/articles/markdown")
def export_articles(payload: ExportRequest):
    return Response(content=export_service.articles_markdown(payload.article_ids), media_type="text/markdown")

