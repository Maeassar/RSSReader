import feedparser
from datetime import datetime, timezone
from http.client import RemoteDisconnected
import socket
import ssl
from time import sleep
from time import mktime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_SECONDS = 12
MAX_FETCH_ATTEMPTS = 3
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 RSSReader/0.1"
)
FEED_REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
}


def parse_feed(url: str) -> dict:
    parsed = feedparser.parse(_fetch_feed_content(url))
    if parsed.bozo and not parsed.entries:
        message = getattr(parsed.bozo_exception, "args", ["Invalid RSS/Atom feed"])[0]
        raise ValueError(f"Invalid RSS/Atom feed: {message}")
    if not parsed.feed and not parsed.entries:
        raise ValueError("Invalid RSS/Atom feed: no feed metadata or entries found.")
    feed_metadata = parsed.feed or {}

    return {
        "url": url,
        "title": feed_metadata.get("title") or url,
        "description": feed_metadata.get("description") or feed_metadata.get("subtitle"),
        "site_url": feed_metadata.get("link"),
        "language": feed_metadata.get("language"),
        "last_build_date": _format_time(feed_metadata.get("updated_parsed") or feed_metadata.get("published_parsed")),
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


def _fetch_feed_content(url: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
        request = Request(url, headers=FEED_REQUEST_HEADERS)
        try:
            with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code < 500 or attempt == MAX_FETCH_ATTEMPTS:
                raise ValueError(_http_error_message(exc)) from exc
            last_error = exc
        except (TimeoutError, RemoteDisconnected, ConnectionResetError, ssl.SSLError, URLError) as exc:
            last_error = exc
            if attempt == MAX_FETCH_ATTEMPTS:
                raise ValueError(_fetch_error_message(exc)) from exc
        except ValueError as exc:
            raise ValueError(f"Invalid feed URL: {exc}") from exc
        sleep(0.5 * attempt)

    raise ValueError(_fetch_error_message(last_error))


def _http_error_message(exc: HTTPError) -> str:
    if exc.code == 403:
        return "HTTP 403 Forbidden while loading feed. The site may block automated requests."
    if exc.code == 404:
        return "HTTP 404 Not Found while loading feed. Check whether the feed URL is correct."
    if 500 <= exc.code < 600:
        return f"HTTP {exc.code} server error while loading feed. The source site is temporarily unavailable."
    return f"HTTP {exc.code} error while loading feed: {exc.reason}"


def _url_error_message(reason) -> str:
    if isinstance(reason, socket.timeout):
        return f"Connection timed out after {DEFAULT_TIMEOUT_SECONDS} seconds while loading feed."
    if isinstance(reason, ssl.SSLError):
        return f"SSL error while loading feed: {reason}"
    if isinstance(reason, OSError):
        text = str(reason)
        lower = text.lower()
        if "getaddrinfo" in lower or "name or service not known" in lower or "nodename nor servname" in lower:
            return f"DNS lookup failed while loading feed: {text}"
        if "timed out" in lower:
            return f"Connection timed out after {DEFAULT_TIMEOUT_SECONDS} seconds while loading feed."
        if "connection refused" in lower or "actively refused" in lower:
            return f"Connection failed while loading feed: {text}"
        return f"Network error while loading feed: {text}"
    return f"Network error while loading feed: {reason}"


def _fetch_error_message(exc: Exception | None) -> str:
    if isinstance(exc, TimeoutError):
        return f"Connection timed out after {DEFAULT_TIMEOUT_SECONDS} seconds while loading feed."
    if isinstance(exc, ssl.SSLError):
        return f"SSL error while loading feed: {exc}"
    if isinstance(exc, URLError):
        return _url_error_message(exc.reason)
    if isinstance(exc, RemoteDisconnected):
        return "Remote server closed the connection while loading feed. Please retry later."
    if isinstance(exc, ConnectionResetError):
        return f"Connection failed while loading feed: {exc}"
    return f"Network error while loading feed: {exc}"


def _entry_content(entry) -> str | None:
    content = entry.get("content")
    if content and isinstance(content, list):
        first = content[0]
        content_html = first.get("value") if isinstance(first, dict) else None
    else:
        content_html = entry.get("summary")

    return content_html


def _format_time(value) -> str | None:
    if not value:
        return None
    return datetime.fromtimestamp(mktime(value), tz=timezone.utc).isoformat()
