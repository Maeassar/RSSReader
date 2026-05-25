# RSSReader 项目说明与开发笔记

## 1. 项目功能概览

RSSReader 是一个本地优先的 RSS/Atom 阅读器课程项目，当前技术栈为
Vue 3 + Vite 前端、FastAPI 后端、SQLite 数据库，并通过 Electron
提供 Windows、macOS、Linux 桌面端运行能力。

当前主要功能包括：

- RSS/Atom 订阅源添加、查询和同步。
- 文章列表、文章详情、已读/未读、收藏状态。
- 文章笔记保存。
- Markdown 导出接口。
- OPML 导入/导出接口预留。
- 同步日志和基础统计接口。
- 标签管理与标签筛选接口预留。
- AI 摘要、AI 翻译、AI 标签建议接口预留，当前仍以 mock 或占位逻辑为主。
- Electron 桌面端自动启动本地 FastAPI 后端。

## 2. 架构设计

项目分为三层：

- 前端层：`frontend/`
  - Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus。
  - 统一 API client 位于 `frontend/src/api/client.ts`。
  - Web 开发模式默认请求 `/api`，由 Vite proxy 转发到 `127.0.0.1:8000`。
  - 桌面端由 Electron 注入真实后端地址。

- 后端层：`backend/`
  - FastAPI 应用入口为 `backend/app/main.py`。
  - 路由、服务、Schema、Repository 分层组织。
  - SQLite 初始化逻辑位于 `backend/app/database.py`。
  - 桌面端后端启动入口为 `backend/desktop_server.py`。

- 桌面层：`electron/`
  - Electron 主进程负责启动后端、等待健康检查、加载前端。
  - 生产桌面端使用 `app://rssreader` 加载构建后的前端资源。
  - 后端通过 PyInstaller 打包到 `backend/dist/RSSReaderBackend/`。

## 3. 数据库说明

Web 开发模式默认使用：

```text
backend/app.db
```

桌面端运行时使用系统用户数据目录：

```text
Windows: %APPDATA%/RSSReader/app.db
macOS: ~/Library/Application Support/RSSReader/app.db
Linux: ~/.config/RSSReader/app.db
```

如果需要让本地 API 调试使用桌面端同一份数据库，可以在启动后端前设置：

```powershell
$env:RSSREADER_DB_PATH="$env:APPDATA\RSSReader\app.db"
cd backend
uvicorn app.main:app --reload
```

然后访问：

```text
http://127.0.0.1:8000/docs
```

## 4. 四种启动和使用方式

### 4.1 Web 后端 API 调试

用于固定端口测试接口和 Swagger 文档。

```bash
cd backend
uvicorn app.main:app --reload
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

### 4.2 Web 前端开发

用于浏览器内开发 Vue 页面。

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://127.0.0.1:5173
```

### 4.3 Electron 开发热更新

用于桌面端开发调试。

```bash
npm install
pip install -r backend/requirements.txt
npm run dev:desktop
```

该模式会启动 Vite、Electron 和本地 FastAPI 后端，并默认打开 DevTools。

### 4.4 桌面端构建和运行

用于生成桌面端产物。

```bash
npm run dist:desktop
```

Windows 本地目录版运行入口：

```text
release/win-unpacked/RSSReader.exe
```

macOS 打包需要在 macOS 机器上执行同样的构建命令，产物会输出到 `release/`。

## 5. 接口测试说明
**后端是随机找到空闲端口，所以每一次都不一样**,可以看终端输出，然后访问

```bash
http://127.0.0.1:端口/docs
```
调试api接口

常用接口：

- `GET /api/health`
- `GET /api/feeds`
- `POST /api/feeds`
- `POST /api/feeds/{feed_id}/sync`
- `POST /api/feeds/sync-all`
- `GET /api/articles`
- `GET /api/articles/{article_id}`
- `GET /api/tags`
- `GET /api/logs/sync`


## 6. Pull Request 流程

### 6.1 分支命名

每个任务新建一个分支，不直接向 `main` 提交代码。

```text
feat/<topic>
fix/<topic>
docs/<topic>
test/<topic>
refactor/<topic>
chore/<topic>
```

示例：

```bash
git checkout -b feat/rss-import
git checkout -b docs/desktop-notes
```

### 6.2 Commit 格式

使用 Conventional Commits：

```text
<type>(<scope>): <short description>
```

常用类型：

```text
feat, fix, docs, test, refactor, chore, revert
```

常用 scope：

```text
frontend, backend, rss, sync, notes, search, export, ai-summary, ai-translation, docs, ci
```

示例：

```bash
git commit -m "feat(desktop): add electron packaging"
git commit -m "docs(docs): update desktop usage notes"
```

### 6.3 PR 模板填写要求

提交 PR 时需要填写 `.github/pull_request_template.md` 中的内容：

- Summary：说明 PR 做了什么，建议 1-3 条。
- Motivation：说明为什么需要这个改动，并关联 issue。
- Changes：勾选涉及的范围，如 Frontend、Backend、Database、Documentation、Tests / CI。
- Test Plan：说明执行过的测试命令和人工验证步骤。
- Documentation：说明是否更新 README、`update_docs/` 或 API 文档。
- Checklist：确认分支、PR 标题、敏感信息、数据库文件和生成产物没有误提交。

### 6.4 文档更新要求

以下情况需要同步更新文档：

- 新增或修改后端 API。
- 修改数据库表结构或迁移方式。
- 修改前端路由、页面、组件或状态假设。
- 修改桌面端启动、打包或数据目录。
- 新增 AI 相关配置、Provider 或环境变量。

每周任务完成后，在 `update_docs/` 下新增或更新：

```text
Week{week_number}_{github_name}.md
```

### 6.5 不应提交的文件

不要提交以下内容：

- `.venv/`
- `node_modules/`
- `.npm-cache/`
- `.electron-cache/`
- `frontend/dist/`
- `backend/build/`
- `backend/dist/`
- `release/`
- `__pycache__/`
- `*.pyc`
- `*.db`
- `*.sqlite`
- 日志文件
- API key 或其它密钥

提交前建议检查：

```bash
git status
```

## 7. Mac 测试说明

由于桌面端需要支持 macOS，Mac 测试需要覆盖：

- macOS 上执行 `npm run dist:desktop` 是否能成功生成桌面端产物。
- 桌面端是否能自动启动后端。
- 数据库是否写入 `~/Library/Application Support/RSSReader/app.db`。
- RSS Feed 添加、同步和阅读是否正常。
- 退出应用后后端进程是否被清理。

Week13 和 Week14 由唐益参与 Mac 端功能测试和桌面端兼容性验证。
