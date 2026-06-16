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
        response = client.chat.completions.create(**request_args)
    except Exception as exc:
        raise TagAgentError(_friendly_provider_error(exc, provider)) from exc

    text = response.choices[0].message.content if response.choices else ""
    text = clean_model_output(text)
    candidates = parse_tag_candidates(text, existing_tags)
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) or _estimate_tokens(system_prompt + user_prompt)
    output_tokens = getattr(usage, "completion_tokens", 0) or _estimate_tokens(text)
    return TagSuggestionResult(
        candidates=candidates,
        usage=SummaryUsage(input_tokens, output_tokens),
        prompt=f"{system_prompt}\n\n{user_prompt}",
        raw_text=text,
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
    payload = _parse_json_payload(text) if isinstance(text, str) else text
    raw_candidates = payload.get("candidates") if isinstance(payload, dict) else payload
    if not isinstance(raw_candidates, list):
        raise TagAgentError("Model response did not contain a candidates list.")

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


def _parse_json_payload(text: str):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.S)
        if not match:
            raise TagAgentError("Model response was not valid JSON.")
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise TagAgentError("Model response was not valid JSON.") from exc


def _clean_tag_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name.strip())
    return name[:40].strip(" ,，.;；:：#")


def _normalize_tag_name(name: str) -> str:
    return _clean_tag_name(name).casefold()
