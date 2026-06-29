# Week15 maeassar - SQLite 全文搜索 & RAG 问答

## 本周完成内容概览

- 后端实现 FTS5 全文搜索接口（`/api/search`）
- 前端新增搜索页面，支持关键词高亮和文章跳转
- 后端实现 RAG 问答系统（`/api/rag/ask`），基于 sqlite-vec 向量检索 + DeepSeek 生成
- 新增 AI 问答页面，支持后台异步建立索引并轮询进度
- AI 设置页新增 RAG 配置区块，API Key / Base URL / 模型名可通过 UI 配置
- 优化前端错误提示，按 HTTP 状态码映射为用户友好文案

---

## 后端部分

### 1. FTS5 全文搜索

文件：
- `backend/schema.sql`
- `backend/app/repositories/sqlite_repository.py`
- `backend/app/routers/search.py`

在 `entries` 表上建立 FTS5 虚拟表 `entries_fts`，tokenize 使用 `unicode61`，通过触发器自动同步插入、删除、更新。

搜索时使用前缀匹配（`"token"*`）支持词干模糊匹配，并使用 `snippet()` 提取带高亮标记的摘要片段。

接口：
```
GET /api/search?q=<keyword>&limit=50
```

### 2. RAG 问答系统

文件：
- `backend/app/services/rag_service.py`
- `backend/app/routers/rag.py`
- `backend/schema.sql`（`app_config` 表）

RAG 流程：
1. 使用 SiliconFlow `BAAI/bge-m3` 对查询文本生成 1024 维 embedding
2. 在 `entries_vec`（sqlite-vec 向量表）中检索 Top-K 最相似文章
3. 将检索结果拼入上下文，调用 DeepSeek Chat API 生成回答

接口：
```
POST /api/rag/ask          # RAG 问答
POST /api/rag/index        # 触发后台异步建立向量索引
GET  /api/rag/index/status # 查询索引进度（轮询用）
GET  /api/rag/config       # 读取 RAG 配置
PUT  /api/rag/config       # 保存 RAG 配置
```

索引构建为后台任务（FastAPI `BackgroundTasks`），避免大量文章时 HTTP 超时。索引完成或失败结果通过 `/index/status` 的 `error` 字段返回。

配置（API Key、Base URL、模型名）持久化到 `app_config` 表，支持 env var 兜底。

### 3. 错误处理优化

文件：
- `backend/app/routers/rag.py`

后端对 AI 服务调用异常按错误类型包装为友好中文提示，而非直接透出 SDK 原始异常（如 `Connection error.`）：

- 网络连接失败 → 提示检查 Base URL
- 401/鉴权失败 → 提示检查 API Key
- 模型不存在 → 提示检查模型名称

---

## 前端部分

### 1. 搜索页面

文件：
- `frontend/src/views/SearchView.vue`
- `frontend/src/router/index.ts`
- `frontend/src/App.vue`

路由：`/search`，导航栏新增搜索入口。

支持 Enter 触发搜索，结果展示文章标题、来源、时间，命中片段用 `<mark>` 高亮渲染。点击结果跳转到阅读页对应文章（通过 `route.query.article`）。使用 `keep-alive` 保持页面状态。

### 2. AI 问答页面

文件：
- `frontend/src/views/AskView.vue`
- `frontend/src/router/index.ts`
- `frontend/src/App.vue`

路由：`/ask`，导航栏新增 AI 问答入口。

功能：
- 输入自然语言问题，Ctrl+Enter 提交
- 展示 LLM 回答及引用来源卡片，点击来源可跳转原文
- "同步索引"按钮触发后台建立向量索引，每 2 秒轮询进度，完成或失败后提示

使用 `keep-alive` 保持页面状态，回答结果不因导航而丢失。

### 3. AI 设置页 RAG 配置区块

文件：
- `frontend/src/views/AISettingsView.vue`

在现有 AI 设置页新增 RAG 问答配置区，支持配置：
- Embedding：API Key、Base URL、模型名
- Chat 生成：API Key、Base URL、模型名

字段使用 placeholder 展示默认示例值（`e.g. https://...`），实际保存值黑色显示。保存后调用 `PUT /api/rag/config` 写入数据库，重启后配置保留。

### 4. 前端错误处理统一

文件：
- `frontend/src/api/client.ts`

新增 `getErrorMessage()` 工具函数，按 HTTP 状态码映射用户友好提示：

| 状态码 | 提示 |
|--------|------|
| 401/403 | 鉴权失败：请检查您的 API 密钥 (API Key) 是否正确 |
| 404/500/无响应 | 连接失败：无法访问后端服务，请检查 API URL 链接是否正确 |
| 其他 | 请求异常，请检查网络或后端配置 |

`AskView.vue`、`AISettingsView.vue` 均使用此函数替换原有裸错误信息。

---

## 新增依赖

```
sqlite-vec==0.1.9   # SQLite 向量扩展
openai==2.41.0      # OpenAI 兼容 SDK（用于 SiliconFlow + DeepSeek）
```

---

## 本地运行验证

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

使用前需在 AI 设置页填写：
- SiliconFlow API Key（用于 Embedding）
- DeepSeek API Key（用于 Chat 生成）

填写后点击"同步索引"建立向量索引，之后即可在 AI 问答页提问。

---

## 后续补丁（同分支）

### RAG 稳定性修复

**问题 1：删除文章后向量索引未清理**

- `sqlite_repository.py`：`delete_feed()` 删除 feed 前先遍历 entry ID，逐条调用 `delete_entry_vec()`
- `rag_service.py`：新增 `delete_entry_vec(entry_id)` 函数
- `rag_service.py`：`index_all_entries()` 执行时同步清理已删除文章的残留向量（stale cleanup）
- `rag_service.py`：`retrieve()` 改为 over-fetch（`top_k * 3`），过滤删除条目后取前 `top_k`，避免返回空结果

**问题 2：Embedding 维度不匹配导致 500 错误**

- `rag_service.py`：`_embed()` 改为从 DB 配置读取维度（而非硬编码 1024），并传入 `dimensions` 参数让 API 截断
- `rag_service.py`：`initialize_vec_table()` 新增检测逻辑——若现有表维度与配置不一致，自动 DROP 重建（无需重启）
- `rag.py`：`save_rag_config()` 保存后自动触发 `initialize_vec_table()`，改维度保存即生效

**问题 3：不兼容的 Embedding 模型**

经测试，阿里云 `text-embedding-async-v2` 和 `tongyi-embedding-vision-flash` 不支持 OpenAI 兼容接口（异步任务设计/多模态接口），调用返回 404。推荐模型：
- 硅基流动：`BAAI/bge-m3`（1024 维）
- 阿里云千问：`text-embedding-v4`（支持 `dimensions=1024`）

AI 设置页向量维度字段提示更新为以上两个推荐模型。

**问题 4：AskView 暗黑模式样式**

- `AskView.vue`：`answer-box` 和 `source-card` 改用 `--app-surface` / `--app-border` CSS 变量适配暗色主题
- 非 scoped `<style>` 块通过 `body.theme-dark` 选择器覆盖文字颜色（主色 `#e8eaed`，次色 `#9aa4b2`）

**功能：索引完成提示新增变更统计**

- 索引完成弹窗改为显示"新增 N 篇，删除 N 篇"，无变化时显示"（无变化）"
- 后端 `index_all_entries()` 返回 `{"added": n, "removed": n}`，`/index/status` 接口暴露 `last_added` / `last_removed` 字段

---

## 当前限制

- 向量索引为全量构建，文章较多时建立索引耗时较长（后台异步处理，不阻塞 UI）
- RAG 基于已同步文章，需先订阅并同步 RSS 源
- sqlite-vec 需要系统支持动态库加载（`enable_load_extension`）
- 不兼容 OpenAI 接口的模型（如 `text-embedding-async-v2`）无法使用，需换用支持兼容模式的模型
