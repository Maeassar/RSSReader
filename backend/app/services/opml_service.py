from __future__ import annotations

from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from pydantic import ValidationError

from app.repositories import repository
from app.schemas import FeedCreate, FeedUpdate


def parse_opml_feeds(text: str) -> list[dict[str, str | None]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid OPML XML: {exc}") from exc

    feeds: list[dict[str, str | None]] = []
    seen_urls: set[str] = set()
    for outline in root.iter():
        if _local_name(outline.tag).lower() != "outline":
            continue
        attributes = {_normalize_attribute_name(key): value for key, value in outline.attrib.items()}
        url = _normalize_text(
            _first_attribute(
                attributes,
                "xmlurl",
                "feedurl",
                "rssurl",
                "atomurl",
                "url",
                "href",
            )
        )
        text_value = _normalize_text(attributes.get("text"))
        if not url and _looks_like_url(text_value):
            url = text_value
        if not url or url in seen_urls:
            continue
        title = _normalize_text(attributes.get("title")) or text_value
        feeds.append({"url": url, "title": title})
        seen_urls.add(url)

    return feeds


async def import_opml(files):
    results = []
    parsed_items = await parse_opml_uploads(files)
    async for item in import_opml_items(parsed_items=parsed_items):
        results.append(item)

    return _build_import_report(_count_source_files(files), results)


async def parse_opml_uploads(files):
    upload_files = list(files if isinstance(files, (list, tuple)) else [files])
    parsed_items = []

    for file in upload_files:
        source_file = getattr(file, "filename", None) or "subscriptions.opml"
        try:
            feed_items = await _read_opml_file(file)
        except ValueError as exc:
            parsed_items.append(
                {
                    "url": None,
                    "title": None,
                    "status": "failed",
                    "message": str(exc),
                    "feed": None,
                    "source_file": source_file,
                }
            )
            continue

        if not feed_items:
            parsed_items.append(
                {
                    "url": None,
                    "title": None,
                    "status": "failed",
                    "message": "No feed URLs found in OPML file.",
                    "feed": None,
                    "source_file": source_file,
                }
            )
            continue

        for item in feed_items:
            parsed_items.append(
                {
                    "url": item["url"],
                    "title": item.get("title"),
                    "status": "pending",
                    "message": "正在上传",
                    "feed": None,
                    "source_file": source_file,
                }
            )

    return parsed_items


async def import_opml_items(files=None, parsed_items=None):
    if parsed_items is None:
        parsed_items = await parse_opml_uploads(files)

    existing_feeds = {feed["url"].strip(): feed for feed in repository.list_feeds()}
    imported_urls: set[str] = set()

    for item in parsed_items:
        if item.get("status") == "failed" and not item.get("url"):
            yield {
                "url": None,
                "title": None,
                "status": "failed",
                "message": item.get("message") or "Invalid OPML file.",
                "feed": None,
                "articles": [],
                "source_file": item.get("source_file"),
            }
            continue

        source_file = item.get("source_file")
        raw_url = item.get("url") or ""
        title = item.get("title")
        try:
            payload = FeedCreate(title=title, url=raw_url)
        except ValidationError as exc:
            message = _validation_message(exc)
            _log_failed_import(raw_url, message)
            yield {
                "url": raw_url,
                "title": title,
                "status": "failed",
                "message": message,
                "feed": None,
                "articles": [],
                "source_file": source_file,
            }
            continue

        url = str(payload.url)
        if url in imported_urls:
            yield {
                "url": url,
                "title": title,
                "status": "skipped",
                "message": "Duplicate feed in selected OPML files.",
                "feed": None,
                "articles": [],
                "source_file": source_file,
            }
            continue
        if url in existing_feeds:
            existing_feed = existing_feeds.get(url)
            yield {
                "url": url,
                "title": title,
                "status": "skipped",
                "message": "Feed already exists.",
                "feed": existing_feed,
                "articles": _list_feed_articles(existing_feed["id"]) if existing_feed else [],
                "source_file": source_file,
            }
            continue

        try:
            feed = repository.create_feed_metadata(payload)
        except ValueError as exc:
            message = str(exc)
            status = "skipped" if "already exists" in message.lower() else "failed"
            if status == "failed":
                _log_failed_import(url, message)
            yield {
                "url": url,
                "title": title,
                "status": status,
                "message": message,
                "feed": None,
                "articles": [],
                "source_file": source_file,
            }
            continue

        existing_feeds[url] = feed
        imported_urls.add(url)
        try:
            synced_feed = repository.sync_feed(feed["id"])
        except Exception as exc:
            message = str(exc)
            feed_after_failure = repository.get_feed(feed["id"]) if hasattr(repository, "get_feed") else feed
            yield {
                "url": url,
                "title": title or feed_after_failure["title"],
                "status": "partial",
                "message": message,
                "feed": feed_after_failure,
                "articles": _list_feed_articles(feed_after_failure["id"]),
                "source_file": source_file,
            }
            continue

        if title:
            synced_feed = repository.update_feed(feed["id"], FeedUpdate(title=title))
        existing_feeds[url] = synced_feed
        articles = _list_feed_articles(synced_feed["id"])
        yield {
            "url": url,
            "title": title or synced_feed["title"],
            "status": "imported",
            "message": "Feed imported and synced successfully.",
            "feed": synced_feed,
            "articles": articles,
            "source_file": source_file,
        }


def _build_import_report(files_count: int, results):
    return {
        "files": files_count,
        "total": len(results),
        "imported": sum(1 for item in results if item["status"] == "imported"),
        "partial": sum(1 for item in results if item["status"] == "partial"),
        "skipped": sum(1 for item in results if item["status"] == "skipped"),
        "failed": sum(1 for item in results if item["status"] == "failed"),
        "results": results,
    }


def export_opml(feed_ids: list[int] | None = None):
    feeds = repository.list_feeds()
    if feed_ids is not None:
        selected_ids = set(feed_ids)
        feeds = [feed for feed in feeds if feed["id"] in selected_ids]
        if not feeds:
            raise ValueError("No matching feeds found for export.")

    root = ET.Element("opml", {"version": "2.0"})
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "title").text = "RSSReader Subscriptions"
    ET.SubElement(head, "dateCreated").text = datetime.now(timezone.utc).isoformat()
    body = ET.SubElement(root, "body")

    for feed in feeds:
        title = feed.get("title") or feed["url"]
        attributes = {
            "text": title,
            "title": title,
            "type": "rss",
            "xmlUrl": feed["url"],
        }
        if feed.get("site_url"):
            attributes["htmlUrl"] = feed["site_url"]
        ET.SubElement(body, "outline", attributes)

    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + ET.tostring(root, encoding="unicode")


async def _read_opml_file(file) -> list[dict[str, str | None]]:
    content = await file.read()
    text = _decode_opml(content)
    return parse_opml_feeds(text)


def _decode_opml(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1]


def _normalize_attribute_name(value: str) -> str:
    local = _local_name(value).lower()
    return "".join(char for char in local if char.isalnum())


def _first_attribute(attributes: dict[str, str], *names: str) -> str | None:
    for name in names:
        normalized = _normalize_attribute_name(name)
        if normalized in attributes:
            return attributes[normalized]
    return None


def _normalize_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _looks_like_url(value: str | None) -> bool:
    text = (value or "").strip().lower()
    return text.startswith("http://") or text.startswith("https://")


def _count_source_files(files) -> int:
    return len(list(files if isinstance(files, (list, tuple)) else [files]))


def _list_feed_articles(feed_id: int):
    if not hasattr(repository, "list_articles"):
        return []
    return repository.list_articles(feed_id=feed_id)


def _validation_message(exc: ValidationError) -> str:
    first = exc.errors()[0] if exc.errors() else {}
    return str(first.get("msg") or "Invalid feed URL")


def _log_failed_import(url: str, message: str) -> None:
    if hasattr(repository, "log_feed_event"):
        repository.log_feed_event(None, url, "failed", message)
