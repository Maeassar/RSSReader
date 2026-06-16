from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

from app.database import get_connection, initialize_database
from app.services.content_cleaner import clean_html
from app.services.secret_store import decrypt_secret, encrypt_secret
from app.services.webpage_extractor import extract_article_html


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteRepository:
    def __init__(self) -> None:
        initialize_database()

    def list_feeds(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM feeds ORDER BY created_at DESC").fetchall()
        return [self._feed(row) for row in rows]

    def get_feed(self, feed_id: int):
        row = self._feed_row(feed_id)
        return self._feed(row)

    def create_feed_metadata(self, payload):
        url = str(payload.url)
        timestamp = now()
        title = payload.title or url
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
                        None,
                        None,
                        None,
                        None,
                        None,
                        timestamp,
                        timestamp,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("Feed already exists") from exc
            feed_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO feed_fetch_logs (feed_id, url, status, message, fetched_at) VALUES (?, ?, ?, ?, ?)",
                (feed_id, url, "pending", "Created feed metadata. Run sync to fetch articles.", timestamp),
            )
            row = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
        return self._feed(row)

    def create_feed(self, payload):
        url = str(payload.url)
        if self._feed_exists_by_url(url):
            raise ValueError("Feed already exists")

        try:
            parsed = self._parse_feed(url)
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
            entry_ids = [r["id"] for r in conn.execute(
                "SELECT id FROM entries WHERE feed_id = ?", (feed_id,)
            ).fetchall()]
            conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        # clean up vector index for deleted entries
        from app.services.rag_service import delete_entry_vec
        for eid in entry_ids:
            delete_entry_vec(eid)

    def sync_feed(self, feed_id):
        feed = self._feed_row(feed_id)
        url = feed["url"]
        timestamp = now()
        try:
            parsed = self._parse_feed(url)
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

    def search_articles(self, query: str, limit: int = 50) -> list[dict]:
        query = query.strip()
        if not query:
            return []
        # Build a prefix-match query: each token gets a trailing * so "LLM" matches "LLMs", "LLM-based", etc.
        tokens = query.replace('"', '').split()
        fts_query = " ".join(f'"{t}"*' for t in tokens if t)
        sql = """
            SELECT entries.*, feeds.title AS feed_title,
                   snippet(entries_fts, 0, '<mark>', '</mark>', '...', 24) AS title_snippet,
                   snippet(entries_fts, 1, '<mark>', '</mark>', '...', 48) AS summary_snippet,
                   snippet(entries_fts, 2, '<mark>', '</mark>', '...', 48) AS content_snippet,
                   rank
            FROM entries_fts
            JOIN entries ON entries.id = entries_fts.rowid
            JOIN feeds ON feeds.id = entries.feed_id
            WHERE entries_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        with get_connection() as conn:
            rows = conn.execute(sql, (fts_query, limit)).fetchall()
        return [self._search_result(row) for row in rows]

    def list_article_items(self, feed_id=None, tag_id=None, unread=None, starred=None, limit=50, offset=0, sort_order="newest"):
        conditions, params = self._article_filter_conditions(feed_id=feed_id, tag_id=tag_id, unread=unread, starred=starred)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        direction = "ASC" if sort_order == "oldest" else "DESC"
        limit = max(1, min(100, int(limit or 50)))
        offset = max(0, int(offset or 0))
        query = f"""
            SELECT
                entries.id, entries.feed_id, feeds.title AS feed_title,
                entries.title, entries.link, entries.author, entries.published_at,
                entries.summary, entries.is_read, entries.is_starred, entries.created_at
            FROM entries
            JOIN feeds ON feeds.id = entries.feed_id
            {where}
            ORDER BY COALESCE(entries.published_at, entries.created_at) {direction}, entries.id {direction}
            LIMIT ? OFFSET ?
        """
        with get_connection() as conn:
            rows = conn.execute(query, [*params, limit, offset]).fetchall()
            total = self.count_articles(conn=conn, feed_id=feed_id, tag_id=tag_id, unread=unread, starred=starred)
            tag_map = self._tag_ids_by_entry(conn, [row["id"] for row in rows])
        return {
            "items": [self._article_list_item(row, tag_map.get(row["id"], [])) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(rows) < total,
        }

    def count_articles(self, conn=None, feed_id=None, tag_id=None, unread=None, starred=None):
        conditions, params = self._article_filter_conditions(feed_id=feed_id, tag_id=tag_id, unread=unread, starred=starred)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT COUNT(*) FROM entries {where}"
        if conn is not None:
            return int(conn.execute(query, params).fetchone()[0])
        with get_connection() as local_conn:
            return int(local_conn.execute(query, params).fetchone()[0])

    def list_articles(self, feed_id=None, tag_id=None, unread=None, starred=None):
        conditions, params = self._article_filter_conditions(feed_id=feed_id, tag_id=tag_id, unread=unread, starred=starred)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT entries.*, feeds.title AS feed_title
            FROM entries
            JOIN feeds ON feeds.id = entries.feed_id
            {where}
            ORDER BY COALESCE(entries.published_at, entries.created_at) DESC
        """
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            tag_map = self._tag_ids_by_entry(conn, [row["id"] for row in rows])
        return [self._article(row, tag_map.get(row["id"], [])) for row in rows]

    def article_counts(self):
        with get_connection() as conn:
            totals = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END), 0) AS unread,
                    COALESCE(SUM(CASE WHEN is_starred = 1 THEN 1 ELSE 0 END), 0) AS starred
                FROM entries
                """
            ).fetchone()
            by_feed = conn.execute(
                "SELECT feed_id, COUNT(*) AS count FROM entries GROUP BY feed_id"
            ).fetchall()
            by_tag = conn.execute(
                "SELECT tag_id, COUNT(*) AS count FROM article_tags GROUP BY tag_id"
            ).fetchall()
        return {
            "total": int(totals["total"]),
            "unread": int(totals["unread"]),
            "starred": int(totals["starred"]),
            "by_feed": {int(row["feed_id"]): int(row["count"]) for row in by_feed},
            "by_tag": {int(row["tag_id"]): int(row["count"]) for row in by_tag},
        }

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
        with get_connection() as conn:
            tag_map = self._tag_ids_by_entry(conn, [article_id])
        return self._article(row, tag_map.get(article_id, []))

    def refresh_article_content(self, article_id: int):
        article = self.get_article(article_id)
        url = article.get("url")
        if not url:
            raise ValueError("Article does not have a source URL.")

        fetched_html = extract_article_html(url)
        if not fetched_html:
            raise ValueError("Unable to load full article content from the source page.")

        cleaned = clean_html(fetched_html)
        cleaned_html = cleaned["cleaned_html"] or fetched_html
        cleaned_markdown = cleaned["cleaned_markdown"]
        current_html = article.get("cleaned_html") or article.get("raw_html") or ""

        with get_connection() as conn:
            conn.execute(
                """
                UPDATE entries
                SET content = ?, raw_html = ?, cleaned_html = ?, cleaned_markdown = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    fetched_html,
                    fetched_html,
                    cleaned_html,
                    cleaned_markdown,
                    now(),
                    article_id,
                ),
            )

        updated = self.get_article(article_id)
        if len((updated.get("cleaned_html") or "").strip()) <= len(current_html.strip()):
            self._log(updated["feed_id"], url, "success", "Loaded full article content but extracted body was not longer than current content.")
        else:
            self._log(updated["feed_id"], url, "success", "Loaded and replaced article with fuller source-page content.")
        return updated

    def set_article_flag(self, article_id, key, value):
        if key not in {"is_read", "is_starred"}:
            raise ValueError(f"Unsupported article flag: {key}")
        self.get_article(article_id)
        with get_connection() as conn:
            conn.execute(f"UPDATE entries SET {key} = ? WHERE id = ?", (1 if value else 0, article_id))
        return self.get_article(article_id)

    def list_logs(self, range: str | None = None):
        cutoff = self._range_cutoff(range)
        conditions = []
        params = []
        if cutoff:
            conditions.append("feed_fetch_logs.fetched_at >= ?")
            params.append(cutoff)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT feed_fetch_logs.*, feeds.title AS feed_title
                FROM feed_fetch_logs
                LEFT JOIN feeds ON feeds.id = feed_fetch_logs.feed_id
                {where}
                ORDER BY fetched_at DESC
                """,
                params,
            ).fetchall()
        return [
            {
                "id": row["id"],
                "feed_id": row["feed_id"],
                "url": row["url"],
                "feed_title": row["feed_title"],
                "status": row["status"],
                "message": row["message"],
                "created_at": row["fetched_at"],
            }
            for row in rows
        ]

    def log_feed_event(self, feed_id: int | None, url: str, status: str, message: str) -> None:
        self._log(feed_id, url, status, message)

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

    def list_llm_providers(self):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM llm_providers
                ORDER BY is_default DESC, enabled DESC, id ASC
                """
            ).fetchall()
        return [self._llm_provider(row, include_api_key=False) for row in rows]

    def get_llm_provider(self, provider_id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM llm_providers WHERE id = ?", (provider_id,)).fetchone()
        if row is None:
            raise ValueError(f"LLM provider {provider_id} not found")
        return self._llm_provider(row, include_api_key=True)

    def get_default_llm_provider(self):
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM llm_providers
                WHERE enabled = 1
                ORDER BY is_default DESC, id ASC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            raise ValueError("No enabled LLM provider configured")
        return self._llm_provider(row, include_api_key=True)

    def create_llm_provider(self, payload):
        data = payload.model_dump()
        timestamp = now()
        with get_connection() as conn:
            if data.get("is_default"):
                conn.execute("UPDATE llm_providers SET is_default = 0")
            cursor = conn.execute(
                """
                INSERT INTO llm_providers (
                    name, provider_type, base_url, api_key, model,
                    enabled, is_default, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["name"],
                    data.get("provider_type") or "openai_compatible",
                    data["base_url"].rstrip("/"),
                    encrypt_secret(data.get("api_key") or ""),
                    data["model"],
                    1 if data.get("enabled", True) else 0,
                    1 if data.get("is_default") else 0,
                    timestamp,
                    timestamp,
                ),
            )
            provider_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM llm_providers WHERE id = ?", (provider_id,)).fetchone()
        return self._llm_provider(row, include_api_key=False)

    def update_llm_provider(self, provider_id: int, payload):
        self.get_llm_provider(provider_id)
        data = payload.model_dump(exclude_unset=True)
        if not data:
            provider = self.get_llm_provider(provider_id)
            provider.pop("api_key", None)
            return provider

        assignments = []
        values = []
        for key, value in data.items():
            if value is None:
                continue
            if key == "api_key":
                if not value:
                    continue
                value = encrypt_secret(value)
            if key == "base_url" and isinstance(value, str):
                value = value.rstrip("/")
            if key in {"enabled", "is_default"}:
                value = 1 if value else 0
            assignments.append(f"{key} = ?")
            values.append(value)

        if not assignments:
            provider = self.get_llm_provider(provider_id)
            provider.pop("api_key", None)
            return provider

        timestamp = now()
        values.extend([timestamp, provider_id])
        with get_connection() as conn:
            if data.get("is_default") is True:
                conn.execute("UPDATE llm_providers SET is_default = 0 WHERE id != ?", (provider_id,))
            conn.execute(
                f"UPDATE llm_providers SET {', '.join(assignments)}, updated_at = ? WHERE id = ?",
                values,
            )
        provider = self.get_llm_provider(provider_id)
        provider.pop("api_key", None)
        return provider

    def delete_llm_provider(self, provider_id: int):
        self.get_llm_provider(provider_id)
        with get_connection() as conn:
            conn.execute("DELETE FROM llm_providers WHERE id = ?", (provider_id,))

    def create_ai_result(
        self,
        article_id,
        result_type,
        prompt,
        result,
        provider: str | None = None,
        model: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        status: str = "success",
    ):
        self.get_article(article_id)
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO ai_results (
                    entry_id, task_type, status, provider, model, prompt, result,
                    input_tokens, output_tokens
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article_id,
                    result_type,
                    status,
                    provider,
                    model,
                    prompt,
                    result,
                    max(0, int(input_tokens or 0)),
                    max(0, int(output_tokens or 0)),
                ),
            )
            row = conn.execute("SELECT * FROM ai_results WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._ai_result(row)

    def get_latest_ai_result(self, article_id, result_type):
        self.get_article(article_id)
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM ai_results
                WHERE entry_id = ? AND task_type = ?
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT 1
                """,
                (article_id, result_type),
            ).fetchone()
        if row is None:
            return None
        return self._ai_result(row)

    def _range_cutoff(self, range_: str | None) -> str | None:
        from datetime import timedelta
        now_local = datetime.now()
        if range_ == "today":
            cutoff = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        elif range_ == "week":
            cutoff = (now_local - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif range_ == "month":
            cutoff = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return None
        return cutoff.strftime("%Y-%m-%d %H:%M:%S")

    def _fill_buckets(self, range_: str | None, rows: list[dict]) -> list[dict]:
        from datetime import timedelta
        existing = {r["time_label"]: r for r in rows}
        empty = {"calls": 0, "failed_calls": 0, "input_tokens": 0, "output_tokens": 0}

        if range_ == "today":
            labels = [f"{h:02d}:00" for h in range(24)]
        elif range_ == "week":
            today = datetime.now().date()
            labels = [(today - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)]
        elif range_ == "month":
            today = datetime.now().date()
            first_of_month = today.replace(day=1)
            days_in_month = (today - first_of_month).days + 1
            labels = [(first_of_month + timedelta(days=i)).strftime("%m-%d") for i in range(days_in_month)]
        else:
            return rows

        return [{"time_label": lbl, **existing.get(lbl, empty)} for lbl in labels]

    def stats(self, range: str | None = None):
        cutoff = self._range_cutoff(range)
        where = "WHERE created_at >= ?" if cutoff else ""
        params = [cutoff] if cutoff else []

        with get_connection() as conn:
            article_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            usage = conn.execute(
                f"""
                SELECT
                    COUNT(*) AS total_calls,
                    COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) AS failed_calls,
                    COALESCE(SUM(input_tokens), 0) AS input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens
                FROM ai_results {where}
                """,
                params,
            ).fetchone()
            by_feature = conn.execute(
                f"""
                SELECT
                    task_type AS name,
                    COUNT(*) AS calls,
                    COALESCE(SUM(input_tokens + output_tokens), 0) AS tokens
                FROM ai_results {where}
                GROUP BY task_type
                ORDER BY calls DESC, name ASC
                """,
                params,
            ).fetchall()
            by_provider = conn.execute(
                f"""
                SELECT
                    COALESCE(provider, 'unknown') AS provider,
                    COALESCE(model, 'unknown') AS model,
                    COUNT(*) AS calls,
                    COALESCE(SUM(input_tokens), 0) AS input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens
                FROM ai_results {where}
                GROUP BY provider, model
                ORDER BY calls DESC, provider ASC, model ASC
                """,
                params,
            ).fetchall()
        return {
            "total_articles": article_count,
            "total_calls": usage["total_calls"],
            "failed_calls": usage["failed_calls"],
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "by_feature": [dict(row) for row in by_feature],
            "by_provider": [dict(row) for row in by_provider],
        }

    def stats_timeseries(self, range: str | None = None) -> list[dict]:
        cutoff = self._range_cutoff(range)
        where = "WHERE created_at >= ?" if cutoff else ""
        params = [cutoff] if cutoff else []

        # Convert stored UTC-like timestamps to local time for bucketing
        now_local = datetime.now()
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        offset_seconds = int((now_local - now_utc).total_seconds())
        tz_modifier = f"{offset_seconds:+d} seconds"

        if range == "today":
            label_expr = f"strftime('%H:00', datetime(created_at, '{tz_modifier}'))"
            bucket_expr = f"strftime('%Y-%m-%d %H:00:00', datetime(created_at, '{tz_modifier}'))"
        else:
            label_expr = f"strftime('%m-%d', datetime(created_at, '{tz_modifier}'))"
            bucket_expr = f"strftime('%Y-%m-%d 00:00:00', datetime(created_at, '{tz_modifier}'))"

        sql = f"""
            SELECT
                {label_expr} AS time_label,
                {bucket_expr} AS bucket_key,
                COUNT(*) AS calls,
                COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) AS failed_calls,
                COALESCE(SUM(input_tokens), 0) AS input_tokens,
                COALESCE(SUM(output_tokens), 0) AS output_tokens
            FROM ai_results
            {where}
            GROUP BY bucket_key
            ORDER BY bucket_key ASC
        """
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return self._fill_buckets(range, [dict(r) for r in rows])

    def list_tags(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM tags ORDER BY name ASC, id ASC").fetchall()
        return [self._tag(row) for row in rows]

    def create_tag(self, payload):
        timestamp = now()
        with get_connection() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO tags (name, color, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (payload.name, payload.color, timestamp, timestamp),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("Tag already exists") from exc
            row = conn.execute("SELECT * FROM tags WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._tag(row)

    def update_tag(self, tag_id, payload):
        self._tag_row(tag_id)
        data = payload.model_dump(exclude_unset=True)
        updates = {key: value for key, value in data.items() if value is not None and key in {"name", "color"}}
        if updates:
            assignments = ", ".join(f"{key} = ?" for key in updates)
            values = [*updates.values(), now(), tag_id]
            with get_connection() as conn:
                conn.execute(f"UPDATE tags SET {assignments}, updated_at = ? WHERE id = ?", values)
        return self._tag(self._tag_row(tag_id))

    def delete_tag(self, tag_id):
        self._tag_row(tag_id)
        with get_connection() as conn:
            conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))

    def set_article_tags(self, article_id, tag_ids):
        self.get_article(article_id)
        unique_tag_ids = sorted({int(tag_id) for tag_id in tag_ids})
        with get_connection() as conn:
            if unique_tag_ids:
                placeholders = ",".join("?" for _ in unique_tag_ids)
                rows = conn.execute(f"SELECT id FROM tags WHERE id IN ({placeholders})", unique_tag_ids).fetchall()
                existing = {row["id"] for row in rows}
                missing = [tag_id for tag_id in unique_tag_ids if tag_id not in existing]
                if missing:
                    raise ValueError(f"Tag {missing[0]} not found")
            conn.execute("DELETE FROM article_tags WHERE entry_id = ?", (article_id,))
            conn.executemany(
                "INSERT INTO article_tags (entry_id, tag_id, created_at) VALUES (?, ?, ?)",
                [(article_id, tag_id, now()) for tag_id in unique_tag_ids],
            )
        return {"article_id": article_id, "tag_ids": unique_tag_ids}

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
        seen_guids: set[str] = set()
        seen_links: set[str] = set()
        for entry in entries:
            guid = entry.get("guid")
            link = entry.get("link")
            if (guid and guid in seen_guids) or (link and link in seen_links):
                continue
            if guid:
                seen_guids.add(guid)
            if link:
                seen_links.add(link)

            if self._entry_exists(conn, feed_id, guid, link):
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
        cleaned = clean_html(fallback)
        return {
            "content": fallback,
            "raw_html": fallback,
            "cleaned_html": cleaned["cleaned_html"] or fallback,
            "cleaned_markdown": cleaned["cleaned_markdown"],
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

    def _tag_row(self, tag_id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
        if row is None:
            raise ValueError(f"Tag {tag_id} not found")
        return row

    def _article_filter_conditions(self, feed_id=None, tag_id=None, unread=None, starred=None):
        conditions = []
        params = []
        if feed_id is not None:
            conditions.append("entries.feed_id = ?")
            params.append(feed_id)
        if tag_id is not None:
            conditions.append("EXISTS (SELECT 1 FROM article_tags WHERE article_tags.entry_id = entries.id AND article_tags.tag_id = ?)")
            params.append(tag_id)
        if unread is True:
            conditions.append("entries.is_read = 0")
        if starred is True:
            conditions.append("entries.is_starred = 1")
        return conditions, params

    def _tag_ids_by_entry(self, conn: sqlite3.Connection, entry_ids: list[int]) -> dict[int, list[int]]:
        if not entry_ids:
            return {}
        placeholders = ",".join("?" for _ in entry_ids)
        rows = conn.execute(
            f"""
            SELECT entry_id, tag_id
            FROM article_tags
            WHERE entry_id IN ({placeholders})
            ORDER BY tag_id ASC
            """,
            entry_ids,
        ).fetchall()
        tag_map: dict[int, list[int]] = {entry_id: [] for entry_id in entry_ids}
        for row in rows:
            tag_map.setdefault(row["entry_id"], []).append(row["tag_id"])
        return tag_map

    def _feed_exists_by_url(self, url: str) -> bool:
        with get_connection() as conn:
            row = conn.execute("SELECT id FROM feeds WHERE url = ?", (url,)).fetchone()
        return row is not None

    def _log(self, feed_id: int | None, url: str, status: str, message: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO feed_fetch_logs (feed_id, url, status, message, fetched_at) VALUES (?, ?, ?, ?, ?)",
                (feed_id, url, status, message, now()),
            )

    def _parse_feed(self, url: str) -> dict:
        from app.services.feed_parser import parse_feed

        return parse_feed(url)

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

    def _tag(self, row):
        return {
            "id": row["id"],
            "name": row["name"],
            "color": row["color"],
        }

    def _article_list_item(self, row, tag_ids=None):
        return {
            "id": row["id"],
            "feed_id": row["feed_id"],
            "feed_title": row["feed_title"],
            "title": row["title"],
            "url": row["link"] or "",
            "author": row["author"],
            "published_at": row["published_at"],
            "summary": row["summary"],
            "is_read": bool(row["is_read"]),
            "is_starred": bool(row["is_starred"]),
            "tag_ids": tag_ids or [],
            "created_at": row["created_at"],
        }

    def _article(self, row, tag_ids=None):
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
            "tag_ids": tag_ids or [],
            "created_at": row["created_at"],
        }

    def _search_result(self, row):
        return {
            "id": row["id"],
            "feed_id": row["feed_id"],
            "feed_title": row["feed_title"],
            "title": row["title"],
            "url": row["link"] or "",
            "author": row["author"],
            "published_at": row["published_at"],
            "is_read": bool(row["is_read"]),
            "is_starred": bool(row["is_starred"]),
            "title_snippet": row["title_snippet"],
            "summary_snippet": row["summary_snippet"],
            "content_snippet": row["content_snippet"],
        }

    def _llm_provider(self, row, include_api_key: bool = False):
        provider = {
            "id": row["id"],
            "name": row["name"],
            "provider_type": row["provider_type"],
            "base_url": row["base_url"],
            "model": row["model"],
            "enabled": bool(row["enabled"]),
            "is_default": bool(row["is_default"]),
            "has_api_key": bool(row["api_key"]),
        }
        if include_api_key:
            provider["api_key"] = decrypt_secret(row["api_key"] or "")
        return provider

    def _ai_result(self, row):
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


repository = SQLiteRepository()
