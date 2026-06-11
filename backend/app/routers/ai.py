from fastapi import APIRouter, HTTPException

from app.repositories import repository
from app.schemas import AIResultRead, LLMProviderCreate, LLMProviderRead, LLMProviderUpdate, SummaryRequest
from app.services import ai_service
from app.services.summary_agent import SummaryAgentError

router = APIRouter()


@router.get("/providers", response_model=list[LLMProviderRead])
def list_providers():
    return repository.list_llm_providers()


@router.post("/providers", response_model=LLMProviderRead)
def create_provider(payload: LLMProviderCreate):
    return repository.create_llm_provider(payload)


@router.put("/providers/{provider_id}", response_model=LLMProviderRead)
def update_provider(provider_id: int, payload: LLMProviderUpdate):
    try:
        return repository.update_llm_provider(provider_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/providers/{provider_id}")
def delete_provider(provider_id: int):
    try:
        repository.delete_llm_provider(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "message": "Provider deleted"}


@router.post("/summary/{article_id}", response_model=AIResultRead)
def summarize(article_id: int, payload: SummaryRequest | None = None):
    request = payload or SummaryRequest()
    try:
        return ai_service.summarize(article_id, provider_id=request.provider_id, refresh=request.refresh)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SummaryAgentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/translate/{article_id}", response_model=AIResultRead)
def translate(article_id: int):
    return ai_service.translate(article_id)


@router.post("/tag-suggest/{article_id}", response_model=AIResultRead)
def suggest_tags(article_id: int):
    return ai_service.suggest_tags(article_id)
