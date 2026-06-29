# 数据库设计

当前阶段暂不创建 SQLite 数据库和表，后端使用 Mock Repository。数据库接口已在 Repository 层预留。

## 计划表结构

## feeds

- `id`: 主键
- `title`: 订阅源标题
- `url`: RSS URL
- `site_url`: 站点 URL
- `description`: 描述
- `last_sync_at`: 最后同步时间
- `created_at`: 创建时间

## articles

- `id`: 主键
- `feed_id`: 所属订阅源
- `title`: 文章标题
- `url`: 文章链接
- `author`: 作者
- `published_at`: 发布时间
- `summary`: 摘要
- `raw_html`: 原始 HTML
- `cleaned_html`: 清洗后的 HTML
- `cleaned_markdown`: 清洗后的 Markdown
- `is_read`: 是否已读
- `is_starred`: 是否收藏
- `created_at`: 创建时间

## tags

- `id`: 主键
- `name`: 标签名
- `color`: 标签颜色

## article_tags

- `article_id`: 文章 ID
- `tag_id`: 标签 ID

## notes

- `id`: 主键
- `article_id`: 文章 ID
- `content_markdown`: Markdown 笔记
- `updated_at`: 更新时间

## llm_providers

- `id`: 主键
- `name`: Provider 名称
- `base_url`: OpenAI-compatible Base URL
- `api_key`: API Key
- `model`: 模型名称
- `enabled`: 是否启用

## ai_results

- `id`: 主键
- `article_id`: 文章 ID
- `type`: summary / translation / tag_suggestion
- `provider_id`: Provider ID
- `prompt`: 提示词
- `result`: 结果
- `input_tokens`: 输入 Token
- `output_tokens`: 输出 Token
- `created_at`: 创建时间

## sync_logs

- `id`: 主键
- `feed_id`: Feed ID
- `status`: success / failed / pending
- `message`: 日志消息
- `created_at`: 创建时间

## 后续接入方式

1. 在 `backend/app/database.py` 中添加 SQLAlchemy engine 和 session。
2. 在 `backend/app/models/` 中实现 SQLAlchemy Model。
3. 新建 SQLAlchemy Repository。
4. 将 Service 依赖从 Mock Repository 切换到 SQLAlchemy Repository。
5. 保持 Router 和前端 API 路径不变。

