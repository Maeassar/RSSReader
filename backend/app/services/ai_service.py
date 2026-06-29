from collections.abc import Callable

from app.repositories import repository
from app.services.summary_agent import SummaryAgentError, SummaryEventHandler, SummaryOptions, summarize_with_provider
from app.services.tag_agent import TagAgentError, generate_default_tag_candidates, suggest_tags_with_provider
from app.services.translation_agent import (
    TranslationAgentError,
    TranslationCancelled,
    TranslationOptions,
    translate_with_provider,
    translate_segment_with_provider,
    extract_aligned_blocks_from_prompt,
    _encode_prompt_with_aligned,
)


def summarize(
    article_id: int,
    provider_id: int | None = None,
    refresh: bool = True,
    mode: str = "structured",
    language: str = "zh",
    max_words: int = 450,
    on_event: SummaryEventHandler | None = None,
):
    if not refresh:
        cached = repository.get_latest_ai_result(article_id, "summary")
        if cached:
            if on_event:
                on_event(
                    {
                        "type": "cache_hit",
                        "title": "读取已有摘要",
                        "detail": "本次请求允许使用缓存，已返回最近一次生成结果。",
                    }
                )
            return cached

    article = repository.get_article(article_id)
    try:
        provider = (
            repository.get_llm_provider(provider_id)
            if provider_id is not None
            else repository.get_default_llm_provider()
        )
    except ValueError as exc:
        raise SummaryAgentError("未配置可用的 LLM Provider，请先在 AI 设置中新增并启用 Provider。") from exc

    try:
        result = summarize_with_provider(
            article,
            provider,
            SummaryOptions(mode=mode, language=language, max_words=max_words),
            on_event=on_event,
        )
    except SummaryAgentError as exc:
        repository.create_ai_result(
            article_id,
            "summary",
            "",
            str(exc),
            provider=provider["name"],
            model=provider["model"],
            status="failed",
        )
        raise
    if on_event:
        on_event(
            {
                "type": "save_start",
                "title": "保存摘要结果",
                "detail": "正在写入摘要文本、prompt trace 和 token 用量。",
            }
        )
    saved = repository.create_ai_result(
        article_id,
        "summary",
        result.prompt,
        result.text,
        provider=provider["name"],
        model=provider["model"],
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
    )
    if on_event:
        on_event(
            {
                "type": "save_done",
                "title": "摘要结果已保存",
                "detail": f"累计用量 {result.usage.input_tokens} 输入 / {result.usage.output_tokens} 输出 tokens。",
                "usage": {
                    "input_tokens": result.usage.input_tokens,
                    "output_tokens": result.usage.output_tokens,
                },
            }
        )
    return saved


def translate(
    article_id: int,
    provider_id: int | None = None,
    refresh: bool = True,
    target_language: str = "zh",
    source_language: str = "auto",
    preserve_markdown: bool = True,
    on_event: Callable[[dict], None] | None = None,
    cancel_event=None,
):
    if not refresh:
        if on_event:
            on_event({"type": "cache_check", "title": "检查翻译缓存", "detail": "正在检查最近一次的翻译缓存。"})
        cached = repository.get_latest_ai_result(article_id, "translation")
        if cached:
            # Don't serve a failed record as a cached translation.
            # Failed records store the error message in `result` and have empty prompt.
            is_failed = cached.get("status") == "failed" or not cached.get("prompt")
            if is_failed:
                if on_event:
                    on_event({"type": "cache_miss", "title": "缓存为失败记录",
                              "detail": "最近一次翻译失败，将重新翻译。"})
            else:
                cached_lang = _extract_target_language(cached.get("prompt", ""))
                if cached_lang is None or cached_lang == target_language:
                    # Restore aligned_blocks from the persisted prompt so the
                    # frontend comparison view works after a page refresh.
                    restored = extract_aligned_blocks_from_prompt(cached.get("prompt", ""))
                    if restored:
                        cached["aligned_blocks"] = restored
                    if on_event:
                        on_event({"type": "cache_hit", "title": "使用缓存译文", "detail": "已返回最近一次翻译结果。"})
                    return cached
                if on_event:
                    on_event({"type": "cache_miss", "title": "语言不匹配",
                              "detail": f"缓存语言 ({cached_lang}) 与请求 ({target_language}) 不同，重新翻译。"})

    article = repository.get_article(article_id)
    try:
        provider = (
            repository.get_translation_provider(provider_id)
            if provider_id is not None
            else repository.get_translation_llm_provider()
        )
    except ValueError as exc:
        raise TranslationAgentError(str(exc)) from exc

    try:
        if on_event:
            on_event({"type": "provider_check", "title": "获取 LLM Provider", "detail": f"正在获取 Provider: {provider_id or '默认'}"})
        result = translate_with_provider(
            article,
            provider,
            TranslationOptions(
                target_language=target_language,
                source_language=source_language,
                preserve_markdown=preserve_markdown,
            ),
            on_event=on_event,
            cancel_event=cancel_event,
        )
    except TranslationCancelled as exc:
        # Cancellation is a user-initiated abort, not a provider failure.
        # Still record a failed result so stats reflect the abandoned call,
        # but re-raise so the SSE worker emits a clean cancel event.
        repository.create_ai_result(
            article_id,
            "translation",
            "",
            str(exc),
            provider=provider["name"],
            model=provider["model"],
            status="failed",
        )
        raise
    except TranslationAgentError as exc:
        if on_event:
            on_event({"type": "save_failed", "title": "翻译失败", "detail": str(exc)})
        repository.create_ai_result(
            article_id,
            "translation",
            "",
            str(exc),
            provider=provider["name"],
            model=provider["model"],
            status="failed",
        )
        raise

    if on_event:
        on_event({
            "type": "save_start",
            "title": "保存翻译结果",
            "detail": "正在写入译文、prompt trace 和 token 用量。",
        })

    # Persist aligned_blocks inside the prompt field so the comparison view
    # can be restored after a page refresh without a schema change.
    persisted_prompt = _encode_prompt_with_aligned(result.prompt, result.aligned_blocks)

    saved = repository.create_ai_result(
        article_id,
        "translation",
        persisted_prompt,
        result.text,
        provider=provider["name"],
        model=provider["model"],
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
    )

    # Attach aligned_blocks for the frontend comparison view (live response).
    aligned_blocks_data = result.aligned_blocks
    if aligned_blocks_data:
        saved["aligned_blocks"] = aligned_blocks_data

    if on_event:
        done_event = {
            "type": "save_done",
            "title": "翻译结果已保存",
            "detail": f"累计用量 {result.usage.input_tokens} 输入 / {result.usage.output_tokens} 输出 tokens。",
            "usage": {
                "input_tokens": result.usage.input_tokens,
                "output_tokens": result.usage.output_tokens,
            },
        }
        if aligned_blocks_data:
            done_event["aligned_blocks"] = aligned_blocks_data
        on_event(done_event)

    return saved


def _extract_target_language(prompt: str) -> str | None:
    """Extract target language code from a translation prompt string.

    The prompt embeds the language display name (e.g. "English", "中文"), so we
    map it back to a code for comparison with the request's target_language code.
    Returns None if no language marker is found.
    """
    import re
    m = re.search(r"目标语言[：:]\s*(\S+)", prompt)
    if not m:
        return None
    display = m.group(1)
    return _LANGUAGE_DISPLAY_TO_CODE.get(display)


# Reverse map of translation_agent._LANGUAGE_NAMES (display name -> code).
# Kept in sync manually; covers all languages supported by TranslationRequest.
_LANGUAGE_DISPLAY_TO_CODE: dict[str, str] = {
    "中文": "zh",
    "English": "en",
    "日本語": "ja",
    "한국어": "ko",
    "Français": "fr",
    "Deutsch": "de",
    "Español": "es",
    "Português": "pt",
    "Русский": "ru",
    "العربية": "ar",
    "auto-detect": "auto",
}


def translate_segment(
    text: str,
    provider_id: int | None = None,
    target_language: str = "zh",
    source_language: str = "auto",
    preserve_markdown: bool = True,
    preserve_html: bool = False,
) -> dict:
    """Translate a single text segment (per-paragraph translate button).

    Stateless: does not read/write ai_results. Returns {text, input_tokens,
    output_tokens}. Raises TranslationAgentError on provider issues.
    """
    try:
        provider = (
            repository.get_translation_provider(provider_id)
            if provider_id is not None
            else repository.get_translation_llm_provider()
        )
    except ValueError as exc:
        raise TranslationAgentError(str(exc)) from exc

    result = translate_segment_with_provider(
        text,
        provider,
        TranslationOptions(
            target_language=target_language,
            source_language=source_language,
            preserve_markdown=preserve_markdown,
            preserve_html=preserve_html,
        ),
    )
    return {
        "text": result.text,
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
    }


def suggest_tags(article_id):
    article = repository.get_article(article_id)
    tags = repository.list_tags()
    try:
        provider = repository.get_default_llm_provider()
    except ValueError:
        candidates = generate_default_tag_candidates(article, tags)
        saved = repository.create_ai_result(
            article_id,
            "tag_suggestion",
            "Local keyword fallback; no available LLM Provider was configured.",
            "Generated from article title, feed, body keywords, and matching existing tags.",
            provider="Local fallback",
            model="keyword-fallback",
            input_tokens=0,
            output_tokens=len(candidates),
        )
        return {
            "article_id": article_id,
            "candidates": [
                {"name": item.name, "tag_id": item.tag_id, "reason": item.reason}
                for item in candidates
            ],
            "ai_result": saved,
        }
    result = suggest_tags_with_provider(article, tags, provider)
    saved = repository.create_ai_result(
        article_id,
        "tag_suggestion",
        result.prompt,
        result.raw_text,
        provider=provider["name"],
        model=provider["model"],
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
    )
    return {
        "article_id": article_id,
        "candidates": [
            {"name": item.name, "tag_id": item.tag_id, "reason": item.reason}
            for item in result.candidates
        ],
        "ai_result": saved,
    }
