from __future__ import annotations

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

DISALLOWED_TAGS = {
    "script",
    "style",
    "iframe",
    "object",
    "embed",
    "form",
    "input",
    "button",
    "select",
    "textarea",
    "noscript",
    "svg",
    "canvas",
}

DROP_EMPTY_TAGS = {
    "p",
    "div",
    "section",
    "article",
    "span",
    "blockquote",
    "li",
}

PREFERRED_ROOTS = ("article", "main", '[role="main"]', ".post-content", ".entry-content", ".article-content")
ALLOWED_ATTRS = {"href", "src", "alt", "title"}
LAZY_IMAGE_ATTRS = ("src", "data-src", "data-original", "data-lazy-src", "data-url")


def clean_html(raw_html: str | None) -> dict[str, str | None]:
    if not raw_html:
        return {"cleaned_html": None, "cleaned_markdown": None}

    soup = BeautifulSoup(raw_html, "html.parser")
    root = _pick_content_root(soup)

    for item in root.find_all(DISALLOWED_TAGS):
        item.decompose()

    _normalize_images(root)
    _sanitize_links(root)
    _strip_attributes(root)
    _unwrap_noise(root)
    _drop_empty_blocks(root)

    cleaned_html = root.decode_contents() if root is not soup else str(root)
    cleaned_html = cleaned_html.strip() or None
    cleaned_markdown = (
        md(
            cleaned_html,
            heading_style="ATX",
            bullets="-",
            strip=["img"],
        ).strip()
        if cleaned_html
        else None
    )

    return {
        "cleaned_html": cleaned_html,
        "cleaned_markdown": cleaned_markdown or None,
    }


def _pick_content_root(soup: BeautifulSoup) -> Tag | BeautifulSoup:
    for selector in PREFERRED_ROOTS:
        node = soup.select_one(selector)
        if isinstance(node, Tag):
            return node
    if soup.body:
        return soup.body
    return soup


def _normalize_images(root: Tag | BeautifulSoup) -> None:
    for image in root.find_all("img"):
        src = None
        for attr in LAZY_IMAGE_ATTRS:
            value = image.get(attr)
            if isinstance(value, str) and value.strip():
                src = value.strip()
                break
        if src:
            image["src"] = src
        else:
            image.decompose()
            continue

        alt = image.get("alt")
        image.attrs = {key: value for key, value in {"src": src, "alt": alt}.items() if value}


def _sanitize_links(root: Tag | BeautifulSoup) -> None:
    for link in root.find_all("a"):
        href = link.get("href")
        if not isinstance(href, str) or not href.strip():
            link.unwrap()
            continue
        link.attrs = {"href": href.strip(), "title": link.get("title")} if link.get("title") else {"href": href.strip()}


def _strip_attributes(root: Tag | BeautifulSoup) -> None:
    for node in root.find_all(True):
        if node.name in {"a", "img"}:
            node.attrs = {key: value for key, value in node.attrs.items() if key in ALLOWED_ATTRS and value}
            continue
        node.attrs = {}


def _unwrap_noise(root: Tag | BeautifulSoup) -> None:
    for node in root.find_all(["font", "figure", "figcaption"]):
        if node.name == "figure":
            continue
        node.unwrap()


def _drop_empty_blocks(root: Tag | BeautifulSoup) -> None:
    changed = True
    while changed:
        changed = False
        for node in root.find_all(DROP_EMPTY_TAGS):
            if node.find(["img", "video", "audio", "iframe"]):
                continue
            if node.get_text(strip=True):
                continue
            node.decompose()
            changed = True
