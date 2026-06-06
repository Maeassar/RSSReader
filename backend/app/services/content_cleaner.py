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
NOISE_MARKERS = (
    "sidebar",
    "aside",
    "related",
    "recommend",
    "recommended",
    "recirc",
    "promo",
    "advert",
    "ad-",
    " ad ",
    "social",
    "share",
    "newsletter",
    "outbrain",
    "taboola",
    "rail",
    "toolbar",
    "breadcrumb",
    "comment",
    "footer",
    "nav",
)
LAZY_IMAGE_ATTRS = (
    "src",
    "data-src",
    "data-original",
    "data-lazy-src",
    "data-url",
    "data-image",
    "data-thumbnail",
    "data-srcset",
    "srcset",
)


def clean_html(raw_html: str | None) -> dict[str, str | None]:
    if not raw_html:
        return {"cleaned_html": None, "cleaned_markdown": None}

    soup = BeautifulSoup(raw_html, "html.parser")
    root = _pick_content_root(soup)
    _replace_embedded_media(root)

    for item in root.find_all(DISALLOWED_TAGS):
        item.decompose()

    _remove_noise_blocks(root)
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


def _replace_embedded_media(root: Tag | BeautifulSoup) -> None:
    for node in root.find_all(["iframe", "embed", "object", "video"]):
        media_url = _embedded_media_url(node)
        if not media_url:
            node.decompose()
            continue

        replacement = root.new_tag("p")
        link = root.new_tag("a", href=media_url)
        link.string = _embedded_media_label(node)
        replacement.append(link)
        node.replace_with(replacement)


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
                src = _first_image_candidate(value.strip())
                break
        if src:
            image["src"] = src
        else:
            image.decompose()
            continue

        alt = image.get("alt")
        image.attrs = {key: value for key, value in {"src": src, "alt": alt}.items() if value}


def _embedded_media_url(node: Tag) -> str | None:
    for attr_name in ("src", "data", "href"):
        value = _node_attr(node, attr_name)
        if isinstance(value, str) and value.strip():
            return value.strip()

    if node.name == "video":
        for source in node.find_all("source"):
            value = _node_attr(source, "src")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _embedded_media_label(node: Tag) -> str:
    title = _node_attr(node, "title")
    if isinstance(title, str) and title.strip():
        return f"打开视频：{title.strip()}"
    return "打开视频原链接"


def _remove_noise_blocks(root: Tag | BeautifulSoup) -> None:
    for node in root.find_all(True):
        if node.name in {"aside", "nav", "footer"} or _has_noise_marker(node) or _is_link_heavy_block(node):
            node.decompose()


def _first_image_candidate(value: str) -> str:
    if "," not in value:
        return value.split()[0]
    first = value.split(",", 1)[0].strip()
    return first.split()[0] if first else value


def _sanitize_links(root: Tag | BeautifulSoup) -> None:
    for link in root.find_all("a"):
        href = _node_attr(link, "href")
        if not isinstance(href, str) or not href.strip():
            link.unwrap()
            continue
        title = _node_attr(link, "title")
        link.attrs = {"href": href.strip(), "title": title} if title else {"href": href.strip()}


def _strip_attributes(root: Tag | BeautifulSoup) -> None:
    for node in root.find_all(True):
        attrs = node.attrs if isinstance(node.attrs, dict) else {}
        if node.name in {"a", "img"}:
            node.attrs = {key: value for key, value in attrs.items() if key in ALLOWED_ATTRS and value}
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


def _has_noise_marker(node: Tag) -> bool:
    values = [
        _node_attr(node, "id"),
        _class_value(node),
        _node_attr(node, "role"),
        _node_attr(node, "aria-label"),
        _node_attr(node, "data-testid"),
    ]
    haystack = " ".join(value.strip().lower() for value in values if isinstance(value, str) and value.strip())
    if not haystack:
        return False
    return any(marker in haystack for marker in NOISE_MARKERS)


def _is_link_heavy_block(node: Tag) -> bool:
    links = node.find_all("a")
    if len(links) < 3:
        return False

    text = node.get_text(" ", strip=True)
    if not text:
        return True

    link_text_length = sum(len(link.get_text(" ", strip=True)) for link in links)
    return link_text_length >= len(text) * 0.6 and len(node.find_all("p")) <= 1


def _node_attr(node: Tag, key: str):
    attrs = node.attrs if isinstance(node.attrs, dict) else {}
    return attrs.get(key)


def _class_value(node: Tag) -> str | None:
    value = _node_attr(node, "class")
    if isinstance(value, (list, tuple)):
        parts = [item for item in value if isinstance(item, str) and item.strip()]
        return " ".join(parts) if parts else None
    if isinstance(value, str) and value.strip():
        return value
    return None
