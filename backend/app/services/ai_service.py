from app.repositories import repository
from app.services.summary_agent import SummaryAgentError, summarize_with_provider


def summarize(article_id: int, provider_id: int | None = None, refresh: bool = True):
    if not refresh:
        cached = repository.get_latest_ai_result(article_id, "summary")
        if cached:
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

    result = summarize_with_provider(article, provider)
    return repository.create_ai_result(
        article_id,
        "summary",
        "RSSReader Summary Agent",
        result.text,
        provider=provider["name"],
        model=provider["model"],
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
    )


def translate(article_id):
    article = repository.get_article(article_id)
    result = f"Mock translation: {article['title']} explains the design of a local-first RSS reader."
    return repository.create_ai_result(article_id, "translation", "Translate article", result)


def suggest_tags(article_id):
    repository.get_article(article_id)
    result = "课程项目, AI, 工程实践"
    return repository.create_ai_result(article_id, "tag_suggestion", "Suggest tags", result)
