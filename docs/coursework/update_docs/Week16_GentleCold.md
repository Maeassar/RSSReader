# Week16 GentleCold - Summary Agent 后端系统

## 本周负责范围

- Summary Agent 核心开发。
- LLM Provider 抽象层。
- OpenAI-Compatible API 接入。
- vLLM / Ollama 本地模型接入配置。
- Summary LLM 用量统计。

## 主要实现

### 1. Summary Agent

新增 `backend/app/services/summary_agent.py`：

- 从文章标题、`cleaned_markdown`、`cleaned_html`、`raw_html`、RSS `summary` 中构造摘要输入。
- 优先使用清洗后的 Markdown，避免把 HTML 标签直接喂给模型。
- 对超长正文做 12000 字符截断，避免一次请求过大。
- 支持 `brief`、`structured`、`deep` 三种摘要模式。
- 支持中文 / 英文输出和 120-1200 词长度预算。
- Prompt 参考 coding agent 的工作方式：先理解输入约束，再提取事实，最后自检是否忠于原文。
- 针对模型上下文限制实现多轮上下文循环：先估算 token 预算，长文自动切块，每个 chunk 生成事实笔记；如果中间笔记仍超预算，再做 compaction；最后进行 final merge 得到整篇文章摘要。
- 短文仍走单轮摘要，长文才进入 chunk summary -> compaction -> final merge，避免普通摘要请求被不必要地变慢。
- 输出增加 `可信度：高/中/低`，用于提醒正文是否充分。
- 对 Qwen3 常见的 `<think>...</think>` 或 `最终答案：` 前缀做清洗，避免内部推理泄露到阅读页。
- 对 Ollama + Qwen3 通过 OpenAI-compatible API 调用时传入 `reasoning_effort: "none"`，避免模型把输出放入 `reasoning` 字段而 `content` 为空。
- 调用失败时将连接失败、鉴权失败、模型不存在等错误转成可读提示。

参考资料：

- Anthropic Engineering, Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- OpenAI Agents SDK 文档：Agents / Guardrails / Tracing / Usage 等模块，https://openai.github.io/openai-agents-python/
- Ollama Qwen3 模型页：`qwen3:8b` 为 5.2GB、40K context，https://ollama.com/library/qwen3

### 2. Provider 抽象与配置

新增 `llm_providers` 表，支持以下 provider 类型：

- `openai_compatible`
- `vllm`
- `ollama`
- `custom`

后端新增接口：

- `GET /api/ai/providers`
- `POST /api/ai/providers`
- `PUT /api/ai/providers/{provider_id}`
- `DELETE /api/ai/providers/{provider_id}`
- `POST /api/ai/summary/{article_id}`
- `POST /api/ai/summary/{article_id}/stream`

Provider 记录字段包括：

- `name`
- `provider_type`
- `base_url`
- `api_key`
- `model`
- `enabled`
- `is_default`

摘要调用统一走 OpenAI-compatible Chat Completions 协议，因此 vLLM 与 Ollama 只要暴露 `/v1/chat/completions` 即可复用同一套 agent。

### 3. vLLM / Qwen3-8B 本地模型

前端 AI 设置页提供 `vLLM Qwen3-8B` 快速模板：

- Provider: `Local vLLM Qwen3-8B`
- 类型: `vllm`
- Base URL: `http://127.0.0.1:8001/v1`
- Model: `Qwen/Qwen3-8B`

Web/Electron 开发时 FastAPI 常用 `8000` 端口，因此模板默认使用 `8001`，避免和后端冲突。如果单独运行 vLLM 且没有端口冲突，也可以使用 vLLM 常见默认端口 `8000`。

ModelScope 下载与 vLLM 启动示例：

```bash
pip install modelscope vllm
modelscope download --model Qwen/Qwen3-8B --local_dir ./models/Qwen3-8B
vllm serve ./models/Qwen3-8B \
  --served-model-name Qwen/Qwen3-8B \
  --host 127.0.0.1 \
  --port 8001
```

然后在 RSSReader 的 AI 设置中选择 `vLLM Qwen3-8B` 模板，确认 Base URL 为：

```text
http://127.0.0.1:8001/v1
```

### 4. Ollama / Qwen3-8B 本地模型

前端 AI 设置页提供 `Ollama` 快速模板：

- Provider: `Local Ollama`
- 类型: `ollama`
- Base URL: `http://127.0.0.1:11434/v1`
- API Key: `ollama`
- Model: `qwen3:8b`

启动示例：

```bash
ollama pull qwen3:8b
ollama serve
```

Ollama 的 OpenAI-compatible endpoint 通常是：

```text
http://127.0.0.1:11434/v1
```

### 5. 前端接入

更新 `frontend/src/views/AISettingsView.vue`：

- 将原“Provider 配置界面预留”改为真实 CRUD。
- 支持 vLLM、Ollama、OpenAI-compatible 三类快速模板。
- 支持设置默认 provider。
- Provider 表格展示名称、类型、模型、Base URL、启用/默认状态。

更新 `frontend/src/views/ReaderView.vue`：

- 摘要按钮改为清晰的摘要设置面板，provider 只是配置项，用户需要点击明确的 `生成摘要` 按钮才会开始生成。
- 可选择默认 provider 或指定 provider。
- 可在摘要面板中选择摘要模式、输出语言和长度预算。
- 摘要生成中会展示后端真实事件流：`prepare`、`budget`、`chunk_plan`、`chunk_start`、`chunk_done`、`final_start`、`final_done`、`save_done` 等事件由 Summary Agent 在实际执行节点发出。
- 前端不再使用 `setInterval` 或固定步骤假装进度；如果模型调用卡在某个 chunk，页面会停留在对应真实步骤。
- 当前运行步骤使用轻量呼吸态，已完成步骤沉淀为阅读页风格的时间线记录，并显示该步骤实际停留时间。
- 摘要完成后思考流自动隐藏，页面展示最终摘要；用户可以点击 `查看思考过程` 重新展开。
- 切换文章时会清空上一篇文章的摘要结果和步骤，避免摘要串到其它文章。
- 摘要结果展示在文章正文下方。
- 展示本次调用的输入 / 输出 token。

### 6. 真实事件流实现

为回应人工验收中“前几步太快、时间全卡在最后一步会误导用户”的反馈，本轮把前端模拟进度改成后端驱动的流式事件。

后端实现：

- `summary_agent.summarize_with_provider(..., on_event=...)` 接收事件回调。
- 在真实执行节点发事件：读取文章、估算预算、长文切分、每个 chunk 开始/结束、compaction 开始/结束、final merge 开始/结束、保存开始/结束、错误。
- `POST /api/ai/summary/{article_id}/stream` 使用 `StreamingResponse` 返回 `text/event-stream`。
- 摘要生成仍复用原同步 agent，但路由使用后台线程 + queue，把事件及时推给前端。
- 数据库仍保存完整 `prompt trace`，但流式 `result` 事件会清空 `prompt` 字段，避免前端最后一帧传输巨大 prompt。

前端实现：

- `frontend/src/api/client.ts` 新增 `streamSummary()`，使用 `fetch` POST body 读取 SSE 文本流。
- `ReaderView.vue` 删除原有 `summaryStepTimer`、`baseSummarySteps()`、`extractSummaryTraceSteps()` 等假进度逻辑。
- `runSummary()` 锁定当前 `articleId`，只有当前文章仍被选中时才接收事件，避免切换文章后上一条流回填到新文章。
- 收到 `result` 事件后展示摘要和 token 用量；收到 `done` 后自动收起过程面板。

更新 `frontend/src/views/StatsView.vue`：

- 统计页继续展示总调用数、输入 token、输出 token。
- 新增按功能统计。
- 新增按 provider + model 统计。

### 6. 用量统计

`ai_results` 表现在记录：

- `provider`
- `model`
- `input_tokens`
- `output_tokens`

`GET /api/stats/llm` 返回：

- `total_articles`
- `total_calls`
- `input_tokens`
- `output_tokens`
- `by_feature`
- `by_provider`

如果 OpenAI-compatible provider 返回 `usage.prompt_tokens` 和 `usage.completion_tokens`，系统直接使用真实用量；如果 provider 没返回 usage，Summary Agent 会做保守 token 估算，保证统计页不为空。

## 实际测试记录

### 单元测试

命令：

```bash
PYTHONPATH=backend /Users/a1234/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s backend/tests
```

结果：

```text
Ran 26 tests
OK
```

新增测试：

- `backend/tests/test_summary_agent.py`
  - 验证 Summary Agent 优先使用清洗后的 Markdown。
  - 验证 OpenAI-compatible 调用、模型名传递和 usage 读取。
  - 验证 agentic workflow prompt、模式 token 上限和 Qwen `<think>` 清洗。
  - 验证 Ollama provider 会携带 `reasoning_effort: "none"`。
  - 验证长文章会触发多轮 chunk summary + final merge，而不是简单截断开头。
  - 验证长文章会发出真实 agent 事件，包括 `chunk_start`、`chunk_done`、`final_start`、`final_done`。
- `backend/tests/test_llm_provider_repository.py`
  - 验证 provider CRUD。
  - 验证默认 provider。
  - 验证摘要结果的 token 用量聚合。

### 前端类型检查

命令：

```bash
cd frontend
./node_modules/.bin/vue-tsc --noEmit --pretty false
```

结果：通过，无类型错误。

### 前端构建

命令：

```bash
cd frontend
npm run build
```

结果：通过。Vite 输出 chunk size warning，但不影响本次功能。

### API 端到端测试

使用本地 OpenAI-compatible 测试服务模拟 vLLM/Qwen3-8B：

- Base URL: `http://127.0.0.1:18000/v1`
- Model: `Qwen/Qwen3-8B`

验证内容：

- 创建 `vllm` provider。
- 创建 `ollama` provider。
- 对文章调用 `POST /api/ai/summary/{article_id}`。
- 检查 `GET /api/stats/llm`。

结果：

- vLLM 类型 provider 调用成功，返回摘要并记录 `123` input tokens / `45` output tokens。
- Ollama 类型 provider 调用成功，返回摘要并记录 `123` input tokens / `45` output tokens。
- 统计接口能按 `summary`、provider、model 聚合。

### Electron 实际软件测试

已打开实际 Electron 应用验证：

1. 使用 `npx electron .` 启动桌面端。
2. Electron 主进程自动启动 FastAPI 后端，实际后端地址为 `http://127.0.0.1:51474`。
3. 确认 preload 注入的 `apiBaseUrl` 生效，前端请求进入 Electron 后端。
4. 在 Electron 应用 AI 设置页中保存 `Local vLLM Qwen3-8B` provider。
5. 通过 Electron 后端实际订阅 RSS：

```text
https://hnrss.org/frontpage
```

结果：

- RSS 源添加成功：`Feed added and synced successfully.`
- 当前 Electron 数据库中有 `21` 篇真实订阅文章。
- 对真实订阅文章调用 Summary Agent 成功。
- 摘要结果成功保存，统计接口返回：

```json
{
  "total_articles": 21,
  "total_calls": 1,
  "input_tokens": 222,
  "output_tokens": 66,
  "by_feature": [
    { "name": "summary", "calls": 1, "tokens": 288 }
  ],
  "by_provider": [
    {
      "provider": "Local vLLM Qwen3-8B",
      "model": "Qwen/Qwen3-8B",
      "calls": 1,
      "input_tokens": 222,
      "output_tokens": 66
    }
  ]
}
```

### Ollama + qwen3:8b 真实本地模型测试

用户补充要求本机必须使用 Ollama 部署 `qwen3:8b` 并完成真实 summary，因此本轮又执行了完整本地模型测试。

模型安装与拉取：

```bash
brew install ollama
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve
ollama pull qwen3:8b
ollama list
```

确认模型已下载：

```text
NAME        ID              SIZE      MODIFIED
qwen3:8b    500a1f067a9f    5.2 GB    14 seconds ago
```

Homebrew formula 版 `ollama 0.30.7` 可以下载模型，但本机第一次推理时报错：

```text
error starting llama-server: llama-server binary not found
```

解决方式：

```bash
brew install --cask ollama-app
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 /Applications/Ollama.app/Contents/Resources/ollama serve
```

原因：当前 Homebrew formula 安装目录中只有 `mlx_metal_v3/libmlxc.dylib`，缺少 GGUF 推理需要的 `llama-server`；官方 App 包含完整运行时。为了不破坏用户现有命令路径，本次测试直接使用 App 内置二进制。

最小模型验证：

```bash
curl http://127.0.0.1:11434/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{
    "model": "qwen3:8b",
    "messages": [
      {"role": "system", "content": "只输出最终答案，不输出思考过程。"},
      {"role": "user", "content": "用中文一句话总结：RSS 阅读器可以订阅文章，并用本地大模型生成摘要。"}
    ],
    "temperature": 0.2,
    "max_tokens": 180,
    "reasoning_effort": "none"
  }'
```

返回：

```text
RSS阅读器可通过订阅文章并利用本地大模型生成摘要来提升阅读效率。
```

RSSReader 端到端测试使用临时数据库，避免污染用户现有 Electron 数据：

```bash
RSSREADER_DB_PATH=/tmp/rssreader-ollama-qwen3.db \
PYTHONPATH=backend \
/Users/a1234/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m uvicorn app.main:app --host 127.0.0.1 --port 18080
```

实际订阅并同步的 RSS：

- `https://hnrss.org/frontpage`
- `https://feeds.bbci.co.uk/news/technology/rss.xml`
- `https://hnrss.org/newest?q=AI`

实际创建的 provider：

```json
{
  "name": "Local Ollama Qwen3 8B",
  "provider_type": "ollama",
  "base_url": "http://127.0.0.1:11434/v1",
  "api_key": "ollama",
  "model": "qwen3:8b",
  "enabled": true,
  "is_default": true
}
```

测试文章：

```text
BBC Technology / Article ID 23
Version of AI tool 'too powerful for public' released to public
```

摘要请求：

```bash
curl -X POST http://127.0.0.1:18080/api/ai/summary/23 \
  -H 'content-type: application/json' \
  -d '{"refresh":true,"mode":"structured","language":"zh","max_words":450}'
```

实际返回摘要片段：

```text
## 一句话概览
Anthropic 的 Claude Mythos 的最新版本 Claude Fable 5 已向公众发布，引发科技、金融和政府领域的关注。

## 关键要点
- Claude Fable 5 是 Anthropic 公司推出的 AI 工具，被认为是“过于强大”而曾被限制公开的版本。
- 该 AI 工具在技术、金融和政府领域引起了广泛讨论，因其潜在能力引发担忧。
- 公众发布后，可能对社会、经济和安全带来深远影响，但具体细节未在文中详述。
- 文章未提供关于 Claude Fable 5 的具体功能、性能数据或用户反馈等详细信息。

可信度：中
```

验收点：

- 使用的是真实本地 Ollama `qwen3:8b`，不是 mock server。
- 结果保存到 `ai_results`。
- `prompt` 中包含 agentic workflow。
- 输出没有泄露 `<think>`。
- 统计记录为 `348` input tokens / `194` output tokens。

统计接口结果：

```json
{
  "total_articles": 61,
  "total_calls": 1,
  "input_tokens": 348,
  "output_tokens": 194,
  "by_feature": [
    { "name": "summary", "calls": 1, "tokens": 542 }
  ],
  "by_provider": [
    {
      "provider": "Local Ollama Qwen3 8B",
      "model": "qwen3:8b",
      "calls": 1,
      "input_tokens": 348,
      "output_tokens": 194
    }
  ]
}
```

### Ollama + qwen3:8b 多轮上下文长文测试

针对“类似 opencode/coding agent 的上下文管理”需求，本轮又补充了长文摘要循环能力，并用真实 Ollama `qwen3:8b` 验证。

实现策略：

- 先估算 `system_prompt + user_prompt` 的 token 是否超过输入预算。
- 未超过预算：直接单轮摘要。
- 超过预算：正文按 token budget 切成多个 chunk，并保留少量 overlap。
- 每个 chunk 先生成事实笔记，重点保留主旨、事实、数字、人名/机构、风险、争议、不确定性。
- 如果所有 chunk 笔记拼接后仍超过最终合并预算，进入一轮或多轮 compaction，压缩中间笔记。
- 最后用压缩后的整篇事实笔记做 final merge，输出用户选择模式的摘要。
- 所有中间调用的 usage 会累加，统计页看到的是整次多轮 agent 的总消耗。

真实验证方式：

- 使用本地 `/Applications/Ollama.app/Contents/Resources/ollama serve`。
- Provider: `Local Ollama Qwen3 8B`
- Model: `qwen3:8b`
- 构造包含三段重复事实的长文，并将 `context_window_tokens` 临时调小到 `1000`，强制触发多轮。

验证结果：

```text
input_tokens 7737
output_tokens 2764
calls_trace_chunks 7
has_final_merge True
```

真实输出片段：

```text
## 一句话概览
RSSReader 的 Summary Agent 通过压缩长文章以适应上下文窗口，生成结构化摘要并评估其可信度。

## 关键要点
- Summary Agent 使用 Ollama 本地模型生成摘要，需配置 provider 支持。
- 压缩机制用于应对上下文窗口限制，可能影响摘要完整性与可信度。
- 摘要目标为结构化输出，包含格式、可信度依据及压缩要素。
- 压缩过程涉及预算控制与内容精简，但具体技术细节未明确。

可信度：中
```

说明：这次验证重点不是文章内容本身，而是确认本地 Qwen3 真实执行了多轮 chunk 摘要和 final merge；`calls_trace_chunks 7` 与 `has_final_merge True` 证明没有只取开头截断。

### Ollama + qwen3:8b 真实事件流测试

本轮针对“不要前端假步骤，要展示和后端的交互逻辑”再次做了真实流式接口验证。

测试环境：

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:5173`
- Provider: `Local Ollama Qwen3 8B`
- Model: `qwen3:8b`
- Base URL: `http://127.0.0.1:11434/v1`

构造本地长文测试文章后，请求：

```bash
curl -N -s -X POST http://127.0.0.1:8000/api/ai/summary/1/stream \
  -H 'Content-Type: application/json' \
  -d '{"provider_id":1,"refresh":true,"mode":"structured","language":"zh","max_words":450}'
```

实际事件顺序片段：

```text
prepare
budget: 文章输入约 15008 tokens，单轮输入预算约 4690 tokens
chunk_plan: 正文约 14657 tokens，已切成 4 个片段
chunk_start 1/4
chunk_done 1/4: 875 input / 227 output
chunk_start 2/4
chunk_done 2/4: 5566 input / 171 output
chunk_start 3/4
chunk_done 3/4: 5623 input / 124 output
chunk_start 4/4
chunk_done 4/4: 1147 input / 132 output
final_start
final_done: final 934 input / 209 output, total 14145 input / 863 output
save_start
save_done
result
done
```

验收结论：

- 前几步快是因为它们是本地读文章、估算 token 和切分文本；这些步骤确实只需毫秒级。
- 真正耗时的地方是模型调用，界面会停在 `提取片段 1/4`、`提取片段 2/4`、`合成最终摘要` 等真实后端事件上。
- 最终摘要成功保存，累计用量 `14145` input tokens / `863` output tokens。
- 缓存路径验证中，流式 `result.prompt` 长度已降为 `0`，避免把完整 prompt trace 推给前端；数据库仍保留 trace 供开发排查。

## 遇到的问题与解决

### 1. 上游仓库地址修正

最初 `GentleCold/RSSReader` 仓库只有文档分支，没有 `develop` 和完整应用代码。后来确认真正上游为：

```text
https://github.com/TheadoraTang/RSSReader
```

解决方式：

- 添加 `upstream` 指向 TheadoraTang/RSSReader。
- 从 `upstream/develop` 切出 `week16-summary-agent` 分支继续开发。

### 2. Python 3.14 本机环境不可用

本机 Homebrew Python 3.14 的 `pyexpat` 动态库报错，导致 `venv` / `pip` 无法正常使用。

解决方式：

- 使用 Codex bundled Python：

```text
/Users/a1234/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

### 3. Electron 依赖安装超时

首次 `npm install` 下载 Electron 二进制时出现 `read ETIMEDOUT`。

解决方式：

```bash
ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ npm install
```

重试后安装成功。

### 4. Electron 数据库路径大小写差异

手工准备测试数据时最初写入：

```text
~/Library/Application Support/RSSReader/app.db
```

但 Electron 实际使用：

```text
~/Library/Application Support/rssreader/app.db
```

解决方式：

- 通过 `GET /api/health` 确认真正数据库路径。
- 后续测试全部使用 Electron 后端 API 或正确数据库路径。

### 5. vLLM 默认端口与 FastAPI 开发端口冲突

FastAPI Web 开发常用 `8000`，vLLM 示例也常用 `8000`。

解决方式：

- 前端 vLLM 模板默认改为 `http://127.0.0.1:8001/v1`。
- 文档说明如无端口冲突也可手动改为 `8000/v1`。

### 6. Ollama Homebrew formula 缺少 llama-server

本机 `brew install ollama` 安装的 formula 版可以启动 HTTP API 和下载模型，但真实调用 `qwen3:8b` 时返回：

```text
error starting llama-server: llama-server binary not found
```

解决方式：

- 安装官方 App cask：`brew install --cask ollama-app`。
- 直接使用 `/Applications/Ollama.app/Contents/Resources/ollama serve` 启动完整运行时。
- RSSReader 的 provider 仍使用标准 OpenAI-compatible 地址 `http://127.0.0.1:11434/v1`，应用代码不需要改特殊路径。

### 7. Qwen3 reasoning 字段兼容

第一次直接调用 Ollama OpenAI-compatible 接口时，Qwen3 将思考过程放到了响应的 `reasoning` 字段，而 `message.content` 为空，导致应用会认为模型返回空摘要。

解决方式：

- Summary Agent 对 `ollama` provider 自动传入 `reasoning_effort: "none"`。
- 同时保留 `<think>...</think>` 清洗，兼容其它 Qwen3/vLLM 输出格式。
- 新增单元测试锁定该行为。

### 8. 长文章不能只截断开头

早期实现为了避免一次请求过大，对正文做 12000 字符截断。这能保证短文可用，但对长文不够像真正的 agent，因为后半篇文章会被丢掉。

解决方式：

- 移除默认截断作为摘要主路径。
- 新增 token 预算估算和 chunk 切分。
- 长文走多轮 context loop：chunk notes -> optional compaction -> final merge。
- 在 `ai_results.prompt` 中保存多轮 trace，便于开发者排查用了多少 chunk、是否进入 final merge。
- 新增回归测试，强制小上下文预算，确认长文至少触发多个模型调用并最终合并。

### 9. 前端假进度会误导用户

人工验收指出：如果前端固定播放“读取上下文、评估预算、提取笔记、合成摘要”等步骤，而真实耗时全部发生在最后一个请求等待上，用户会被误导，不知道后端到底卡在哪里。

解决方式：

- 删除前端固定 `setInterval` 步骤。
- 后端 Summary Agent 在真实执行节点通过 `on_event` 发事件。
- 新增流式 API，把事件实时推到前端。
- 前端只渲染后端事件，不再事后解析 prompt 或本地模拟进度。
- UI 中明确说明“步骤由后端真实事件驱动，耗时停留在哪里就代表当前正在做哪里”。

## 当前限制

- 已在本机通过 Ollama 官方 App 运行真实 `qwen3:8b` 完成摘要测试。
- 已在本机通过真实 `qwen3:8b` 验证多轮长文摘要循环，能够避免只总结文章开头。
- vLLM 路线已完成配置模板和 OpenAI-compatible 链路测试，但未在本机再额外启动 vLLM 加载 ModelScope 权重。
- HN RSS 多数条目正文只有原文链接、评论链接、分数和评论数；Summary Agent 会识别信息不足并降低可信度。真实正文更完整的源建议优先使用 BBC、OpenAI News 等提供摘要或正文的 RSS。
- RAG 问答配置仍沿用原有模块，本次只完成 Summary Agent 相关 provider 和统计。

## 后续建议

- 如果课程演示需要 vLLM 路线，也可以在具备 GPU 或足够内存的机器上运行真实 `Qwen/Qwen3-8B` vLLM 服务，执行同样的摘要测试。
- 后续 Translation Agent 可以复用本次 `llm_providers` 表和 provider 调用逻辑。
- 可增加 provider “测试连接”按钮，保存前检查 `/v1/models` 或执行一次轻量 chat completion。
