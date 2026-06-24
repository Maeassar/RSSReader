from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from html import unescape
import json
import re
import threading
import time

from openai import OpenAI

from app.services.summary_agent import clean_model_output


class TranslationAgentError(RuntimeError):
    pass


class TranslationCancelled(TranslationAgentError):
    """Raised when the caller signals cancellation via a CancelEvent."""

    def __init__(self, message: str = "翻译已取消。"):
        super().__init__(message)


TranslationEventHandler = Callable[[dict], None]


@dataclass
class CancelEvent:
    """Thread-safe cancellation signal shared between the SSE consumer and the worker.

    The SSE generator sets the event when the client disconnects; the translation
    worker checks it before each LLM call and aborts promptly.
    """
    _event: threading.Event = None

    def __post_init__(self) -> None:
        if self._event is None:
            self._event = threading.Event()

    def set(self) -> None:
        self._event.set()

    def is_set(self) -> bool:
        return self._event.is_set()

    def clear(self) -> None:
        self._event.clear()


@dataclass
class TranslationUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class TranslationResult:
    text: str
    usage: TranslationUsage
    prompt: str
    aligned_blocks: list[dict] | None = None


# Marker used to embed aligned_blocks JSON inside the persisted prompt field.
# Format: "<marker>\n<json>\n</marker>\n<prompt trace>"
# This keeps the comparison-view data available after page refresh without
# adding a new database column, while preserving the existing prompt trace
# for debugging (stats/timeseries queries read prompt length, not content).
_ALIGNED_BLOCKS_MARKER = "---aligned_blocks---"
_ALIGNED_BLOCKS_END = "---aligned_blocks-end---"


def _encode_prompt_with_aligned(prompt_trace: str, aligned_blocks: list[dict] | None) -> str:
    """Embed aligned_blocks JSON at the front of the prompt field for persistence."""
    if not aligned_blocks:
        return prompt_trace
    payload = json.dumps(aligned_blocks, ensure_ascii=False)
    return f"{_ALIGNED_BLOCKS_MARKER}\n{payload}\n{_ALIGNED_BLOCKS_END}\n{prompt_trace}"


def extract_aligned_blocks_from_prompt(prompt: str) -> list[dict] | None:
    """Parse aligned_blocks JSON embedded by _encode_prompt_with_aligned.

    Returns the list if the marker is present and the JSON parses, else None.
    Used by ai_service when serving cached results so the comparison view
    still works after a page refresh.
    """
    if not prompt or _ALIGNED_BLOCKS_MARKER not in prompt:
        return None
    try:
        start = prompt.index(_ALIGNED_BLOCKS_MARKER) + len(_ALIGNED_BLOCKS_MARKER)
        end = prompt.index(_ALIGNED_BLOCKS_END, start)
        payload = prompt[start:end].strip()
        data = json.loads(payload)
        if isinstance(data, list):
            return data
    except (ValueError, json.JSONDecodeError):
        return None
    return None


def _strip_aligned_blocks_marker(prompt: str) -> str:
    """Return the prompt trace without the aligned_blocks prefix (for display/debugging)."""
    if not prompt or _ALIGNED_BLOCKS_MARKER not in prompt:
        return prompt
    try:
        end = prompt.index(_ALIGNED_BLOCKS_END) + len(_ALIGNED_BLOCKS_END)
        return prompt[end:].lstrip("\n")
    except ValueError:
        return prompt


@dataclass
class TranslationOptions:
    target_language: str = "zh"
    source_language: str = "auto"
    preserve_markdown: bool = True
    context_window_tokens: int = 6000
    chunk_token_budget: int = 2600
    chunk_overlap_tokens: int = 0  # Translation uses sentence-aligned, no overlap needed


# --- Block & Sentence data structures ---

@dataclass
class Block:
    type: str       # heading|paragraph|list_item|blockquote|code_block|hr|blank
    prefix: str     # 原样回填的前导字符（# / - / > / 缩进空格）
    content: str    # 待翻译的纯文本（code_block/hr/blank 为空）
    raw: str        # 原始行（用于回退）


@dataclass
class Sentence:
    index: int      # block 内序号
    text: str       # 含行内 Markdown 符号的句子文本


_LANGUAGE_NAMES: dict[str, str] = {
    "auto": "auto-detect",
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "pt": "Português",
    "ru": "Русский",
    "ar": "العربية",
}


# ============================================================
#  Block & Sentence parsing
# ============================================================

_CODE_FENCE_RE = re.compile(r"^(`{3,}|~{3,})\s*(\w*)")


def parse_blocks(markdown: str) -> list[Block]:
    """Parse cleaned_markdown into structural blocks, stripping prefixes for translation."""
    if not markdown:
        return []
    lines = markdown.split("\n")
    blocks: list[Block] = []
    in_code = False
    code_fence = ""
    code_lines: list[str] = []
    buffer_type = ""
    buffer_lines: list[str] = []
    buffer_prefix = ""

    def _flush_buffer() -> None:
        nonlocal buffer_type, buffer_lines, buffer_prefix
        if not buffer_lines:
            return
        content = _strip_prefix_lines(buffer_lines, buffer_prefix)
        blocks.append(Block(type=buffer_type, prefix=buffer_prefix, content=content, raw="\n".join(buffer_lines)))
        buffer_type = ""
        buffer_lines = []
        buffer_prefix = ""

    for line in lines:
        if in_code:
            code_lines.append(line)
            if line.startswith(code_fence):
                in_code = False
                blocks.append(Block(type="code_block", prefix="", content="", raw="\n".join(code_lines)))
                code_lines = []
            continue

        # Check for code fence start
        m = _CODE_FENCE_RE.match(line)
        if m:
            _flush_buffer()
            code_lines = [line]
            code_fence = m.group(1)
            in_code = True
            continue

        # Blank line
        if not line.strip():
            _flush_buffer()
            blocks.append(Block(type="blank", prefix="", content="", raw=line))
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}\s*$", line):
            _flush_buffer()
            blocks.append(Block(type="hr", prefix="", content="", raw=line))
            continue

        # Heading
        hm = re.match(r"^(#{1,6})\s+(.*)", line)
        if hm:
            _flush_buffer()
            prefix = f"{hm.group(1)} "
            content = hm.group(2)
            blocks.append(Block(type="heading", prefix=prefix, content=content, raw=line))
            continue

        # Blockquote (> prefix, possibly nested >)
        bqm = re.match(r"^((?:\s*>)+(?:\s)?)(.*)", line)
        if bqm:
            if buffer_type == "blockquote" and buffer_prefix == bqm.group(1):
                buffer_lines.append(line)
            else:
                _flush_buffer()
                buffer_type = "blockquote"
                buffer_prefix = bqm.group(1)
                buffer_lines = [line]
            continue

        # List item (- / * / + / 1. with optional leading spaces)
        lm = re.match(r"^(\s*[-*+]|\s*\d+\.)\s+(.*)", line)
        if lm:
            item_prefix = lm.group(1) + " "
            item_content = lm.group(2)
            # Each list item is its own block for simpler alignment
            if buffer_type == "list_item" and buffer_prefix == item_prefix:
                # Same indentation level — could be continuation
                buffer_lines.append(line)
            else:
                _flush_buffer()
                buffer_type = "list_item"
                buffer_prefix = item_prefix
                buffer_lines = [line]
            continue

        # Paragraph (default)
        if buffer_type == "paragraph":
            buffer_lines.append(line)
        else:
            _flush_buffer()
            buffer_type = "paragraph"
            buffer_prefix = ""
            buffer_lines = [line]

    _flush_buffer()
    return blocks


def _strip_prefix_lines(lines: list[str], prefix: str) -> str:
    """Remove common prefix from each line, returning joined content."""
    stripped = []
    for line in lines:
        if prefix and line.startswith(prefix):
            stripped.append(line[len(prefix):])
        else:
            stripped.append(line)
    return "\n".join(stripped)


# ============================================================
#  Sentence splitting
# ============================================================

# Notes on sentence boundary detection:
# - Split on sentence-ending punctuation (。！？.!?) when followed by whitespace or end-of-text.
# - Avoid splitting on decimals (3.14) and common abbreviations (U.S., e.g., Mr.).
# - Heuristic: a period preceded by an uppercase letter is likely an abbreviation.


def _is_abbreviation_period(text: str, pos: int) -> bool:
    """Check if the period at position pos is likely an abbreviation."""
    if pos <= 0 or pos >= len(text):
        return False
    before = text[pos - 1]
    if not before.isalpha():
        return False
    # Common abbreviation patterns: single letter + period (e.g., U.S.), or short word
    # Simple check: if prev char is uppercase letter, it might be an abbreviation
    if before.isupper():
        return True
    return False


def split_sentences(content: str) -> list[Sentence]:
    """Split content into sentences, keeping delimiters attached."""
    if not content.strip():
        return []
    raw_sentences = _split_sentences_text(content)
    # Remove empty
    raw_sentences = [s.strip() for s in raw_sentences if s.strip()]
    return [Sentence(index=i, text=s) for i, s in enumerate(raw_sentences)]


def _split_sentences_text(text: str) -> list[str]:
    """Split text into sentences with careful handling of abbreviations and decimals.

    Boundary rules:
    - 。！？ always end a sentence (Chinese full-width punctuation).
    - .!? end a sentence when followed by whitespace or end-of-text, UNLESS the period
      is part of a decimal (digit on both sides) or an abbreviation (uppercase letter
      immediately before, e.g. "U.S.").
    - Newline characters separate sentences.
    """
    result: list[str] = []
    current = ""
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        current += ch

        if ch in "。！？":
            # Chinese full-width punctuation: always a boundary
            result.append(current)
            current = ""
        elif ch in ".!?":
            # Look at what follows
            at_end = i + 1 >= n
            next_is_space = (i + 1 < n) and text[i + 1].isspace()
            next_is_newline = (i + 1 < n) and text[i + 1] == "\n"

            if at_end or next_is_space or next_is_newline:
                # Potential boundary — but rule out decimals and abbreviations for "."
                is_boundary = True
                if ch == ".":
                    if _is_decimal_period(text, i):
                        is_boundary = False
                    elif _is_abbreviation_period(text, i):
                        is_boundary = False
                if is_boundary:
                    result.append(current)
                    current = ""
            # else: punctuation mid-token (e.g. "3.14" or "e.g."), keep accumulating
        elif ch == "\n" and current.strip():
            result.append(current)
            current = ""
        i += 1

    if current.strip():
        result.append(current)

    return [s.strip() for s in result if s.strip()] or [text.strip()]


def _is_decimal_period(text: str, pos: int) -> bool:
    """Check if the period at position pos is a decimal point (digit on both sides)."""
    if pos <= 0 or pos >= len(text) - 1:
        return False
    return text[pos - 1].isdigit() and text[pos + 1].isdigit()


# ============================================================
#  Chunk packing (sentence-aligned, does not cross block boundaries)
# ============================================================

@dataclass
class AlignedChunk:
    block_index: int          # Which block this chunk belongs to
    block: Block              # Reference to the original block
    sentences: list[Sentence] # Sentences in this chunk
    sentence_start: int       # Local sentence index start within block


@dataclass
class _GlobalSentence:
    """A sentence tagged with the block it originated from, so translation
    results can be mapped back to the correct block for reassembly even
    when sentences from multiple blocks are packed into a single chunk."""
    block_index: int
    local_index: int
    text: str
    block: Block


def _pack_aligned_chunks(blocks: list[Block], token_budget: int) -> list[AlignedChunk]:
    """Pack sentences into chunks without crossing block boundaries."""
    token_budget = max(200, token_budget)
    chunks: list[AlignedChunk] = []
    for bi, block in enumerate(blocks):
        if block.type in ("code_block", "hr", "blank"):
            # Non-translatable blocks: skip (will be reinserted during reassembly)
            continue
        sentences = split_sentences(block.content)
        if not sentences:
            continue
        current_sentences: list[Sentence] = []
        current_tokens = 0
        for sent in sentences:
            sent_tokens = _estimate_tokens(sent.text)
            if current_sentences and current_tokens + sent_tokens > token_budget:
                chunks.append(AlignedChunk(
                    block_index=bi,
                    block=block,
                    sentences=current_sentences,
                    sentence_start=current_sentences[0].index,
                ))
                current_sentences = []
                current_tokens = 0
            current_sentences.append(sent)
            current_tokens += sent_tokens
        if current_sentences:
            chunks.append(AlignedChunk(
                block_index=bi,
                block=block,
                sentences=current_sentences,
                sentence_start=current_sentences[0].index,
            ))
    return chunks


# ============================================================
#  Prompt building
# ============================================================

def build_translation_source(article: dict) -> str:
    source = (
        article.get("cleaned_markdown")
        or article.get("cleaned_html")
        or article.get("raw_html")
        or article.get("summary")
        or ""
    )
    if article.get("cleaned_markdown"):
        return str(source).strip()
    return _html_to_text(str(source))


def build_translation_prompt(
    article: dict,
    article_text: str,
    options: TranslationOptions | None = None,
) -> tuple[str, str]:
    """Legacy prompt builder for paragraph-level translation (fallback path)."""
    options = options or TranslationOptions()
    target = _language_display(options.target_language)
    source = _language_display(options.source_language)
    title = article.get("title") or "Untitled"
    feed_title = article.get("feed_title") or "Unknown feed"
    preserve_instruction = (
        "尽量保留原文 Markdown 结构、标题层级、列表、引用和链接；不要翻译 URL。"
        if options.preserve_markdown
        else "输出自然流畅的纯文本译文。"
    )
    system_prompt = (
        "你是 RSSReader 的文章翻译智能体。"
        "你只翻译用户提供的文章内容，不添加原文没有的事实，不写摘要，不解释翻译过程。"
        "如果遇到无法确定的专有名词，保留原文或使用常见译名。"
    )
    user_prompt = (
        f"文章标题：{title}\n"
        f"订阅源：{feed_title}\n"
        f"源语言：{source}\n"
        f"目标语言：{target}\n\n"
        f"{preserve_instruction}\n"
        '请直接输出完整译文，不要添加"以下是翻译"等前言。\n\n'
        f"待翻译正文：\n{article_text}"
    )
    return system_prompt, user_prompt


def _build_aligned_prompt(
    article: dict,
    chunk: AlignedChunk,
    options: TranslationOptions,
) -> tuple[str, str]:
    """Build sentence-aligned prompt with |N| line anchors."""
    target = _language_display(options.target_language)
    source = _language_display(options.source_language)
    title = article.get("title") or "Untitled"

    # Build numbered input lines
    numbered_input = "\n".join(
        f"|{i + 1}| {s.text}" for i, s in enumerate(chunk.sentences)
    )
    num_lines = len(chunk.sentences)

    preserve_instruction = (
        "保留原文行内的所有 Markdown 符号（**、`、[]()、标点风格）。"
        if options.preserve_markdown
        else "输出自然流畅的纯文本译文。"
    )

    system_prompt = (
        "你是 RSSReader 的逐句翻译智能体。\n"
        "规则：\n"
        f"1. 严格逐行翻译，输入 {num_lines} 行则输出 {num_lines} 行，第 i 行对应第 i 行原文。\n"
        "2. 保留原文行内的 Markdown 符号（**加粗**、`代码`、[链接]、标点风格）。\n"
        "3. 不合并、不拆分、不增删行，不加前言/注释/解释。\n"
        "4. 目标语言使用其习惯标点，句末标点与原文数量一致。\n"
        "5. 遇到无法确定的专有名词，保留原文或用常见译名。\n"
        "6. 输出必须严格以 |行号| 格式开头，每行一个译文。"
    )

    user_prompt = (
        f"文章标题：{title}\n"
        f"源语言：{source}\n"
        f"目标语言：{target}\n\n"
        f"{preserve_instruction}\n\n"
        f"请逐行翻译，输出格式严格为 |行号|译文，禁止增删行数：\n"
        f"{numbered_input}"
    )
    return system_prompt, user_prompt


# ============================================================
#  Parse aligned response
# ============================================================

def _parse_aligned_response(response_text: str, expected_lines: int) -> list[str] | None:
    """Parse |N| prefixed response back to sentence list.

    Returns the translated sentences in order if every expected line was produced;
    otherwise returns None so the caller can fall back to paragraph translation.
    We deliberately do NOT return a partial fill with empty strings — that would
    inject blank lines into the reassembled translation.
    """
    lines = response_text.strip().split("\n")
    parsed: list[str | None] = [None] * expected_lines

    for line in lines:
        m = re.match(r"^\|(\d+)\|\s*(.*)", line.strip())
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < expected_lines:
                candidate = m.group(2).strip()
                # Only accept non-empty translations; an empty |N| means the model
                # skipped that line, which is an alignment failure.
                if candidate:
                    parsed[idx] = candidate
        # blank lines between entries are ignored

    if all(p is not None for p in parsed):
        return [p for p in parsed]  # type: ignore[list-item]

    return None


# ============================================================
#  Reassembly
# ============================================================

def _reassemble_translation(
    blocks: list[Block],
    aligned_results: list[tuple[AlignedChunk, list[str]]],
) -> str:
    """Reassemble translated sentences back into original structure with prefixes."""
    # Map: block_index -> list of (sentence_start, translated_sentences)
    block_translations: dict[int, list[tuple[int, list[str]]]] = {}
    for chunk, translations in aligned_results:
        if chunk.block_index not in block_translations:
            block_translations[chunk.block_index] = []
        block_translations[chunk.block_index].append((chunk.sentence_start, translations))

    output_lines: list[str] = []
    for bi, block in enumerate(blocks):
        if block.type in ("code_block", "hr", "blank"):
            output_lines.append(block.raw)
            continue

        if bi not in block_translations:
            # Block that wasn't translated (empty content), keep raw
            if block.raw:
                output_lines.append(block.raw)
            continue

        # Merge translations for this block, sorted by sentence_start
        parts = sorted(block_translations[bi], key=lambda x: x[0])
        all_sentences: list[str] = []
        for _, sents in parts:
            all_sentences.extend(sents)

        # Reattach prefix to each line of the block
        if block.prefix:
            for sent_text in all_sentences:
                output_lines.append(f"{block.prefix}{sent_text}")
        else:
            output_lines.extend(all_sentences)

    return "\n".join(output_lines)


# ============================================================
#  Main translation flow
# ============================================================

def translate_with_provider(
    article: dict,
    provider: dict,
    options: TranslationOptions | None = None,
    on_event: TranslationEventHandler | None = None,
    cancel_event: CancelEvent | None = None,
) -> TranslationResult:
    if not provider.get("enabled", True):
        raise TranslationAgentError("当前 LLM Provider 未启用，请在 AI 设置中启用后重试。")

    base_url = (provider.get("base_url") or "").rstrip("/")
    model = provider.get("model") or ""
    if not base_url or not model:
        raise TranslationAgentError("LLM Provider 缺少 Base URL 或模型名称。")

    options = options or TranslationOptions()
    article_text = build_translation_source(article)
    if not article_text.strip():
        raise TranslationAgentError("当前文章没有可翻译的正文。")

    _check_cancel(cancel_event)
    _emit(on_event, "prepare", "读取文章上下文",
          "已整理标题、源正文和翻译参数。",
          provider=provider.get("name"), model=provider.get("model"))

    try:
        client = OpenAI(
            api_key=provider.get("api_key") or "EMPTY",
            base_url=base_url,
            timeout=90,
        )

        # Decide: use aligned (sentence-level) or legacy (paragraph-level) flow
        # Aligned flow only works with preserve_markdown and sufficient content
        can_use_aligned = (
            options.preserve_markdown
            and article.get("cleaned_markdown")
        )

        if can_use_aligned:
            return _translate_aligned(client, article, article_text, provider, options, on_event, cancel_event)
        else:
            return _translate_paragraph(client, article, article_text, provider, options, on_event, cancel_event)

    except TranslationCancelled:
        raise
    except TranslationAgentError:
        raise
    except Exception as exc:
        raise TranslationAgentError(_friendly_provider_error(exc, provider)) from exc


def _check_cancel(cancel_event: CancelEvent | None) -> None:
    """Raise TranslationCancelled if the caller has signalled cancellation."""
    if cancel_event is not None and cancel_event.is_set():
        raise TranslationCancelled()


# ============================================================
#  Legacy paragraph-level translation (fallback / non-Markdown)
# ============================================================

def _translate_paragraph(
    client: OpenAI,
    article: dict,
    article_text: str,
    provider: dict,
    options: TranslationOptions,
    on_event: TranslationEventHandler | None = None,
    cancel_event: CancelEvent | None = None,
) -> TranslationResult:
    """Paragraph-level translation (existing approach, preserved for non-Markdown sources)."""
    _emit(on_event, "parse", "解析文章结构",
          "原文为 HTML/纯文本，使用段落级翻译。")

    if _estimate_tokens(article_text) > _input_token_budget(options):
        return _translate_long_paragraph(client, article, article_text, provider, options, on_event, cancel_event)

    _check_cancel(cancel_event)
    system_prompt, user_prompt = build_translation_prompt(article, article_text, options)
    _emit(on_event, "single_start", "调用模型翻译",
          "文本未超过上下文预算，正在执行单轮翻译请求。")
    completion = _complete_chat(client, provider, system_prompt, user_prompt,
                                _max_tokens_for_text(article_text))
    _emit(on_event, "single_done", "单轮翻译完成",
          _usage_detail(completion.usage), usage=_usage_payload(completion.usage))
    return TranslationResult(
        text=completion.text,
        usage=completion.usage,
        prompt=f"{system_prompt}\n\n{user_prompt}",
    )


def _translate_long_paragraph(
    client: OpenAI,
    article: dict,
    article_text: str,
    provider: dict,
    options: TranslationOptions,
    on_event: TranslationEventHandler | None = None,
    cancel_event: CancelEvent | None = None,
) -> TranslationResult:
    """Long article paragraph-level translation with chunking."""
    chunks = _split_paragraph_by_token_budget(article_text, options.chunk_token_budget, 80)
    _emit(on_event, "chunk_plan", "切分长文",
          f"正文约 {_estimate_tokens(article_text)} tokens，切成 {len(chunks)} 段。",
          chunks=len(chunks))

    total_usage = TranslationUsage(0, 0)
    translated_chunks: list[str] = []
    trace = [
        "多段长文翻译流程：",
        f"- source_tokens≈{_estimate_tokens(article_text)}",
        f"- chunks={len(chunks)}",
    ]
    for index, chunk_text in enumerate(chunks, start=1):
        _check_cancel(cancel_event)
        system_prompt, user_prompt = build_translation_prompt(article, chunk_text, options)
        user_prompt = (
            f"这是长文第 {index}/{len(chunks)} 段。请只翻译本段，保持术语和前后文一致。\n\n"
            f"{user_prompt}"
        )
        _emit(on_event, "chunk_start", f"翻译段落 {index}/{len(chunks)}",
              f"正在翻译第 {index} 段。", index=index, total=len(chunks))
        completion = _complete_chat(client, provider, system_prompt, user_prompt,
                                    _max_tokens_for_text(chunk_text))
        total_usage.input_tokens += completion.usage.input_tokens
        total_usage.output_tokens += completion.usage.output_tokens
        translated_chunks.append(completion.text)
        trace.append(f"[chunk {index}/{len(chunks)}]\n{system_prompt}\n\n{user_prompt}")
        _emit(on_event, "chunk_done", f"段落 {index}/{len(chunks)} 完成",
              _usage_detail(completion.usage), index=index, total=len(chunks),
              usage=_usage_payload(completion.usage))

    return TranslationResult(
        text="\n\n".join(translated_chunks).strip(),
        usage=total_usage,
        prompt="\n\n".join(trace),
    )


def _split_paragraph_by_token_budget(text: str, token_budget: int, overlap_tokens: int) -> list[str]:
    """Legacy paragraph splitting (paragraph-level, by double newlines)."""
    token_budget = max(200, token_budget)
    overlap_tokens = max(0, min(overlap_tokens, token_budget // 3))
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()] or [text.strip()]
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
    return chunks


# ============================================================
#  Sentence-aligned translation flow (核心)
# ============================================================

def _empty_aligned_result(article_text: str) -> TranslationResult:
    """Return a no-op result when there is nothing to translate."""
    return TranslationResult(
        text=article_text,
        usage=TranslationUsage(0, 0),
        prompt="No translatable content, returned as-is.",
        aligned_blocks=None,
    )


def _translate_aligned(
    client: OpenAI,
    article: dict,
    article_text: str,
    provider: dict,
    options: TranslationOptions,
    on_event: TranslationEventHandler | None = None,
    cancel_event: CancelEvent | None = None,
) -> TranslationResult:
    """Block-parsed, sentence-aligned translation flow."""
    # Step A: Parse blocks
    blocks = parse_blocks(article_text)
    total_sentences = sum(len(split_sentences(b.content)) for b in blocks if b.type not in ("code_block", "hr", "blank"))

    _emit(on_event, "parse", "解析文章结构",
          f"识别到 {len(blocks)} 个内容块，{total_sentences} 个待翻译句子。",
          blocks=len(blocks), sentences=total_sentences)

    # Step B+C: Pack into chunks
    aligned_chunks = _pack_aligned_chunks(blocks, options.chunk_token_budget)
    total_tokens = _estimate_tokens(article_text)
    input_budget = _input_token_budget(options)

    _emit(on_event, "budget", "评估上下文预算",
          f"文章输入约 {total_tokens} tokens，单轮输入预算约 {input_budget} tokens。",
          estimated_tokens=total_tokens, input_budget=input_budget)

    if not aligned_chunks:
        # No translatable content (e.g. article is only code blocks / hr / blank).
        # Return the original text as-is rather than crashing on aligned_chunks[0].
        _emit(on_event, "single_start", "调用模型翻译",
              "文章没有可翻译的文本内容，原样返回。")
        _emit(on_event, "single_done", "无可翻译内容",
              "未调用模型，原文结构已保留。")
        return TranslationResult(
            text=article_text,
            usage=TranslationUsage(0, 0),
            prompt="无可翻译内容，原文返回。",
            aligned_blocks=None,
        )

    if len(aligned_chunks) <= 1:
        # Short enough for single request
        chunk = aligned_chunks[0]
        _check_cancel(cancel_event)
        system_prompt, user_prompt = _build_aligned_prompt(article, chunk, options)
        _emit(on_event, "single_start", "调用模型翻译",
              "文章未超过上下文预算，正在执行逐行对齐翻译。")
        completion = _complete_chat(client, provider, system_prompt, user_prompt,
                                    _max_tokens_for_text(user_prompt))

        # Parse aligned response
        translated = _parse_aligned_response(completion.text, len(chunk.sentences))
        aligned_ok = translated is not None

        if aligned_ok and translated:
            # Reassemble single chunk
            result_text = _reassemble_translation(blocks, [(chunk, translated)])
            aligned_blocks_data = _build_aligned_blocks_data_all(
                blocks, {chunk.block_index: translated}
            )
        else:
            # Fallback: use paragraph translation for this chunk
            _check_cancel(cancel_event)
            fallback_text = "\n".join(s.text for s in chunk.sentences)
            sys_p, usr_p = build_translation_prompt(article, fallback_text, options)
            fallback_completion = _complete_chat(client, provider, sys_p, usr_p,
                                                  _max_tokens_for_text(fallback_text))
            result_text = _reassemble_translation(blocks, [
                (chunk, [fallback_completion.text])
            ])
            aligned_blocks_data = None
            completion = fallback_completion

        _emit(on_event, "single_done", "单轮对齐翻译完成",
              _usage_detail(completion.usage), usage=_usage_payload(completion.usage),
              aligned=aligned_ok)

        return TranslationResult(
            text=result_text,
            usage=completion.usage,
            prompt=f"{system_prompt}\n\n{user_prompt}",
            aligned_blocks=aligned_blocks_data,
        )

    # Long article: multi-chunk
    _emit(on_event, "chunk_plan", "切分翻译片段",
          f"共 {len(aligned_chunks)} 个待翻译片段。",
          chunks=len(aligned_chunks))

    total_usage = TranslationUsage(0, 0)
    aligned_results: list[tuple[AlignedChunk, list[str]]] = []
    trace = [
        "逐句对齐翻译流程：",
        f"- blocks={len(blocks)}",
        f"- sentences={total_sentences}",
        f"- chunks={len(aligned_chunks)}",
    ]
    all_fallback = True
    aligned_blocks_all: dict[int, list[str]] = {}

    for ci, chunk in enumerate(aligned_chunks, start=1):
        _check_cancel(cancel_event)
        system_prompt, user_prompt = _build_aligned_prompt(article, chunk, options)
        _emit(on_event, "chunk_start", f"翻译片段 {ci}/{len(aligned_chunks)}",
              f"正在逐句翻译第 {ci} 个片段（{len(chunk.sentences)} 句）。",
              index=ci, total=len(aligned_chunks),
              estimated_tokens=_estimate_tokens(system_prompt + user_prompt))

        completion = _complete_chat(client, provider, system_prompt, user_prompt,
                                    _max_tokens_for_text(user_prompt))
        total_usage.input_tokens += completion.usage.input_tokens
        total_usage.output_tokens += completion.usage.output_tokens

        # Parse aligned response
        translated = _parse_aligned_response(completion.text, len(chunk.sentences))
        is_aligned = translated is not None

        if is_aligned and translated:
            aligned_results.append((chunk, translated))
            if chunk.block_index not in aligned_blocks_all:
                aligned_blocks_all[chunk.block_index] = []
            aligned_blocks_all[chunk.block_index].extend(translated)
            all_fallback = False
            chunk_usage = completion.usage
        else:
            # Fallback: paragraph translate the combined sentences
            _check_cancel(cancel_event)
            fallback_text = "\n".join(s.text for s in chunk.sentences)
            sys_p, usr_p = build_translation_prompt(article, fallback_text, options)
            sys_p = sys_p + "\n这是长文的一个片段，请直接翻译。"
            fallback_completion = _complete_chat(client, provider, sys_p, usr_p,
                                                  _max_tokens_for_text(fallback_text))
            total_usage.input_tokens += fallback_completion.usage.input_tokens
            total_usage.output_tokens += fallback_completion.usage.output_tokens
            aligned_results.append((chunk, [fallback_completion.text]))
            chunk_usage = fallback_completion.usage

        trace.append(f"[chunk {ci}/{len(aligned_chunks)}]\n{system_prompt}\n\n{user_prompt}")

        _emit(on_event, "chunk_done", f"片段 {ci}/{len(aligned_chunks)} 完成",
              _usage_detail(chunk_usage), index=ci, total=len(aligned_chunks),
              usage=_usage_payload(chunk_usage), aligned=is_aligned)

        _emit(on_event, "align_check", "对齐校验",
              "译文行数与原文一致。" if is_aligned else "对齐失败，已回退为段落翻译。",
              aligned=is_aligned, fallback=not is_aligned)

    # Reassemble
    result_text = _reassemble_translation(blocks, aligned_results)

    # Build aligned_blocks data if at least some chunks were aligned
    aligned_blocks_data = _build_aligned_blocks_data_all(blocks, aligned_blocks_all) if not all_fallback else None

    return TranslationResult(
        text=result_text,
        usage=total_usage,
        prompt="\n\n".join(trace),
        aligned_blocks=aligned_blocks_data,
    )


# ============================================================
#  Aligned blocks data (for frontend comparison view)
# ============================================================

def _build_aligned_blocks_data_all(
    blocks: list[Block],
    block_translations: dict[int, list[str]],
) -> list[dict]:
    """Build aligned blocks data for the frontend comparison view.

    For each translated block, emit {type, original, translated} so the frontend
    can render a side-by-side comparison. Non-translatable blocks (code/hr/blank)
    are omitted from the comparison view.
    """
    result: list[dict] = []
    for bi, block in enumerate(blocks):
        if block.type in ("code_block", "hr", "blank"):
            continue
        if bi in block_translations:
            sents = split_sentences(block.content)
            translated_list = block_translations[bi]
            result.append({
                "type": block.type,
                "original": "\n".join(s.text for s in sents),
                "translated": "\n".join(translated_list) if isinstance(translated_list, list) else str(translated_list),
            })
    return result


# ============================================================
#  Shared helpers
# ============================================================

def _emit(
    on_event: TranslationEventHandler | None,
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


@dataclass
class _Completion:
    text: str
    usage: TranslationUsage


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
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    if provider.get("provider_type") == "ollama":
        request_args["reasoning_effort"] = "none"
    response = client.chat.completions.create(**request_args)
    text = response.choices[0].message.content if response.choices else ""
    text = clean_model_output(text)
    if not text.strip():
        raise TranslationAgentError("模型返回了空译文，请检查模型服务是否正常。")

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) or _estimate_tokens(system_prompt + user_prompt)
    output_tokens = getattr(usage, "completion_tokens", 0) or _estimate_tokens(text)
    return _Completion(text.strip(), TranslationUsage(input_tokens, output_tokens))


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


def _input_token_budget(options: TranslationOptions) -> int:
    return max(500, options.context_window_tokens - 1600)


def _max_tokens_for_text(text: str) -> int:
    return min(4096, max(700, int(_estimate_tokens(text) * 1.6)))


def _estimate_tokens(text: str) -> int:
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    non_ascii_chars = max(0, len(text) - ascii_chars)
    return max(1, non_ascii_chars + ascii_chars // 4)


def _html_to_text(value: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", value, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|div|h[1-6]|li|blockquote)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _language_display(language: str) -> str:
    return _LANGUAGE_NAMES.get(language, language or "auto-detect")


def _usage_payload(usage: TranslationUsage) -> dict:
    return {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}


def _usage_detail(usage: TranslationUsage) -> str:
    return f"本步用量 {usage.input_tokens} 输入 / {usage.output_tokens} 输出 tokens"


def _friendly_provider_error(exc: Exception, provider: dict) -> str:
    message = str(exc)
    provider_type = provider.get("provider_type")
    if "Connection" in message or "connect" in message.lower() or "refused" in message.lower():
        if provider_type == "vllm":
            return "无法连接 vLLM 本地服务，请确认 OpenAI-compatible server 已启动。"
        if provider_type == "ollama":
            return "无法连接 Ollama 服务，请确认 Ollama 已启动且 Base URL 指向 /v1。"
        return "无法连接 LLM Provider，请检查 Base URL。"
    if "401" in message or "403" in message or "Unauthorized" in message:
        return "LLM Provider 鉴权失败，请检查 API Key。"
    if "model" in message.lower() and ("not found" in message.lower() or "does not exist" in message.lower()):
        return "模型不存在或未加载，请检查模型名称。"
    return f"LLM Provider 调用失败：{message}"


# ============================================================
#  Single-segment translation (for inline per-paragraph translate)
# ============================================================

@dataclass
class SegmentTranslationResult:
    text: str
    usage: TranslationUsage


def translate_segment_with_provider(
    text: str,
    provider: dict,
    options: TranslationOptions | None = None,
) -> SegmentTranslationResult:
    """Translate a single segment of text (one paragraph / heading / list block).

    This is a lightweight, stateless call used by the per-paragraph translate
    button in the reader. It does NOT persist to ai_results (single-segment
    calls are not worth polluting the stats table); the caller may aggregate
    usage if desired. Raises TranslationAgentError on failure.
    """
    text = (text or "").strip()
    if not text:
        raise TranslationAgentError("没有可翻译的内容。")

    if not provider.get("enabled", True):
        raise TranslationAgentError("当前 LLM Provider 未启用，请在 AI 设置中启用后重试。")

    base_url = (provider.get("base_url") or "").rstrip("/")
    model = provider.get("model") or ""
    if not base_url or not model:
        raise TranslationAgentError("LLM Provider 缺少 Base URL 或模型名称。")

    options = options or TranslationOptions()
    target = _language_display(options.target_language)
    source = _language_display(options.source_language)

    preserve_instruction = (
        "保留原文行内的所有 Markdown 符号（**、`、[]()、标点风格）。"
        if options.preserve_markdown
        else "输出自然流畅的纯文本译文。"
    )
    system_prompt = (
        "你是 RSSReader 的翻译智能体。你只翻译用户提供的文本片段，"
        "不添加原文没有的事实，不写摘要，不解释翻译过程。"
        "遇到无法确定的专有名词，保留原文或使用常见译名。"
    )
    user_prompt = (
        f"源语言：{source}\n"
        f"目标语言：{target}\n\n"
        f"{preserve_instruction}\n"
        '请直接输出译文，不要添加"以下是翻译"等前言。\n\n'
        f"待翻译文本：\n{text}"
    )

    try:
        client = OpenAI(api_key=provider.get("api_key") or "EMPTY", base_url=base_url, timeout=90)
        completion = _complete_chat(client, provider, system_prompt, user_prompt,
                                    _max_tokens_for_text(text))
        return SegmentTranslationResult(text=completion.text, usage=completion.usage)
    except TranslationCancelled:
        raise
    except TranslationAgentError:
        raise
    except Exception as exc:
        raise TranslationAgentError(_friendly_provider_error(exc, provider)) from exc
