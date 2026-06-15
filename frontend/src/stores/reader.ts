import { defineStore } from 'pinia'
import { Article, Feed, rssApi, Tag } from '../api/client'

const PINNED_ARTICLES_KEY = 'rssreader.pinnedArticleIds'
const SUMMARY_LINES_KEY = 'rssreader.summaryLineCount'
const SHOW_THUMBNAILS_KEY = 'rssreader.showThumbnails'
const LEFT_SIDEBAR_VISIBLE_KEY = 'rssreader.leftSidebarVisible'
const ARTICLE_LIST_VISIBLE_KEY = 'rssreader.articleListVisible'
const FILTER_PANEL_EXPANDED_KEY = 'rssreader.filterPanelExpanded'
const FEED_PANEL_EXPANDED_KEY = 'rssreader.feedPanelExpanded'
const TAG_PANEL_EXPANDED_KEY = 'rssreader.tagPanelExpanded'
const ARTICLE_SORT_ORDER_KEY = 'rssreader.articleSortOrder'
const ARTICLE_TAG_OVERRIDES_KEY = 'rssreader.articleTagOverrides'

type SortOrder = 'newest' | 'oldest'

type ArticleTagOverrides = Record<number, number[]>

function storedJsonArray(key: string): number[] {
  const raw = localStorage.getItem(key)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((item) => Number.isInteger(item)) : []
  } catch {
    return []
  }
}

function storedBoolean(key: string, fallback: boolean) {
  const raw = localStorage.getItem(key)
  if (raw === null) return fallback
  return raw === 'true'
}

function storedSummaryLines() {
  const raw = localStorage.getItem(SUMMARY_LINES_KEY)
  const value = raw ? Number(raw) : 3
  return Number.isFinite(value) && value >= 1 && value <= 5 ? Math.round(value) : 3
}

function storedSortOrder(): SortOrder {
  return localStorage.getItem(ARTICLE_SORT_ORDER_KEY) === 'oldest' ? 'oldest' : 'newest'
}

function storedArticleTagOverrides(): ArticleTagOverrides {
  const raw = localStorage.getItem(ARTICLE_TAG_OVERRIDES_KEY)
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return {}
    return Object.fromEntries(
      Object.entries(parsed).filter(([, value]) => Array.isArray(value))
    ) as ArticleTagOverrides
  } catch {
    return {}
  }
}

function sortArticles(articles: Article[], pinnedArticleIds: number[], sortOrder: SortOrder) {
  const pinned = new Set(pinnedArticleIds)
  return [...articles].sort((left, right) => {
    const leftPinned = pinned.has(left.id)
    const rightPinned = pinned.has(right.id)
    if (leftPinned !== rightPinned) {
      return leftPinned ? -1 : 1
    }

    const leftTime = Date.parse(left.published_at ?? left.created_at ?? '') || 0
    const rightTime = Date.parse(right.published_at ?? right.created_at ?? '') || 0
    return sortOrder === 'oldest' ? leftTime - rightTime : rightTime - leftTime
  })
}

export const useReaderStore = defineStore('reader', {
  state: () => ({
    feeds: [] as Feed[],
    articles: [] as Article[],
    tags: [] as Tag[],
    selectedArticle: null as Article | null,
    loading: false,
    articleMutationVersion: 0,
    pinnedArticleIds: storedJsonArray(PINNED_ARTICLES_KEY),
    summaryLineCount: storedSummaryLines(),
    showThumbnails: storedBoolean(SHOW_THUMBNAILS_KEY, false),
    leftSidebarVisible: storedBoolean(LEFT_SIDEBAR_VISIBLE_KEY, true),
    articleListVisible: storedBoolean(ARTICLE_LIST_VISIBLE_KEY, true),
    filterPanelExpanded: storedBoolean(FILTER_PANEL_EXPANDED_KEY, true),
    feedPanelExpanded: storedBoolean(FEED_PANEL_EXPANDED_KEY, true),
    tagPanelExpanded: storedBoolean(TAG_PANEL_EXPANDED_KEY, true),
    articleSortOrder: storedSortOrder(),
    articleTagOverrides: storedArticleTagOverrides()
  }),
  actions: {
    async loadAll() {
      this.loading = true
      const articleMutationVersion = this.articleMutationVersion
      try {
        const [feeds, articles, tags] = await Promise.allSettled([rssApi.feeds(), rssApi.articles(), rssApi.tags()])

        if (feeds.status === 'fulfilled') {
          this.feeds = feeds.value
        } else {
          console.error('Failed to load feeds', feeds.reason)
        }

        if (articles.status === 'fulfilled') {
          if (this.articleMutationVersion === articleMutationVersion) {
            this.articles = sortArticles(
              articles.value.map((article) => this.applyArticleOverrides(article)),
              this.pinnedArticleIds,
              this.articleSortOrder
            )
            this.articleMutationVersion += 1
          } else {
            this.mergeArticles(articles.value)
          }
        } else {
          console.error('Failed to load articles', articles.reason)
          this.articles = []
          this.articleMutationVersion += 1
        }

        if (tags.status === 'fulfilled') {
          this.tags = tags.value
        } else {
          console.error('Failed to load tags', tags.reason)
          this.tags = []
        }

        this.selectedArticle = this.articles[0] ?? null
      } finally {
        this.loading = false
      }
    },
    async selectArticle(id: number) {
      const article = this.applyArticleOverrides(await rssApi.article(id))
      this.selectedArticle = article
      if (!article.is_read) {
        const updated = await rssApi.markRead(article.id, true)
        this.replaceArticle(updated)
      }
    },
    setArticles(articles: Article[]) {
      this.articles = sortArticles(
        articles.map((article) => this.applyArticleOverrides(article)),
        this.pinnedArticleIds,
        this.articleSortOrder
      )
      this.articleMutationVersion += 1
      if (!this.selectedArticle) {
        this.selectedArticle = this.articles[0] ?? null
        return
      }
      this.selectedArticle = this.articles.find((article) => article.id === this.selectedArticle?.id) ?? this.articles[0] ?? null
    },
    mergeArticles(articles: Article[]) {
      const articleMap = new Map(this.articles.map((article) => [article.id, article]))
      articles.forEach((article) => {
        articleMap.set(article.id, this.applyArticleOverrides(article))
      })
      this.articles = sortArticles(Array.from(articleMap.values()), this.pinnedArticleIds, this.articleSortOrder)
      this.articleMutationVersion += 1
      if (!this.selectedArticle) {
        this.selectedArticle = this.articles[0] ?? null
        return
      }
      this.selectedArticle = this.articles.find((article) => article.id === this.selectedArticle?.id) ?? this.selectedArticle
    },
    async refreshFeedArticles(feedId: number) {
      const articles = await rssApi.articles({ feed_id: feedId })
      this.mergeArticles(articles)
    },
    upsertFeed(feed: Feed) {
      const index = this.feeds.findIndex((item) => item.id === feed.id)
      if (index >= 0) {
        this.feeds.splice(index, 1, feed)
        return
      }
      this.feeds = [feed, ...this.feeds]
    },
    removeFeeds(feedIds: number[]) {
      const ids = new Set(feedIds)
      this.feeds = this.feeds.filter((feed) => !ids.has(feed.id))
      this.articles = this.articles.filter((article) => !ids.has(article.feed_id))
      this.articleMutationVersion += 1
      if (this.selectedArticle && ids.has(this.selectedArticle.feed_id)) {
        this.selectedArticle = this.articles[0] ?? null
      }
    },
    async toggleRead(article: Article) {
      const updated = await rssApi.markRead(article.id, !article.is_read)
      this.replaceArticle(updated)
    },
    async toggleStar(article: Article) {
      const updated = await rssApi.markStarred(article.id, !article.is_starred)
      this.replaceArticle(updated)
    },
    async setArticleTags(articleId: number, tagIds: number[]) {
      this.articleTagOverrides = { ...this.articleTagOverrides, [articleId]: tagIds }
      localStorage.setItem(ARTICLE_TAG_OVERRIDES_KEY, JSON.stringify(this.articleTagOverrides))
      try {
        await rssApi.setArticleTags(articleId, tagIds)
      } catch (error) {
        console.warn('Falling back to local tag assignment only.', error)
      }
      const current = this.articles.find((item) => item.id === articleId) ?? this.selectedArticle
      if (current) {
        this.replaceArticle({ ...current, tag_ids: tagIds })
      }
    },
    togglePinned(articleId: number) {
      const set = new Set(this.pinnedArticleIds)
      if (set.has(articleId)) {
        set.delete(articleId)
      } else {
        set.add(articleId)
      }
      this.pinnedArticleIds = Array.from(set)
      localStorage.setItem(PINNED_ARTICLES_KEY, JSON.stringify(this.pinnedArticleIds))
      this.articles = sortArticles(this.articles, this.pinnedArticleIds, this.articleSortOrder)
    },
    isPinned(articleId: number) {
      return this.pinnedArticleIds.includes(articleId)
    },
    setSummaryLineCount(value: number) {
      const normalized = Number.isFinite(value) && value >= 1 && value <= 5 ? Math.round(value) : 2
      this.summaryLineCount = normalized
      localStorage.setItem(SUMMARY_LINES_KEY, String(normalized))
    },
    setShowThumbnails(value: boolean) {
      this.showThumbnails = value
      localStorage.setItem(SHOW_THUMBNAILS_KEY, String(value))
    },
    setLeftSidebarVisible(value: boolean) {
      this.leftSidebarVisible = value
      localStorage.setItem(LEFT_SIDEBAR_VISIBLE_KEY, String(value))
    },
    setArticleListVisible(value: boolean) {
      this.articleListVisible = value
      localStorage.setItem(ARTICLE_LIST_VISIBLE_KEY, String(value))
    },
    setFilterPanelExpanded(value: boolean) {
      this.filterPanelExpanded = value
      localStorage.setItem(FILTER_PANEL_EXPANDED_KEY, String(value))
    },
    setFeedPanelExpanded(value: boolean) {
      this.feedPanelExpanded = value
      localStorage.setItem(FEED_PANEL_EXPANDED_KEY, String(value))
    },
    setTagPanelExpanded(value: boolean) {
      this.tagPanelExpanded = value
      localStorage.setItem(TAG_PANEL_EXPANDED_KEY, String(value))
    },
    setArticleSortOrder(value: SortOrder) {
      this.articleSortOrder = value
      localStorage.setItem(ARTICLE_SORT_ORDER_KEY, value)
      this.articles = sortArticles(this.articles, this.pinnedArticleIds, this.articleSortOrder)
    },
    replaceArticle(article: Article) {
      const normalized = this.applyArticleOverrides(article)
      this.articles = sortArticles(
        this.articles.map((item) => (item.id === normalized.id ? normalized : item)),
        this.pinnedArticleIds,
        this.articleSortOrder
      )
      if (this.selectedArticle?.id === article.id) {
        this.selectedArticle = normalized
      }
    },
    applyArticleOverrides(article: Article) {
      const overrideTagIds = this.articleTagOverrides[article.id]
      return {
        ...article,
        tag_ids: overrideTagIds ?? article.tag_ids
      }
    }
  }
})
