# Week13 唐小卉 - Backend, SQLite, RSS/Atom Feed API

## Completed Scope

- Added a FastAPI backend that starts from `backend/app/main.py`.
- Added reproducible SQLite initialization with `backend/schema.sql` and `backend/init_db.py`.
- Added SQLite-backed feed and entry persistence.
- Added RSS/Atom parsing through `feedparser`.
- Added APIs for creating feeds, syncing feeds, listing feeds, and querying feed entries.

## Database Initialization

Install backend dependencies first:

```bash
cd backend
pip install -r requirements.txt
```

Initialize the SQLite database:

```bash
python init_db.py
```

This creates or updates:

```text
backend/app.db
```

The database file is local runtime data and should not be committed.

## Tables

### feeds

Stores RSS/Atom subscription sources.

Important fields:

- `id`: primary key
- `url`: unique feed URL
- `title`: feed title
- `description`: feed description
- `site_url`: original website URL
- `language`: feed language
- `last_build_date`: timestamp from the feed
- `last_fetched_at`: last local sync time

### entries

Stores parsed articles from feeds.

Important fields:

- `id`: primary key
- `feed_id`: parent feed
- `guid`: RSS/Atom entry identifier
- `title`: article title
- `link`: article URL
- `author`: author name
- `summary`: article summary
- `content`: article content HTML or summary fallback
- `published_at`: published time
- `updated_at`: updated time
- `is_read`: read flag
- `is_starred`: favorite flag

Entries are deduplicated by `guid` first and `link` second inside the same feed.
The current Week13 backend does not fetch full article pages. If a feed only provides summaries, the API only stores and returns those summaries.

### feed_fetch_logs

Stores feed sync results.

Important fields:

- `feed_id`: related feed, nullable for failed create attempts
- `url`: fetched URL
- `status`: `success` or `failed`
- `message`: sync result or error message
- `fetched_at`: fetch time

### notes

Stores article notes for later note features.

### ai_results

Stores AI summary or translation results for later AI features.

## Start Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /api/health
```

Expected response:

```json
{
  "status": "ok",
  "storage": "sqlite",
  "database": "app.db"
}
```

## Feed APIs

## API Development Status

### Network Ports

- `8000`: FastAPI backend. Development ready.
- `5173`: Vite frontend. Development ready.

### Development Ready APIs

These APIs are backed by SQLite and real RSS/Atom data:

- `GET /api/health`
- `GET /api/feeds`
- `POST /api/feeds`
- `GET /api/feeds/{feed_id}`
- `PUT /api/feeds/{feed_id}`
- `DELETE /api/feeds/{feed_id}`
- `POST /api/feeds/{feed_id}/sync`
- `POST /api/feeds/sync-all`
- `GET /api/feeds/{feed_id}/entries`
- `GET /api/articles`
- `GET /api/articles/{article_id}`
- `PATCH /api/articles/{article_id}/read`
- `PATCH /api/articles/{article_id}/star`
- `GET /api/articles/{article_id}/note`
- `PUT /api/articles/{article_id}/note`
- `GET /api/logs/sync`
- `GET /api/export/articles/{article_id}/markdown`
- `POST /api/export/articles/markdown`

### Simplified APIs

- `GET /api/stats/llm`

This endpoint currently returns simple local statistics and is not a complete LLM usage analytics implementation.

### Mock or Reserved APIs

These APIs exist for frontend integration and later contributors, but they are not complete production implementations yet:

- `POST /api/ai/summary/{article_id}`
- `POST /api/ai/translate/{article_id}`
- `POST /api/ai/tag-suggest/{article_id}`

AI APIs read real article data, but the generated summary, translation, and tag suggestion content is still mock text. OpenAI-compatible, Ollama, or vLLM providers are not connected yet.

- `GET /api/tags`
- `POST /api/tags`
- `PUT /api/tags/{tag_id}`
- `DELETE /api/tags/{tag_id}`
- `POST /api/articles/{article_id}/tags`

Tag APIs currently use in-memory data and are not persisted to SQLite.

- `POST /api/opml/import`
- `GET /api/opml/export`

OPML import/export is still mock. Import does not create real feeds yet, and export returns fixed sample XML.

### Add Feed

```text
POST /api/feeds
```

Request:

```json
{
  "url": "https://example.com/feed.xml"
}
```

The backend parses the RSS/Atom feed, saves the feed metadata to `feeds`, and saves articles to `entries`.
It only uses content provided by the RSS/Atom feed and does not crawl each article URL.

### List Feeds

```text
GET /api/feeds
```

Returns all saved feeds.

### Get One Feed

```text
GET /api/feeds/{feed_id}
```

Returns one saved feed.

### Sync Feed

```text
POST /api/feeds/{feed_id}/sync
```

Fetches the feed again and inserts only new articles.

### Query Feed Entries

```text
GET /api/feeds/{feed_id}/entries
```

Returns articles saved for one feed.

### Query All Articles

```text
GET /api/articles
```

Optional filters:

- `feed_id`
- `unread`
- `starred`

## Notes

- RSS/Atom parsing is implemented in `backend/app/services/feed_parser.py`.
- SQLite persistence is implemented in `backend/app/repositories/sqlite_repository.py`.
- The local database file, cache folders, and frontend dependencies are ignored by `.gitignore`.
