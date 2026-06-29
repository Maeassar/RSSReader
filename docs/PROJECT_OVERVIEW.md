# RSSReader 项目快速理解指南

> 本文档用于帮助新加入的开发者快速理解项目全貌。  
> 创建日期：2026-05-27

---

## 一、项目定位

**RSSReader** 是一个**本地优先的 RSS/Atom 阅读器**课程项目（Week12–Week18），由约 9 名学生协作开发，目标是**实践开源协作流程**。

核心产出是一个可以在浏览器和桌面端（Windows/macOS/Linux）运行的 RSS 阅读工具，支持订阅管理、文章阅读、笔记、标签、搜索、导出、AI 摘要翻译等功能。

---

## 二、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端框架** | [`Vue 3`](frontend/package.json:20) + [`Vite`](frontend/vite.config.ts:1) | 组合式 API + SFC |
| **UI 组件库** | [`Element Plus`](frontend/package.json:14) | 完整的 Web 界面组件 |
| **状态管理** | [`Pinia`](frontend/src/stores/reader.ts:1) | Vue 3 官方状态管理 |
| **路由** | [`Vue Router`](frontend/src/router/index.ts:1) | Hash/History 模式双支持 |
| **HTTP 客户端** | [`Axios`](frontend/src/api/client.ts:1) | 封装在 `rssApi` 对象中 |
| **国际化** | [`vue-i18n`](frontend/src/i18n/index.ts:1) | 已预留中英文结构 |
| **后端框架** | [`FastAPI`](backend/app/main.py:1) | Python 异步 Web 框架 |
| **数据库** | [`SQLite`](backend/app/database.py:1) | 文件级嵌入式数据库 |
| **ORM** | 直接使用 [`sqlite3`](backend/app/database.py:1) | 轻量直连，未使用 SQLAlchemy |
| **RSS 解析** | [`feedparser`](backend/app/services/feed_parser.py:1) | 标准 RSS/Atom 解析 |
| **内容清洗** | [`BeautifulSoup4`](backend/app/services/content_cleaner.py:5) + [`markdownify`](backend/app/services/content_cleaner.py:6) | HTML 清洗 + Markdown 转换 |
| **桌面端** | [`Electron`](electron/main.js:1) + [`PyInstaller`](backend/requirements.txt:9) | 跨平台桌面打包 |
| **AI 接口** | OpenAI-compatible API | 支持云端和本地模型（Ollama/vLLM） |

---

## 三、项目结构

```
RSSReader/
├─ backend/                    # FastAPI 后端
│  ├─ app/
│  │  ├─ main.py              # 入口：注册路由、中间件
│  │  ├─ database.py          # SQLite 连接与初始化
│  │  ├─ models/              # 数据模型（预留）
│  │  ├─ schemas/rss.py       # Pydantic 请求/响应模型
│  │  ├─ routers/             # API 路由
│  │  │  ├─ feeds.py          # 订阅源 CRUD + 同步
│  │  │  ├─ articles.py       # 文章列表/详情/标记
│  │  │  ├─ opml.py           # OPML 导入导出
│  │  │  ├─ tags.py           # 标签管理
│  │  │  ├─ notes.py          # 笔记
│  │  │  ├─ ai.py             # AI 摘要/翻译
│  │  │  ├─ export.py         # Markdown 导出
│  │  │  ├─ stats.py          # LLM 用量统计
│  │  │  └─ logs.py           # 同步日志
│  │  ├─ services/            # 业务逻辑层
│  │  │  ├─ feed_parser.py    # RSS/Atom 解析
│  │  │  ├─ feed_service.py   # 订阅源业务逻辑
│  │  │  ├─ article_service.py
│  │  │  ├─ content_cleaner.py # HTML 清洗
│  │  │  ├─ export_service.py  # 导出逻辑
│  │  │  ├─ ai_service.py     # AI 接口（当前为 Mock）
│  │  │  └─ ...
│  │  └─ repositories/        # 数据访问层
│  │     ├─ sqlite_repository.py  # SQLite 实现（当前使用）
│  │     └─ mock_repository.py    # Mock 实现（已废弃）
│  ├─ schema.sql              # 数据库 DDL
│  ├─ init_db.py              # 手动初始化数据库脚本
│  ├─ desktop_server.py       # Electron 桌面端后端入口
│  └─ requirements.txt        # Python 依赖
├─ frontend/                  # Vue 3 前端
│  ├─ src/
│  │  ├─ main.ts              # 前端入口
│  │  ├─ App.vue              # 根组件+导航栏
│  │  ├─ styles.css           # 全局样式
│  │  ├─ api/client.ts        # 统一 API 客户端
│  │  ├─ stores/
│  │  │  ├─ reader.ts         # 阅读器状态（Feed/文章/标签）
│  │  │  └─ preferences.ts    # 用户偏好（主题/字体）
│  │  ├─ router/index.ts      # 路由配置
│  │  ├─ i18n/index.ts        # 国际化（已预留）
│  │  ├─ types/electron.d.ts  # Electron 类型声明
│  │  └─ views/
│  │     ├─ ReaderView.vue    # 阅读首页（核心）
│  │     ├─ FeedManageView.vue # 订阅管理页
│  │     ├─ TagsView.vue      # 标签管理页
│  │     ├─ AISettingsView.vue # AI 设置页
│  │     ├─ StatsView.vue     # 统计日志页
│  │     └─ SettingsView.vue  # 设置页
│  ├─ vite.config.ts          # Vite 配置（代理 /api 到后端）
│  └─ package.json
├─ electron/                  # Electron 桌面端
│  ├─ main.js                 # 主进程：自启后端 + 加载前端
│  └─ preload.js              # 预加载桥接
├─ docs/                      # 文档
│  ├─ REQUIREMENTS.md         # 需求对照
│  ├─ API_DESIGN.md           # API 设计
│  ├─ DATABASE_DESIGN.md      # 数据库设计
│  ├─ NOTES.md                # 开发笔记与启动指南
│  ├─ PROJECT_OVERVIEW.md     # 本文档
│  └─ AI_COLLABORATION.md     # AI 协作记录
└─ scripts/                   # 构建/开发脚本
```

---

## 四、架构设计

### 4.1 分层架构

```
[浏览器 / Electron]           ← 前端
      ↓ HTTP
[Router (API路由)]            ← 后端路由层
      ↓
[Service (业务逻辑)]          ← 服务层
      ↓
[Repository (数据访问)]       ← 数据访问层
      ↓
[SQLite (数据库)]             ← 持久化
```

关键设计原则：
- **Router 不直接操作数据库**，通过 Service 调用 Repository
- **Repository 可替换**：当前使用 [`SQLiteRepository`](../backend/app/repositories/sqlite_repository.py:432)，之前的设计是 Mock-first（见 [`PLAN.md`](coursework/PLAN.md:53)）
- **Service 层复用 Repository 接口**，切换数据库无需修改业务逻辑

### 4.2 前后端通信

- **Web 开发模式**：Vite dev server 在 `127.0.0.1:5173`，通过 [`proxy`](frontend/vite.config.ts:11) 将 `/api` 请求转发到 `127.0.0.1:8000`
- **桌面端模式**：Electron 通过环境变量注入真实后端地址，前端 API client 读取 [`window.rssReaderDesktop.apiBaseUrl`](frontend/src/api/client.ts:3)
- **统一 API 客户端**：[`frontend/src/api/client.ts`](frontend/src/api/client.ts) 中的 `rssApi` 对象封装了所有后端调用

### 4.3 数据库设计

[`schema.sql`](backend/schema.sql) 定义了 5 张核心表：

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `feeds` | 订阅源 | url, title, site_url, last_fetched_at |
| `entries` | 文章 | feed_id, guid, title, content, is_read, is_starred |
| `feed_fetch_logs` | 同步日志 | feed_id, status, message |
| `notes` | 笔记 | entry_id (1:1 关联), content |
| `ai_results` | AI 结果 | entry_id, task_type, provider, result, tokens |

- 数据库文件默认位置：`backend/app.db`（Web 模式）或 OS 用户数据目录（桌面端）
- 可通过环境变量 `RSSREADER_DB_PATH` 自定义
- 启动时自动执行 [`initialize_database()`](backend/app/database.py:23) 建表 + 迁移

---

## 五、功能清单与实现状态

| 功能模块 | 当前状态 | 关键文件 |
|----------|----------|----------|
| ✅ RSS/Atom 解析 & 添加订阅 | **已完成** | [`feed_parser.py`](backend/app/services/feed_parser.py:6), [`feeds.py`](backend/app/routers/feeds.py:15) |
| ✅ 文章列表/详情/已读/收藏 | **已完成** | [`articles.py`](backend/app/routers/articles.py:9), [`sqlite_repository.py`](backend/app/repositories/sqlite_repository.py:128) |
| ✅ 同步全部/单源 | **已完成** | [`sqlite_repository.py`](backend/app/repositories/sqlite_repository.py:90) |
| ✅ OPML 导入导出 | **接口已实现** | [`opml.py`](backend/app/routers/opml.py:1) |
| ✅ HTML 内容清洗 | **已完成** | [`content_cleaner.py`](backend/app/services/content_cleaner.py:5) |
| ✅ Markdown 导出 | **已完成**（单篇导出 + 批量 digest 导出） | [`export_service.py`](backend/app/services/export_service.py:1) |
| ✅ 笔记 | **已完成** | [`notes.py`](backend/app/routers/notes.py:1) |
| ⚠️ 标签管理 | **部分完成**（内存存储） | [`sqlite_repository.py`](backend/app/repositories/sqlite_repository.py:236) |
| ⚠️ AI 摘要/翻译 | **接口骨架**（Mock 实现） | [`ai_service.py`](backend/app/services/ai_service.py:1) |
| 🔲 AI 真实 LLM 接入 | **待开发** | 已预留 Provider 抽象层 |
| 🔲 全文搜索 | **待开发** | - |
| 🔲 Docker 部署 | **待开发** | - |
| ✅ Electron 桌面端 | **已完成** | [`electron/main.js`](electron/main.js:1) |
| ✅ 跨平台打包 | **已完成** | PyInstaller + Electron builder |

---

## 六、API 总览

完整 API 列表见 [`docs/API_DESIGN.md`](docs/API_DESIGN.md)，核心端点：

```
Feed:    GET/POST    /api/feeds
         PUT/DELETE  /api/feeds/{id}
         POST        /api/feeds/{id}/sync
Article: GET         /api/articles?feed_id=&unread=&starred=
         GET/PATCH   /api/articles/{id}
         PATCH       /api/articles/{id}/read
         PATCH       /api/articles/{id}/star
OPML:    POST        /api/opml/import
         GET         /api/opml/export
Tag:     CRUD        /api/tags
Note:    GET/PUT     /api/articles/{id}/note
Export:  GET         /api/export/articles/{id}/markdown
         POST        /api/export/articles/markdown
         POST        /api/export/digests/markdown
AI:      POST        /api/ai/summary|translate|tag-suggest/{article_id}
Stats:   GET         /api/stats/llm
Logs:    GET         /api/logs/sync
```

FastAPI 自动生成 Swagger 文档：`http://127.0.0.1:8000/docs`

---

## 七、四种启动方式

### 7.1 Web 后端调试（固定端口）
```bash
cd backend
uvicorn app.main:app --reload
# → http://127.0.0.1:8000/docs
```

### 7.2 Web 前端开发（浏览器）
```bash
cd frontend
npm install
npm run dev
# → http://127.0.0.1:5173
```

### 7.3 Electron 开发（热更新）
```bash
npm install
pip install -r backend/requirements.txt
npm run dev:desktop
# 自动启动 Vite + FastAPI + Electron
```

### 7.4 桌面端构建
```bash
npm run dist:desktop
# 产物在 release/ 目录
```

详见 [`docs/NOTES.md`](docs/NOTES.md:72)

---

## 八、可行性分析

### ✅ 技术可行性

| 维度 | 评估 |
|------|------|
| **前端** | Vue 3 + Element Plus 已完善搭建，6 个页面覆盖所有功能入口，架构合理 |
| **后端** | FastAPI 分层清晰，SQLite 持久化已完整实现，23+ 个 API 端点均可调用 |
| **数据库** | schema.sql 定义完整，启动自动建表 + 列迁移，已适配桌面端用户数据目录 |
| **桌面端** | Electron + PyInstaller 打包链路打通，支持跨平台 |
| **AI 功能** | 接口骨架已预留，采用 OpenAI-compatible API 设计，可对接云端/本地模型 |
| **协作** | GitHub Issues + PR 流程 + AGENTS.md + Conventional Commits 已建立 |

### ⚠️ 待完善风险点

1. **AI 真实集成未做**：当前 [`ai_service.py`](backend/app/services/ai_service.py:1) 返回 Mock 数据，需接入真实 LLM Provider
2. **标签未持久化**：标签数据存储在内存列表中（见 [`sqlite_repository.py`](backend/app/repositories/sqlite_repository.py:240) 的 `self.tags`）
3. **全文搜索未实现**：SQLite FTS 索引尚未建立
4. **OPML 导入解析未做**：路由结构已预留但解析逻辑待完成
5. **Docker 部署未做**：需要编写 Dockerfile + docker-compose.yml

### ✅ 总体结论

**项目可行性强，风险可控**。核心骨架（前后端通信、数据库持久化、桌面端打包、API 体系）已完全搭建完毕，剩余工作集中在功能完善和真实 AI 集成上，符合课程 18 周的渐进式开发节奏。

---

## 九、快速理解要点

1. **这是一个"先搭骨架再填肉"的项目**：Router → Service → Repository 三层架构先完整搭建，再逐个替换实现
2. **核心入口是两个文件**：
   - 前端一切从 [`App.vue`](frontend/src/App.vue:1) 开始（导航 -> 路由 -> 页面）
   - 后端一切从 [`main.py`](backend/app/main.py:1) 开始（路由注册 -> Service -> Repository -> SQLite）
3. **数据流很直观**：`ReaderView.vue` → `reader.ts` (Pinia) → `client.ts` (Axios) → `/api/*` → Router → Service → Repository → SQLite
4. **API 定义在前端和后端是**双写的**：前端 [`client.ts`](frontend/src/api/client.ts) 的 `rssApi` 和后端 Router 一一对应
5. **Mock 转 SQLite**已完成：项目初期用 Mock 数据，现在 [`sqlite_repository.py`](backend/app/repositories/sqlite_repository.py:432) 已是真实 SQLite 持久化
