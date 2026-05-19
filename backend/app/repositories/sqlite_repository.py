from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

from app.database import get_connection, initialize_database
from app.services.feed_parser import parse_feed


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteRepository:
    def __init__(self) -> None:
        initialize_database()
        self.tags: list[dict] = []

    def list_feeds(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM feeds ORDER BY created_at DESC").fetchall()
        return [self._feed(row) for row in rows]

    def get_feed(self, feed_id: int):
        row = self._feed_row(feed_id)
        return self._feed(row)

    def create_feed(self, payload):
        url = str(payload.url)
        try:
            parsed = parse_feed(url)
        except Exception as exc:
            self._log(None, url, "failed", str(exc))
            raise ValueError(str(exc)) from exc

        timestamp = now()
        title = payload.title or parsed["title"]
        with get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO feeds (
                        url, title, description, site_url, language,
                        last_build_date, last_fetched_at, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        url,
                        title,
                        parsed.get("description"),
                        parsed.get("site_url"),
                        parsed.get("language"),
                        parsed.get("last_build_date"),
                        timestamp,
                        timestamp,
                        timestamp,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("Feed already exists") from exc
            feed_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO feed_fetch_logs (feed_id, url, status, message, fetched_at) VALUES (?, ?, ?, ?, ?)",
                (feed_id, url, "success", "Created feed metadata.", timestamp),
            )
            row = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
        inserted = self._save_entries_for_feed(feed_id, parsed["entries"])
        self._log(feed_id, url, "success", f"Saved {inserted} entries.")
        return self._feed(row)

    def update_feed(self, feed_id, payload):
        self._feed_row(feed_id)
        data = payload.model_dump(exclude_unset=True)
        allowed = {key: value for key, value in data.items() if value is not None and key in {"title", "url", "description"}}
        if not allowed:
            return self.get_feed(feed_id)
        columns = ", ".join(f"{key} = ?" for key in allowed)
        values = [str(value) if key == "url" else value for key, value in allowed.items()]
        values.extend([now(), feed_id])
        with get_connection() as conn:
            conn.execute(f"UPDATE feeds SET {columns}, updated_at = ? WHERE id = ?", values)
        return self.get_feed(feed_id)

    def delete_feed(self, feed_id):
        self._feed_row(feed_id)
        with get_connection() as conn:
            conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))

    def sync_feed(self, feed_id):
        feed = self._feed_row(feed_id)
        url = feed["url"]
        timestamp = now()
        try:
            parsed = parse_feed(url)
            inserted = self._save_entries_for_feed(feed_id, parsed["entries"])
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE feeds
                    SET title = ?, description = ?, site_url = ?, language = ?,
                        last_build_date = ?, last_fetched_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        parsed["title"],
                        parsed.get("description"),
                        parsed.get("site_url"),
                        parsed.get("language"),
                        parsed.get("last_build_date"),
                        timestamp,
                        timestamp,
                        feed_id,
                    ),
                )
                conn.execute(
                    "INSERT INTO feed_fetch_logs (feed_id, url, status, message, fetched_at) VALUES (?, ?, ?, ?, ?)",
                    (feed_id, url, "success", f"Synced feed and saved {inserted} new entries.", timestamp),
                )
        except Exception as exc:
            self._log(feed_id, url, "failed", str(exc))
            raise ValueError(str(exc)) from exc
        return self.get_feed(feed_id)

    def sync_all_feeds(self):
        return [self.sync_feed(feed["id"]) for feed in self.list_feeds()]

    def list_articles(self, feed_id=None, tag_id=None, unread=None, starred=None):
        query = """
            SELECT entries.*, feeds.title AS feed_title
            FROM entries
            JOIN feeds ON feeds.id = entries.feed_id
            WHERE 1 = 1
        """
        params = []
        if feed_id is not None:
            query += " AND entries.feed_id = ?"
            params.append(feed_id)
        if unread is True:
            query += " AND entries.is_read = 0"
        if starred is True:
            query += " AND entries.is_starred = 1"
        query += " ORDER BY COALESCE(entries.published_at, entries.created_at) DESC"
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._article(row) for row in rows]

    def get_article(self, article_id):
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT entries.*, feeds.title AS feed_title
                FROM entries
                JOIN feeds ON feeds.id = entries.feed_id
                WHERE entries.id = ?
                """,
                (article_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Article {article_id} not found")
        return self._article(row)

    def set_article_flag(self, article_id, key, value):
        if key not in {"is_read", "is_starred"}:
            raise ValueError(f"Unsupported article flag: {key}")
        self.get_article(article_id)
        with get_connection() as conn:
            conn.execute(f"UPDATE entries SET {key} = ? WHERE id = ?", (1 if value else 0, article_id))
        return self.get_article(article_id)

    def list_logs(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM feed_fetch_logs ORDER BY fetched_at DESC").fetchall()
        return [
            {
                "id": row["id"],
                "feed_id": row["feed_id"],
                "status": row["status"],
                "message": row["message"],
                "created_at": row["fetched_at"],
            }
            for row in rows
        ]

    def get_note(self, article_id):
        self.get_article(article_id)
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM notes WHERE entry_id = ?", (article_id,)).fetchone()
        if row is None:
            return {"id": 0, "article_id": article_id, "content_markdown": "", "updated_at": now()}
        return {"id": row["id"], "article_id": row["entry_id"], "content_markdown": row["content"], "updated_at": row["updated_at"]}

    def update_note(self, article_id, payload):
        self.get_article(article_id)
        timestamp = now()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO notes (entry_id, content, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(entry_id) DO UPDATE SET content = excluded.content, updated_at = excluded.updated_at
                """,
                (article_id, payload.content_markdown, timestamp, timestamp),
            )
        return self.get_note(article_id)

    def create_ai_result(self, article_id, result_type, prompt, result):
        self.get_article(article_id)
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO ai_results (entry_id, task_type, prompt, result)
                VALUES (?, ?, ?, ?)
                """,
                (article_id, result_type, prompt, result),
            )
            row = conn.execute("SELECT * FROM ai_results WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return {
            "id": row["id"],
            "article_id": row["entry_id"],
            "type": row["task_type"],
            "provider_id": None,
            "prompt": row["prompt"],
            "result": row["result"],
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "created_at": row["created_at"],
        }

    def stats(self):
        with get_connection() as conn:
            article_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            ai_count = conn.execute("SELECT COUNT(*) FROM ai_results").fetchone()[0]
        return {"total_articles": article_count, "total_calls": ai_count, "input_tokens": 0, "output_tokens": 0, "by_feature": []}

    def list_tags(self):
        return self.tags

    def create_tag(self, payload):
        tag = {"id": len(self.tags) + 1, **payload.model_dump()}
        self.tags.append(tag)
        return tag

    def update_tag(self, tag_id, payload):
        for tag in self.tags:
            if tag["id"] == tag_id:
                tag.update({key: value for key, value in payload.model_dump(exclude_unset=True).items() if value is not None})
                return tag
        raise ValueError(f"Tag {tag_id} not found")

    def delete_tag(self, tag_id):
        self.tags = [tag for tag in self.tags if tag["id"] != tag_id]

    def set_article_tags(self, article_id, tag_ids):
        self.get_article(article_id)
        return {"article_id": article_id, "tag_ids": tag_ids}

    def _save_entries_for_feed(self, feed_id: int, entries: list[dict]) -> int:
        with get_connection() as conn:
            pending_entries, existing_entries = self._split_entries_by_existence(conn, feed_id, entries)

        prepared_entries = [(entry, self._entry_content(entry)) for entry in pending_entries]
        prepared_existing = [(entry, self._entry_content(entry)) for entry in existing_entries]

        with get_connection() as conn:
            return self._save_prepared_entries(conn, feed_id, prepared_entries, prepared_existing)

    def _split_entries_by_existence(
        self,
        conn: sqlite3.Connection,
        feed_id: int,
        entries: list[dict],
    ) -> tuple[list[dict], list[dict]]:
        pending_entries = []
        existing_entries = []
        for entry in entries:
            if self._entry_exists(conn, feed_id, entry.get("guid"), entry.get("link")):
                existing_entries.append(entry)
            else:
                pending_entries.append(entry)
        return pending_entries, existing_entries

    def _save_prepared_entries(
        self,
        conn: sqlite3.Connection,
        feed_id: int,
        prepared_entries: list[tuple[dict, dict[str, str | None]]],
        prepared_existing: list[tuple[dict, dict[str, str | None]]],
    ) -> int:
        inserted = 0
        for entry, content in prepared_entries:
            conn.execute(
                """
                INSERT INTO entries (
                    feed_id, guid, title, link, author, summary, content,
                    raw_html, cleaned_html, cleaned_markdown,
                    published_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feed_id,
                    entry.get("guid"),
                    entry["title"],
                    entry.get("link"),
                    entry.get("author"),
                    entry.get("summary"),
                    content["content"],
                    content["raw_html"],
                    content["cleaned_html"],
                    content["cleaned_markdown"],
                    entry.get("published_at"),
                    entry.get("updated_at"),
                ),
            )
            inserted += 1

        for entry, content in prepared_existing:
            self._update_existing_entry_content(conn, feed_id, entry, content)
        return inserted

    def _entry_exists(self, conn: sqlite3.Connection, feed_id: int, guid: str | None, link: str | None) -> bool:
        if guid:
            row = conn.execute("SELECT id FROM entries WHERE feed_id = ? AND guid = ?", (feed_id, guid)).fetchone()
            if row:
                return True
        if link:
            row = conn.execute("SELECT id FROM entries WHERE feed_id = ? AND link = ?", (feed_id, link)).fetchone()
            if row:
                return True
        return False

    def _entry_content(self, entry: dict) -> dict[str, str | None]:
        fallback = entry.get("content") or entry.get("summary")
        return {
            "content": fallback,
            "raw_html": fallback,
            "cleaned_html": fallback,
            "cleaned_markdown": None,
        }

    def _update_existing_entry_content(
        self,
        conn: sqlite3.Connection,
        feed_id: int,
        entry: dict,
        content: dict[str, str | None],
    ) -> None:
        if not content.get("cleaned_html"):
            return
        row = None
        if entry.get("guid"):
            row = conn.execute(
                "SELECT id, cleaned_html, content FROM entries WHERE feed_id = ? AND guid = ?",
                (feed_id, entry["guid"]),
            ).fetchone()
        if row is None and entry.get("link"):
            row = conn.execute(
                "SELECT id, cleaned_html, content FROM entries WHERE feed_id = ? AND link = ?",
                (feed_id, entry["link"]),
            ).fetchone()
        if row is None:
            return
        current = row["cleaned_html"] or row["content"] or ""
        incoming = content["cleaned_html"] or ""
        if len(incoming) <= len(current):
            return
        conn.execute(
            """
            UPDATE entries
            SET content = ?, raw_html = ?, cleaned_html = ?, cleaned_markdown = ?,
                summary = COALESCE(summary, ?), updated_at = COALESCE(?, updated_at)
            WHERE id = ?
            """,
            (
                content["content"],
                content["raw_html"],
                content["cleaned_html"],
                content["cleaned_markdown"],
                entry.get("summary"),
                entry.get("updated_at"),
                row["id"],
            ),
        )

    def _feed_row(self, feed_id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
        if row is None:
            raise ValueError(f"Feed {feed_id} not found")
        return row

    def _log(self, feed_id: int | None, url: str, status: str, message: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO feed_fetch_logs (feed_id, url, status, message, fetched_at) VALUES (?, ?, ?, ?, ?)",
                (feed_id, url, status, message, now()),
            )

    def _feed(self, row):
        return {
            "id": row["id"],
            "title": row["title"],
            "url": row["url"],
            "site_url": row["site_url"],
            "description": row["description"],
            "last_sync_at": row["last_fetched_at"],
            "created_at": row["created_at"],
        }

    def _article(self, row):
        return {
            "id": row["id"],
            "feed_id": row["feed_id"],
            "feed_title": row["feed_title"],
            "title": row["title"],
            "url": row["link"] or "",
            "author": row["author"],
            "published_at": row["published_at"],
            "summary": row["summary"],
            "raw_html": row["raw_html"] or row["content"],
            "cleaned_html": row["cleaned_html"] or row["content"],
            "cleaned_markdown": row["cleaned_markdown"],
            "is_read": bool(row["is_read"]),
            "is_starred": bool(row["is_starred"]),
            "tag_ids": [],
            "created_at": row["created_at"],
        }


repository = SQLiteRepository()
