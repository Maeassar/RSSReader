import feedparser
from datetime import datetime, timezone
from time import mktime

from app.services.webpage_extractor import extract_article_html, should_fetch_full_article


def parse_feed(url: str) -> dict:
    parsed = feedparser.parse(url)
    if parsed.bozo and not parsed.entries:
        message = getattr(parsed.bozo_exception, "args", ["Invalid RSS/Atom feed"])[0]
        raise ValueError(f"Failed to parse feed: {message}")

    return {
        "url": url,
        "title": parsed.feed.get("title") or url,
        "description": parsed.feed.get("description") or parsed.feed.get("subtitle"),
        "site_url": parsed.feed.get("link"),
        "language": parsed.feed.get("language"),
        "last_build_date": _format_time(parsed.feed.get("updated_parsed") or parsed.feed.get("published_parsed")),
        "entries": [
            {
                "guid": entry.get("id") or entry.get("guid"),
                "title": entry.get("title") or "Untitled",
                "link": entry.get("link"),
                "author": entry.get("author"),
                "summary": entry.get("summary"),
                "content": _entry_content(entry),
                "published_at": _format_time(entry.get("published_parsed")),
                "updated_at": _format_time(entry.get("updated_parsed")),
            }
            for entry in parsed.entries
        ],
    }


def _entry_content(entry) -> str | None:
    content = entry.get("content")
    if content and isinstance(content, list):
        first = content[0]
        content_html = first.get("value") if isinstance(first, dict) else None
    else:
        content_html = entry.get("summary")

    if should_fetch_full_article(content_html, entry.get("summary"), entry.get("link")):
        fetched_html = extract_article_html(entry.get("link"))
        if fetched_html:
            return fetched_html

    return content_html


def _format_time(value) -> str | None:
    if not value:
        return None
    return datetime.fromtimestamp(mktime(value), tz=timezone.utc).isoformat()
