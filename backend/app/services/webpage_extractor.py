from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

DEFAULT_TIMEOUT_SECONDS = 10
MIN_CONTENT_TEXT_LENGTH = 280
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 RSSReader/0.1"
)


def should_fetch_full_article(content: str | None, summary: str | None, link: str | None) -> bool:
    if not link:
        return False
    source_text = _text_length(content) or _text_length(summary)
    return source_text < MIN_CONTENT_TEXT_LENGTH


def extract_article_html(url: str) -> str | None:
    document_class = _get_document_class()
    if document_class is None:
        return None

    html = _fetch_html(url)
    if not html:
        return None

    document = document_class(html)
    article_html = document.summary(html_partial=True)
    if not article_html:
        return None

    article_soup = BeautifulSoup(article_html, "html.parser")
    _absolutize_media_urls(article_soup, url)
    cleaned = str(article_soup)
    return cleaned.strip() or None


def _fetch_html(url: str) -> str | None:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None


def _absolutize_media_urls(soup: BeautifulSoup, base_url: str) -> None:
    for tag_name, attr_name in (("img", "src"), ("source", "src"), ("video", "src"), ("audio", "src"), ("a", "href")):
        for node in soup.find_all(tag_name):
            value = node.get(attr_name)
            if isinstance(value, str) and value.strip():
                node[attr_name] = urljoin(base_url, value.strip())


def _text_length(value: str | None) -> int:
    if not value:
        return 0
    return len(BeautifulSoup(value, "html.parser").get_text(" ", strip=True))


def _get_document_class():
    try:
        from readability import Document
    except ImportError:
        return None
    return Document
