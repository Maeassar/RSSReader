from __future__ import annotations

from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from pydantic import ValidationError

from app.repositories import repository
from app.schemas import FeedCreate


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
        attributes = {_local_name(key).lower(): value for key, value in outline.attrib.items()}
        url = _normalize_text(attributes.get("xmlurl"))
        if not url or url in seen_urls:
            continue
        title = _normalize_text(attributes.get("title")) or _normalize_text(attributes.get("text"))
        feeds.append({"url": url, "title": title})
        seen_urls.add(url)

    return feeds


async def import_opml(files):
    upload_files = list(files if isinstance(files, (list, tuple)) else [files])
    existing_feeds = {feed["url"].strip(): feed for feed in repository.list_feeds()}
    imported_urls: set[str] = set()
    results = []

    for file in upload_files:
        source_file = getattr(file, "filename", None) or "subscriptions.opml"
        try:
            feed_items = await _read_opml_file(file)
        except ValueError as exc:
            results.append(
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

        for item in feed_items:
            raw_url = item["url"] or ""
            title = item.get("title")
            try:
                payload = FeedCreate(title=title, url=raw_url)
            except ValidationError as exc:
                message = _validation_message(exc)
                _log_failed_import(raw_url, message)
                results.append(
                    {
                        "url": raw_url,
                        "title": title,
                        "status": "failed",
                        "message": message,
                        "feed": None,
                        "source_file": source_file,
                    }
                )
                continue

            url = str(payload.url)
            if url in imported_urls:
                results.append(
                    {
                        "url": url,
                        "title": title,
                        "status": "skipped",
                        "message": "Duplicate feed in selected OPML files.",
                        "feed": None,
                        "source_file": source_file,
                    }
                )
                continue
            if url in existing_feeds:
                results.append(
                    {
                        "url": url,
                        "title": title,
                        "status": "skipped",
                        "message": "Feed already exists.",
                        "feed": existing_feeds.get(url),
                        "source_file": source_file,
                    }
                )
                continue

            try:
                feed = repository.create_feed_metadata(payload)
            except ValueError as exc:
                message = str(exc)
                status = "skipped" if "already exists" in message.lower() else "failed"
                if status == "failed":
                    _log_failed_import(url, message)
                results.append(
                    {
                        "url": url,
                        "title": title,
                        "status": status,
                        "message": message,
                        "feed": None,
                        "source_file": source_file,
                    }
                )
                continue

            existing_feeds[url] = feed
            imported_urls.add(url)
            results.append(
                {
                    "url": url,
                    "title": title or feed["title"],
                    "status": "imported",
                    "message": "Feed imported. Run sync to fetch articles.",
                    "feed": feed,
                    "source_file": source_file,
                }
            )

    return {
        "files": len(upload_files),
        "total": len(results),
        "imported": sum(1 for item in results if item["status"] == "imported"),
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


def _normalize_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _validation_message(exc: ValidationError) -> str:
    first = exc.errors()[0] if exc.errors() else {}
    return str(first.get("msg") or "Invalid feed URL")


def _log_failed_import(url: str, message: str) -> None:
    if hasattr(repository, "log_feed_event"):
        repository.log_feed_event(None, url, "failed", message)
