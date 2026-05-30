from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class OperationResult(BaseModel):
    ok: bool = True
    message: str


class FeedCreate(BaseModel):
    title: str | None = None
    url: HttpUrl


class FeedUpdate(BaseModel):
    title: str | None = None
    url: HttpUrl | None = None
    description: str | None = None


class FeedRead(BaseModel):
    id: int
    title: str
    url: str
    site_url: str | None = None
    description: str | None = None
    last_sync_at: datetime | None = None
    created_at: datetime


class ArticleRead(BaseModel):
    id: int
    feed_id: int
    feed_title: str
    title: str
    url: str
    author: str | None = None
    published_at: datetime | None = None
    summary: str | None = None
    raw_html: str | None = None
    cleaned_html: str | None = None
    cleaned_markdown: str | None = None
    is_read: bool = False
    is_starred: bool = False
    tag_ids: list[int] = Field(default_factory=list)
    created_at: datetime


class TagCreate(BaseModel):
    name: str
    color: str = "#409eff"


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagRead(BaseModel):
    id: int
    name: str
    color: str


class NoteUpdate(BaseModel):
    content_markdown: str


class NoteRead(BaseModel):
    id: int
    article_id: int
    content_markdown: str
    updated_at: datetime


class LLMProviderCreate(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str
    enabled: bool = True


class LLMProviderRead(BaseModel):
    id: int
    name: str
    base_url: str
    model: str
    enabled: bool


class AIResultRead(BaseModel):
    id: int
    article_id: int
    type: Literal["summary", "translation", "tag_suggestion"]
    provider_id: int | None = None
    prompt: str
    result: str
    input_tokens: int
    output_tokens: int
    created_at: datetime


class SyncLogRead(BaseModel):
    id: int
    feed_id: int | None = None
    status: Literal["success", "failed", "pending"]
    message: str
    created_at: datetime


class ExportRequest(BaseModel):
    article_ids: list[int]


class BatchDigestExportRequest(BaseModel):
    article_ids: list[int] = Field(min_length=1)
    include_summary: bool = False
    include_note: bool = False


class BatchDigestExportResponse(BaseModel):
    digest_title: str
    filename: str
    markdown: str
    summary_available_count: int = 0
    exported_article_ids: list[int] = Field(default_factory=list)
    skipped_article_ids: list[int] = Field(default_factory=list)
