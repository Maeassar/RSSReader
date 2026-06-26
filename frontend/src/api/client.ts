import axios from 'axios'

const desktopApiBaseUrl = window.rssReaderDesktop?.apiBaseUrl
const apiBaseUrl = desktopApiBaseUrl ? `${desktopApiBaseUrl}/api` : '/api'

export const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000
})

/** 从 axios 错误中提取可读的错误信息，按规则映射为用户友好文案 */
export function getErrorMessage(e: unknown, fallback = '请求异常，请检查网络或后端配置'): string {
  if (axios.isAxiosError(e)) {
    const status = e.response?.status
    if (status === 401 || status === 403) {
      return '鉴权失败：请检查您的 API 密钥 (API Key) 是否正确'
    }
    const detail = e.response?.data?.detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
    if (status === 404 || status === 500 || !e.response) {
      return '连接失败：无法访问后端服务，请检查 API URL 链接是否正确'
    }
  }
  return fallback
}

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

export type ArticleListItem = Omit<Article, 'raw_html' | 'cleaned_html' | 'cleaned_markdown'>

export interface PaginatedArticles {
  items: ArticleListItem[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface ArticleCounts {
  total: number
  unread: number
  starred: number
  by_feed: Record<number, number>
  by_tag: Record<number, number>
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
  provider_id?: number | null
  prompt: string
  result: string
  input_tokens: number
  output_tokens: number
  created_at: string
  aligned_blocks?: Array<{type: string, original: string, translated: string}>
}

export interface TagSuggestionCandidate {
  name: string
  tag_id?: number | null
  reason?: string | null
}

export interface TagSuggestionResponse {
  article_id: number
  candidates: TagSuggestionCandidate[]
  ai_result: AIResult
}

export interface SummaryRequestPayload {
  provider_id?: number | null
  refresh?: boolean
  mode?: 'brief' | 'structured' | 'deep'
  language?: string
  max_words?: number
}

export interface TranslationRequestPayload {
  provider_id?: number | null
  refresh?: boolean
  target_language?: string
  source_language?: string
  preserve_markdown?: boolean
}

export interface SegmentTranslationPayload {
  text: string
  provider_id?: number | null
  target_language?: string
  source_language?: string
  preserve_markdown?: boolean
  preserve_html?: boolean
}

export interface SegmentTranslationResponse {
  text: string
  input_tokens: number
  output_tokens: number
}

export interface SummaryStreamEvent {
  type: string
  title?: string
  detail?: string
  result?: AIResult
  usage?: {
    input_tokens: number
    output_tokens: number
  }
  total_usage?: {
    input_tokens: number
    output_tokens: number
  }
  index?: number
  total?: number
  round?: number
  chunks?: number
  estimated_tokens?: number
  input_budget?: number
  ts?: number
}

export type LLMProviderType = 'openai_compatible' | 'vllm' | 'ollama' | 'custom'

export interface LLMProvider {
  id: number
  name: string
  provider_type: LLMProviderType
  base_url: string
  model: string
  enabled: boolean
  is_default: boolean
  is_translation_default: boolean
  has_api_key: boolean
}

export interface LLMProviderPayload {
  name: string
  provider_type: LLMProviderType
  base_url: string
  api_key?: string
  model: string
  enabled: boolean
  is_default: boolean
}

export interface TranslationProvider {
  id: number
  name: string
  provider_type: LLMProviderType
  base_url: string
  model: string
  enabled: boolean
  is_default: boolean
  has_api_key: boolean
}

export interface TranslationProviderPayload {
  name: string
  provider_type: LLMProviderType
  base_url: string
  api_key?: string
  model: string
  enabled: boolean
  is_default: boolean
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
  embedding_dim: number
  chat_provider_name: string
  chat_provider_model: string
  has_siliconflow_api_key: boolean
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

export interface FeedBatchDeleteItem {
  feed_id: number
  status: 'success' | 'failed' | 'skipped'
  message: string
}

export interface FeedBatchDeleteReport {
  total: number
  success: number
  failed: number
  skipped: number
  results: FeedBatchDeleteItem[]
}

export interface FeedCreateResult {
  status: 'success' | 'partial'
  message: string
  feed: Feed
}

export interface OPMLImportItem {
  url?: string | null
  title?: string
  status: 'pending' | 'imported' | 'partial' | 'skipped' | 'failed'
  message: string
  feed?: Feed | null
  articles?: Article[]
  source_file?: string
}

export interface OPMLImportReport {
  files: number
  total: number
  imported: number
  partial: number
  skipped: number
  failed: number
  results: OPMLImportItem[]
}

export interface OPMLImportStreamEvent {
  type: 'parsed' | 'item' | 'done'
  items?: OPMLImportItem[]
  item?: OPMLImportItem
  report: OPMLImportReport
}

export interface LLMTimeseriesBucket {
  time_label: string
  calls: number
  failed_calls: number
  input_tokens: number
  output_tokens: number
}

export type StatsRange = 'today' | 'week' | 'month' | 'all'

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
  include_full_text: boolean
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
  createFeed: (payload: { title?: string; url: string }) => api.post<FeedCreateResult>('/feeds', payload, { timeout: 60000 }).then((res) => res.data),
  deleteFeed: (id: number) => api.delete<OperationResult>(`/feeds/${id}`).then((res) => res.data),
  deleteFeeds: (feedIds: number[]) =>
    api.post<FeedBatchDeleteReport>('/feeds/batch-delete', { feed_ids: feedIds }).then((res) => res.data),
  syncFeed: (id: number) => api.post<Feed>(`/feeds/${id}/sync`, null, { timeout: 60000 }).then((res) => res.data),
  syncAll: () => api.post<FeedSyncReport>('/feeds/sync-all', null, { timeout: 120000 }).then((res) => res.data),
  importOpml: (input: File | File[]) => {
    const files = Array.isArray(input) ? input : [input]
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    return api.post<OPMLImportReport>('/opml/import', formData, { timeout: 120000 }).then((res) => res.data)
  },
  importOpmlStream: (input: File | File[], onEvent: (event: OPMLImportStreamEvent) => void) => {
    const files = Array.isArray(input) ? input : [input]
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    return streamFormDataSse<OPMLImportStreamEvent>(`${apiBaseUrl}/opml/import/stream`, formData, onEvent)
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
  articles: (params?: Record<string, unknown>) => api.get<PaginatedArticles>('/articles', { params }).then((res) => res.data),
  articleCounts: () => api.get<ArticleCounts>('/articles/counts').then((res) => res.data),
  article: (id: number) => api.get<Article>(`/articles/${id}`).then((res) => res.data),
  refreshArticleContent: (id: number) => api.post<Article>(`/articles/${id}/refresh-content`).then((res) => res.data),
  markRead: (id: number, is_read: boolean) => api.patch<Article>(`/articles/${id}/read`, null, { params: { is_read } }).then((res) => res.data),
  markStarred: (id: number, is_starred: boolean) => api.patch<Article>(`/articles/${id}/star`, null, { params: { is_starred } }).then((res) => res.data),
  tags: () => api.get<Tag[]>('/tags').then((res) => res.data),
  createTag: (payload: { name: string; color: string }) => api.post<Tag>('/tags', payload).then((res) => res.data),
  deleteTag: (id: number) => api.delete<OperationResult>(`/tags/${id}`).then((res) => res.data),
  setArticleTags: (articleId: number, tagIds: number[]) =>
    api.post<{ article_id: number; tag_ids: number[] }>(`/articles/${articleId}/tags`, tagIds).then((res) => res.data),
  note: (articleId: number) => api.get<Note>(`/articles/${articleId}/note`).then((res) => res.data),
  saveNote: (articleId: number, content_markdown: string) => api.put<Note>(`/articles/${articleId}/note`, { content_markdown }).then((res) => res.data),
  exportArticleMarkdown: (articleId: number) =>
    api.get<Blob>(`/export/articles/${articleId}/markdown`, { responseType: 'blob' }).then((res) => res.data),
  exportBatchDigestMarkdown: (payload: BatchDigestExportRequest) =>
    api.post<BatchDigestExportResponse>('/export/digests/markdown', payload).then((res) => res.data),
  getCachedSummary: (articleId: number) =>
    api.post<AIResult>(`/ai/summary/${articleId}`, { refresh: false }, { timeout: 10000 })
      .then((res) => res.data)
      .catch(() => null),
  summary: (
    articleId: number,
    payload?: SummaryRequestPayload
  ) =>
    api.post<AIResult>(`/ai/summary/${articleId}`, payload ?? {}, { timeout: 300000 }).then((res) => res.data),
  streamSummary: (articleId: number, payload: SummaryRequestPayload | undefined, onEvent: (event: SummaryStreamEvent) => void, signal?: AbortSignal) =>
    streamSse<SummaryStreamEvent>(`${apiBaseUrl}/ai/summary/${articleId}/stream`, payload ?? {}, onEvent, signal),
  translate: (articleId: number, payload?: TranslationRequestPayload) =>
    api.post<AIResult>(`/ai/translate/${articleId}`, payload ?? {}, { timeout: 300000 }).then((res) => res.data),
  streamTranslate: (articleId: number, payload: TranslationRequestPayload | undefined, onEvent: (event: SummaryStreamEvent) => void, signal?: AbortSignal) =>
    streamSse<SummaryStreamEvent>(`${apiBaseUrl}/ai/translate/${articleId}/stream`, payload ?? {}, onEvent, signal),
  translateSegment: (payload: SegmentTranslationPayload) =>
    api.post<SegmentTranslationResponse>(`/ai/translate/segment`, payload, { timeout: 120000 }).then((res) => res.data),
  suggestTags: (articleId: number) =>
    api.post<TagSuggestionResponse>(`/ai/tag-suggest/${articleId}`, null, { timeout: 120000 }).then((res) => res.data),
  llmProviders: () => api.get<LLMProvider[]>('/ai/providers').then((res) => res.data),
  createLLMProvider: (payload: LLMProviderPayload) => api.post<LLMProvider>('/ai/providers', payload).then((res) => res.data),
  updateLLMProvider: (id: number, payload: Partial<LLMProviderPayload>) => api.put<LLMProvider>(`/ai/providers/${id}`, payload).then((res) => res.data),
  deleteLLMProvider: (id: number) => api.delete<OperationResult>(`/ai/providers/${id}`).then((res) => res.data),
  translationProviders: () => api.get<TranslationProvider[]>('/ai/translation-providers').then((res) => res.data),
  createTranslationProvider: (payload: TranslationProviderPayload) => api.post<TranslationProvider>('/ai/translation-providers', payload).then((res) => res.data),
  updateTranslationProvider: (id: number, payload: Partial<TranslationProviderPayload>) => api.put<TranslationProvider>(`/ai/translation-providers/${id}`, payload).then((res) => res.data),
  deleteTranslationProvider: (id: number) => api.delete<OperationResult>(`/ai/translation-providers/${id}`).then((res) => res.data),
  llmStats: (range?: StatsRange, filter?: { provider?: string; model?: string }) =>
    api.get('/stats/llm', { params: { ...(range ? { range } : {}), ...filter } }).then((res) => res.data),
  llmTimeseries: (range: StatsRange = 'today', filter?: { provider?: string; model?: string }) =>
    api.get<LLMTimeseriesBucket[]>('/stats/llm/timeseries', { params: { range, ...filter } }).then((res) => res.data),
  deleteModelStats: (provider: string, model: string) =>
    api.delete('/stats/llm', { params: { provider, model } }).then((res) => res.data),
  syncLogs: (range?: StatsRange) =>
    api.get<SyncLog[]>('/logs/sync', { params: range ? { range } : {} }).then((res) => res.data),
  search: (q: string, limit = 50) =>
    api.get<SearchResult[]>('/search', { params: { q, limit } }).then((res) => res.data),
  ragAsk: (question: string) =>
    api.post<AskResponse>('/rag/ask', { question }, { timeout: 60000 }).then((res) => res.data),
  ragIndex: () =>
    api.post<{ status: string; message: string }>('/rag/index').then((res) => res.data),
  ragIndexStatus: () =>
    api.get<{ running: boolean; last_added: number; last_removed: number; error: string }>('/rag/index/status').then((res) => res.data),
  getRagConfig: () =>
    api.get<RagConfig>('/rag/config').then((res) => res.data),
  saveRagConfig: (config: RagConfig) =>
    api.put<RagConfig>('/rag/config', config).then((res) => res.data)
  
}

async function streamFormDataSse<T>(url: string, formData: FormData, onEvent: (event: T) => void) {
  const response = await fetch(url, {
    method: 'POST',
    body: formData
  })
  if (!response.ok || !response.body) {
    throw new Error(await fetchErrorMessage(response))
  }

  await readSseResponse(response, onEvent)
}

async function streamSse<T>(
  url: string,
  payload: unknown,
  onEvent: (event: T) => void,
  signal?: AbortSignal,
) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
  if (!response.ok || !response.body) {
    throw new Error(await fetchErrorMessage(response))
  }

  await readSseResponse(response, onEvent)
}

async function readSseResponse<T>(response: Response, onEvent: (event: T) => void) {
  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''
    for (const frame of frames) {
      const data = frame
        .split('\n')
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.slice(5).trim())
        .join('\n')
      if (!data) continue
      const event = JSON.parse(data) as T
      throwIfStreamError(event)
      onEvent(event)
    }
  }

  buffer += decoder.decode()
  if (buffer.trim()) {
    const data = buffer
      .split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trim())
      .join('\n')
    if (data) {
      const event = JSON.parse(data) as T
      throwIfStreamError(event)
      onEvent(event)
    }
  }
}

function throwIfStreamError(event: unknown) {
  const streamEvent = event as { type?: string; detail?: string }
  if (streamEvent.type === 'error') {
    throw new Error(streamEvent.detail || '摘要生成失败，请检查 Provider 配置')
  }
}

async function fetchErrorMessage(response: Response) {
  try {
    const data = await response.json()
    if (typeof data?.detail === 'string' && data.detail.trim()) return data.detail
  } catch {
    // Ignore non-JSON error bodies.
  }
  if (response.status === 401 || response.status === 403) return '鉴权失败：请检查您的 API 密钥 (API Key) 是否正确'
  return '连接失败：无法访问后端服务，请检查 API URL 链接是否正确'
}
