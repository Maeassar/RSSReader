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

export interface SearchResult {
  id: number
  feed_id: number
  feed_title: string
  title: string
  url: string
  author?: string
  published_at?: string
  is_read: boolean
  is_starred: boolean
  title_snippet?: string
  summary_snippet?: string
  content_snippet?: string
}

export interface RagConfig {
  siliconflow_api_key: string
  siliconflow_base_url: string
  embedding_model: string
  deepseek_api_key: string
  deepseek_base_url: string
  deepseek_model: string
}

export interface AskSource {
  id: number
  title: string
  url: string
  feed_title: string
  published_at?: string
  snippet?: string
}

export interface AskResponse {
  answer: string
  sources: AskSource[]
}

export interface FeedSyncItem {
  feed_id?: number
  url?: string
  title?: string
  status: 'success' | 'failed' | 'skipped'
  message: string
  feed?: Feed | null
}

export interface FeedSyncReport {
  total: number
  success: number
  failed: number
  skipped: number
  results: FeedSyncItem[]
}

export interface OPMLImportItem {
  url?: string | null
  title?: string
  status: 'imported' | 'skipped' | 'failed'
  message: string
  feed?: Feed | null
  source_file?: string
}

export interface OPMLImportReport {
  files: number
  total: number
  imported: number
  skipped: number
  failed: number
  results: OPMLImportItem[]
}

export interface SyncLog {
  id: number
  feed_id?: number | null
  url?: string | null
  feed_title?: string | null
  status: 'success' | 'failed' | 'pending'
  message: string
  created_at: string
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
  createFeed: (payload: { title?: string; url: string }) => api.post<Feed>('/feeds', payload, { timeout: 60000 }).then((res) => res.data),
  deleteFeed: (id: number) => api.delete<OperationResult>(`/feeds/${id}`).then((res) => res.data),
  syncFeed: (id: number) => api.post<Feed>(`/feeds/${id}/sync`, null, { timeout: 60000 }).then((res) => res.data),
  syncAll: () => api.post<FeedSyncReport>('/feeds/sync-all', null, { timeout: 120000 }).then((res) => res.data),
  importOpml: (input: File | File[]) => {
    const files = Array.isArray(input) ? input : [input]
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    return api.post<OPMLImportReport>('/opml/import', formData, { timeout: 30000 }).then((res) => res.data)
  },
  exportOpml: (feedIds?: number[]) => {
    const params = new URLSearchParams()
    feedIds?.forEach((id) => params.append('feed_ids', String(id)))
    return api
      .get<Blob>('/opml/export', {
        params: feedIds?.length ? params : undefined,
        responseType: 'blob'
      })
      .then((res) => res.data)
  },
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
  syncLogs: () => api.get<SyncLog[]>('/logs/sync').then((res) => res.data),
  search: (q: string, limit = 50) =>
    api.get<SearchResult[]>('/search', { params: { q, limit } }).then((res) => res.data),
  ragAsk: (question: string) =>
    api.post<AskResponse>('/rag/ask', { question }, { timeout: 60000 }).then((res) => res.data),
  ragIndex: () =>
    api.post<{ status: string; message: string }>('/rag/index').then((res) => res.data),
  ragIndexStatus: () =>
    api.get<{ running: boolean; last_indexed: number }>('/rag/index/status').then((res) => res.data),
  getRagConfig: () =>
    api.get<RagConfig>('/rag/config').then((res) => res.data),
  saveRagConfig: (config: RagConfig) =>
    api.put<RagConfig>('/rag/config', config).then((res) => res.data)
  
}
