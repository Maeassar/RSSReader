import feedparser


def parse_feed(url: str) -> dict:
    parsed = feedparser.parse(url)
    return {
        "title": parsed.feed.get("title", url),
        "site_url": parsed.feed.get("link"),
        "entries": [
            {
                "title": entry.get("title", "Untitled"),
                "url": entry.get("link"),
                "summary": entry.get("summary"),
            }
            for entry in parsed.entries
        ],
    }

