# RSSReader

RSSReader 是一个基于 **Vue 3 + FastAPI + SQLite** 的本地优先 RSS 阅读器课程项目。当前阶段已经搭建 Web 应用框架、API 契约、页面流程和 SQLite Repository；AI 摘要、翻译、标签推荐等 Agent 能力仍以 Mock 或预留接口为主，后续会继续接入真实 Provider。

## 当前功能

| 功能模块 | 当前状态 |
| --- | --- |
| Feed / RSS 解析 | 已接入 `feedparser`，支持通过 Feed API 添加订阅源并解析 RSS/Atom 元数据和文章条目 |
| SQLite 持久化 | 已接入 `sqlite3` Repository，使用 `backend/schema.sql` 初始化 `backend/app.db`，保存 feeds、entries、notes、AI 结果和抓取日志 |
| OPML / Sync | 已提供 OPML、Feed Sync 和同步日志相关 API，支持后续继续完善订阅迁移和自动同步流程 |
| 内容呈现 | 已搭建 Vue 3 + Vite 前端、路由、Pinia Store、API Client 和阅读页面，用于展示 Feed 列表与文章内容 |
| 笔记和导出 | 已提供文章笔记 API 和 Markdown 导出 API，后续继续扩展单篇/多篇导出和 PDF 导出 |
| 内容清洗 | 已提供 `content_cleaner.py`，支持 HTML 清洗和 Markdown 转换能力，后续继续优化文章详情渲染 |
| 搜索 | README 规划 Week15 实现 SQLite 全文搜索 API 和搜索页面 UI，当前仍属于后续计划 |
| Summary Agent | 已提供 `/api/ai/summary/{article_id}` Mock 接口，后续接入 LLM Provider 抽象层和 OpenAI-compatible API |
| Translation Agent | 已提供 `/api/ai/translate/{article_id}` Mock 接口，后续实现翻译 Agent 和多语言阅读支持 |
| 多语言、日志和统计 | 前端预留 i18n；后端提供同步日志 API 和 `/api/stats/llm` Mock 统计接口 |
| 标签系统 | 已提供标签管理、文章标签筛选和 Tag Agent Mock 接口，标签关联的持久化结构仍需继续完善 |

## 技术栈

- Frontend: Vue 3, Vite, TypeScript, Pinia, Vue Router, Element Plus
- Backend: FastAPI, Pydantic
- Database: SQLite with `sqlite3`; SQLAlchemy is listed as a possible future
  migration path
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

当前后端已经接入 SQLite。`backend/app/database.py` 负责创建连接、开启外键约束并执行 `backend/schema.sql`；`backend/app/repositories/__init__.py` 默认导出 `sqlite_repository.py` 中的 Repository。当前实现使用 Python 标准库 `sqlite3`，不是 SQLAlchemy Repository。

现有核心表：

- `feeds`
- `entries`
- `feed_fetch_logs`
- `notes`
- `ai_results`

仍待完善的规划能力：

- 标签持久化与文章标签关联表，例如 `tags`、`article_tags`
- LLM Provider 配置表，例如 `llm_providers`
- SQLite 全文搜索索引或 FTS 表
- 更明确的迁移机制，替代当前启动时执行 schema 和轻量字段补齐的方式

Router 和 Service 保持不直接操作数据库，数据访问集中在 Repository 层。后续扩展 SQLite 表结构、迁移到 SQLAlchemy，或接入真实 AI Provider 时，应尽量保持前端 API 路径稳定。

## 文档

- [需求对照](REQUIREMENTS.md)
- [数据库设计](DATABASE_DESIGN.md)
- [API 设计](API_DESIGN.md)
- [开发日志](DEVELOPMENT_LOG.md)
- [AI 协作记录](AI_COLLABORATION.md)

