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

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL DEFAULT '#409eff',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS article_tags (
    entry_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entry_id, tag_id),
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_results (
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
);

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
);

CREATE TABLE IF NOT EXISTS llm_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider_type TEXT NOT NULL DEFAULT 'openai_compatible',
    base_url TEXT NOT NULL,
    api_key TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    is_default INTEGER NOT NULL DEFAULT 0,
    is_translation_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entries_feed_id ON entries(feed_id);
CREATE INDEX IF NOT EXISTS idx_entries_published_at ON entries(published_at);
CREATE INDEX IF NOT EXISTS idx_entries_feed_sort ON entries(feed_id, published_at, created_at);
CREATE INDEX IF NOT EXISTS idx_entries_read_sort ON entries(is_read, published_at, created_at);
CREATE INDEX IF NOT EXISTS idx_entries_starred_sort ON entries(is_starred, published_at, created_at);
CREATE INDEX IF NOT EXISTS idx_article_tags_tag_id ON article_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_logs_feed_id ON feed_fetch_logs(feed_id);
CREATE INDEX IF NOT EXISTS idx_ai_results_task_type ON ai_results(task_type);
CREATE INDEX IF NOT EXISTS idx_ai_results_provider_model ON ai_results(provider, model);
CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_task_type ON ai_usage_logs(task_type);
CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_provider_model ON ai_usage_logs(provider, model);
CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_created_at ON ai_usage_logs(created_at);


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
);

CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

-- FTS5 virtual table for full-text search over entries
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    title,
    summary,
    cleaned_markdown,
    content='entries',
    content_rowid='id',
    tokenize='unicode61'
);

-- Keep FTS index in sync with entries table
CREATE TRIGGER IF NOT EXISTS entries_fts_insert AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(rowid, title, summary, cleaned_markdown)
    VALUES (new.id, new.title, new.summary, new.cleaned_markdown);
END;

CREATE TRIGGER IF NOT EXISTS entries_fts_delete AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, title, summary, cleaned_markdown)
    VALUES ('delete', old.id, old.title, old.summary, old.cleaned_markdown);
END;

CREATE TRIGGER IF NOT EXISTS entries_fts_update AFTER UPDATE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, title, summary, cleaned_markdown)
    VALUES ('delete', old.id, old.title, old.summary, old.cleaned_markdown);
    INSERT INTO entries_fts(rowid, title, summary, cleaned_markdown)
    VALUES (new.id, new.title, new.summary, new.cleaned_markdown);
END;
