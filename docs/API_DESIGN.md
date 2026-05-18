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

## AI

- `POST /api/ai/summary/{article_id}`
- `POST /api/ai/translate/{article_id}`
- `POST /api/ai/tag-suggest/{article_id}`

## Stats and Logs

- `GET /api/stats/llm`
- `GET /api/logs/sync`

