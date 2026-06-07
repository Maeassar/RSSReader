from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile

from app.schemas import OPMLImportReport
from app.services import opml_service

router = APIRouter()


@router.post("/import", response_model=OPMLImportReport)
async def import_opml(
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
):
    try:
        upload_files = list(files or [])
        if file is not None:
            upload_files.append(file)
        if not upload_files:
            raise ValueError("No OPML files uploaded.")
        return await opml_service.import_opml(upload_files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/export")
def export_opml(feed_ids: list[int] | None = Query(default=None)):
    try:
        return Response(content=opml_service.export_opml(feed_ids), media_type="application/xml")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

