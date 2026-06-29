# Week17 张宥 AI Translation 工作记录

## 本周负责范围

- Translation Agent 开发。
- AI 翻译接口实现。
- 阅读页翻译入口接入。
- 翻译用量统计接入。

## 主要实现

### 1. Translation Agent

新增 `backend/app/services/translation_agent.py`：

- 优先读取文章的 `cleaned_markdown`，缺失时回退到 `cleaned_html`、`raw_html`、RSS `summary`。
- 通过现有 `llm_providers` 表读取 OpenAI-compatible Provider 配置。
- 支持 OpenAI-compatible、vLLM、Ollama 等已接入的 provider 类型。
- 对 Ollama provider 自动传入 `reasoning_effort: "none"`，避免 Qwen3 输出空 `content`。
- 默认保留 Markdown 标题、列表、引用和链接结构。
- 支持目标语言与源语言参数，源语言默认自动识别。
- 对长文按 token 预算分段翻译，并累计 token 用量。
- 清理模型输出中的 `<think>...</think>` 和 `最终答案：` 前缀，避免思考过程泄露。

### 2. 后端接口

更新 `POST /api/ai/translate/{article_id}`，请求体如下：

```json
{
  "provider_id": null,
  "refresh": true,
  "target_language": "zh",
  "source_language": "auto",
  "preserve_markdown": true
}
```

字段说明：

- `provider_id`: 可选。为空时使用默认启用的 LLM Provider。
- `refresh`: 为 `false` 时优先返回最近一次 translation 缓存。
- `target_language`: 目标语言代码，支持 `zh/en/ja/ko/fr/de/es/pt/ru/ar` 等。
- `source_language`: 源语言代码，默认 `auto`。
- `preserve_markdown`: 是否尽量保留 Markdown 结构。

响应仍复用 `AIResultRead`：

```json
{
  "id": 1,
  "article_id": 12,
  "type": "translation",
  "provider_id": null,
  "prompt": "...",
  "result": "译文内容",
  "input_tokens": 210,
  "output_tokens": 64,
  "created_at": "2026-06-17T12:00:00"
}
```

### 3. 数据库与统计

本次不新增表结构，继续使用 `ai_results`：

- `task_type = "translation"`
- `provider` / `model` 记录调用来源。
- `input_tokens` / `output_tokens` 记录模型用量。
- 翻译失败时写入 `status = "failed"` 的记录，便于统计异常调用。

因此 `GET /api/stats/llm` 和 `GET /api/stats/llm/timeseries` 会自动包含 translation 用量。

### 4. 前端接入

更新 `frontend/src/api/client.ts`：

- `rssApi.translate(articleId, payload)` 支持传入 provider、目标语言和缓存参数。

更新 `frontend/src/views/ReaderView.vue`：

- 顶部工具栏翻译按钮调用真实翻译接口。
- 复用阅读页底部 AI 抽屉展示翻译结果。
- 翻译目标语言复用抽屉中的语言下拉框。
- Provider 复用当前 AI Provider 选择，未选择时使用后端默认 Provider。
- 翻译运行期间显示加载态，完成后展示 token 用量。
- 复制按钮根据结果类型显示“复制译文”或“复制摘要”。

## 测试

新增 `backend/tests/test_translation_agent.py`：

- 验证优先使用 `cleaned_markdown`。
- 验证 prompt 包含源语言、目标语言和 Markdown 保留指令。
- 验证 OpenAI-compatible client 调用、模型名传递和 usage 读取。
- 验证 Ollama provider 会携带 `reasoning_effort: "none"`。
- 验证长文触发分段翻译并累计 token。
- 验证空正文返回可读错误。

建议验证命令：

```bash
PYTHONPATH=backend python -m unittest backend.tests.test_translation_agent
PYTHONPATH=backend python -m unittest discover -s backend/tests
cd frontend && npm run build
```

## 当前限制

- 翻译接口暂未实现 SSE 事件流，长文翻译期间前端只展示统一加载态。
- 翻译结果暂未覆盖原文正文，只在 AI 抽屉中展示。
- UI 多语言 i18n 的完整页面文本替换尚未展开，本次优先完成文章内容翻译 Agent。

---

## 2026-06-22 追加：逐句对齐 + SSE 事件流 + 对照视图 + i18n

### 本次实现内容

#### 1. 逐句格式保持翻译（核心重构）

**背景**：上一轮实现的段落级翻译无法保证「保持原句子格式、符号、缩进」的需求。

**实现见** `backend/app/services/translation_agent.py`：

- **`parse_blocks(markdown)`** — Markdown 块级解析器，识别 heading / paragraph / list_item / blockquote / code_block / hr / blank 类型，去除前缀 `（# / - / > / 缩进）` 仅保留待翻译内容
- **`split_sentences(content)`** — 句子级切分，保留行内 Markdown 符号；对缩写（U.S.、e.g.）和小数点做了启发式不切分
- **`_pack_aligned_chunks(blocks, token_budget)`** — 在 block 边界内按 token budget 打包句子，不跨 block，overlap=0（翻译局部性强）
- **`_build_aligned_prompt()`** — 用 `|行号|` 前缀锚点要求 LLM 逐行对齐翻译，输出行数必须等于输入行数
- **`_parse_aligned_response()`** — 解析 LLM 的 `|N|` 前缀输出，行数不一致时回退整段翻译
- **`_reassemble_translation()`** — 将译文句按原 block prefix 回填，code_block/hr/blank 原样保留
- **`_translate_aligned()`** — 主流程：parse → split → pack → translate → reassemble → 对齐校验
- **对齐失败回退**：行数不一致时使用段落级翻译（fallback），不阻断流程
- **`aligned_blocks`**：返回结构化 `[{type, original, translated}]` 供前端对照视图

#### 2. SSE 事件流

**新增** `POST /api/ai/translate/{article_id}/stream`：

- 照搬 `summarize_stream` 的 `queue.Queue` + `threading.Thread` + `StreamingResponse` 架构
- 事件序列：`prepare` → `parse` → `budget` → [`chunk_plan` → `chunk_start` → `chunk_done` → `align_check`] → `save_start` → `result` → `save_done` → `done`/`error`
- 前端 `rssApi.streamTranslate()` 复用 `streamSse` 泛型函数
- `ReaderView.vue.runTranslate()` 改为流式调用，复用 `handleSummaryStreamEvent` 步骤流渲染

#### 3. 译文/原文对照视图

- 正文区新增「原文/译文/对照」三态切换（`readerViewMode` ref）
- `readerViewMode='translation'`：将译文通过 `markdownToHtml()` 渲染到正文区
- `readerViewMode='comparison'`：左右分栏渲染 `aligned_blocks[{original, translated}]`，逐块对照
- `aligned_blocks` 通过 SSE `result` 事件返回（不持久化数据库，附在响应 dict 中）
- 切换文章时自动重置为原文模式

#### 4. UI i18n 国际化（阅读页 AI 文案）

- 新增 `frontend/src/i18n/locales/{zh,en}.ts`，覆盖阅读页 AI 相关文案 key
- `i18n/index.ts` 加载语言包，通过 `localStorage.getItem('ui-language')` 持久化语言选择
- 界面语言与 AI 输出语言解耦（语言下拉只控制 AI 输出目标语言）
- 本次范围限定阅读页 AI 文案（全站 i18n 留待后续）

#### 5. 请求校验与缓存优化

- `TranslationRequest.target_language` 添加 `Field(pattern=r"^(zh|en|ja|ko|fr|de|es|pt|ru|ar)$")` 校验
- `ai_service.translate()` 缓存检查时通过解析 `prompt` 提取目标语言，语言不匹配时不命中缓存

### 新增/修改文件清单

| 文件 | 变更 |
|------|------|
| `backend/app/services/translation_agent.py` | 重构：Block-Sentence-Aligned 翻译引擎 + SSE 事件 |
| `backend/app/services/ai_service.py` | 新增 `on_event` 透传 + `aligned_blocks` 返回 + 缓存语言校验 |
| `backend/app/routers/ai.py` | 新增 `POST /ai/translate/{article_id}/stream` |
| `backend/app/schemas/rss.py` | `target_language` 正则校验 |
| `backend/tests/test_translation_agent.py` | 扩展 27 个测试（块解析/句子切分/对齐/回退/前缀保留） |
| `backend/tests/test_translation_stream.py` | 新增 5 个 SSE 事件流测试 |
| `frontend/src/api/client.ts` | 新增 `streamTranslate` + `AIResult.aligned_blocks` |
| `frontend/src/views/ReaderView.vue` | 流式翻译 + 三步切换 + 对照视图 + i18n 文案 |
| `frontend/src/i18n/index.ts` | 加载语言资源文件 |
| `frontend/src/i18n/locales/zh.ts` | 新增中文 AI 文案 |
| `frontend/src/i18n/locales/en.ts` | 新增英文 AI 文案 |
| `update_docs/Week17_sdfhjisd.md` | 本次追加日志 |

### 当前限制

- 译文 `aligned_blocks` 未持久化到数据库（只在 SSE `result` 事件返回），刷新页面后需重新翻译才能对照
- SSE 事件流翻译尚未实现 cancel（中途取消翻译线程）
- 全站 i18n 文本替换未展开（只覆盖了阅读页 AI 文案）
- `summaryEventTitle` 函数仍为硬编码中文（作为 SSE 事件 title 字段的 fallback）
- 桌面端 Electron 导出翻译结果尚未集成

### 建议验证命令

```bash
PYTHONPATH=backend python -m unittest backend.tests.test_translation_agent
PYTHONPATH=backend python -m unittest backend.tests.test_translation_stream
cd frontend && npm run build
```

---

## 2026-06-22 代码审查与缺陷修复（Claude 复审 deepseek 实现）

对 deepseek 完成的代码做深度审查，发现并修复 7 类缺陷，新增 7 个回归测试（后端测试总数 39 个）。

### 已修复缺陷

| # | 严重度 | 缺陷 | 修复 |
|---|--------|------|------|
| 1 | **高（崩溃）** | 纯 code_block 文章 → `aligned_chunks[0]` IndexError，被包装成「Provider 调用失败」 | 空 chunks 时原样返回原文，usage=0 |
| 2 | 高 | `_parse_aligned_response` 70% 阈值返回含空字符串列表 → 译文出现空行 | 只接受全非空对齐，否则 None 触发回退 |
| 3 | 中 | 多 chunk 分支 `fallback_completion` 作用域风险，`_complete_chat` 异常时 NameError | 抽取 `chunk_usage` 统一变量 |
| 4 | 中 | 句子切分：句末 `.` 无空格时漏切；小数末尾句号误切 | 新增 `_is_decimal_period`，重写边界规则 |
| 5 | **高（逻辑错误）** | 缓存语言提取用显示名 vs 请求代码比较，`English==en` 永不相等，**语言过滤从未生效**；失败记录被当译文缓存 | 新增显示名→代码反向映射；排除 `status=failed` 记录 |
| 6 | 低 | 死代码：`import json/field`、`_SENTENCE_BOUNDARY`、`min_sentences_for_aligned`、`_build_aligned_blocks_data` 空循环、`_emit` 内 `import time` | 全部移除 |
| 7 | 中 | 前端 `runSummary` 未重置 `readerViewMode`/`alignedBlocks` → 翻译后切摘要正文区仍显示对照视图；对照视图窄屏溢出 | `runSummary` 重置两状态；CSS 加 `@media(max-width:720px)` 堆叠布局 + `overflow-wrap` |

### 当前剩余限制与优化方案

#### 限制 1：`aligned_blocks` 未持久化，刷新后需重新翻译才能对照 ✅ 已优化（2026-06-22）

**现状**：`aligned_blocks` 只通过 SSE `result` 事件返回，不写入数据库。刷新页面或重新进入文章后，对照视图无数据。

**已采用方案 A**：在 `ai_results.prompt` 字段前缀嵌入 `aligned_blocks` JSON（`---aligned_blocks---\n{json}\n---aligned_blocks-end---\n<prompt trace>`）。
- 写入：`_encode_prompt_with_aligned()` 在 `ai_service.translate()` 保存前编码进 prompt。
- 读取：缓存命中时 `extract_aligned_blocks_from_prompt()` 解析前缀还原 `aligned_blocks`，附到响应 dict 返回前端。
- 优势：**不改表结构**，兼容现有 stats 聚合（stats 查询不读 prompt 内容）。
- 代价：prompt 字段语义混杂，但 `_strip_aligned_blocks_marker()` 可剥离前缀用于调试展示。
- 回归测试：`AlignedBlocksPersistenceTest` 4 个用例（roundtrip / None / 空 prompt / 损坏 JSON）。

#### 限制 2：SSE 翻译未实现 cancel（中途取消）✅ 已优化（2026-06-22）

**现状**：用户切走文章或关闭抽屉时，后端线程仍继续调用 LLM，浪费 token。

**已实现方案**：`request.is_disconnected()` + `threading.Event` + 前端 `AbortController`。
- 后端：新增 `CancelEvent`（`threading.Event` 封装），`translate_with_provider` 在每次 `_complete_chat` 前调 `_check_cancel()`，置位则抛 `TranslationCancelled`。路由 `translate_stream` 的 `event_stream` 生成器每次 yield 前检测 `request.is_disconnected()`，断开则 `cancel_event.set()`。worker 捕获 `TranslationCancelled` 发 `cancelled` 事件（非 error）。
- 前端：`streamSse` 接受可选 `AbortSignal`；`runTranslate` 创建 `AbortController`，切文章（`clearSummaryResult`）或重新翻译时 `abort()`，同时传 `signal` 给 fetch。`handleSummaryStreamEvent` 新增 `cancelled` 事件分支（markSummaryStepsDone，不显示失败）。`catch` 里区分 `AbortError`（主动取消，静默）与真实错误（显示失败）。
- 优势：无需新端点，客户端断开自动触发后端 abort，token 不再浪费。
- 回归测试：`CancellationTest` 3 个用例（预设取消 / chunk 间取消 / 无 cancel_event 正常工作）。

#### 限制 3：全站 i18n 未完成（只覆盖阅读页 AI 文案）

**现状**：`zh.ts`/`en.ts` 只有 `reader.ai.*` 命名空间，其它页面（订阅管理、设置、统计）仍硬编码中文。

**优化方案**：
- 按「优先级页面」渐进抽取：阅读页全文 → 设置页 → 订阅管理 → 统计页。
- 每个页面建独立命名空间（`settings.*`/`feeds.*`/`stats.*`），避免单文件过大。
- `summaryEventTitle` 等 fallback 文案也纳入 i18n。
- 工作量大，建议拆成独立 Week 任务，不塞进 Week17。

#### 限制 4：`summaryEventTitle` 仍硬编码中文

**现状**：SSE 事件 title 字段的 fallback 映射是中文 Record，非 i18n。

**优化方案**：把 `summaryEventTitle`/`summaryEventDetail` 改为 `t('reader.ai.event.chunk_start')` 等 key 查找。代价：需要补全所有事件类型的 locale key。本次未做因为事件 title 主要由后端发送（已是中文），前端 fallback 只在后端未发 title 时用。

#### 限制 5：`_estimate_tokens` 粗估偏差

**现状**：中文 1 char≈1 token、英文 4 char≈1 token，混合内容偏差大。仅用于切分决策，不影响最终质量，但可能导致切分不均。

**优化方案**：
- 接入 `tiktoken`（OpenAI 模型）精确计数，但增加依赖且对非 OpenAI 模型不准。
- 或按 provider 类型选不同估计系数（中文模型 vs 英文模型）。
- **推荐**：保持现状，仅在出现「切分导致单 chunk 过大被 provider 拒绝」时再优化。低优先级。

#### 限制 6：桌面端 Electron 导出翻译结果未集成

**现状**：翻译结果只能在阅读页查看/复制，不能导出为 Markdown。

**优化方案**：复用现有 `POST /api/export/articles/{id}/markdown` 链路，新增「包含译文」选项，后端导出时把 `ai_results(task_type=translation)` 的 result 拼入。前端导出菜单加复选框。改动中等，建议作为 Week17 收尾的可选任务。

### 验证

- 后端：`PYTHONPATH=backend python -m unittest backend.tests.test_translation_agent backend.tests.test_translation_stream` → 39 个测试通过
- 前端：`cd frontend && npm run build` → 通过
- 手动回归：纯 code_block 文章不再崩溃；翻译后切摘要正文区正确切回原文；窄屏对照视图上下堆叠


---

## 2026-06-24 PR Review 修复：翻译专用模型与统计保留

### 背景

PR review 反馈：

1. 翻译功能在 reviewer 环境无法使用，原因之一是翻译复用了摘要/标签/RAG 的通用默认 Provider，模型不一定适合翻译或未正确配置。
2. 翻译模型应单独配置，前端 AI 设置页需要增加翻译模型选择栏，后端翻译调用走该配置。
3. GitHub Issue #44：清空 feed 后，token 统计和日志统计会一起清空；重新添加 feed 后日志恢复，token 统计清零无法恢复。

### 本次修复

- `llm_providers` 新增 `is_translation_default` 字段，用于标记翻译专用 Provider。
- AI 设置页新增「翻译模型」选择栏，可在已有 Provider 列表中单独选择翻译默认模型；Provider 表格新增「翻译默认」状态与「翻译」操作。
- 后端 `ai_service.translate()` 与 `translate_segment()` 在未显式传 `provider_id` 时，改为读取 `repository.get_translation_llm_provider()`，不再复用通用默认 Provider。
- 阅读页段落翻译不再传摘要 Provider ID，让后端统一使用翻译专用配置。
- 新增 `ai_usage_logs` 独立用量流水表，`create_ai_result()` 写入结果表时同步写入该表；统计接口改读 `ai_usage_logs`，避免 `ai_results` 随文章被级联删除后 token 统计丢失。
- 数据库迁移会为旧库自动补 `is_translation_default`、创建 `ai_usage_logs`，并回填历史 `ai_results` 用量；若已有通用默认 Provider 且未设置翻译默认，会自动把该 Provider 作为初始翻译默认，减少升级后不可用风险。

### 接口/数据表变更

- `GET /api/ai/providers` 响应新增：`is_translation_default: boolean`。
- `POST /api/ai/providers` / `PUT /api/ai/providers/{provider_id}` 支持 `is_translation_default`。
- 新增表 `ai_usage_logs`：字段包括 `source_result_id`、`entry_id`、`task_type`、`status`、`provider`、`model`、`input_tokens`、`output_tokens`、`created_at`。
- `GET /api/stats/llm` 与 `/api/stats/llm/timeseries` 改为基于 `ai_usage_logs` 聚合。

### 建议验证命令

```bash
PYTHONPATH=backend python -m unittest backend.tests.test_llm_provider_repository backend.tests.test_translation_agent backend.tests.test_translation_stream
cd frontend && npm run build
```


### 2026-06-24 追加：翻译不可用问题的兼容性修复

- 后端 `get_translation_llm_provider()` 增加兜底：优先使用 `is_translation_default=1` 的启用 Provider；若未配置翻译默认模型，则回退到通用默认 Provider，避免旧数据库或同学本地未单独设置翻译模型时直接不可用。
- 阅读页顶部「翻译全文」改为遍历实际渲染用的 `articleRenderedBlocks`，保证翻译块索引和正文展示块一致。
- HTML-only 文章增加正文纯文本提取：没有 `cleaned_markdown` 时不再只依赖 RSS summary，减少“页面有正文但提示无可翻译段落”的情况。
- 段落翻译请求继续不传摘要 Provider ID，由后端统一选择翻译专用/兜底 Provider。
- 新增回归测试：`test_translation_provider_falls_back_to_default_provider` 覆盖未设置翻译默认时使用通用默认 Qwen/Ollama Provider。


### 2026-06-24 追加：SOCKS 代理依赖修复

- 翻译调用国外 OpenAI-compatible Provider 时，如果系统启用了 SOCKS 代理，`httpx` 需要 `socksio` 支持，否则会报：`Using SOCKS proxy, but the 'socksio' package is not installed`。
- 已在当前 `.venv` 安装 `socksio==1.0.0`，并写入 `backend/requirements.txt`，同学同步后执行 `pip install -r backend/requirements.txt` 即可。
- 保留系统代理能力，不禁用代理；本地/国外模型都按当前环境代理设置访问。


### 2026-06-24 追加：翻译 Provider 独立卡片调整

- 前端 AI 设置页将「翻译模型配置」从 AI Provider 卡片中拆出，移动到 RAG 问答配置卡片下方，作为独立 panel 展示。
- 独立卡片保留 Provider 下拉选择；未显式设置翻译 Provider 时展示后端实际回退的默认 AI Provider，并在下拉中标注「回退默认」。
- AI Provider 表格仍保留「翻译」快捷操作，便于直接把某个 Provider 设为翻译默认。
- 验证：`npm run build --prefix frontend` 通过。


### 2026-06-24 追加：翻译 Provider 独立存储

- 新增 `translation_providers` 表，翻译模型配置不再直接调用通用 `llm_providers` 中的模型。
- 新增后端接口：
  - `GET /api/ai/translation-providers`
  - `POST /api/ai/translation-providers`
  - `PUT /api/ai/translation-providers/{provider_id}`
  - `DELETE /api/ai/translation-providers/{provider_id}`
- 迁移策略：若旧库存在 `llm_providers.is_translation_default=1` 的 Provider，会复制一条到 `translation_providers`；否则复制通用默认 Provider 作为初始翻译 Provider，避免升级后不可用。
- 前端「翻译模型配置」卡片改为独立 CRUD 表单和列表，默认模板新增 Tencent Hy-MT2：`base_url=https://tokenhub.tencentmaas.com/v1`、`model=hy-mt2-pro`。
- 后端 `ai_service.translate()` 和 `translate_segment()` 现在只读取 `translation_providers` 的默认启用 Provider。


### 2026-06-24 追加：点击译文标签恢复原文

- 阅读页段落翻译后的「译文」标签改为可点击按钮，点击后清除该段译文状态并恢复原文显示。
- 对照模式中的「译文」标签也支持同样操作，便于从双语对照快速回到原文。
- 验证：`npm run build --prefix frontend` 通过。

### 2026-06-24 追加：PR 前全量验证与回归修复

- 修复 RAG 向量库连接泄漏：`_vec_conn()` 改为上下文管理器，确保 sqlite-vec 连接在 Windows 下及时关闭，避免全量测试清理临时数据库时报 `WinError 32` 文件占用。
- 修复指定翻译 Provider 时仍查询通用 `llm_providers` 的问题：`ai_service.translate()` 与 `translate_segment()` 的显式 `provider_id` 现在读取 `translation_providers`，确保翻译配置完全独立于通用 AI Provider。
- 新增 `test_ai_service_translation_provider.py` 回归测试，覆盖全文翻译和段落翻译都不会回退查通用 Provider。
- 验证：后端全量 `pytest backend/tests` 共 90 项通过；前端 `npm run build --prefix frontend` 通过，仅保留既有 Rollup 大 chunk / pure annotation 警告。
