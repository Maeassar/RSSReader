import json
import queue
import threading

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.repositories import repository
from app.schemas import AIResultRead, LLMProviderCreate, LLMProviderRead, LLMProviderUpdate, SegmentTranslationRequest, SegmentTranslationResponse, SummaryRequest, TagSuggestionResponse, TranslationProviderCreate, TranslationProviderRead, TranslationProviderUpdate, TranslationRequest
from app.services import ai_service
from app.services.summary_agent import SummaryAgentError
from app.services.tag_agent import TagAgentError
from app.services.translation_agent import TranslationAgentError, TranslationCancelled

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


@router.get("/translation-providers", response_model=list[TranslationProviderRead])
def list_translation_providers():
    return repository.list_translation_providers()


@router.post("/translation-providers", response_model=TranslationProviderRead)
def create_translation_provider(payload: TranslationProviderCreate):
    return repository.create_translation_provider(payload)


@router.put("/translation-providers/{provider_id}", response_model=TranslationProviderRead)
def update_translation_provider(provider_id: int, payload: TranslationProviderUpdate):
    try:
        return repository.update_translation_provider(provider_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/translation-providers/{provider_id}")
def delete_translation_provider(provider_id: int):
    try:
        repository.delete_translation_provider(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "message": "Translation provider deleted"}


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


@router.post("/translate/segment", response_model=SegmentTranslationResponse)
def translate_segment(payload: SegmentTranslationRequest):
    """Translate a single text segment (per-paragraph inline translate).

    Stateless — does not persist to ai_results. Used by the reader's
    per-paragraph translate button. Registered BEFORE /translate/{article_id}
    so "segment" is not captured as an article_id path param.
    """
    try:
        return ai_service.translate_segment(
            payload.text,
            provider_id=payload.provider_id,
            target_language=payload.target_language,
            source_language=payload.source_language,
            preserve_markdown=payload.preserve_markdown,
        )
    except TranslationAgentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/translate/{article_id}", response_model=AIResultRead)
def translate(article_id: int, payload: TranslationRequest | None = None):
    request = payload or TranslationRequest()
    try:
        return ai_service.translate(
            article_id,
            provider_id=request.provider_id,
            refresh=request.refresh,
            target_language=request.target_language,
            source_language=request.source_language,
            preserve_markdown=request.preserve_markdown,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TranslationAgentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/translate/{article_id}/stream")
def translate_stream(article_id: int, payload: TranslationRequest | None = None):
    request_body = payload or TranslationRequest()
    events: queue.Queue[dict | None] = queue.Queue()

    def emit(event: dict) -> None:
        events.put(event)

    cancel_event = _new_cancel_event()

    def worker() -> None:
        try:
            result = ai_service.translate(
                article_id,
                provider_id=request_body.provider_id,
                refresh=request_body.refresh,
                target_language=request_body.target_language,
                source_language=request_body.source_language,
                preserve_markdown=request_body.preserve_markdown,
                on_event=emit,
                cancel_event=cancel_event,
            )
            emit({"type": "result", "title": "翻译已生成", "detail": "译文已返回前端。", "result": _stream_result(result)})
            emit({"type": "done", "title": "完成", "detail": "本次翻译任务已结束。"})
        except TranslationCancelled as exc:
            emit({"type": "cancelled", "title": "翻译已取消", "detail": str(exc)})
            emit({"type": "done", "title": "完成", "detail": "本次翻译任务已取消。"})
        except (ValueError, TranslationAgentError) as exc:
            emit({"type": "error", "title": "翻译生成失败", "detail": str(exc)})
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


def _new_cancel_event():
    """Create a CancelEvent, isolating the import to avoid circular deps."""
    from app.services.translation_agent import CancelEvent
    return CancelEvent()


@router.post("/tag-suggest/{article_id}", response_model=TagSuggestionResponse)
def suggest_tags(article_id: int):
    try:
        return ai_service.suggest_tags(article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TagAgentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
