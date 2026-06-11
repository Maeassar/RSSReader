import sqlite3
import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGED_BASE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
DB_PATH = Path(os.environ.get("RSSREADER_DB_PATH", BASE_DIR / "app.db")).expanduser()
SCHEMA_PATH = PACKAGED_BASE_DIR / "schema.sql"
DATABASE_URL = f"sqlite:///{DB_PATH}"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def initialize_database() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema)
        _migrate_entries_table(conn)
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


def _migrate_ai_tables(conn: sqlite3.Connection) -> None:
    ai_columns = {row["name"] for row in conn.execute("PRAGMA table_info(ai_results)").fetchall()}
    ai_migrations = {
        "provider": "ALTER TABLE ai_results ADD COLUMN provider TEXT",
        "model": "ALTER TABLE ai_results ADD COLUMN model TEXT",
    }
    for column, statement in ai_migrations.items():
        if column not in ai_columns:
            conn.execute(statement)

    provider_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(llm_providers)").fetchall()
    }
    provider_migrations = {
        "provider_type": "ALTER TABLE llm_providers ADD COLUMN provider_type TEXT NOT NULL DEFAULT 'openai_compatible'",
        "is_default": "ALTER TABLE llm_providers ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0",
        "created_at": "ALTER TABLE llm_providers ADD COLUMN created_at TEXT NOT NULL DEFAULT ''",
        "updated_at": "ALTER TABLE llm_providers ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''",
    }
    for column, statement in provider_migrations.items():
        if column not in provider_columns:
            conn.execute(statement)


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
