# RSSReader Web 应用开发计划

## Summary

开发一个基于 **Vue 3 + FastAPI + SQLite** 的本地优先 RSS 阅读器。当前阶段先完成 Web 应用框架、页面、API 结构和业务流程，并**保留数据库相关接口与数据模型设计**；由于目前还没有建立 SQLite 数据库和表，后端先使用临时 Mock / 内存数据实现接口联调，后续再替换为真实 SQLite + SQLAlchemy 持久化。

目标是满足 `demand.png` 中的功能与技术约束：RSS/OPML 订阅、文章同步、内容清洗、AI 摘要与翻译、标签、笔记导出、LLM 用量统计、本地优先、跨平台 Web 运行，以及完整开发文档。

## Key Changes

- 前端使用 `Vue 3 + Vite + TypeScript + Pinia + Vue Router + Element Plus`。
- 后端使用 `FastAPI`，先建立 API、Service、Repository 分层。
- 数据库层先只保留接口，不强制创建 SQLite 文件和表。
- 后续数据库正式接入时使用 `SQLite + SQLAlchemy`。
- 当前阶段 Repository 可以返回 Mock 数据，保证前后端可以先跑通。
- 所有数据库相关代码要预留替换点，避免后续大改业务逻辑。
- AI Provider 采用 OpenAI-compatible API 设计，支持后续配置 Base URL、API Key、Model。

## Implementation Plan

### 1. 项目结构

建立如下结构：

```text
RSSReader/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ database.py
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ routers/
│  │  ├─ services/
│  │  ├─ repositories/
│  │  └─ utils/
│  ├─ requirements.txt
│  └─ rssreader.db
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ stores/
│  │  ├─ router/
│  │  ├─ views/
│  │  ├─ components/
│  │  └─ i18n/
├─ docs/
└─ README.md
```

其中 `repositories/` 是重点预留层：

- 当前阶段：Repository 使用 Mock / 内存列表返回数据。
- 后续阶段：Repository 替换为 SQLAlchemy 查询 SQLite。
- Router 和 Service 不直接操作数据库。

### 2. 数据库预留设计

先设计但暂不强制创建的表：

```text
feeds
articles
tags
article_tags
notes
llm_providers
ai_results
sync_logs
```

对应数据含义：

- `feeds`：RSS 源信息。
- `articles`：文章内容、清洗内容、已读、收藏。
- `tags`：标签信息。
- `article_tags`：文章和标签关系。
- `notes`：文章笔记。
- `llm_providers`：AI 服务配置。
- `ai_results`：摘要、翻译、标签推荐结果。
- `sync_logs`：同步日志。

当前阶段需要先写好 Pydantic Schema，例如：

```text
FeedCreate
FeedRead
ArticleRead
TagRead
NoteRead
LLMProviderRead
AIResultRead
SyncLogRead
```

SQLAlchemy Model 可以先建立文件和类名，也可以先用注释 / TODO 标明字段，等数据库创建时再完善。

### 3. 后端 API 预留

先实现 API 路由结构，接口返回 Mock 数据或占位响应，保证前端可调用。

```text
GET    /api/feeds
POST   /api/feeds
PUT    /api/feeds/{id}
DELETE /api/feeds/{id}
POST   /api/feeds/{id}/sync
POST   /api/feeds/sync-all

GET    /api/articles
GET    /api/articles/{id}
PATCH  /api/articles/{id}/read
PATCH  /api/articles/{id}/star

POST   /api/opml/import
GET    /api/opml/export

GET    /api/tags
POST   /api/tags
PUT    /api/tags/{id}
DELETE /api/tags/{id}
POST   /api/articles/{id}/tags

GET    /api/articles/{id}/note
PUT    /api/articles/{id}/note

POST   /api/ai/summary/{article_id}
POST   /api/ai/translate/{article_id}
POST   /api/ai/tag-suggest/{article_id}

GET    /api/export/articles/{id}/markdown
POST   /api/export/articles/markdown

GET    /api/stats/llm
GET    /api/logs/sync
```

当前阶段接口行为：

- `GET` 接口返回示例数据。
- `POST / PUT / PATCH / DELETE` 接口返回成功响应，但可暂不真实持久化。
- RSS 同步接口先返回“同步任务已触发”的模拟结果。
- AI 接口先返回模拟摘要、模拟翻译、模拟标签。
- 日志和统计接口先返回示例统计数据。

### 4. 前端页面

先按真实业务页面开发，不依赖真实数据库。

需要实现：

- 阅读首页：左侧订阅源，中间文章列表，右侧文章内容。
- 订阅管理页：添加 RSS、同步、OPML 导入导出按钮。
- 标签管理页：标签列表、创建、编辑、删除。
- AI 设置页：Provider、Base URL、API Key、Model 配置表单。
- 统计日志页：同步日志、AI 调用次数、token 用量。
- 设置页：语言切换、阅读样式。

前端 API 调用真实后端接口，即使后端当前返回 Mock 数据，也要保持最终接口路径不变。

### 5. 后续 SQLite 接入方式

等数据库和表建立后，只需要替换 Repository 层：

- `FeedRepository` 改为查询 `feeds` 表。
- `ArticleRepository` 改为查询 `articles` 表。
- `TagRepository` 改为查询 `tags` 和 `article_tags`。
- `NoteRepository` 改为查询 `notes`。
- `LLMRepository` 改为查询 `llm_providers` 和 `ai_results`。
- `LogRepository` 改为查询 `sync_logs`。

Router、Service、前端页面、API 路径保持不变。

## Development Order

1. 搭建 FastAPI 项目结构。
2. 建立 Pydantic Schema。
3. 建立 Repository 接口和 Mock Repository。
4. 建立 Router 和 Service。
5. 搭建 Vue 项目结构。
6. 实现前端页面和 API 调用。
7. 用 Mock 数据跑通阅读器基础流程。
8. 实现 RSS 解析和内容清洗服务，但结果可先不入库。
9. 实现 OPML 导入导出接口结构。
10. 实现 AI 摘要、翻译、标签推荐的接口结构。
11. 编写数据库设计文档。
12. 后续建立 SQLite 表。
13. 将 Mock Repository 替换为 SQLAlchemy Repository。
14. 补充真实数据同步、查询、更新逻辑。
15. 完成 README、API 文档、开发日志和 AI 协作记录。

## Test Plan

- API 可访问：FastAPI `/docs` 中能看到所有预留接口。
- Mock 数据测试：前端能正常展示订阅源、文章、标签、日志和统计数据。
- 页面流程测试：点击同步、收藏、已读、摘要、翻译等按钮有明确反馈。
- 接口契约测试：后续接入 SQLite 时，接口路径和前端调用不需要改。
- Repository 替换测试：Mock Repository 替换为 SQLAlchemy Repository 后，Service 层不需要大改。
- RSS 解析测试：有效 RSS URL 能解析出文章结构。
- OPML 测试：能解析 OPML 文件中的订阅源 URL。
- AI 接口测试：未配置 Provider 时返回清晰错误；配置后可调用真实模型。
- 文档测试：README 能说明当前阶段哪些功能是 Mock，哪些接口为后续数据库预留。

## Assumptions

- 当前阶段不强制创建 SQLite 数据库和表。
- 当前阶段允许使用 Mock / 内存数据，重点是先固定接口和页面结构。
- 数据库最终仍然使用 SQLite。
- 后续接入数据库时不改变前端 API 路径。
- 后续接入数据库时优先修改 Repository 层，不重写 Router 和前端页面。
- AI 功能当前可先返回模拟结果，等 Provider 配置完成后再接入真实模型。
- 项目最终交付时需要在 README 中说明：早期阶段使用 Mock 数据，后续已预留 SQLite 接口。
