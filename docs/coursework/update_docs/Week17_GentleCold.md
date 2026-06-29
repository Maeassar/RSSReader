# Week17 GentleCold - RAG 与 AI 配置集成

## 本周负责范围

- RAG 配置的 Chat 模型和 AI Summary/通用 AI Provider 保持一致，共用一套 AI 配置。
- Embedding 仍保留独立配置，避免向量检索和文本生成模型参数混在一起。
- 调整 AI 设置页 UI，让用户能清楚看到 RAG Chat 当前复用的 Provider。

## 分支说明

用户要求从 master/main 新建分支。实际检查后发现：

- `upstream/main` 只有 README、模板和 `update_docs` 等文档内容。
- 当前应用代码目录 `backend`、`frontend`、`electron` 位于 `upstream/develop`。

因此本次分支命名参考项目中 `Week数字_负责人` 的记录方式：

```text
Week17_GentleCold
```

但代码基点使用 `upstream/develop`，否则无法修改 RAG 与 AI 设置实现。

## 修改内容

### 1. RAG Chat 复用默认 LLM Provider

上游最新 `develop` 已经提供 `/api/ai/providers` 多 Provider 配置，用于 Summary Agent 和 AI 标签生成。本次没有再新增平行的单 Provider 配置，而是让 RAG Chat 直接复用同一套默认启用 Provider：

- `backend/app/services/rag_service.py` 中的 `get_chat_provider_config()` 优先读取 `repository.get_default_llm_provider()`。
- 如果本地已有旧 `rag_deepseek_*` 配置，仍保留兜底读取，避免历史配置立即失效。
- RAG `ask()` 生成回答时使用默认 Provider 的 `base_url`、`api_key` 和 `model`。

这样文章摘要、AI 标签和 RAG Chat 统一由 AI 设置页里的默认 Provider 控制。

### 2. Embedding 继续独立配置

`GET/PUT /api/rag/config` 只保留向量检索需要的 Embedding 参数：

- `siliconflow_api_key`
- `siliconflow_base_url`
- `embedding_model`
- `embedding_dim`

响应额外返回只读展示字段：

- `chat_provider_name`
- `chat_provider_model`
- `has_siliconflow_api_key`

前端据此提示当前 RAG Chat 使用哪个默认 Provider，并显示 Embedding API Key 是否已经保存。

### 3. API Key 加密保存

新增后端本地密钥加密工具：

- `backend/app/services/secret_store.py`

覆盖范围：

- `llm_providers.api_key`：创建或更新 Provider 时加密写入数据库；摘要、AI 标签和 RAG Chat 调用前再解密。
- `app_config.rag_siliconflow_api_key`：保存 RAG Embedding Key 时加密；读取 RAG 配置时不向前端回传明文。

编辑 Provider 或 RAG 配置时，如果 API Key 输入框留空，会保留数据库中已有 Key，不会误清空。

### 4. UI 调整

更新 `frontend/src/views/AISettingsView.vue`：

- 上方 “AI Provider” 说明改为文章摘要、AI 标签和 RAG Chat 共用默认 Provider。
- Provider API Key 输入框提示“已加密保存，留空则不修改”。
- Provider 列表通过 `Key 已加密` 标签展示 Key 保存状态，不回显明文。
- RAG 配置区说明改为只配置向量检索 Embedding。
- 移除 RAG 内部 Chat API Key / Base URL / 模型字段。
- 新增只读“Chat 生成 / 使用 Provider”展示，显示当前复用的 Provider 名称和模型。

## 测试记录

后端单元测试：

```bash
PYTHONPATH=backend /Users/a1234/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s backend/tests
```

结果：

```text
Ran 22 tests
OK
```

新增测试：

- `backend/tests/test_ai_rag_config.py`
  - 验证保存默认 LLM Provider 后，RAG Chat 会读取同一套 Provider 配置。
  - 验证 RAG Embedding API Key 写入数据库时会加密，接口不会回传明文。
- `backend/tests/test_llm_provider_repository.py`
  - 验证 LLM Provider API Key 数据库落盘值不是明文，并能正常解密供调用链路使用。

前端类型检查：

```bash
cd frontend
./node_modules/.bin/vue-tsc --noEmit --pretty false
```

结果：通过。

前端生产构建：

```bash
npm run build --prefix frontend
```

结果：通过。Vite 仍有 chunk size warning，不影响本次功能。

代码格式检查：

```bash
git diff --check
```

结果：通过。

## 遇到的问题

### main/master 与实际应用代码不一致

最初按要求从上游 `main` 切分支后，发现 `backend/`、`frontend/`、`electron/` 都变成未跟踪文件。进一步检查 `git ls-tree upstream/main` 与 `git ls-tree upstream/develop` 后确认，应用代码目前仍在 `develop`。

解决方式：

- 分支命名改为 `Week17_GentleCold`，与 `update_docs` 中已有周任务文档风格一致。
- 基点改为 `upstream/develop`。
- 在文档中明确记录原因。

### 上游 develop 已新增多 Provider 配置

最新 `develop` 已包含 `/api/ai/providers`、Summary Agent 流式摘要和 AI 标签生成，如果继续保留本分支早先实现的单 Provider 接口，会形成两套配置入口。

解决方式：

- 使用上游已有的多 Provider CRUD 作为唯一 AI Provider 配置入口。
- RAG Chat 复用默认启用 Provider。
- 旧 `rag_deepseek_*` 保留为兜底读取，不再在 UI 中展示和保存。

### API Key 不能明文存库

需求要求大模型 API Key 不要明文保存到数据库，并且前端需要说明已加密。

解决方式：

- 新增 `secret_store`，使用 `RSSREADER_SECRET_KEY` 或本机用户信息派生本地密钥。
- Provider Key 和 RAG Embedding Key 保存前统一加密，数据库值以 `enc:v1:` 开头。
- 前端只展示是否已保存 Key，不展示明文；留空更新时保留旧 Key。
