import unittest
from http.client import RemoteDisconnected
from unittest.mock import patch

from app.services import feed_parser


class FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self.content


class FakeParsedFeed:
    bozo = False
    feed = {}
    entries = [
        {
            "id": "entry-1",
            "title": "Entry without feed metadata",
            "summary": "This summary is long enough to avoid fetching the source page. " * 8,
        }
    ]


class FeedParserTest(unittest.TestCase):
    def test_fetch_feed_retries_remote_disconnect(self):
        calls = []

        def flaky_urlopen(_request, timeout):
            calls.append(timeout)
            if len(calls) == 1:
                raise RemoteDisconnected("remote closed")
            return FakeResponse(b"<rss><channel><title>OK</title></channel></rss>")

        with patch.object(feed_parser, "urlopen", side_effect=flaky_urlopen), patch.object(feed_parser, "sleep"):
            content = feed_parser._fetch_feed_content("https://openai.com/news/rss.xml")

        self.assertEqual(content, b"<rss><channel><title>OK</title></channel></rss>")
        self.assertEqual(len(calls), 2)

    def test_parse_feed_allows_entries_when_feed_metadata_is_empty(self):
        with patch.object(feed_parser, "_fetch_feed_content", return_value=b"<rss />"), patch.object(feed_parser.feedparser, "parse", return_value=FakeParsedFeed()):
            parsed = feed_parser.parse_feed("https://openai.com/news/rss.xml")

        self.assertEqual(parsed["title"], "https://openai.com/news/rss.xml")
        self.assertEqual(len(parsed["entries"]), 1)


if __name__ == "__main__":
    unittest.main()
