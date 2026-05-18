import { defineStore } from 'pinia'
import { Article, Feed, rssApi, Tag } from '../api/client'

export const useReaderStore = defineStore('reader', {
  state: () => ({
    feeds: [] as Feed[],
    articles: [] as Article[],
    tags: [] as Tag[],
    selectedArticle: null as Article | null,
    loading: false
  }),
  actions: {
    async loadAll() {
      this.loading = true
      try {
        const [feeds, articles, tags] = await Promise.all([rssApi.feeds(), rssApi.articles(), rssApi.tags()])
        this.feeds = feeds
        this.articles = articles
        this.tags = tags
        this.selectedArticle = articles[0] ?? null
      } finally {
        this.loading = false
      }
    },
    async selectArticle(id: number) {
      this.selectedArticle = await rssApi.article(id)
    },
    async toggleRead(article: Article) {
      const updated = await rssApi.markRead(article.id, !article.is_read)
      this.replaceArticle(updated)
    },
    async toggleStar(article: Article) {
      const updated = await rssApi.markStarred(article.id, !article.is_starred)
      this.replaceArticle(updated)
    },
    replaceArticle(article: Article) {
      this.articles = this.articles.map((item) => (item.id === article.id ? article : item))
      if (this.selectedArticle?.id === article.id) {
        this.selectedArticle = article
      }
    }
  }
})

