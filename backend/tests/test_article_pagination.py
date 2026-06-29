import sqlite3
import unittest

from app.repositories import sqlite_repository as sqlite_module
from app.repositories.sqlite_repository import SQLiteRepository


class ArticlePaginationRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()
        self.repository = object.__new__(SQLiteRepository)
        self.original_get_connection = sqlite_module.get_connection
        sqlite_module.get_connection = lambda: self.conn

    def tearDown(self) -> None:
        sqlite_module.get_connection = self.original_get_connection
        self.conn.close()

    def test_list_article_items_is_paginated_and_omits_body_fields(self):
        page = self.repository.list_article_items(limit=2, offset=0)

        self.assertEqual(page["total"], 3)
        self.assertEqual(page["limit"], 2)
        self.assertEqual(page["offset"], 0)
        self.assertTrue(page["has_more"])
        self.assertEqual([item["id"] for item in page["items"]], [3, 2])
        self.assertNotIn("raw_html", page["items"][0])
        self.assertNotIn("cleaned_html", page["items"][0])
        self.assertNotIn("cleaned_markdown", page["items"][0])

    def test_filtering_and_counts_include_tags(self):
        unread_tagged = self.repository.list_article_items(tag_id=1, unread=True, limit=50, offset=0)
        counts = self.repository.article_counts()
        detail = self.repository.get_article(1)

        self.assertEqual([item["id"] for item in unread_tagged["items"]], [1])
        self.assertEqual(unread_tagged["total"], 1)
        self.assertEqual(counts["total"], 3)
        self.assertEqual(counts["unread"], 2)
        self.assertEqual(counts["starred"], 1)
        self.assertEqual(counts["by_feed"], {1: 2, 2: 1})
        self.assertEqual(counts["by_tag"], {1: 2, 2: 1})
        self.assertEqual(detail["tag_ids"], [1, 2])
        self.assertIn("cleaned_html", detail)

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                site_url TEXT,
                description TEXT,
                last_fetched_at TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                guid TEXT,
                title TEXT NOT NULL,
                link TEXT,
                author TEXT,
                summary TEXT,
                content TEXT,
                raw_html TEXT,
                cleaned_html TEXT,
                cleaned_markdown TEXT,
                published_at TEXT,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                is_starred INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE
            );
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL DEFAULT '#409eff',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE article_tags (
                entry_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (entry_id, tag_id),
                FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
            INSERT INTO feeds (id, title, url, site_url, description, last_fetched_at, created_at)
            VALUES
                (1, 'Feed One', 'https://example.com/one.xml', NULL, NULL, NULL, '2026-01-01T00:00:00+00:00'),
                (2, 'Feed Two', 'https://example.com/two.xml', NULL, NULL, NULL, '2026-01-01T00:00:00+00:00');
            INSERT INTO entries (
                id, feed_id, guid, title, link, author, summary, content,
                raw_html, cleaned_html, cleaned_markdown, published_at, created_at,
                is_read, is_starred
            )
            VALUES
                (1, 1, 'a', 'Old unread', 'https://example.com/a', NULL, 'Summary A', 'Body A',
                 '<p>Raw A</p>', '<p>Clean A</p>', 'Clean A', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00', 0, 1),
                (2, 1, 'b', 'Middle read', 'https://example.com/b', NULL, 'Summary B', 'Body B',
                 '<p>Raw B</p>', '<p>Clean B</p>', 'Clean B', '2026-01-02T00:00:00+00:00', '2026-01-02T00:00:00+00:00', 1, 0),
                (3, 2, 'c', 'New unread', 'https://example.com/c', NULL, 'Summary C', 'Body C',
                 '<p>Raw C</p>', '<p>Clean C</p>', 'Clean C', '2026-01-03T00:00:00+00:00', '2026-01-03T00:00:00+00:00', 0, 0);
            INSERT INTO tags (id, name, color, created_at, updated_at)
            VALUES
                (1, 'AI', '#3366ff', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00'),
                (2, 'Docs', '#00aa66', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00');
            INSERT INTO article_tags (entry_id, tag_id, created_at)
            VALUES
                (1, 1, '2026-01-01T00:00:00+00:00'),
                (1, 2, '2026-01-01T00:00:00+00:00'),
                (2, 1, '2026-01-01T00:00:00+00:00');
            """
        )


if __name__ == "__main__":
    unittest.main()
