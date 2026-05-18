from fastapi import APIRouter

from app.schemas import AIResultRead
from app.services import ai_service

router = APIRouter()


@router.post("/summary/{article_id}", response_model=AIResultRead)
def summarize(article_id: int):
    return ai_service.summarize(article_id)


@router.post("/translate/{article_id}", response_model=AIResultRead)
def translate(article_id: int):
    return ai_service.translate(article_id)


@router.post("/tag-suggest/{article_id}", response_model=AIResultRead)
def suggest_tags(article_id: int):
    return ai_service.suggest_tags(article_id)

