import axios from 'axios'

const desktopApiBaseUrl = window.rssReaderDesktop?.apiBaseUrl

export const api = axios.create({
  baseURL: desktopApiBaseUrl ? `${desktopApiBaseUrl}/api` : '/api',
  timeout: 10000
})

export interface Feed {
  id: number
  title: string
  url: string
  site_url?: string
  description?: string
  last_sync_at?: string
  created_at: string
}

export interface Article {
  id: number
  feed_id: number
  feed_title: string
  title: string
  url: string
  author?: string
  published_at?: string
  summary?: string
  raw_html?: string
  cleaned_html?: string
  cleaned_markdown?: string
  is_read: boolean
  is_starred: boolean
  tag_ids: number[]
  created_at: string
}

export interface Tag {
  id: number
  name: string
  color: string
}

export interface Note {
  id: number
  article_id: number
  content_markdown: string
  updated_at: string
}

export interface AIResult {
  id: number
  article_id: number
  type: string
  result: string
  input_tokens: number
  output_tokens: number
  created_at: string
}

export interface OperationResult {
  ok: boolean
  message: string
}

export interface FeedSyncItem {
  feed_id?: number
  url?: string
  title?: string
  status: 'success' | 'failed' | 'skipped'
  message: string
  feed?: Feed
}

export interface FeedSyncReport {
  total: number
  success: number
  failed: number
  skipped: number
  results: FeedSyncItem[]
}

export interface OPMLImportItem {
  url: string
  title?: string
  status: 'imported' | 'skipped' | 'failed'
  message: string
  feed?: Feed
}

export interface OPMLImportReport {
  total: number
  imported: number
  skipped: number
  failed: number
  results: OPMLImportItem[]
}

export interface BatchDigestExportRequest {
  article_ids: number[]
  include_summary: boolean
  include_note: boolean
}

export interface BatchDigestExportResponse {
  digest_title: string
  filename: string
  markdown: string
  summary_available_count: number
  exported_article_ids: number[]
  skipped_article_ids: number[]
}

export const rssApi = {
  feeds: () => api.get<Feed[]>('/feeds').then((res) => res.data),
  createFeed: (payload: { title?: string; url: string }) => api.post<Feed>('/feeds', payload).then((res) => res.data),
  deleteFeed: (id: number) => api.delete<OperationResult>(`/feeds/${id}`).then((res) => res.data),
  syncFeed: (id: number) => api.post<Feed>(`/feeds/${id}/sync`).then((res) => res.data),
  syncAll: () => api.post<FeedSyncReport>('/feeds/sync-all').then((res) => res.data),
  importOpml: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<OPMLImportReport>('/opml/import', formData).then((res) => res.data)
  },
  exportOpml: () => api.get<Blob>('/opml/export', { responseType: 'blob' }).then((res) => res.data),
  articles: (params?: Record<string, unknown>) => api.get<Article[]>('/articles', { params }).then((res) => res.data),
  article: (id: number) => api.get<Article>(`/articles/${id}`).then((res) => res.data),
  refreshArticleContent: (id: number) => api.post<Article>(`/articles/${id}/refresh-content`).then((res) => res.data),
  markRead: (id: number, is_read: boolean) => api.patch<Article>(`/articles/${id}/read`, null, { params: { is_read } }).then((res) => res.data),
  markStarred: (id: number, is_starred: boolean) => api.patch<Article>(`/articles/${id}/star`, null, { params: { is_starred } }).then((res) => res.data),
  tags: () => api.get<Tag[]>('/tags').then((res) => res.data),
  createTag: (payload: { name: string; color: string }) => api.post<Tag>('/tags', payload).then((res) => res.data),
  setArticleTags: (articleId: number, tagIds: number[]) =>
    api.post<{ article_id: number; tag_ids: number[] }>(`/articles/${articleId}/tags`, tagIds).then((res) => res.data),
  note: (articleId: number) => api.get<Note>(`/articles/${articleId}/note`).then((res) => res.data),
  saveNote: (articleId: number, content_markdown: string) => api.put<Note>(`/articles/${articleId}/note`, { content_markdown }).then((res) => res.data),
  exportArticleMarkdown: (articleId: number) =>
    api.get<Blob>(`/export/articles/${articleId}/markdown`, { responseType: 'blob' }).then((res) => res.data),
  exportBatchDigestMarkdown: (payload: BatchDigestExportRequest) =>
    api.post<BatchDigestExportResponse>('/export/digests/markdown', payload).then((res) => res.data),
  summary: (articleId: number) => api.post<AIResult>(`/ai/summary/${articleId}`).then((res) => res.data),
  translate: (articleId: number) => api.post<AIResult>(`/ai/translate/${articleId}`).then((res) => res.data),
  suggestTags: (articleId: number) => api.post<AIResult>(`/ai/tag-suggest/${articleId}`).then((res) => res.data),
  llmStats: () => api.get('/stats/llm').then((res) => res.data),
  syncLogs: () => api.get('/logs/sync').then((res) => res.data)
}
