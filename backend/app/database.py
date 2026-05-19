from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "app.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
DATABASE_URL = f"sqlite:///{DB_PATH}"


def get_connection() -> sqlite3.Connection:
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

