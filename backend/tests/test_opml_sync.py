import asyncio
import sqlite3
import unittest
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from app.repositories.sqlite_repository import SQLiteRepository
from app.services import feed_service, opml_service


class FakeUploadFile:
    def __init__(self, content: str, filename: str = "subscriptions.opml") -> None:
        self.filename = filename
        self.content = content.encode("utf-8")

    async def read(self) -> bytes:
        return self.content


class FakeOPMLRepository:
    def __init__(self) -> None:
        self.feeds = [
            {
                "id": 1,
                "title": "Existing",
                "url": "https://example.com/existing.xml",
                "site_url": "https://example.com",
                "description": None,
                "last_sync_at": None,
                "created_at": datetime.now(timezone.utc),
            }
        ]
        self.logs = []
        self.articles = []
        self.create_feed_calls = 0
        self.create_feed_metadata_calls = 0
        self.sync_feed_calls = 0

    def list_feeds(self):
        return list(self.feeds)

    def get_feed(self, feed_id):
        for feed in self.feeds:
            if feed["id"] == feed_id:
                return feed
        raise ValueError(f"Feed {feed_id} not found")

    def create_feed(self, payload):
        self.create_feed_calls += 1
        raise AssertionError("OPML import should create metadata before syncing feeds")

    def create_feed_metadata(self, payload):
        self.create_feed_metadata_calls += 1
        url = str(payload.url)
        if url == "https://example.com/failing.xml":
            raise ValueError("Unable to save feed metadata")
        feed = {
            "id": len(self.feeds) + 1,
            "title": payload.title or url,
            "url": url,
            "site_url": None,
            "description": None,
            "last_sync_at": None,
            "created_at": datetime.now(timezone.utc),
        }
        self.feeds.append(feed)
        self.log_feed_event(feed["id"], url, "pending", "Imported feed metadata from OPML. Run sync to fetch articles.")
        return feed

    def sync_feed(self, feed_id):
        self.sync_feed_calls += 1
        feed = self.get_feed(feed_id)
        if feed["url"] == "https://example.com/sync-fails.xml":
            self.log_feed_event(feed_id, feed["url"], "failed", "network error")
            raise ValueError("network error")
        feed["title"] = "Parsed title"
        feed["last_sync_at"] = datetime.now(timezone.utc)
        self.articles.append(self._article(feed_id, feed["title"]))
        self.log_feed_event(feed_id, feed["url"], "success", "Synced feed and saved 1 new entries.")
        return feed

    def update_feed(self, feed_id, payload):
        feed = self.get_feed(feed_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                feed[key] = str(value) if key == "url" else value
        return feed

    def log_feed_event(self, feed_id, url, status, message):
        feed = next((feed for feed in self.feeds if feed["id"] == feed_id), None)
        self.logs.append(
            {
                "feed_id": feed_id,
                "url": url,
                "feed_title": feed["title"] if feed else None,
                "status": status,
                "message": message,
            }
        )

    def list_articles(self, feed_id=None, tag_id=None, unread=None, starred=None):
        articles = list(self.articles)
        if feed_id is not None:
            articles = [article for article in articles if article["feed_id"] == feed_id]
        return articles

    def _article(self, feed_id, feed_title):
        article_id = len(self.articles) + 1
        return {
            "id": article_id,
            "feed_id": feed_id,
            "feed_title": feed_title,
            "title": f"Article {article_id}",
            "url": f"https://example.com/articles/{article_id}",
            "author": None,
            "published_at": datetime.now(timezone.utc),
            "summary": None,
            "raw_html": None,
            "cleaned_html": None,
            "cleaned_markdown": None,
            "is_read": False,
            "is_starred": False,
            "tag_ids": [],
            "created_at": datetime.now(timezone.utc),
        }


class FakeSyncRepository:
    def list_feeds(self):
        return [
            {"id": 1, "title": "Working", "url": "https://example.com/working.xml"},
            {"id": 2, "title": "Broken", "url": "https://example.com/broken.xml"},
        ]

    def sync_feed(self, feed_id):
        if feed_id == 2:
            raise ValueError("network error")
        return {
            "id": 1,
            "title": "Working",
            "url": "https://example.com/working.xml",
            "site_url": None,
            "description": None,
            "last_sync_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
        }


class FakeDeleteRepository:
    def __init__(self) -> None:
        self.feed_ids = {1, 2}
        self.deleted = []

    def delete_feed(self, feed_id):
        if feed_id not in self.feed_ids:
            raise ValueError(f"Feed {feed_id} not found")
        self.feed_ids.remove(feed_id)
        self.deleted.append(feed_id)


class FakeCreateRepository:
    def __init__(self, sync_error: str | None = None) -> None:
        self.sync_error = sync_error
        self.feeds = []
        self.articles = []
        self.logs = []

    def create_feed_metadata(self, payload):
        feed = {
            "id": len(self.feeds) + 1,
            "title": payload.title or str(payload.url),
            "url": str(payload.url),
            "site_url": None,
            "description": None,
            "last_sync_at": None,
            "created_at": datetime.now(timezone.utc),
        }
        self.feeds.append(feed)
        return feed

    def get_feed(self, feed_id):
        for feed in self.feeds:
            if feed["id"] == feed_id:
                return feed
        raise ValueError(f"Feed {feed_id} not found")

    def sync_feed(self, feed_id):
        feed = self.get_feed(feed_id)
        if self.sync_error:
            self.logs.append({"feed_id": feed_id, "status": "failed", "message": self.sync_error})
            raise ValueError(self.sync_error)
        feed["title"] = "Parsed title"
        feed["last_sync_at"] = datetime.now(timezone.utc)
        self.articles.append({"feed_id": feed_id, "title": "Synced article"})
        self.logs.append({"feed_id": feed_id, "status": "success", "message": "Synced feed and saved 1 new entries."})
        return feed

    def update_feed(self, feed_id, payload):
        feed = self.get_feed(feed_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                feed[key] = str(value) if key == "url" else value
        return feed


class OPMLServiceTest(unittest.TestCase):
    def test_parse_nested_opml_deduplicates_feed_urls(self):
        items = opml_service.parse_opml_feeds(
            """
            <opml version="2.0">
              <body>
                <outline text="Folder">
                  <outline text="One" type="rss" xmlUrl="https://example.com/one.xml" />
                  <outline text="Duplicate" type="rss" xmlUrl="https://example.com/one.xml" />
                </outline>
              </body>
            </opml>
            """
        )

        self.assertEqual(items, [{"url": "https://example.com/one.xml", "title": "One"}])

    def test_parse_opml_accepts_common_url_attribute_variants(self):
        items = opml_service.parse_opml_feeds(
            """
            <opml version="2.0">
              <body>
                <outline text="Feed URL" feedUrl="https://example.com/feed-url.xml" />
                <outline title="Plain URL" url="https://example.com/plain-url.xml" />
                <outline text="https://example.com/text-url.xml" />
              </body>
            </opml>
            """
        )

        self.assertEqual(
            items,
            [
                {"url": "https://example.com/feed-url.xml", "title": "Feed URL"},
                {"url": "https://example.com/plain-url.xml", "title": "Plain URL"},
                {"url": "https://example.com/text-url.xml", "title": "https://example.com/text-url.xml"},
            ],
        )

    def test_parse_opml_uploads_returns_pending_items_before_importing(self):
        items = asyncio.run(
            opml_service.parse_opml_uploads(
                [
                    FakeUploadFile(
                        """
                        <opml version="2.0">
                          <body>
                            <outline text="One" xmlUrl="https://example.com/one.xml" />
                          </body>
                        </opml>
                        """,
                        "one.opml",
                    )
                ]
            )
        )

        self.assertEqual(items[0]["status"], "pending")
        self.assertEqual(items[0]["message"], "正在上传")
        self.assertEqual(items[0]["url"], "https://example.com/one.xml")
        self.assertEqual(items[0]["source_file"], "one.opml")

    def test_parse_opml_uploads_reports_empty_files(self):
        items = asyncio.run(
            opml_service.parse_opml_uploads(
                [
                    FakeUploadFile(
                        """
                        <opml version="2.0">
                          <body>
                            <outline text="Folder" />
                          </body>
                        </opml>
                        """,
                        "empty.opml",
                    )
                ]
            )
        )

        self.assertEqual(items[0]["status"], "failed")
        self.assertEqual(items[0]["message"], "No feed URLs found in OPML file.")

    def test_import_opml_reports_imported_skipped_and_failed_items(self):
        old_repository = opml_service.repository
        fake_repository = FakeOPMLRepository()
        opml_service.repository = fake_repository
        try:
            report = asyncio.run(
                opml_service.import_opml(
                    [
                        FakeUploadFile(
                        """
                        <opml version="2.0">
                          <body>
                            <outline text="Existing" xmlUrl="https://example.com/existing.xml" />
                            <outline text="New Feed" xmlUrl="https://example.com/new.xml" />
                            <outline text="Invalid" xmlUrl="not-a-url" />
                            <outline text="Failing" xmlUrl="https://example.com/failing.xml" />
                            <outline text="Sync Fails" xmlUrl="https://example.com/sync-fails.xml" />
                          </body>
                        </opml>
                        """
                        )
                    ]
                )
            )
        finally:
            opml_service.repository = old_repository

        self.assertEqual(report["files"], 1)
        self.assertEqual(report["total"], 5)
        self.assertEqual(report["imported"], 1)
        self.assertEqual(report["partial"], 1)
        self.assertEqual(report["skipped"], 1)
        self.assertEqual(report["failed"], 2)
        self.assertEqual([item["status"] for item in report["results"]], ["skipped", "imported", "failed", "failed", "partial"])
        self.assertEqual(fake_repository.create_feed_calls, 0)
        self.assertEqual(fake_repository.create_feed_metadata_calls, 3)
        self.assertEqual(fake_repository.sync_feed_calls, 2)
        self.assertEqual(len([item for item in fake_repository.logs if item["status"] == "failed"]), 3)
        self.assertIsNotNone(report["results"][1]["feed"]["last_sync_at"])
        self.assertEqual(report["results"][1]["feed"]["title"], "New Feed")
        self.assertEqual(len(report["results"][1]["articles"]), 1)
        self.assertEqual(report["results"][1]["articles"][0]["feed_id"], report["results"][1]["feed"]["id"])
        self.assertIsNone(report["results"][4]["feed"]["last_sync_at"])
        self.assertEqual(report["results"][4]["message"], "network error")

    def test_import_multiple_opml_files_merges_results_and_reports_file_errors(self):
        old_repository = opml_service.repository
        fake_repository = FakeOPMLRepository()
        opml_service.repository = fake_repository
        try:
            report = asyncio.run(
                opml_service.import_opml(
                    [
                        FakeUploadFile(
                            """
                            <opml version="2.0">
                              <body>
                                <outline text="One" xmlUrl="https://example.com/one.xml" />
                              </body>
                            </opml>
                            """,
                            "one.opml",
                        ),
                        FakeUploadFile(
                            """
                            <opml version="2.0">
                              <body>
                                <outline text="Duplicate One" xmlUrl="https://example.com/one.xml" />
                                <outline text="Two" xmlUrl="https://example.com/two.xml" />
                              </body>
                            </opml>
                            """,
                            "two.opml",
                        ),
                        FakeUploadFile("<opml><body>", "broken.opml"),
                    ]
                )
            )
        finally:
            opml_service.repository = old_repository

        self.assertEqual(report["files"], 3)
        self.assertEqual(report["total"], 4)
        self.assertEqual(report["imported"], 2)
        self.assertEqual(report["partial"], 0)
        self.assertEqual(report["skipped"], 1)
        self.assertEqual(report["failed"], 1)
        self.assertEqual([item["source_file"] for item in report["results"]], ["one.opml", "two.opml", "two.opml", "broken.opml"])
        self.assertEqual(report["results"][1]["message"], "Duplicate feed in selected OPML files.")

    def test_export_opml_uses_current_repository_feeds(self):
        old_repository = opml_service.repository
        fake_repository = FakeOPMLRepository()
        opml_service.repository = fake_repository
        try:
            xml_text = opml_service.export_opml()
        finally:
            opml_service.repository = old_repository

        root = ET.fromstring(xml_text)
        outlines = [item for item in root.iter("outline")]
        self.assertEqual(len(outlines), 1)
        self.assertEqual(outlines[0].attrib["xmlUrl"], "https://example.com/existing.xml")
        self.assertEqual(outlines[0].attrib["htmlUrl"], "https://example.com")

    def test_export_opml_can_filter_selected_feed_ids(self):
        old_repository = opml_service.repository
        fake_repository = FakeOPMLRepository()
        fake_repository.feeds.append(
            {
                "id": 2,
                "title": "Second",
                "url": "https://example.com/second.xml",
                "site_url": None,
                "description": None,
                "last_sync_at": None,
                "created_at": datetime.now(timezone.utc),
            }
        )
        opml_service.repository = fake_repository
        try:
            xml_text = opml_service.export_opml([2])
        finally:
            opml_service.repository = old_repository

        root = ET.fromstring(xml_text)
        outlines = [item for item in root.iter("outline")]
        self.assertEqual(len(outlines), 1)
        self.assertEqual(outlines[0].attrib["xmlUrl"], "https://example.com/second.xml")

    def test_export_opml_rejects_unknown_selected_feed_ids(self):
        old_repository = opml_service.repository
        fake_repository = FakeOPMLRepository()
        opml_service.repository = fake_repository
        try:
            with self.assertRaises(ValueError):
                opml_service.export_opml([999])
        finally:
            opml_service.repository = old_repository


class SyncAllServiceTest(unittest.TestCase):
    def test_create_feed_syncs_new_feed_and_reports_success(self):
        old_repository = feed_service.repository
        fake_repository = FakeCreateRepository()
        feed_service.repository = fake_repository
        try:
            result = feed_service.create_feed(type("Payload", (), {"url": "https://example.com/feed.xml", "title": "Example"})())
        finally:
            feed_service.repository = old_repository

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Feed added and synced successfully.")
        self.assertEqual(result["feed"]["title"], "Example")
        self.assertIsNotNone(result["feed"]["last_sync_at"])
        self.assertEqual(fake_repository.articles, [{"feed_id": 1, "title": "Synced article"}])

    def test_create_feed_keeps_feed_and_reports_partial_when_initial_sync_fails(self):
        old_repository = feed_service.repository
        fake_repository = FakeCreateRepository(sync_error="network error")
        feed_service.repository = fake_repository
        try:
            result = feed_service.create_feed(type("Payload", (), {"url": "https://example.com/feed.xml", "title": "Example"})())
        finally:
            feed_service.repository = old_repository

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["message"], "network error")
        self.assertEqual(len(fake_repository.feeds), 1)
        self.assertIsNone(result["feed"]["last_sync_at"])
        self.assertEqual(fake_repository.logs[0]["status"], "failed")

    def test_sync_all_keeps_syncing_when_one_feed_fails(self):
        old_repository = feed_service.repository
        feed_service.repository = FakeSyncRepository()
        try:
            report = feed_service.sync_all_feeds()
        finally:
            feed_service.repository = old_repository

        self.assertEqual(report["total"], 2)
        self.assertEqual(report["success"], 1)
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["results"][0]["status"], "success")
        self.assertEqual(report["results"][1]["status"], "failed")

    def test_batch_delete_keeps_deleting_when_one_feed_fails(self):
        old_repository = feed_service.repository
        fake_repository = FakeDeleteRepository()
        feed_service.repository = fake_repository
        try:
            report = feed_service.delete_feeds([1, 999, 1, 2])
        finally:
            feed_service.repository = old_repository

        self.assertEqual(report["total"], 4)
        self.assertEqual(report["success"], 2)
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["skipped"], 1)
        self.assertEqual(fake_repository.deleted, [1, 2])
        self.assertEqual([item["status"] for item in report["results"]], ["success", "failed", "skipped", "success"])


class EntryDeduplicationTest(unittest.TestCase):
    def test_create_feed_checks_existing_url_before_parsing(self):
        repository = object.__new__(SQLiteRepository)
        with sqlite3.connect(":memory:") as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("CREATE TABLE feeds (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE)")
            conn.execute("INSERT INTO feeds (url) VALUES (?)", ("https://openai.com/news/rss.xml",))

            original_get_connection = __import__("app.repositories.sqlite_repository", fromlist=["get_connection"]).get_connection
            sqlite_module = __import__("app.repositories.sqlite_repository", fromlist=["get_connection"])
            sqlite_module.get_connection = lambda: conn
            repository._parse_feed = lambda _url: (_ for _ in ()).throw(AssertionError("should not parse existing feed"))
            try:
                with self.assertRaisesRegex(ValueError, "Feed already exists"):
                    repository.create_feed(type("Payload", (), {"url": "https://openai.com/news/rss.xml", "title": None})())
            finally:
                sqlite_module.get_connection = original_get_connection

    def test_split_entries_deduplicates_items_with_same_link_in_one_feed_payload(self):
        repository = object.__new__(SQLiteRepository)
        with sqlite3.connect(":memory:") as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(
                """
                CREATE TABLE entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_id INTEGER NOT NULL,
                    guid TEXT,
                    link TEXT,
                    UNIQUE(feed_id, guid),
                    UNIQUE(feed_id, link)
                )
                """
            )
            pending, existing = repository._split_entries_by_existence(
                conn,
                1,
                [
                    {"guid": "first", "link": "https://feeds.bbci.co.uk/news/rss.xml#shared", "title": "First"},
                    {"guid": "second", "link": "https://feeds.bbci.co.uk/news/rss.xml#shared", "title": "Second"},
                ],
            )

        self.assertEqual(len(pending), 1)
        self.assertEqual(existing, [])
        self.assertEqual(pending[0]["title"], "First")


if __name__ == "__main__":
    unittest.main()
