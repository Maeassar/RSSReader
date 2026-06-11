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
    prompt: str


@dataclass
class SummaryOptions:
    mode: str = "structured"
    language: str = "zh"
    max_words: int = 450


def build_article_text(article: dict, max_chars: int = 12000) -> str:
    title = article.get("title") or "Untitled"
    feed_title = article.get("feed_title") or "Unknown feed"
    published_at = article.get("published_at") or ""
    url = article.get("url") or ""
    source = (
        article.get("cleaned_markdown")
        or article.get("cleaned_html")
        or article.get("raw_html")
        or article.get("summary")
        or ""
    )
    text = _html_to_text(source)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit("\n", 1)[0].strip()
    metadata = [
        f"标题：{title}",
        f"订阅源：{feed_title}",
    ]
    if published_at:
        metadata.append(f"发布时间：{published_at}")
    if url:
        metadata.append(f"原文链接：{url}")
    return "\n".join(metadata) + f"\n\n正文：\n{text or '无正文，仅可基于标题生成摘要。'}"


def build_summary_prompt(article: dict, options: SummaryOptions | None = None) -> tuple[str, str]:
    options = options or SummaryOptions()
    output_language = "中文" if options.language == "zh" else "English"
    mode_instruction = _mode_instruction(options.mode)
    system_prompt = (
        "你是 RSSReader 的文章摘要智能体，工作方式类似可靠的 coding agent："
        "先理解输入与约束，再提炼关键信息，最后做一次自检。"
        "你不会编造正文没有的信息；如果正文只包含链接、评论数或分数，需要明确说明信息不足。"
        "输出必须面向阅读者，不能泄露内部推理过程或 <think> 内容。"
    )
    user_prompt = (
        f"{build_article_text(article)}\n\n"
        f"摘要模式：{options.mode}\n"
        f"输出语言：{output_language}\n"
        f"长度上限：约 {options.max_words} 个词以内\n\n"
        "请执行以下 agentic workflow 并只输出最终结果：\n"
        "1. 判断正文是否足够生成摘要。\n"
        "2. 提炼中心论点、事实、数字、风险或争议点。\n"
        "3. 自检摘要是否忠于原文，删除无法从原文支持的判断。\n\n"
        f"{mode_instruction}\n"
        "最后增加一行 `可信度：高/中/低`，反映正文信息是否充分。"
    )
    return system_prompt, user_prompt


def summarize_with_provider(
    article: dict,
    provider: dict,
    options: SummaryOptions | None = None,
) -> SummaryResult:
    if not provider.get("enabled", True):
        raise SummaryAgentError("当前 LLM Provider 未启用，请在 AI 设置中启用后重试。")

    base_url = (provider.get("base_url") or "").rstrip("/")
    model = provider.get("model") or ""
    if not base_url or not model:
        raise SummaryAgentError("LLM Provider 缺少 Base URL 或模型名称。")

    options = options or SummaryOptions()
    system_prompt, user_prompt = build_summary_prompt(article, options)
    try:
        client = OpenAI(
            api_key=provider.get("api_key") or "EMPTY",
            base_url=base_url,
            timeout=60,
        )
        request_args = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": _max_tokens_for_options(options),
        }
        if provider.get("provider_type") == "ollama":
            request_args["reasoning_effort"] = "none"
        response = client.chat.completions.create(
            **request_args,
        )
    except Exception as exc:
        raise SummaryAgentError(_friendly_provider_error(exc, provider)) from exc

    text = response.choices[0].message.content if response.choices else ""
    text = clean_model_output(text)
    if not text or not text.strip():
        raise SummaryAgentError("模型返回了空摘要，请检查模型服务是否正常。")

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) or _estimate_tokens(system_prompt + user_prompt)
    output_tokens = getattr(usage, "completion_tokens", 0) or _estimate_tokens(text)
    return SummaryResult(
        text=text.strip(),
        usage=SummaryUsage(input_tokens, output_tokens),
        prompt=f"{system_prompt}\n\n{user_prompt}",
    )


def clean_model_output(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.I | re.S)
    text = re.sub(r"^\s*(final answer|最终答案)[:：]\s*", "", text, flags=re.I)
    return text.strip()


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


def _mode_instruction(mode: str) -> str:
    if mode == "brief":
        return (
            "请按以下格式输出：\n"
            "- 一句话概览：...\n"
            "- 关键点：最多 3 条\n"
            "- 关键词：3-5 个"
        )
    if mode == "deep":
        return (
            "请按以下格式输出：\n"
            "## 一句话概览\n...\n"
            "## 背景与问题\n...\n"
            "## 关键要点\n- 4-6 条\n"
            "## 值得继续追踪\n- 2-4 条\n"
            "## 关键词\n..."
        )
    return (
        "请按以下格式输出：\n"
        "## 一句话概览\n...\n"
        "## 关键要点\n- 3-5 条\n"
        "## 关键词\n..."
    )


def _max_tokens_for_options(options: SummaryOptions) -> int:
    return min(1800, max(500, int(options.max_words * 1.8)))


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
