from __future__ import annotations

from dataclasses import dataclass
import json
import re

from openai import OpenAI

from app.services.summary_agent import (
    SummaryAgentError,
    SummaryUsage,
    build_article_text,
    clean_model_output,
    _estimate_tokens,
    _friendly_provider_error,
)


class TagAgentError(RuntimeError):
    pass


_TAG_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "article",
    "content",
    "for",
    "from",
    "has",
    "into",
    "its",
    "that",
    "the",
    "this",
    "with",
    "\u4e00\u4e2a",
    "\u4e0d\u662f",
    "\u4e2d\u7684",
    "\u5185\u5bb9",
    "\u6587\u7ae0",
    "\u6807\u9898",
    "\u8ba8\u8bba",
}


@dataclass
class TagSuggestionCandidate:
    name: str
    tag_id: int | None = None
    reason: str | None = None


@dataclass
class TagSuggestionResult:
    candidates: list[TagSuggestionCandidate]
    usage: SummaryUsage
    prompt: str
    raw_text: str


def suggest_tags_with_provider(article: dict, existing_tags: list[dict], provider: dict) -> TagSuggestionResult:
    if not provider.get("enabled", True):
        raise TagAgentError("Current LLM Provider is disabled. Enable it in AI settings and try again.")

    base_url = (provider.get("base_url") or "").rstrip("/")
    model = provider.get("model") or ""
    if not base_url or not model:
        raise TagAgentError("LLM Provider is missing Base URL or model name.")

    system_prompt, user_prompt = build_tag_prompt(article, existing_tags)
    response = None
    text = ""
    fallback_detail = ""
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
            "max_tokens": 700,
        }
        if provider.get("provider_type") == "ollama":
            request_args["reasoning_effort"] = "none"
        else:
            request_args["response_format"] = {"type": "json_object"}
        try:
            response = client.chat.completions.create(**request_args)
        except Exception as exc:
            if "response_format" in request_args and _should_retry_without_json_mode(exc):
                request_args.pop("response_format", None)
                response = client.chat.completions.create(**request_args)
            else:
                raise
    except Exception as exc:
        fallback_detail = f"Local fallback: {_friendly_provider_error(exc, provider)}"

    if response is not None:
        text = response.choices[0].message.content if response.choices else ""
    text = clean_model_output(text)
    try:
        candidates = parse_tag_candidates(text, existing_tags)
    except TagAgentError:
        candidates = generate_default_tag_candidates(article, existing_tags, text)
    usage = getattr(response, "usage", None) if response is not None else None
    input_tokens = getattr(usage, "prompt_tokens", 0) or _estimate_tokens(system_prompt + user_prompt)
    output_tokens = getattr(usage, "completion_tokens", 0) or _estimate_tokens(text)
    return TagSuggestionResult(
        candidates=candidates,
        usage=SummaryUsage(input_tokens, output_tokens),
        prompt=f"{system_prompt}\n\n{user_prompt}",
        raw_text=text or fallback_detail,
    )


def build_tag_prompt(article: dict, existing_tags: list[dict]) -> tuple[str, str]:
    tag_catalog = [
        {"id": int(tag["id"]), "name": str(tag["name"])}
        for tag in existing_tags
        if tag.get("id") is not None and tag.get("name")
    ]
    system_prompt = (
        "You are RSSReader's article tagging assistant. Suggest concise, reusable tags for one RSS article. "
        "Prefer existing tags when they fit, but you may propose new tag names. "
        "Return only valid JSON. Do not include markdown fences, commentary, or hidden reasoning."
    )
    user_prompt = (
        f"Existing tags JSON:\n{json.dumps(tag_catalog, ensure_ascii=False)}\n\n"
        f"Article:\n{build_article_text(article, max_chars=6000)}\n\n"
        "Suggest up to 8 candidate tags. Use this exact JSON shape:\n"
        '{"candidates":[{"name":"tag name","tag_id":123,"reason":"short reason"}]}\n'
        "Rules:\n"
        "- If the candidate is an existing tag, copy its exact name and id.\n"
        "- If the candidate is new, omit tag_id or set it to null.\n"
        "- Keep tag names short, stable, and useful for later filtering.\n"
        "- Avoid duplicates, overly broad labels, and article-specific one-off phrases.\n"
    )
    return system_prompt, user_prompt


def parse_tag_candidates(text, existing_tags: list[dict]) -> list[TagSuggestionCandidate]:
    if isinstance(text, str):
        try:
            payload = _parse_json_payload(text)
            raw_candidates = payload.get("candidates") if isinstance(payload, dict) else payload
            if not isinstance(raw_candidates, list):
                raw_candidates = _extract_tag_candidates_from_text(text)
        except TagAgentError:
            raw_candidates = _extract_tag_candidates_from_text(text)
    else:
        raw_candidates = text.get("candidates") if isinstance(text, dict) else text
    if not isinstance(raw_candidates, list):
        raise TagAgentError("Model response did not contain a candidates list.")
    return _normalize_candidate_items(raw_candidates, existing_tags)


def _normalize_candidate_items(raw_candidates: list, existing_tags: list[dict]) -> list[TagSuggestionCandidate]:
    tags_by_name = {
        _normalize_tag_name(tag.get("name", "")): tag
        for tag in existing_tags
        if tag.get("name")
    }
    seen: set[str] = set()
    candidates: list[TagSuggestionCandidate] = []
    for item in raw_candidates:
        if isinstance(item, str):
            name = item
            tag_id = None
            reason = None
        elif isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            raw_tag_id = item.get("tag_id")
            tag_id = int(raw_tag_id) if isinstance(raw_tag_id, int) else None
            raw_reason = item.get("reason")
            reason = str(raw_reason).strip() if raw_reason else None
        else:
            continue
        name = _clean_tag_name(name)
        key = _normalize_tag_name(name)
        if not key or key in seen:
            continue
        matched = tags_by_name.get(key)
        if matched:
            name = str(matched["name"])
            tag_id = int(matched["id"])
        candidates.append(TagSuggestionCandidate(name=name, tag_id=tag_id, reason=reason))
        seen.add(key)
        if len(candidates) >= 8:
            break

    if not candidates:
        raise TagAgentError("Model returned no usable tag candidates.")
    return candidates


def generate_default_tag_candidates(
    article: dict,
    existing_tags: list[dict],
    model_text: str = "",
) -> list[TagSuggestionCandidate]:
    raw_candidates: list[dict] = []
    raw_candidates.extend(_extract_tag_candidates_from_text(model_text))
    raw_candidates.extend(_matching_existing_tags_from_article(article, existing_tags))
    raw_candidates.extend(_keyword_candidates_from_article(article))
    if not raw_candidates:
        fallback_name = str(article.get("feed_title") or article.get("source") or "").strip()
        raw_candidates.append({"name": fallback_name or "General", "reason": "Generated from article metadata."})
    return _normalize_candidate_items(raw_candidates, existing_tags)


def _matching_existing_tags_from_article(article: dict, existing_tags: list[dict]) -> list[dict]:
    text = _article_text_for_tag_fallback(article).casefold()
    matches: list[dict] = []
    for tag in existing_tags:
        name = str(tag.get("name") or "").strip()
        if not name:
            continue
        key = name.casefold()
        words = re.findall(r"[A-Za-z0-9+#.-]+|[\u4e00-\u9fff]+", key)
        if key in text or (words and all(word in text for word in words)):
            matches.append({"name": name, "tag_id": tag.get("id"), "reason": "Matched existing tag in article text."})
    return matches


def _keyword_candidates_from_article(article: dict) -> list[dict]:
    weighted_text = " ".join([
        str(article.get("title") or ""),
        str(article.get("title") or ""),
        str(article.get("feed_title") or ""),
        _article_text_for_tag_fallback(article),
    ])
    weighted_text = re.sub(r"<[^>]+>", " ", weighted_text)
    weighted_text = re.sub(r"https?://\S+", " ", weighted_text)
    counts: dict[str, int] = {}
    display: dict[str, str] = {}
    for raw in re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{1,30}|[\u4e00-\u9fff]{2,8}", weighted_text):
        name = _format_keyword_tag(raw)
        key = _normalize_tag_name(name)
        if not _looks_like_tag_name(name) or key in _TAG_STOPWORDS:
            continue
        counts[key] = counts.get(key, 0) + 1
        display.setdefault(key, name)
    ranked = sorted(counts, key=lambda key: (-counts[key], len(display[key]), display[key].casefold()))
    return [
        {"name": display[key], "reason": "Generated from article keywords."}
        for key in ranked[:8]
    ]


def _article_text_for_tag_fallback(article: dict) -> str:
    return "\n".join(
        str(article.get(field) or "")
        for field in ("title", "feed_title", "summary", "cleaned_markdown", "cleaned_html", "raw_html")
    )


def _format_keyword_tag(raw: str) -> str:
    raw = raw.strip(" .,:;!?()[]{}\"'")
    if not raw:
        return raw
    if re.fullmatch(r"[A-Z0-9+#.-]{2,}", raw):
        return raw
    if re.search(r"[\u4e00-\u9fff]", raw):
        return raw
    return raw[:1].upper() + raw[1:].lower()


def _extract_tag_candidates_from_text(text: str) -> list[dict]:
    cleaned = clean_model_output(text)
    cleaned = re.sub(r"```(?:json)?|```", "\n", cleaned, flags=re.I)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    raw_items: list[dict] = []

    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[\-\*\u2022]\s*", "", line)
        line = re.sub(r"^\d+[\.\)、)]\s*", "", line)
        if not line:
            continue

        label_match = re.search(r"(?:tags?|标签|標籤|候选标签|推薦标签|推荐标签)\s*[:：]\s*(.+)", line, flags=re.I)
        candidate_text = label_match.group(1) if label_match else line

        split_parts = re.split(r"[,，、;；/|]+", candidate_text)
        if len(split_parts) > 1:
            for part in split_parts:
                _append_fallback_candidate(raw_items, part)
            continue

        _append_fallback_candidate(raw_items, candidate_text)

    return raw_items


def _append_fallback_candidate(items: list[dict], raw_name: str) -> None:
    name = raw_name.strip()
    name = re.sub(r"^[\"'“”‘’`]+|[\"'“”‘’`]+$", "", name)
    name = re.split(r"\s+(?:-|–|—)\s+|[:：]\s*", name, maxsplit=1)[0]
    name = re.sub(r"^(?:tag|标签|標籤)\s*[:：]\s*", "", name, flags=re.I).strip()
    name = _clean_tag_name(name)
    name = name.strip(" .,:;!?()[]{}\"'`。！？，、：；")
    if not _looks_like_tag_name(name):
        return
    items.append({"name": name, "reason": "Extracted from non-JSON model response."})


def _looks_like_tag_name(name: str) -> bool:
    if not name or len(name) > 40:
        return False
    lowered = name.casefold()
    normalized = lowered.strip(" .,:;!?()[]{}\"'`")
    if lowered in {
        "json",
        "candidate",
        "candidates",
        "id",
        "name",
        "null",
        "false",
        "true",
        "tag",
        "tag_id",
        "tags",
        "reason",
        "reasons",
        "推荐标签",
        "候选标签",
    } or normalized in {
        "json",
        "candidate",
        "candidates",
        "id",
        "name",
        "null",
        "false",
        "true",
        "tag",
        "tag_id",
        "tags",
        "reason",
        "reasons",
    }:
        return False
    if re.fullmatch(r"[\W_]*(?:name|id|tag_id|reason|candidates?|null|true|false)[\W_]*", lowered):
        return False
    if any(char in name for char in "{}[]<>"):
        return False
    if re.search(r"[。！？!?]$", name):
        return False
    if len(re.findall(r"[A-Za-z]+", name)) > 5:
        return False
    return True


def _parse_json_payload(text: str):
    cleaned = clean_model_output(text).strip()
    parse_candidates = [
        cleaned,
        re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I),
    ]
    parse_candidates.append(re.sub(r"\s*```$", "", parse_candidates[-1]))

    for candidate in parse_candidates:
        try:
            return json.loads(candidate.strip())
        except json.JSONDecodeError:
            pass

    for match in re.finditer(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.I | re.S):
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    for payload in _iter_json_payloads(cleaned):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            continue

    raise TagAgentError("Model response was not valid JSON.")


def _iter_json_payloads(text: str):
    for index, char in enumerate(text):
        if char not in "{[":
            continue
        payload = _balanced_json_slice(text, index)
        if payload:
            yield payload


def _balanced_json_slice(text: str, start: int) -> str | None:
    pairs = {"{": "}", "[": "]"}
    stack = [pairs[text[start]]]
    in_string = False
    escaped = False
    for index in range(start + 1, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in pairs:
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
            if not stack:
                return text[start:index + 1]
    return None


def _should_retry_without_json_mode(exc: Exception) -> bool:
    message = str(exc).lower()
    return "response_format" in message or "json mode" in message or "json_object" in message


def _clean_tag_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name.strip())
    return name[:40].strip(" ,，.;；:：#")


def _normalize_tag_name(name: str) -> str:
    return _clean_tag_name(name).casefold()
