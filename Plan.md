# RSSReader

RSSReader 是一个基于 **Vue 3 + FastAPI + SQLite 预留接口** 的本地优先 RSS 阅读器课程项目。当前阶段已经搭建 Web 应用框架、API 契约、页面流程和 Mock Repository；SQLite 数据库与表结构将在后续阶段接入。

## 当前功能

| 作业要求 | 当前实现 |
| --- | --- |
| Feed / OPML 解析 + Sync + 内容呈现 | 已提供 Feed、Article、OPML、Sync API 和阅读页面；当前使用 Mock 数据 |
| 内容清洗 | 已预留 `content_cleaner.py`，支持 HTML 清洗和 Markdown 转换 |
| Summary Agent | 已提供 `/api/ai/summary/{article_id}` Mock 接口 |
| Translation Agent | 已提供 `/api/ai/translate/{article_id}` Mock 接口 |
| 多语言、日志和调试工具 | 前端预留 i18n；后端提供同步日志 API |
| LLM 用量统计 | 已提供 `/api/stats/llm` Mock 统计接口 |
| 笔记和文摘导出 | 已提供文章笔记 API 和 Markdown 导出 API |
| 标签系统 | 已提供标签管理、文章标签筛选和 Tag Agent Mock 接口 |

## 技术栈

- Frontend: Vue 3, Vite, TypeScript, Pinia, Vue Router, Element Plus
- Backend: FastAPI, Pydantic
- Database: SQLite + SQLAlchemy reserved, current stage uses Mock Repository
- RSS: feedparser
- Content Cleaning: BeautifulSoup, readability-lxml, markdownify
- AI: OpenAI-compatible Provider design reserved

## 本地运行

后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端 API 文档：

```text
http://127.0.0.1:8000/docs
```

前端：

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://127.0.0.1:5173
```

## 数据库接入说明

当前没有强制创建 SQLite 数据库文件和表。后续只需要将 `backend/app/repositories/mock_repository.py` 替换为 SQLAlchemy Repository，并在 `backend/app/database.py` 中启用 SQLite session。

已规划的数据表：

- `feeds`
- `articles`
- `tags`
- `article_tags`
- `notes`
- `llm_providers`
- `ai_results`
- `sync_logs`

Router 和 Service 不直接操作数据库，因此后续接入 SQLite 时不需要改动前端 API 路径。

## 文档

- [需求对照](docs/REQUIREMENTS.md)
- [数据库设计](docs/DATABASE_DESIGN.md)
- [API 设计](docs/API_DESIGN.md)
- [开发日志](docs/DEVELOPMENT_LOG.md)
- [AI 协作记录](docs/AI_COLLABORATION.md)

