from app.repositories import repository
from app.services.summary_agent import SummaryAgentError, SummaryEventHandler, SummaryOptions, summarize_with_provider


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

    result = summarize_with_provider(
        article,
        provider,
        SummaryOptions(mode=mode, language=language, max_words=max_words),
        on_event=on_event,
    )
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


def translate(article_id):
    article = repository.get_article(article_id)
    result = f"Mock translation: {article['title']} explains the design of a local-first RSS reader."
    return repository.create_ai_result(article_id, "translation", "Translate article", result)


def suggest_tags(article_id):
    repository.get_article(article_id)
    result = "课程项目, AI, 工程实践"
    return repository.create_ai_result(article_id, "tag_suggestion", "Suggest tags", result)
