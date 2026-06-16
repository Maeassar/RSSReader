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

## Stats and Logs

- `GET /api/stats/llm`
- `GET /api/logs/sync`
