import json
import queue
import threading

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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
        return ai_service.summarize(
            article_id,
            provider_id=request.provider_id,
            refresh=request.refresh,
            mode=request.mode,
            language=request.language,
            max_words=request.max_words,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SummaryAgentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/summary/{article_id}/stream")
def summarize_stream(article_id: int, payload: SummaryRequest | None = None):
    request = payload or SummaryRequest()
    events: queue.Queue[dict | None] = queue.Queue()

    def emit(event: dict) -> None:
        events.put(event)

    def worker() -> None:
        try:
            result = ai_service.summarize(
                article_id,
                provider_id=request.provider_id,
                refresh=request.refresh,
                mode=request.mode,
                language=request.language,
                max_words=request.max_words,
                on_event=emit,
            )
            emit({"type": "result", "title": "摘要已生成", "detail": "摘要文本已返回前端。", "result": _stream_result(result)})
            emit({"type": "done", "title": "完成", "detail": "本次摘要任务已结束。"})
        except (ValueError, SummaryAgentError) as exc:
            emit({"type": "error", "title": "摘要生成失败", "detail": str(exc)})
        finally:
            events.put(None)

    def event_stream():
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        while True:
            event = events.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _stream_result(result: dict) -> dict:
    payload = dict(result)
    payload["prompt"] = ""
    return payload


@router.post("/translate/{article_id}", response_model=AIResultRead)
def translate(article_id: int):
    return ai_service.translate(article_id)


@router.post("/tag-suggest/{article_id}", response_model=AIResultRead)
def suggest_tags(article_id: int):
    return ai_service.suggest_tags(article_id)
