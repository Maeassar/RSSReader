from fastapi import APIRouter, File, Response, UploadFile

from app.services import opml_service

router = APIRouter()


@router.post("/import")
async def import_opml(file: UploadFile = File(...)):
    return await opml_service.import_opml(file)


@router.get("/export")
def export_opml():
    return Response(content=opml_service.export_opml(), media_type="application/xml")

