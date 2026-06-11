from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re

from openai import OpenAI


class SummaryAgentError(RuntimeError):
    pass


@dataclass
class SummaryUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class SummaryResult:
    text: str
    usage: SummaryUsage


def build_article_text(article: dict) -> str:
    title = article.get("title") or "Untitled"
    source = (
        article.get("cleaned_markdown")
        or article.get("cleaned_html")
        or article.get("raw_html")
        or article.get("summary")
        or ""
    )
    text = _html_to_text(source)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > 12000:
        text = text[:12000].rsplit("\n", 1)[0].strip()
    return f"标题：{title}\n\n正文：\n{text or '无正文，仅可基于标题生成摘要。'}"


def build_summary_prompt(article: dict) -> tuple[str, str]:
    system_prompt = (
        "你是 RSSReader 的文章摘要智能体。请阅读用户提供的 RSS 文章，"
        "输出中文摘要，要求准确、克制，不编造正文没有的信息。"
    )
    user_prompt = (
        f"{build_article_text(article)}\n\n"
        "请按以下格式输出：\n"
        "1. 一句话概览\n"
        "2. 3-5 个关键要点\n"
        "3. 适合后续检索的关键词"
    )
    return system_prompt, user_prompt


def summarize_with_provider(article: dict, provider: dict) -> SummaryResult:
    if not provider.get("enabled", True):
        raise SummaryAgentError("当前 LLM Provider 未启用，请在 AI 设置中启用后重试。")

    base_url = (provider.get("base_url") or "").rstrip("/")
    model = provider.get("model") or ""
    if not base_url or not model:
        raise SummaryAgentError("LLM Provider 缺少 Base URL 或模型名称。")

    system_prompt, user_prompt = build_summary_prompt(article)
    try:
        client = OpenAI(
            api_key=provider.get("api_key") or "EMPTY",
            base_url=base_url,
            timeout=60,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=900,
        )
    except Exception as exc:
        raise SummaryAgentError(_friendly_provider_error(exc, provider)) from exc

    text = response.choices[0].message.content if response.choices else ""
    if not text or not text.strip():
        raise SummaryAgentError("模型返回了空摘要，请检查模型服务是否正常。")

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) or _estimate_tokens(system_prompt + user_prompt)
    output_tokens = getattr(usage, "completion_tokens", 0) or _estimate_tokens(text)
    return SummaryResult(text=text.strip(), usage=SummaryUsage(input_tokens, output_tokens))


def _html_to_text(value: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", value, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|div|h[1-6]|li|blockquote)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _estimate_tokens(text: str) -> int:
    # Mixed Chinese/English approximation used only when providers omit usage.
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    non_ascii_chars = max(0, len(text) - ascii_chars)
    return max(1, non_ascii_chars + ascii_chars // 4)


def _friendly_provider_error(exc: Exception, provider: dict) -> str:
    message = str(exc)
    provider_type = provider.get("provider_type")
    if "Connection" in message or "connect" in message.lower() or "refused" in message.lower():
        if provider_type == "vllm":
            return "无法连接 vLLM 本地服务，请确认已启动 OpenAI-compatible server，例如 http://127.0.0.1:8000/v1。"
        if provider_type == "ollama":
            return "无法连接 Ollama 服务，请确认 Ollama 已启动且 Base URL 指向 /v1。"
        return "无法连接 LLM Provider，请检查 Base URL。"
    if "401" in message or "403" in message or "Unauthorized" in message:
        return "LLM Provider 鉴权失败，请检查 API Key。"
    if "model" in message.lower() and ("not found" in message.lower() or "does not exist" in message.lower()):
        return "模型不存在或未加载，请检查模型名称。"
    return f"LLM Provider 调用失败：{message}"
