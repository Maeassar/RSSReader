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

export const rssApi = {
  feeds: () => api.get<Feed[]>('/feeds').then((res) => res.data),
  createFeed: (payload: { title?: string; url: string }) => api.post<Feed>('/feeds', payload).then((res) => res.data),
  syncFeed: (id: number) => api.post<Feed>(`/feeds/${id}/sync`).then((res) => res.data),
  syncAll: () => api.post<Feed[]>('/feeds/sync-all').then((res) => res.data),
  articles: (params?: Record<string, unknown>) => api.get<Article[]>('/articles', { params }).then((res) => res.data),
  article: (id: number) => api.get<Article>(`/articles/${id}`).then((res) => res.data),
  markRead: (id: number, is_read: boolean) => api.patch<Article>(`/articles/${id}/read`, null, { params: { is_read } }).then((res) => res.data),
  markStarred: (id: number, is_starred: boolean) => api.patch<Article>(`/articles/${id}/star`, null, { params: { is_starred } }).then((res) => res.data),
  tags: () => api.get<Tag[]>('/tags').then((res) => res.data),
  createTag: (payload: { name: string; color: string }) => api.post<Tag>('/tags', payload).then((res) => res.data),
  note: (articleId: number) => api.get<Note>(`/articles/${articleId}/note`).then((res) => res.data),
  saveNote: (articleId: number, content_markdown: string) => api.put<Note>(`/articles/${articleId}/note`, { content_markdown }).then((res) => res.data),
  summary: (articleId: number) => api.post<AIResult>(`/ai/summary/${articleId}`).then((res) => res.data),
  translate: (articleId: number) => api.post<AIResult>(`/ai/translate/${articleId}`).then((res) => res.data),
  suggestTags: (articleId: number) => api.post<AIResult>(`/ai/tag-suggest/${articleId}`).then((res) => res.data),
  llmStats: () => api.get('/stats/llm').then((res) => res.data),
  syncLogs: () => api.get('/logs/sync').then((res) => res.data)
}

