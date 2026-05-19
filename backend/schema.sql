PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    site_url TEXT,
    language TEXT,
    last_build_date TEXT,
    last_fetched_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entries (
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
    updated_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read INTEGER NOT NULL DEFAULT 0,
    is_starred INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE,
    UNIQUE(feed_id, guid),
    UNIQUE(feed_id, link)
);

CREATE TABLE IF NOT EXISTS feed_fetch_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER,
    url TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL UNIQUE,
    content TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    prompt TEXT NOT NULL DEFAULT '',
    result TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_entries_feed_id ON entries(feed_id);
CREATE INDEX IF NOT EXISTS idx_entries_published_at ON entries(published_at);
CREATE INDEX IF NOT EXISTS idx_logs_feed_id ON feed_fetch_logs(feed_id);
