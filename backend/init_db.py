from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def init_db() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema)


if __name__ == "__main__":
    init_db()
    print(f"SQLite database initialized: {DB_PATH}")
