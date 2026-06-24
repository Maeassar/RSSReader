# API 设计

后端 API 基础路径为 `/api`，FastAPI 文档地址为 `/docs`。

## Feed

- `GET /api/feeds`
- `POST /api/feeds`
- `PUT /api/feeds/{id}`
- `DELETE /api/feeds/{id}`
- `POST /api/feeds/{id}/sync`
- `POST /api/feeds/sync-all`

## Article

- `GET /api/articles`
- `GET /api/articles/{id}`
- `PATCH /api/articles/{id}/read`
- `PATCH /api/articles/{id}/star`

## OPML

- `POST /api/opml/import`
- `GET /api/opml/export`

## Tag

- `GET /api/tags`
- `POST /api/tags`
- `PUT /api/tags/{id}`
- `DELETE /api/tags/{id}`
- `POST /api/articles/{id}/tags`

## Note and Export

- `GET /api/articles/{id}/note`
- `PUT /api/articles/{id}/note`
- `GET /api/export/articles/{id}/markdown`
- `POST /api/export/articles/markdown`
- `POST /api/export/digests/markdown`

### `POST /api/export/digests/markdown`

批量生成 digest Markdown 预览内容，供 Web 下载或 Electron 保存对话框使用。

请求体示例：

```json
{
  "article_ids": [12, 8, 3],
  "include_summary": true,
  "include_note": true,
  "include_full_text": false
}
```

响应体示例：

```json
{
  "digest_title": "Digest 26-05-30",
  "filename": "2026-05-30-digest.md",
  "markdown": "+++\ndate = '2026-05-30T21:30:00+08:00'\n...",
  "exported_article_ids": [12, 8],
  "skipped_article_ids": [3]
}
```

行为说明：

- 导出顺序以 `article_ids` 提供的顺序为准
- `include_summary=true` 时，仅取最新一条 AI 摘要结果
- `include_full_text=true` 时，导出文章清洗后的 Markdown 正文；若正文缺失，则回退到文章摘要
- 缺少标题或链接的文章会被跳过，并写入 `skipped_article_ids`

## AI

- `POST /api/ai/summary/{article_id}`
- `POST /api/ai/translate/{article_id}`
- `POST /api/ai/tag-suggest/{article_id}`

### `POST /api/ai/tag-suggest/{article_id}`

Uses the default enabled LLM Provider from AI settings to generate tag candidates for one article. Fewer than 5 usable candidates are allowed, and more than 8 candidates are truncated to the first 8. The endpoint only creates an `ai_results` audit row; it does not create tags or assign tags to the article. The frontend must call `POST /api/tags` and `POST /api/articles/{id}/tags` after the user confirms which candidates to keep.

Response example:

```json
{
  "article_id": 12,
  "candidates": [
    { "name": "AI", "tag_id": 2, "reason": "Existing tag that matches the article topic." },
    { "name": "Local Models", "tag_id": null, "reason": "New reusable topic suggested from the article." }
  ],
  "ai_result": {
    "id": 31,
    "article_id": 12,
    "type": "tag_suggestion",
    "provider_id": null,
    "prompt": "...",
    "result": "{\"candidates\":[...]}",
    "input_tokens": 640,
    "output_tokens": 90,
    "created_at": "2026-06-16T12:00:00"
  }
}
```

### `POST /api/ai/translate/{article_id}`

使用已配置的 LLM Provider 翻译文章正文。为空时使用默认启用的
Provider，结果写入 `ai_results`，`task_type` 为 `translation`。

请求体示例：

```json
{
  "provider_id": null,
  "refresh": true,
  "target_language": "zh",
  "source_language": "auto",
  "preserve_markdown": true
}
```

响应体示例：

```json
{
  "id": 18,
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

行为说明：

- `refresh=false` 时优先返回最近一次翻译缓存（且目标语言匹配时命中）
- `target_language` 支持 `zh/en/ja/ko/fr/de/es/pt/ru/ar` 等语言代码，后端按正则校验
- `preserve_markdown=true` 时尽量保留标题、列表、引用和链接结构，并逐句对齐
- 失败调用会写入 `status=failed` 的 `ai_results` 记录，供统计页展示异常请求

### `POST /api/ai/translate/{article_id}/stream`

SSE 流式翻译端点，事件序列与 `summarize_stream` 对齐：

| 事件类型 | 标题示例 | 说明 |
|---------|---------|------|
| `prepare` | 读取文章上下文 | 已整理标题、源正文与翻译参数 |
| `parse` | 解析文章结构 | 识别到 N 个块、M 个句子 |
| `budget` | 评估上下文预算 | 输入约 X tokens，预算 Y tokens |
| `chunk_plan` | 切分翻译片段 | 长文分段时发出 |
| `chunk_start` | 翻译片段 i/N | 每个 chunk 开始 |
| `chunk_done` | 片段 i/N 完成 | 每个 chunk 完成，含 usage |
| `align_check` | 对齐校验 | 译文行数与原文一致/回退 |
| `save_start` | 保存翻译结果 | 写入 ai_results |
| `result` | 翻译已生成 | 返回译文与用量（prompt 置空） |
| `save_done` | 翻译结果已保存 | 累计用量 |
| `done`/`error` | 完成/失败 | 流结束 |

请求体同 `POST /api/ai/translate/{article_id}`。

## Stats and Logs

- `GET /api/stats/llm`
- `GET /api/logs/sync`
