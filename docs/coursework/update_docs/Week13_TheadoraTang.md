# Week13 唐小卉 - 后端、SQLite、RSS/Atom Feed API

## 完成范围

- 完成 FastAPI 后端基础启动，入口文件为 `backend/app/main.py`。
- 新增可复现的 SQLite 初始化方式，包括 `backend/schema.sql` 和 `backend/init_db.py`。
- 接入 SQLite 持久化，实现 Feed 和文章条目的保存与查询。
- 使用 `feedparser` 实现 RSS/Atom Feed 解析。
- 实现 Feed 相关 API，包括添加订阅源、同步订阅源、查询订阅源、查询文章条目。

## 数据库初始化

先安装后端依赖：

```bash
cd backend
pip install -r requirements.txt
```

初始化 SQLite 数据库：

```bash
python init_db.py
```

执行后会创建或更新：

```text
backend/app.db
```

`app.db` 是本地运行数据，不应该提交到 Git 仓库。

## 数据表说明

### feeds

用于保存 RSS/Atom 订阅源信息。

主要字段：

- `id`：主键
- `url`：Feed 地址，唯一
- `title`：Feed 标题
- `description`：Feed 描述
- `site_url`：原网站地址
- `language`：Feed 语言
- `last_build_date`：Feed 自身声明的更新时间
- `last_fetched_at`：本地最后一次同步时间

### entries

用于保存从 Feed 中解析出的文章条目。

主要字段：

- `id`：主键
- `feed_id`：所属 Feed
- `guid`：RSS/Atom 原始文章唯一标识
- `title`：文章标题
- `link`：文章链接
- `author`：作者
- `summary`：文章摘要
- `content`：文章正文内容或摘要兜底内容
- `published_at`：发布时间
- `updated_at`：更新时间
- `is_read`：是否已读
- `is_starred`：是否收藏

文章去重逻辑：同一个 Feed 下优先使用 `guid` 去重，没有 `guid` 时使用 `link` 去重。
当前 Week13 后端不会抓取文章原网页全文。如果 RSS 源只提供摘要，API 保存和返回的也只是摘要。

### feed_fetch_logs

用于保存 Feed 抓取和同步日志。

主要字段：

- `feed_id`：关联的 Feed，添加 Feed 失败时可以为空
- `url`：抓取的 Feed 地址
- `status`：同步状态，例如 `success` 或 `failed`
- `message`：同步结果或错误信息
- `fetched_at`：抓取时间

### notes

用于保存文章笔记，为后续笔记功能预留。

### ai_results

用于保存 AI 摘要或翻译结果，为后续 AI 功能预留。

## 启动后端

进入 `backend` 目录：

```bash
uvicorn app.main:app --reload
```

启动后可以打开接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查接口：

```text
GET /api/health
```

预期返回：

```json
{
  "status": "ok",
  "storage": "sqlite",
  "database": "app.db"
}
```

## Feed API 说明

## API 开发状态

### 网络端口

- `8000`：FastAPI 后端端口，开发可用。
- `5173`：Vite 前端端口，开发可用。

### 已开发可用的 API

以下接口已经接入 SQLite 和真实 RSS/Atom 数据，可以用于当前开发：

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

### 简化实现的 API

- `GET /api/stats/llm`

该接口目前只返回简单的本地统计信息，还不是完整的 LLM 调用量统计分析。

### Mock 或预留 API

以下接口已经保留给前端和后续开发，但目前还不是完整生产实现：

- `POST /api/ai/summary/{article_id}`
- `POST /api/ai/translate/{article_id}`
- `POST /api/ai/tag-suggest/{article_id}`

AI 接口会读取真实文章数据，但摘要、翻译和标签建议结果仍然是 mock 文本，还没有接入 OpenAI-compatible、Ollama 或 vLLM 等真实模型服务。

- `GET /api/tags`
- `POST /api/tags`
- `PUT /api/tags/{tag_id}`
- `DELETE /api/tags/{tag_id}`
- `POST /api/articles/{article_id}/tags`

标签接口目前使用内存数据，没有真正持久化到 SQLite。

- `POST /api/opml/import`
- `GET /api/opml/export`

OPML 导入导出目前仍是 mock。导入不会真正创建 Feed，导出返回的是固定示例 XML。

### 添加 Feed

```text
POST /api/feeds
```

请求示例：

```json
{
  "url": "https://example.com/feed.xml"
}
```

后端会解析该 RSS/Atom 地址，将 Feed 元信息保存到 `feeds` 表，并将文章保存到 `entries` 表。
当前实现只使用 RSS/Atom Feed 自带内容，不会逐篇访问文章链接进行全文爬取。

### 查询 Feed 列表

```text
GET /api/feeds
```

返回所有已保存的订阅源。

### 查询单个 Feed

```text
GET /api/feeds/{feed_id}
```

返回指定订阅源信息。

### 同步 Feed

```text
POST /api/feeds/{feed_id}/sync
```

重新抓取该 Feed，并只插入新增文章。

### 查询某个 Feed 的文章

```text
GET /api/feeds/{feed_id}/entries
```

返回指定 Feed 下保存的文章条目。

### 查询所有文章

```text
GET /api/articles
```

支持的可选过滤参数：

- `feed_id`
- `unread`
- `starred`

示例：

```text
GET /api/articles?feed_id=1
GET /api/articles?unread=true
GET /api/articles?starred=true
```

## 关键文件

- `backend/schema.sql`：SQLite 建表 SQL。
- `backend/init_db.py`：数据库初始化脚本。
- `backend/app/database.py`：SQLite 连接和初始化逻辑。
- `backend/app/services/feed_parser.py`：RSS/Atom 解析逻辑。
- `backend/app/repositories/sqlite_repository.py`：SQLite 数据读写逻辑。
- `backend/app/routers/feeds.py`：Feed API 路由。
- `.gitignore`：忽略本地数据库、缓存、依赖目录等不应提交的文件。

## 使用流程

推荐按以下顺序操作：

```bash
cd backend
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload
```

然后打开：

```text
http://127.0.0.1:8000/docs
```

在 Swagger 页面中可以依次测试：

1. `GET /api/health` 检查后端是否启动。
2. `POST /api/feeds` 添加 RSS/Atom 地址。
3. `GET /api/feeds` 查询订阅源列表。
4. `GET /api/feeds/{feed_id}/entries` 查询该订阅源下的文章。
5. `POST /api/feeds/{feed_id}/sync` 重新同步订阅源。

## 注意事项

- `backend/app.db` 是本地数据库文件，不提交到 Git。
- 如果修改了表结构，可以删除本地 `backend/app.db` 后重新执行 `python init_db.py`。
- Feed 同步时会根据 `guid` 或 `link` 去重，避免重复插入同一篇文章。
- RSS/Atom 地址必须是可访问的 URL，否则添加或同步时会返回错误信息。
- 如果 RSS/Atom 源没有提供全文，当前后端不会额外抓取原网页全文。





# Week13 TheadoraTang - Backend, SQLite, RSS/Atom Feed API

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


# Week13 Desktop Packaging - Electron, FastAPI, SQLite

## Completed Scope

- Added an Electron desktop shell for RSSReader.
- Added `backend/desktop_server.py` so the FastAPI API can be started by Electron or packaged by PyInstaller.
- Updated backend database configuration so `RSSREADER_DB_PATH` can move SQLite data into the desktop app user data directory.
- Updated the frontend API client so Electron production builds can inject the local backend base URL.
- Added root-level scripts for desktop development and packaging.

## Desktop Architecture

Electron starts a local FastAPI backend on `127.0.0.1` with a free dynamic port, waits for `GET /api/health`, then loads the Vue UI.

In development, run:

```bash
npm install
npm run dev:desktop
```

For packaging, run:

```bash
npm run dist:desktop
```

The packaging flow builds:

- Vue frontend into `frontend/dist`
- FastAPI backend into `backend/dist/RSSReaderBackend/`
- Electron installers into `release`

## Runtime Data

The desktop backend reads the SQLite path from `RSSREADER_DB_PATH`. Electron sets this to the app user data folder:

- Windows: `%APPDATA%/RSSReader/app.db`
- macOS: `~/Library/Application Support/RSSReader/app.db`
- Linux: `~/.config/RSSReader/app.db`

The old development default remains `backend/app.db`.

## Notes

- The backend only binds to `127.0.0.1`.
- Electron uses `contextIsolation: true` and `nodeIntegration: false`.
- Code signing and notarization are not configured for the course version.
