# RSS Reader Web Application - Implementation Plan

## Context

This is a university course final project to build a web-based RSS Reader application. The assignment requirements (from demand.png) specify features like RSS subscription management, focused reading mode, AI summary, AI translation, tag system, notes & export, and LLM usage statistics.

Reference: Mercury (macOS desktop app in Swift) - shows similar feature set but we're building a web version.

## Tech Stack

- **Frontend**: Vue 3 + Vite + Pinia + Vue Router + TypeScript
- **Backend**: Python FastAPI
- **Database**: SQLite (via SQLAlchemy)
- **AI**: OpenAI-compatible API (configurable base_url for any provider)

## Project Structure

```
RSSReader/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app factory
│   │   ├── config.py               # Pydantic BaseSettings
│   │   ├── database.py             # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── feed.py             # Feed, Category
│   │   │   ├── article.py          # Article
│   │   │   ├── tag.py              # Tag, ArticleTag
│   │   │   ├── note.py             # Note
│   │   │   ├── ai_task.py          # AITask
│   │   │   ├── llm_stat.py         # LLMUsageStat
│   │   │   └── user_setting.py     # UserSetting
│   │   ├── schemas/                # Pydantic request/response
│   │   ├── api/                    # FastAPI routers
│   │   │   ├── feeds.py
│   │   │   ├── articles.py
│   │   │   ├── tags.py
│   │   │   ├── notes.py
│   │   │   ├── ai.py
│   │   │   ├── stats.py
│   │   │   ├── settings.py
│   │   │   └── export.py
│   │   ├── services/
│   │   │   ├── feed_fetcher.py     # HTTP fetch + parse
│   │   │   ├── content_extractor.py # Readability extraction
│   │   │   ├── opml_service.py     # OPML import/export
│   │   │   ├── ai_client.py        # OpenAI-compatible client
│   │   │   ├── summarizer.py
│   │   │   ├── translator.py
│   │   │   ├── tag_recommender.py
│   │   │   ├── llm_stat_service.py
│   │   │   ├── markdown_export.py
│   │   │   └── scheduler.py        # APScheduler
│   │   └── utils/
│   │       ├── html_cleaner.py
│   │       └── streaming.py
│   ├── migrations/                 # Alembic
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/index.ts
│   │   ├── stores/                 # Pinia stores
│   │   ├── components/             # Vue components
│   │   ├── views/                  # Page views
│   │   ├── services/               # API clients
│   │   ├── composables/            # Reusable logic
│   │   └── assets/styles/
│   ├── vite.config.ts
│   └── package.json
│
└── docker-compose.yml (optional)
```

## Database Schema

### feeds
- id (PK), title, url (unique), site_url, category_id (FK -> categories.id)
- icon_url, fetch_interval, last_fetched_at, last_fetched_error, enabled
- created_at, updated_at

### categories
- id (PK), name, sort_order, created_at

### articles
- id (PK), feed_id (FK -> feeds.id), guid, title, author, published_at
- link, summary, content_html, content_extracted, content_text
- is_read, is_starred, fetched_at, created_at
- Unique constraint: (feed_id, guid)

### tags
- id (PK), name (unique), color, is_ai, created_at

### article_tags
- article_id (FK), tag_id (FK), source ('manual'/'ai'), created_at
- PK: (article_id, tag_id)

### notes
- id (PK), article_id (FK, nullable), content (Markdown), created_at, updated_at

### ai_tasks
- id (PK), article_id (FK), task_type ('summary'/'translation'/'tagging')
- status ('pending'/'running'/'completed'/'failed')
- request_data (JSON), result (JSON), error
- created_at, completed_at

### llm_usage_stats
- id (PK), provider, model, agent, task_id (FK, nullable)
- prompt_tokens, completion_tokens, total_tokens, cost_usd, created_at

### user_settings
- id (PK), setting_key (unique), setting_value (JSON), updated_at
- Keys: theme, font_size, ai_api_base, ai_api_key, ai_model, ai_summary_prompt, etc.

## API Endpoints (/api/v1)

### Feeds
- GET /feeds - List all feeds
- POST /feeds - Add feed
- GET /feeds/{id} - Get feed
- PUT /feeds/{id} - Update feed
- DELETE /feeds/{id} - Delete feed
- POST /feeds/{id}/fetch - Trigger fetch
- POST /feeds/fetch-all - Fetch all feeds
- POST /feeds/import-opml - Import OPML
- GET /feeds/export-opml - Export OPML

### Categories
- GET /feeds/categories, POST /feeds/categories, PUT/DELETE /feeds/categories/{id}

### Articles
- GET /articles - List (filters: feed, read, tag, search, sort)
- GET /articles/{id} - Get with extracted content
- PUT /articles/{id}/read - Mark read/unread
- PUT /articles/{id}/star - Toggle star
- PUT /articles/{id}/extract - Trigger extraction
- POST /articles/mark-all-read

### Tags
- GET /tags, POST /tags, PUT/DELETE /tags/{id}
- POST /articles/{id}/tags, DELETE /articles/{id}/tags/{tag_id}
- POST /articles/batch-tags, POST /articles/{id}/tags/ai-recommend

### Notes
- GET /notes, POST /notes, GET/PUT/DELETE /notes/{id}

### AI
- POST /ai/summary - Generate summary (SSE streaming)
- POST /ai/translate - Generate translation (SSE streaming)
- POST /ai/translate/paragraph/{task_id}/{idx} - Retry paragraph
- POST /ai/tags/recommend - Recommend tags
- GET /ai/tasks/{id} - Get task status

### Export
- POST /export/markdown - Batch export
- GET /export/markdown/{article_id} - Single article export

### Stats
- GET /stats/llm-usage - LLM usage by provider/model/agent

### Settings
- GET /settings, PUT /settings, PUT /settings/{key}

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- FastAPI project scaffold + SQLAlchemy + Alembic
- Feed CRUD API + Category CRUD API
- feed_fetcher.py: HTTP fetch + feedparser parsing
- Article storage with deduplication
- APScheduler for periodic polling
- Vue 3 + Vite + Pinia + Router scaffold
- Feed list view, article list view, basic layout

### Phase 2: Reading Experience (Week 2-3)
- content_extractor.py using justext
- Article reader view with extracted content
- Theme system (dark/light) + font size control
- OPML import/export
- Mark as read / star functionality

### Phase 3: AI Summary (Week 3-4)
- ai_client.py: OpenAI-compatible client with streaming
- summarizer.py: Build prompt, call LLM, parse response
- /ai/summary endpoint with SSE streaming
- Frontend: summary panel with streaming display
- LLM usage stats tracking

### Phase 4: AI Translation + Tags (Week 4-5)
- translator.py: Paragraph-level bilingual translation
- /ai/translate endpoint with SSE
- Frontend: bilingual comparison view
- Tag CRUD + manual tagging UI
- AI tag recommendation + batch tagging
- Tag filtering + tag library management

### Phase 5: Notes + Export + Stats (Week 5-6)
- Notes API + Markdown editor
- Markdown export (single + batch ZIP)
- LLM stats dashboard with charts
- Search functionality
- Polish: error handling, loading states

### Phase 6: Final Polish (Week 6-7)
- Edge case handling
- Performance optimization (pagination)
- Documentation + README
- Demo preparation

## Key Libraries

**Backend**: fastapi, uvicorn, sqlalchemy, aiosqlite, alembic, pydantic-settings, feedparser, justext, openai, apscheduler, httpx, python-multipart, lxml, aiofiles

**Frontend**: vue, vite, pinia, vue-router, axios, element-plus, markdown-it, echarts, jszip, file-saver, dayjs

## Background Feed Fetching

Use APScheduler (AsyncIOScheduler) inside FastAPI process via lifespan hook.
Job runs every 5 minutes: query due feeds -> async fetch each -> parse -> upsert articles -> update feed timestamps.
No Redis needed - keeps it simple for a student project.

## Content Extraction

Primary: justext (Python-native, no browser deps)
Fallback: Use feed-provided <content:encoded> if justext output is too short
Store in articles.content_extracted, render with v-html + CSS reading styles
