import sqlite3
import os
import sys
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGED_BASE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
DB_PATH = Path(os.environ.get("RSSREADER_DB_PATH", BASE_DIR / "app.db")).expanduser()
SCHEMA_PATH = PACKAGED_BASE_DIR / "schema.sql"
DATABASE_URL = f"sqlite:///{DB_PATH}"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema)
        _migrate_entries_table(conn)
        _migrate_tag_tables(conn)
        _migrate_ai_tables(conn)
        _migrate_fts_table(conn)
    # Vector table requires the sqlite-vec extension, initialized separately
    try:
        from app.services.rag_service import initialize_vec_table
        initialize_vec_table()
    except Exception:
        pass  # sqlite-vec not available or not configured — skip silently


def get_db():
    with get_connection() as conn:
        yield conn


def _migrate_entries_table(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(entries)").fetchall()}
    migrations = {
        "raw_html": "ALTER TABLE entries ADD COLUMN raw_html TEXT",
        "cleaned_html": "ALTER TABLE entries ADD COLUMN cleaned_html TEXT",
        "cleaned_markdown": "ALTER TABLE entries ADD COLUMN cleaned_markdown TEXT",
    }
    for column, statement in migrations.items():
        if column not in columns:
            conn.execute(statement)


def _migrate_tag_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT '#409eff',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS article_tags (
            entry_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (entry_id, tag_id),
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_feed_sort ON entries(feed_id, published_at, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_read_sort ON entries(is_read, published_at, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_starred_sort ON entries(is_starred, published_at, created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_article_tags_tag_id ON article_tags(tag_id)")


def _migrate_ai_tables(conn: sqlite3.Connection) -> None:
    ai_columns = {row["name"] for row in conn.execute("PRAGMA table_info(ai_results)").fetchall()}
    ai_migrations = {
        "provider": "ALTER TABLE ai_results ADD COLUMN provider TEXT",
        "model": "ALTER TABLE ai_results ADD COLUMN model TEXT",
        "status": "ALTER TABLE ai_results ADD COLUMN status TEXT NOT NULL DEFAULT 'success'",
    }
    for column, statement in ai_migrations.items():
        if column not in ai_columns:
            conn.execute(statement)

    # Migrate ai_results foreign key from ON DELETE CASCADE to ON DELETE SET NULL
    # so token records survive when feeds/entries are deleted.
    create_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='ai_results'"
    ).fetchone()
    if create_sql and "ON DELETE CASCADE" in create_sql[0]:
        conn.execute("ALTER TABLE ai_results RENAME TO ai_results_old")
        conn.execute(
            """
            CREATE TABLE ai_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'success',
                provider TEXT,
                model TEXT,
                prompt TEXT NOT NULL DEFAULT '',
                result TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE SET NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO ai_results
                (id, entry_id, task_type, status, provider, model, prompt, result,
                 input_tokens, output_tokens, created_at)
            SELECT id, entry_id, task_type, status, provider, model, prompt, result,
                   input_tokens, output_tokens, created_at
            FROM ai_results_old
            """
        )
        conn.execute("DROP TABLE ai_results_old")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_results_task_type ON ai_results(task_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_results_provider_model ON ai_results(provider, model)")

    provider_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(llm_providers)").fetchall()
    }
    provider_migrations = {
        "provider_type": "ALTER TABLE llm_providers ADD COLUMN provider_type TEXT NOT NULL DEFAULT 'openai_compatible'",
        "is_default": "ALTER TABLE llm_providers ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0",
        "is_translation_default": "ALTER TABLE llm_providers ADD COLUMN is_translation_default INTEGER NOT NULL DEFAULT 0",
        "created_at": "ALTER TABLE llm_providers ADD COLUMN created_at TEXT NOT NULL DEFAULT ''",
        "updated_at": "ALTER TABLE llm_providers ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''",
    }
    for column, statement in provider_migrations.items():
        if column not in provider_columns:
            conn.execute(statement)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_result_id INTEGER,
            entry_id INTEGER,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'success',
            provider TEXT,
            model TEXT,
            input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_task_type ON ai_usage_logs(task_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_provider_model ON ai_usage_logs(provider, model)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_created_at ON ai_usage_logs(created_at)")
    conn.execute(
        """
        INSERT INTO ai_usage_logs (
            source_result_id, entry_id, task_type, status, provider, model,
            input_tokens, output_tokens, created_at
        )
        SELECT id, entry_id, task_type, status, provider, model, input_tokens, output_tokens, created_at
        FROM ai_results
        WHERE id NOT IN (
            SELECT source_result_id FROM ai_usage_logs WHERE source_result_id IS NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS translation_providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            provider_type TEXT NOT NULL DEFAULT 'openai_compatible',
            base_url TEXT NOT NULL,
            api_key TEXT NOT NULL DEFAULT '',
            model TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            is_default INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        INSERT INTO translation_providers (
            name, provider_type, base_url, api_key, model,
            enabled, is_default, created_at, updated_at
        )
        SELECT name, provider_type, base_url, api_key, model,
               enabled, 1, created_at, updated_at
        FROM llm_providers
        WHERE enabled = 1
          AND is_translation_default = 1
          AND NOT EXISTS (SELECT 1 FROM translation_providers)
        ORDER BY id ASC
        LIMIT 1
        """
    )
    conn.execute(
        """
        INSERT INTO translation_providers (
            name, provider_type, base_url, api_key, model,
            enabled, is_default, created_at, updated_at
        )
        SELECT name, provider_type, base_url, api_key, model,
               enabled, 1, created_at, updated_at
        FROM llm_providers
        WHERE enabled = 1
          AND is_default = 1
          AND NOT EXISTS (SELECT 1 FROM translation_providers)
        ORDER BY id ASC
        LIMIT 1
        """
    )

    conn.execute(
        """
        UPDATE llm_providers
        SET is_translation_default = 1
        WHERE id = (
            SELECT id FROM llm_providers
            WHERE enabled = 1 AND is_default = 1
            ORDER BY id ASC
            LIMIT 1
        )
        AND NOT EXISTS (
            SELECT 1 FROM llm_providers WHERE enabled = 1 AND is_translation_default = 1
        )
        """
    )


def _migrate_fts_table(conn: sqlite3.Connection) -> None:
    # Backfill FTS index for any existing rows that were inserted before the triggers existed.
    # entries_fts uses content= so we check if it's empty while entries has rows.
    fts_count = conn.execute("SELECT COUNT(*) FROM entries_fts").fetchone()[0]
    if fts_count == 0:
        entries_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        if entries_count > 0:
            conn.execute(
                "INSERT INTO entries_fts(rowid, title, summary, cleaned_markdown) "
                "SELECT id, title, summary, cleaned_markdown FROM entries"
            )
