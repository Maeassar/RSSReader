import json

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas import OPMLImportReport
from app.services import opml_service

router = APIRouter()


class BufferedUploadFile:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


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


@router.post("/import/stream")
async def import_opml_stream(
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
):
    upload_files = list(files or [])
    if file is not None:
        upload_files.append(file)
    if not upload_files:
        raise HTTPException(status_code=400, detail="No OPML files uploaded.")

    buffered_files = [
        BufferedUploadFile(upload_file.filename or "subscriptions.opml", await upload_file.read())
        for upload_file in upload_files
    ]
    parsed_items = await opml_service.parse_opml_uploads(buffered_files)

    async def event_stream():
        results = []
        yield _sse(
            {
                "type": "parsed",
                "items": parsed_items,
                "report": opml_service._build_import_report(len(buffered_files), parsed_items),
            }
        )
        async for item in opml_service.import_opml_items(parsed_items=parsed_items):
            results.append(item)
            yield _sse(
                {
                    "type": "item",
                    "item": item,
                    "report": opml_service._build_import_report(len(buffered_files), results),
                }
            )
        yield _sse(
            {
                "type": "done",
                "report": opml_service._build_import_report(len(buffered_files), results),
            }
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/export")
def export_opml(feed_ids: list[int] | None = Query(default=None)):
    try:
        return Response(content=opml_service.export_opml(feed_ids), media_type="application/xml")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"

