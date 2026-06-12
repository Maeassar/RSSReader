from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from html import unescape
import re
import time

from openai import OpenAI


class SummaryAgentError(RuntimeError):
    pass


SummaryEventHandler = Callable[[dict], None]


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
    context_window_tokens: int = 6000
    chunk_token_budget: int = 2600
    chunk_overlap_tokens: int = 120
    max_rounds: int = 4


def build_article_text(article: dict, max_chars: int | None = None) -> str:
    metadata = _article_metadata(article)
    text = _article_body(article)
    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars].rsplit("\n", 1)[0].strip()
    return metadata + f"\n\n正文：\n{text or '无正文，仅可基于标题生成摘要。'}"


def _article_metadata(article: dict) -> str:
    title = article.get("title") or "Untitled"
    feed_title = article.get("feed_title") or "Unknown feed"
    published_at = article.get("published_at") or ""
    url = article.get("url") or ""
    metadata = [
        f"标题：{title}",
        f"订阅源：{feed_title}",
    ]
    if published_at:
        metadata.append(f"发布时间：{published_at}")
    if url:
        metadata.append(f"原文链接：{url}")
    return "\n".join(metadata)


def _article_body(article: dict) -> str:
    source = (
        article.get("cleaned_markdown")
        or article.get("cleaned_html")
        or article.get("raw_html")
        or article.get("summary")
        or ""
    )
    text = _html_to_text(source)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


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
    on_event: SummaryEventHandler | None = None,
) -> SummaryResult:
    if not provider.get("enabled", True):
        raise SummaryAgentError("当前 LLM Provider 未启用，请在 AI 设置中启用后重试。")

    base_url = (provider.get("base_url") or "").rstrip("/")
    model = provider.get("model") or ""
    if not base_url or not model:
        raise SummaryAgentError("LLM Provider 缺少 Base URL 或模型名称。")

    options = options or SummaryOptions()
    system_prompt, user_prompt = build_summary_prompt(article, options)
    article_tokens = _estimate_tokens(system_prompt + user_prompt)
    input_budget = _input_token_budget(options)
    _emit(
        on_event,
        "prepare",
        "读取文章上下文",
        "已整理标题、订阅源、正文和摘要参数。",
        provider=provider.get("name"),
        model=provider.get("model"),
    )
    _emit(
        on_event,
        "budget",
        "评估上下文预算",
        f"文章输入约 {article_tokens} tokens，当前单轮输入预算约 {input_budget} tokens。",
        estimated_tokens=article_tokens,
        input_budget=input_budget,
    )
    try:
        client = OpenAI(
            api_key=provider.get("api_key") or "EMPTY",
            base_url=base_url,
            timeout=60,
        )
        if article_tokens > input_budget:
            return _summarize_long_article(client, article, provider, options, on_event=on_event)
        _emit(
            on_event,
            "single_start",
            "调用模型生成摘要",
            "文章未超过上下文预算，正在执行单轮摘要请求。",
            max_tokens=_max_tokens_for_options(options),
        )
        completion = _complete_chat(
            client,
            provider,
            system_prompt,
            user_prompt,
            _max_tokens_for_options(options),
        )
        _emit(
            on_event,
            "single_done",
            "单轮摘要完成",
            _usage_detail(completion.usage),
            usage=_usage_payload(completion.usage),
        )
    except Exception as exc:
        _emit(on_event, "error", "摘要生成失败", _friendly_provider_error(exc, provider))
        raise SummaryAgentError(_friendly_provider_error(exc, provider)) from exc

    return SummaryResult(
        text=completion.text,
        usage=completion.usage,
        prompt=f"{system_prompt}\n\n{user_prompt}",
    )


@dataclass
class _Completion:
    text: str
    usage: SummaryUsage


def _summarize_long_article(
    client: OpenAI,
    article: dict,
    provider: dict,
    options: SummaryOptions,
    on_event: SummaryEventHandler | None = None,
) -> SummaryResult:
    body = _article_body(article)
    if not body:
        system_prompt, user_prompt = build_summary_prompt(article, options)
        _emit(on_event, "single_start", "调用模型生成摘要", "正文为空，正在基于标题和元信息生成摘要。")
        completion = _complete_chat(client, provider, system_prompt, user_prompt, _max_tokens_for_options(options))
        _emit(on_event, "single_done", "单轮摘要完成", _usage_detail(completion.usage), usage=_usage_payload(completion.usage))
        return SummaryResult(completion.text, completion.usage, f"{system_prompt}\n\n{user_prompt}")

    chunks = _split_text_by_token_budget(body, options.chunk_token_budget, options.chunk_overlap_tokens)
    _emit(
        on_event,
        "chunk_plan",
        "切分长文上下文",
        f"正文约 {_estimate_tokens(body)} tokens，已切成 {len(chunks)} 个片段逐段摘要。",
        source_tokens=_estimate_tokens(body),
        chunks=len(chunks),
        chunk_token_budget=options.chunk_token_budget,
    )
    total_usage = SummaryUsage(0, 0)
    trace = [
        "多轮上下文摘要流程：",
        f"- source_tokens≈{_estimate_tokens(body)}",
        f"- context_window_tokens={options.context_window_tokens}",
        f"- chunk_token_budget={options.chunk_token_budget}",
        f"- chunks={len(chunks)}",
    ]
    notes: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        system_prompt, user_prompt = _build_chunk_prompt(article, chunk, index, len(chunks), options)
        _emit(
            on_event,
            "chunk_start",
            f"提取片段 {index}/{len(chunks)}",
            f"正在调用模型读取第 {index} 个片段，生成可合并的事实笔记。",
            index=index,
            total=len(chunks),
            estimated_tokens=_estimate_tokens(system_prompt + user_prompt),
        )
        completion = _complete_chat(client, provider, system_prompt, user_prompt, 650)
        _add_usage(total_usage, completion.usage)
        notes.append(f"片段 {index}/{len(chunks)} 笔记：\n{completion.text}")
        trace.append(_trace_prompt(f"chunk {index}/{len(chunks)}", system_prompt, user_prompt))
        _emit(
            on_event,
            "chunk_done",
            f"片段 {index}/{len(chunks)} 完成",
            _usage_detail(completion.usage),
            index=index,
            total=len(chunks),
            usage=_usage_payload(completion.usage),
        )

    notes_text = "\n\n".join(notes)
    round_number = 1
    while _estimate_tokens(notes_text) > _input_token_budget(options) and round_number <= options.max_rounds:
        compressed_notes: list[str] = []
        note_chunks = _split_text_by_token_budget(notes_text, options.chunk_token_budget, 0)
        _emit(
            on_event,
            "compact_plan",
            f"压缩中间笔记 第 {round_number} 轮",
            f"中间笔记仍约 {_estimate_tokens(notes_text)} tokens，超过最终合并预算，将分成 {len(note_chunks)} 组压缩。",
            round=round_number,
            chunks=len(note_chunks),
            estimated_tokens=_estimate_tokens(notes_text),
        )
        for index, note_chunk in enumerate(note_chunks, start=1):
            system_prompt, user_prompt = _build_compaction_prompt(note_chunk, index, len(note_chunks), round_number, options)
            _emit(
                on_event,
                "compact_start",
                f"压缩笔记 {index}/{len(note_chunks)}",
                f"正在压缩第 {round_number} 轮的第 {index} 组中间笔记。",
                round=round_number,
                index=index,
                total=len(note_chunks),
            )
            completion = _complete_chat(client, provider, system_prompt, user_prompt, 700)
            _add_usage(total_usage, completion.usage)
            compressed_notes.append(f"压缩轮 {round_number} - {index}/{len(note_chunks)}：\n{completion.text}")
            trace.append(_trace_prompt(f"compact r{round_number} {index}/{len(note_chunks)}", system_prompt, user_prompt))
            _emit(
                on_event,
                "compact_done",
                f"压缩笔记 {index}/{len(note_chunks)} 完成",
                _usage_detail(completion.usage),
                round=round_number,
                index=index,
                total=len(note_chunks),
                usage=_usage_payload(completion.usage),
            )
        notes_text = "\n\n".join(compressed_notes)
        round_number += 1

    if _estimate_tokens(notes_text) > _input_token_budget(options):
        notes_text = _trim_to_token_budget(notes_text, _input_token_budget(options))
        trace.append("- 中间笔记超过最大压缩轮数，已按 token 预算保留前部压缩笔记。")
        _emit(
            on_event,
            "trim",
            "裁剪中间笔记",
            "中间笔记超过最大压缩轮数，已按 token 预算保留前部压缩笔记。",
            estimated_tokens=_estimate_tokens(notes_text),
        )

    system_prompt, user_prompt = _build_final_from_notes_prompt(article, notes_text, options)
    _emit(
        on_event,
        "final_start",
        "合成最终摘要",
        "正在基于所有片段笔记执行最终去重、排序和忠实性自检。",
        estimated_tokens=_estimate_tokens(system_prompt + user_prompt),
    )
    completion = _complete_chat(client, provider, system_prompt, user_prompt, _max_tokens_for_options(options))
    _add_usage(total_usage, completion.usage)
    trace.append(_trace_prompt("final merge", system_prompt, user_prompt))
    _emit(
        on_event,
        "final_done",
        "最终摘要完成",
        f"{_usage_detail(completion.usage)}；累计 {_usage_detail(total_usage)}。",
        usage=_usage_payload(completion.usage),
        total_usage=_usage_payload(total_usage),
    )
    return SummaryResult(
        text=completion.text,
        usage=total_usage,
        prompt="\n\n".join(trace),
    )


def _complete_chat(
    client: OpenAI,
    provider: dict,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> _Completion:
    request_args = {
        "model": provider.get("model") or "",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    if provider.get("provider_type") == "ollama":
        request_args["reasoning_effort"] = "none"
    response = client.chat.completions.create(**request_args)
    text = response.choices[0].message.content if response.choices else ""
    text = clean_model_output(text)
    if not text or not text.strip():
        raise SummaryAgentError("模型返回了空摘要，请检查模型服务是否正常。")

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) or _estimate_tokens(system_prompt + user_prompt)
    output_tokens = getattr(usage, "completion_tokens", 0) or _estimate_tokens(text)
    return _Completion(text.strip(), SummaryUsage(input_tokens, output_tokens))


def clean_model_output(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.I | re.S)
    text = re.sub(r"^\s*(final answer|最终答案)[:：]\s*", "", text, flags=re.I)
    return text.strip()


def _build_chunk_prompt(
    article: dict,
    chunk: str,
    index: int,
    total: int,
    options: SummaryOptions,
) -> tuple[str, str]:
    output_language = "中文" if options.language == "zh" else "English"
    system_prompt = (
        "你是 RSSReader 的长文摘要子任务 agent。"
        "当前输入只是整篇文章的一个片段，你的任务是提取可复用的事实笔记，"
        "不要写最终摘要，不要编造本片段没有的信息。"
    )
    user_prompt = (
        f"{_article_metadata(article)}\n\n"
        f"片段：{index}/{total}\n"
        f"输出语言：{output_language}\n\n"
        "请输出用于后续汇总的压缩笔记，格式：\n"
        "- 本片段主旨：...\n"
        "- 事实/数字/人名/机构：...\n"
        "- 因果、风险或争议：...\n"
        "- 与前后文相关的线索：...\n"
        "- 信息不足或不确定处：...\n\n"
        f"片段正文：\n{chunk}"
    )
    return system_prompt, user_prompt


def _build_compaction_prompt(
    notes: str,
    index: int,
    total: int,
    round_number: int,
    options: SummaryOptions,
) -> tuple[str, str]:
    output_language = "中文" if options.language == "zh" else "English"
    system_prompt = (
        "你是 RSSReader 的上下文压缩 agent。"
        "你的任务是在保留事实覆盖面的前提下压缩中间笔记，"
        "合并重复点，保留数字、因果、争议和不确定性。"
    )
    user_prompt = (
        f"压缩轮次：{round_number}\n"
        f"笔记分块：{index}/{total}\n"
        f"输出语言：{output_language}\n\n"
        "请把下面的中间笔记压缩为更短的事实清单，禁止加入新事实：\n\n"
        f"{notes}"
    )
    return system_prompt, user_prompt


def _build_final_from_notes_prompt(
    article: dict,
    notes: str,
    options: SummaryOptions,
) -> tuple[str, str]:
    output_language = "中文" if options.language == "zh" else "English"
    mode_instruction = _mode_instruction(options.mode)
    system_prompt = (
        "你是 RSSReader 的最终摘要 agent。"
        "你会基于多个片段 agent 产生的事实笔记整合全文摘要。"
        "必须覆盖整篇文章的主要线索，不能只总结开头；不能泄露内部推理。"
    )
    user_prompt = (
        f"{_article_metadata(article)}\n\n"
        f"摘要模式：{options.mode}\n"
        f"输出语言：{output_language}\n"
        f"长度上限：约 {options.max_words} 个词以内\n\n"
        "下面是从整篇文章多轮提取并压缩后的事实笔记。"
        "请执行最终合成：去重、按重要性排序、保留不确定性，并自检是否只使用笔记中支持的信息。\n\n"
        f"{mode_instruction}\n"
        "最后增加一行 `可信度：高/中/低`，反映正文信息是否充分。\n\n"
        f"事实笔记：\n{notes}"
    )
    return system_prompt, user_prompt


def _split_text_by_token_budget(text: str, token_budget: int, overlap_tokens: int) -> list[str]:
    token_budget = max(200, token_budget)
    overlap_tokens = max(0, min(overlap_tokens, token_budget // 3))
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for paragraph in paragraphs:
        paragraph_tokens = _estimate_tokens(paragraph)
        if paragraph_tokens > token_budget:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_tokens = 0
            chunks.extend(_split_large_paragraph(paragraph, token_budget, overlap_tokens))
            continue

        if current and current_tokens + paragraph_tokens > token_budget:
            chunks.append("\n\n".join(current))
            current = _overlap_tail(current, overlap_tokens)
            current_tokens = _estimate_tokens("\n\n".join(current)) if current else 0
        current.append(paragraph)
        current_tokens += paragraph_tokens

    if current:
        chunks.append("\n\n".join(current))
    return chunks or [text[: max(1, token_budget * 4)]]


def _split_large_paragraph(paragraph: str, token_budget: int, overlap_tokens: int) -> list[str]:
    chunk_chars = max(800, token_budget * 3)
    overlap_chars = max(0, overlap_tokens * 3)
    chunks: list[str] = []
    start = 0
    while start < len(paragraph):
        end = min(len(paragraph), start + chunk_chars)
        chunks.append(paragraph[start:end].strip())
        if end >= len(paragraph):
            break
        start = max(end - overlap_chars, start + 1)
    return [chunk for chunk in chunks if chunk]


def _overlap_tail(paragraphs: list[str], overlap_tokens: int) -> list[str]:
    if overlap_tokens <= 0:
        return []
    selected: list[str] = []
    total = 0
    for paragraph in reversed(paragraphs):
        total += _estimate_tokens(paragraph)
        selected.insert(0, paragraph)
        if total >= overlap_tokens:
            break
    return selected


def _input_token_budget(options: SummaryOptions) -> int:
    completion_budget = _max_tokens_for_options(options)
    return max(500, options.context_window_tokens - completion_budget - 500)


def _trim_to_token_budget(text: str, token_budget: int) -> str:
    if _estimate_tokens(text) <= token_budget:
        return text
    max_chars = max(500, token_budget * 3)
    return text[:max_chars].rsplit("\n", 1)[0].strip() or text[:max_chars].strip()


def _add_usage(total: SummaryUsage, usage: SummaryUsage) -> None:
    total.input_tokens += usage.input_tokens
    total.output_tokens += usage.output_tokens


def _emit(
    on_event: SummaryEventHandler | None,
    event_type: str,
    title: str,
    detail: str,
    **payload,
) -> None:
    if on_event is None:
        return
    event = {
        "type": event_type,
        "title": title,
        "detail": detail,
        "ts": time.time(),
    }
    event.update(payload)
    on_event(event)


def _usage_payload(usage: SummaryUsage) -> dict:
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
    }


def _usage_detail(usage: SummaryUsage) -> str:
    return f"本步用量 {usage.input_tokens} 输入 / {usage.output_tokens} 输出 tokens"


def _trace_prompt(label: str, system_prompt: str, user_prompt: str) -> str:
    return f"[{label}]\n{system_prompt}\n\n{user_prompt}"


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
