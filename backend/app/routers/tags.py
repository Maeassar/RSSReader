from fastapi import APIRouter

from app.schemas import OperationResult, TagCreate, TagRead, TagUpdate
from app.services import tag_service

router = APIRouter()


@router.get("", response_model=list[TagRead])
def list_tags():
    return tag_service.list_tags()


@router.post("", response_model=TagRead)
def create_tag(payload: TagCreate):
    return tag_service.create_tag(payload)


@router.put("/{tag_id}", response_model=TagRead)
def update_tag(tag_id: int, payload: TagUpdate):
    return tag_service.update_tag(tag_id, payload)


@router.delete("/{tag_id}", response_model=OperationResult)
def delete_tag(tag_id: int):
    tag_service.delete_tag(tag_id)
    return OperationResult(message="Tag deleted from mock repository.")

