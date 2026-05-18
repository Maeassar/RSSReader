from fastapi import APIRouter

from app.schemas import NoteRead, NoteUpdate
from app.services import note_service

router = APIRouter()


@router.get("/{article_id}/note", response_model=NoteRead)
def get_note(article_id: int):
    return note_service.get_note(article_id)


@router.put("/{article_id}/note", response_model=NoteRead)
def update_note(article_id: int, payload: NoteUpdate):
    return note_service.update_note(article_id, payload)


@router.post("/{article_id}/tags")
def set_article_tags(article_id: int, tag_ids: list[int]):
    from app.services import tag_service

    return tag_service.set_article_tags(article_id, tag_ids)

