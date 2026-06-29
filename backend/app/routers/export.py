from fastapi import APIRouter, HTTPException, Response

from app.schemas import BatchDigestExportRequest, BatchDigestExportResponse, ExportRequest
from app.services import export_service

router = APIRouter()


@router.get("/articles/{article_id}/markdown")
def export_article(article_id: int):
    return Response(content=export_service.article_markdown(article_id), media_type="text/markdown")


@router.post("/articles/markdown")
def export_articles(payload: ExportRequest):
    return Response(content=export_service.articles_markdown(payload.article_ids), media_type="text/markdown")


@router.post("/digests/markdown", response_model=BatchDigestExportResponse)
def export_batch_digest(payload: BatchDigestExportRequest):
    try:
        return export_service.batch_digest_export(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
