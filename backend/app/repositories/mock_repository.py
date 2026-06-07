from copy import deepcopy
from datetime import datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


class MockRepository:
    """In-memory repository used until SQLite tables are created."""

    def __init__(self) -> None:
        created_at = now()
        self.feeds = [
            {
                "id": 1,
                "title": "Open Source Weekly",
                "url": "https://example.com/open-source.xml",
                "site_url": "https://example.com",
                "description": "开源软件治理、社区与工程实践示例订阅源",
                "last_sync_at": created_at,
                "created_at": created_at,
            },
            {
                "id": 2,
                "title": "AI Research Digest",
                "url": "https://example.com/ai.xml",
                "site_url": "https://example.com/ai",
                "description": "大模型、智能体和信息处理的示例订阅源",
                "last_sync_at": created_at,
                "created_at": created_at,
            },
        ]
        self.tags = [
            {"id": 1, "name": "课程项目", "color": "#3b82f6"},
            {"id": 2, "name": "AI", "color": "#8b5cf6"},
            {"id": 3, "name": "工程实践", "color": "#10b981"},
        ]
        self.articles = [
            {
                "id": 1,
                "feed_id": 1,
                "feed_title": "Open Source Weekly",
                "title": "如何设计一个本地优先的 RSS 阅读器",
                "url": "https://example.com/articles/local-first-rss",
                "author": "RSSReader Team",
                "published_at": created_at,
                "summary": "介绍本地优先、订阅同步、内容清洗与导出的基础设计。",
                "raw_html": "<article><h1>本地优先 RSS</h1><p>所有阅读数据保存在本地。</p></article>",
                "cleaned_html": "<h1>本地优先 RSS</h1><p>所有阅读数据保存在本地。</p>",
                "cleaned_markdown": "# 本地优先 RSS\n\n所有阅读数据保存在本地。",
                "is_read": False,
                "is_starred": True,
                "tag_ids": [1, 3],
                "created_at": created_at,
            },
            {
                "id": 2,
                "feed_id": 2,
                "feed_title": "AI Research Digest",
                "title": "用 Summary Agent 提升长文阅读效率",
                "url": "https://example.com/articles/summary-agent",
                "author": "Mercury Notes",
                "published_at": created_at,
                "summary": "摘要智能体可以为长文生成结构化要点，并记录模型用量。",
                "raw_html": "<article><h1>Summary Agent</h1><p>AI 摘要可减少信息过载。</p></article>",
                "cleaned_html": "<h1>Summary Agent</h1><p>AI 摘要可减少信息过载。</p>",
                "cleaned_markdown": "# Summary Agent\n\nAI 摘要可减少信息过载。",
                "is_read": False,
                "is_starred": False,
                "tag_ids": [2],
                "created_at": created_at,
            },
        ]
        self.notes = {
            1: {
                "id": 1,
                "article_id": 1,
                "content_markdown": "- 可以作为数据库设计说明中的案例\n- 后续接 SQLite Repository",
                "updated_at": created_at,
            }
        }
        self.providers = [
            {
                "id": 1,
                "name": "OpenAI Compatible Demo",
                "base_url": "https://api.example.com/v1",
                "api_key": "mock-hidden",
                "model": "gpt-compatible-demo",
                "enabled": True,
            }
        ]
        self.ai_results = []
        self.sync_logs = [
            {"id": 1, "feed_id": 1, "status": "success", "message": "Mock 同步完成，新增 2 篇文章。", "created_at": created_at},
            {"id": 2, "feed_id": None, "status": "pending", "message": "SQLite 持久化接口已预留。", "created_at": created_at},
        ]

    def list_feeds(self):
        return deepcopy(self.feeds)

    def create_feed(self, payload):
        feed = {
            "id": self._next_id(self.feeds),
            "title": payload.title or str(payload.url),
            "url": str(payload.url),
            "site_url": None,
            "description": "Mock feed，后续接入真实 RSS 解析。",
            "last_sync_at": None,
            "created_at": now(),
        }
        self.feeds.append(feed)
        return deepcopy(feed)

    def create_feed_metadata(self, payload):
        feed = self.create_feed(payload)
        self.sync_logs.append(
            {
                "id": self._next_id(self.sync_logs),
                "feed_id": feed["id"],
                "url": feed["url"],
                "feed_title": feed["title"],
                "status": "pending",
                "message": "Imported feed metadata from OPML. Run sync to fetch articles.",
                "created_at": now(),
            }
        )
        return feed

    def update_feed(self, feed_id, payload):
        feed = self._find(self.feeds, feed_id)
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            if value is not None:
                feed[key] = str(value) if key == "url" else value
        return deepcopy(feed)

    def delete_feed(self, feed_id):
        self.feeds = [feed for feed in self.feeds if feed["id"] != feed_id]

    def sync_feed(self, feed_id):
        feed = self._find(self.feeds, feed_id)
        feed["last_sync_at"] = now()
        self.sync_logs.append({"id": self._next_id(self.sync_logs), "feed_id": feed_id, "status": "success", "message": "Mock 同步任务已触发。", "created_at": now()})
        return deepcopy(feed)

    def list_articles(self, feed_id=None, tag_id=None, unread=None, starred=None):
        articles = deepcopy(self.articles)
        if feed_id is not None:
            articles = [item for item in articles if item["feed_id"] == feed_id]
        if tag_id is not None:
            articles = [item for item in articles if tag_id in item["tag_ids"]]
        if unread:
            articles = [item for item in articles if not item["is_read"]]
        if starred:
            articles = [item for item in articles if item["is_starred"]]
        return articles

    def get_article(self, article_id):
        return deepcopy(self._find(self.articles, article_id))

    def set_article_flag(self, article_id, key, value):
        article = self._find(self.articles, article_id)
        article[key] = value
        return deepcopy(article)

    def list_tags(self):
        return deepcopy(self.tags)

    def create_tag(self, payload):
        tag = {"id": self._next_id(self.tags), **payload.model_dump()}
        self.tags.append(tag)
        return deepcopy(tag)

    def update_tag(self, tag_id, payload):
        tag = self._find(self.tags, tag_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                tag[key] = value
        return deepcopy(tag)

    def delete_tag(self, tag_id):
        self.tags = [tag for tag in self.tags if tag["id"] != tag_id]
        for article in self.articles:
            article["tag_ids"] = [item for item in article["tag_ids"] if item != tag_id]

    def set_article_tags(self, article_id, tag_ids):
        article = self._find(self.articles, article_id)
        article["tag_ids"] = tag_ids
        return deepcopy(article)

    def get_note(self, article_id):
        note = self.notes.get(article_id)
        if note:
            return deepcopy(note)
        return {"id": self._next_id(list(self.notes.values())), "article_id": article_id, "content_markdown": "", "updated_at": now()}

    def update_note(self, article_id, payload):
        note = {"id": self.notes.get(article_id, {}).get("id", len(self.notes) + 1), "article_id": article_id, "content_markdown": payload.content_markdown, "updated_at": now()}
        self.notes[article_id] = note
        return deepcopy(note)

    def create_ai_result(self, article_id, result_type, prompt, result):
        item = {
            "id": self._next_id(self.ai_results),
            "article_id": article_id,
            "type": result_type,
            "provider_id": 1,
            "prompt": prompt,
            "result": result,
            "input_tokens": 256,
            "output_tokens": 128,
            "created_at": now(),
        }
        self.ai_results.append(item)
        return deepcopy(item)

    def list_logs(self):
        return deepcopy(self.sync_logs)

    def log_feed_event(self, feed_id, url, status, message):
        feed = next((item for item in self.feeds if item["id"] == feed_id), None)
        self.sync_logs.append(
            {
                "id": self._next_id(self.sync_logs),
                "feed_id": feed_id,
                "url": url,
                "feed_title": feed["title"] if feed else None,
                "status": status,
                "message": message,
                "created_at": now(),
            }
        )

    def stats(self):
        total_input = sum(item["input_tokens"] for item in self.ai_results) or 1024
        total_output = sum(item["output_tokens"] for item in self.ai_results) or 512
        return {
            "total_calls": len(self.ai_results) or 3,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "by_feature": [
                {"name": "summary", "calls": 1, "tokens": 512},
                {"name": "translation", "calls": 1, "tokens": 640},
                {"name": "tag_suggestion", "calls": 1, "tokens": 384},
            ],
        }

    def _find(self, rows, item_id):
        for row in rows:
            if row["id"] == item_id:
                return row
        raise ValueError(f"Item {item_id} not found")

    def _next_id(self, rows):
        return max([row["id"] for row in rows], default=0) + 1


repository = MockRepository()

