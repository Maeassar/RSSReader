from bs4 import BeautifulSoup
from markdownify import markdownify as md


def clean_html(raw_html: str) -> dict[str, str]:
    soup = BeautifulSoup(raw_html, "html.parser")
    for item in soup(["script", "style"]):
        item.decompose()
    cleaned_html = str(soup)
    return {"cleaned_html": cleaned_html, "cleaned_markdown": md(cleaned_html)}

