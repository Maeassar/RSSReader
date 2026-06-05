<template>
  <div class="reader-shell">
    <div class="reader-grid" v-loading="store.loading">
      <section class="panel sidebar-panel">
        <div class="sidebar-header">
          <h2>订阅与筛选</h2>
        </div>

        <div class="sidebar-static-filters">
          <button
            v-for="item in quickFilters"
            :key="item.key"
            type="button"
            class="sidebar-primary-link"
            :class="{ active: activeFilterKey === item.key }"
            @click="applyQuickFilter(item.key)"
          >
            <span>{{ item.label }}</span>
            <span class="sidebar-filter-count">{{ item.count }}</span>
          </button>
        </div>

        <button type="button" class="sidebar-group-toggle" @click="store.setTagPanelExpanded(!store.tagPanelExpanded)">
          <span>标签</span>
          <span class="sidebar-chevron" :class="{ expanded: store.tagPanelExpanded }">›</span>
        </button>
        <div v-show="store.tagPanelExpanded" class="sidebar-group-content">
          <div class="tag-create-row">
            <el-input
              v-model="newTagName"
              size="small"
              placeholder="新建标签"
              @keyup.enter="createTag"
            />
            <input v-model="newTagColor" class="tag-color-input" type="color" aria-label="选择标签颜色" />
            <el-button size="small" @click="createTag">添加</el-button>
          </div>
          <button
            v-for="tag in store.tags"
            :key="tag.id"
            type="button"
            class="sidebar-filter-button"
            :class="{ active: activeTagId === tag.id }"
            @click="activeTagId = activeTagId === tag.id ? null : tag.id"
          >
            <span class="tag-filter-label">
              <span class="tag-dot" :style="{ background: tag.color }"></span>
              <span>{{ tag.name }}</span>
            </span>
            <span class="sidebar-filter-count">{{ tagArticleCount(tag.id) }}</span>
          </button>
        </div>

        <div class="sidebar-section-header">
          <span class="sidebar-section-title">订阅源</span>
          <div class="sidebar-section-actions">
            <button type="button" class="sidebar-section-action" aria-label="添加订阅源" @click="openFeedManager">
              <el-icon><Plus /></el-icon>
            </button>
            <el-dropdown trigger="click" @command="handleFeedSectionCommand">
              <button type="button" class="sidebar-section-action" aria-label="订阅源更多操作">
                <el-icon><MoreFilled /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="manage-feeds">管理订阅源</el-dropdown-item>
                  <el-dropdown-item command="sync-feeds">同步全部订阅</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <div class="sidebar-group-content sidebar-feed-list">
          <button
            v-for="feed in store.feeds"
            :key="feed.id"
            type="button"
            class="sidebar-feed-button"
            :class="{ active: activeFeedId === feed.id }"
            @click="applyFeedFilter(feed.id)"
          >
            <span class="sidebar-feed-mark">{{ feed.title.slice(0, 1) }}</span>
            <span class="sidebar-feed-name" :title="feed.title">{{ feed.title }}</span>
          </button>
        </div>
      </section>

      <section v-if="!feedManagerOpen" class="panel scroll-panel article-list-panel">
        <div class="article-list-header">
          <h2>{{ currentListTitle }}</h2>
          <div class="article-list-topbar-right">
            <el-dropdown trigger="click" @command="handleListMenuCommand">
              <button type="button" class="list-menu-button" aria-label="列表设置">
                <el-icon><MoreFilled /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="sync">
                    <el-icon><Refresh /></el-icon>
                    <span>同步全部</span>
                  </el-dropdown-item>
                  <el-dropdown-item command="batch-export">
                    <el-icon><Files /></el-icon>
                    <span>批量文摘</span>
                  </el-dropdown-item>
                  <el-dropdown-item disabled>排序</el-dropdown-item>
                  <el-dropdown-item command="sort:newest">
                    {{ store.articleSortOrder === 'newest' ? '✓ ' : '' }}从新到旧
                  </el-dropdown-item>
                  <el-dropdown-item command="sort:oldest">
                    {{ store.articleSortOrder === 'oldest' ? '✓ ' : '' }}从旧到新
                  </el-dropdown-item>
                  <el-dropdown-item divided disabled>视图</el-dropdown-item>
                  <div class="dropdown-inline-control" @click.stop>
                    <span class="dropdown-inline-label">摘要行数</span>
                    <div class="dropdown-inline-stepper">
                      <button type="button" class="stepper-button" @click.stop="decreaseSummaryLines">-</button>
                      <span class="stepper-value">{{ store.summaryLineCount }}</span>
                      <button type="button" class="stepper-button" @click.stop="increaseSummaryLines">+</button>
                    </div>
                  </div>
                  <el-dropdown-item command="toggle:thumbnails">
                    {{ store.showThumbnails ? '✓ ' : '' }}显示缩略图
                  </el-dropdown-item>
                  <el-dropdown-item divided command="unsubscribe" :disabled="!activeFeedForMenu">
                    退订
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <article
          v-for="article in filteredArticles"
          :key="article.id"
          class="article-card"
          :class="{ active: store.selectedArticle?.id === article.id, pinned: store.isPinned(article.id) }"
          @click="handleArticleClick(article.id)"
        >
          <div class="article-card-meta-row">
            <span class="article-card-source">{{ article.feed_title }}</span>
            <span class="article-card-date">{{ formatArticleDate(article) }}</span>
          </div>

          <div class="article-card-main" :class="{ 'with-thumbnail': Boolean(store.showThumbnails && articleThumbnail(article)) }">
            <div class="article-card-copy">
              <h3>{{ article.title }}</h3>
              <p v-if="article.summary" class="article-card-summary" :style="summaryClampStyle">
                {{ article.summary }}
              </p>
              <div class="article-card-tags">
                <el-tag v-if="!article.is_read" size="small">未读</el-tag>
                <el-tag v-if="article.is_starred" size="small" type="warning">收藏</el-tag>
                <el-tag v-if="store.isPinned(article.id)" size="small" effect="plain">置顶</el-tag>
                <el-tag
                  v-for="tagId in article.tag_ids"
                  :key="`${article.id}-${tagId}`"
                  size="small"
                  effect="plain"
                >
                  {{ tagName(tagId) }}
                </el-tag>
              </div>
            </div>

            <div v-if="store.showThumbnails && articleThumbnail(article)" class="article-card-thumb">
              <img :src="articleThumbnail(article) || ''" alt="" class="article-thumbnail" />
            </div>
          </div>
        </article>
      </section>

      <section v-if="store.selectedArticle && !feedManagerOpen" class="panel scroll-panel reader-detail-panel">
        <div class="toolbar detail-toolbar">
          <el-tooltip :content="store.selectedArticle.is_read ? '标记未读' : '标记已读'" placement="top">
            <el-button class="toolbar-icon-button" :class="{ active: store.selectedArticle.is_read }" :icon="Check" circle @click="store.toggleRead(store.selectedArticle)" />
          </el-tooltip>
          <el-tooltip :content="store.isPinned(store.selectedArticle.id) ? '取消置顶' : '置顶'" placement="top">
            <el-button class="toolbar-icon-button" :class="{ active: store.isPinned(store.selectedArticle.id) }" :icon="Top" circle @click="togglePinnedSelected" />
          </el-tooltip>
          <el-tooltip :content="store.selectedArticle.is_starred ? '取消收藏' : '收藏'" placement="top">
            <el-button class="toolbar-icon-button" :class="{ active: store.selectedArticle.is_starred }" :icon="Star" circle @click="store.toggleStar(store.selectedArticle)" />
          </el-tooltip>
          <el-tooltip content="生成摘要" placement="top">
            <el-button class="toolbar-icon-button" :icon="MagicStick" circle @click="runSummary" />
          </el-tooltip>
          <el-popover placement="bottom" :width="320" trigger="click" popper-class="tag-popover">
            <template #reference>
              <el-button class="toolbar-icon-button" :icon="CollectionTag" circle aria-label="标签" title="标签" />
            </template>
            <div class="tag-popover-body">
              <div class="tag-selection-list">
                <button
                  v-for="tag in store.tags"
                  :key="tag.id"
                  type="button"
                  class="tag-selection-item"
                  :class="{ active: selectedArticleTagIds.includes(tag.id) }"
                  @click="toggleSelectedArticleTag(tag.id)"
                >
                  <span class="tag-selection-main">
                    <span class="tag-dot" :style="{ background: tag.color }"></span>
                    <span>{{ tag.name }}</span>
                  </span>
                  <el-icon v-if="selectedArticleTagIds.includes(tag.id)"><Check /></el-icon>
                </button>
              </div>
              <div class="tag-creator-card">
                <div class="tag-create-row">
                  <el-input
                    v-model="newTagName"
                    size="small"
                    placeholder="创建标签"
                    @keyup.enter="createTag"
                  />
                  <input v-model="newTagColor" class="tag-color-input" type="color" aria-label="选择标签颜色" />
                  <el-button size="small" @click="createTag">+</el-button>
                </div>
              </div>
            </div>
          </el-popover>
          <el-tooltip content="翻译" placement="top">
            <el-button class="toolbar-icon-button" :icon="Switch" circle @click="runTranslate" />
          </el-tooltip>
          <el-tooltip :content="fullTextEnabled ? '切回摘要' : '加载网页原文'" placement="top">
            <el-button
              class="toolbar-icon-button load-fulltext-button"
              :class="{ active: fullTextEnabled }"
              plain
              :icon="DocumentAdd"
              :loading="refreshingArticleContent"
              circle
              @click="refreshArticleContent"
            />
          </el-tooltip>
          <el-dropdown trigger="click" @command="handleExportCommand">
            <el-button class="toolbar-icon-button export-trigger" :loading="exportingMarkdown" circle aria-label="导出">
              <el-icon><Download /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="digest">导出文摘</el-dropdown-item>
                <el-dropdown-item command="markdown">导出清洗后 Markdown</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <h1 class="reader-title">
          <a class="reader-title-link" :href="store.selectedArticle.url" target="_blank" rel="noopener noreferrer">
            {{ store.selectedArticle.title }}
          </a>
        </h1>
        <p class="muted">
          <span v-if="store.selectedArticle.author">{{ store.selectedArticle.author }}</span>
        </p>
        <div class="article-reading-surface">
          <div ref="articleBodyRef" class="article-body" v-html="renderedArticleHtml"></div>
        </div>
        <el-alert v-if="fulltextHint" :title="fulltextHint" type="info" show-icon :closable="false" class="reader-inline-alert" />
        <el-alert v-if="aiResult" :title="aiResult" type="success" show-icon :closable="false" />
        <el-divider />
        <h2 class="reader-section-title">笔记</h2>
        <el-input v-model="note" type="textarea" :rows="6" placeholder="写下这篇文章的 Markdown 笔记" />
        <div class="note-actions">
          <el-button type="primary" @click="saveNote">保存笔记</el-button>
          <el-button class="note-export-button" @click="exportNote">
            导出笔记
            <el-icon class="button-icon-right"><Download /></el-icon>
          </el-button>
        </div>
      </section>

      <section v-if="feedManagerOpen" class="panel feed-manager-overlay">
        <FeedManageView embedded @close="closeFeedManager" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check, CollectionTag, DocumentAdd, Download, Files, MagicStick, MoreFilled, Plus, Refresh, Star, Switch, Top } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Article } from '../api/client'
import { rssApi } from '../api/client'
import { useReaderStore } from '../stores/reader'
import FeedManageView from './FeedManageView.vue'

const store = useReaderStore()
const route = useRoute()
const router = useRouter()
const note = ref('')
const aiResult = ref('')
const articleBodyRef = ref<HTMLElement | null>(null)
const exportingMarkdown = ref(false)
const refreshingArticleContent = ref(false)
const fullTextEnabled = ref(false)
const feedManagerOpen = ref(false)
const activeFilterKey = ref<'all' | 'unread' | 'starred'>('all')
const activeFeedId = ref<number | null>(null)
const activeTagId = ref<number | null>(null)
const newTagName = ref('')
const newTagColor = ref('#5b8def')
const fulltextHint = ref('')

const renderedArticleHtml = computed(() => {
  const article = store.selectedArticle
  if (!article) return ''
  if (fullTextEnabled.value && article.cleaned_html?.trim()) return article.cleaned_html
  if (article.summary?.trim()) return `<p>${escapeHtml(article.summary)}</p>`
  if (article.cleaned_html?.trim()) return article.cleaned_html
  return '<p>这篇文章暂时没有可展示的正文内容。</p>'
})

const selectedArticleTagIds = computed(() => store.selectedArticle?.tag_ids ?? [])
const quickFilters = computed(() => [
  { key: 'all' as const, label: '全部文章', count: store.articles.length },
  { key: 'unread' as const, label: '未读文章', count: store.articles.filter((article) => !article.is_read).length },
  { key: 'starred' as const, label: '收藏', count: store.articles.filter((article) => article.is_starred).length }
])

const activeFeedForMenu = computed(() => {
  if (activeFeedId.value !== null) return store.feeds.find((feed) => feed.id === activeFeedId.value) ?? null
  if (store.selectedArticle) return store.feeds.find((feed) => feed.id === store.selectedArticle?.feed_id) ?? null
  return null
})

const filteredArticles = computed(() => {
  let list = [...store.articles]
  if (activeFilterKey.value === 'unread') list = list.filter((article) => !article.is_read)
  if (activeFilterKey.value === 'starred') list = list.filter((article) => article.is_starred)
  if (activeFeedId.value !== null) list = list.filter((article) => article.feed_id === activeFeedId.value)
  if (activeTagId.value !== null) {
    const tagId = activeTagId.value
    list = list.filter((article) => article.tag_ids.includes(tagId))
  }
  return list
})

const currentListTitle = computed(() => {
  if (activeFeedId.value !== null) return store.feeds.find((feed) => feed.id === activeFeedId.value)?.title ?? '当前订阅'
  if (activeTagId.value !== null) return `标签 · ${tagName(activeTagId.value)}`
  if (activeFilterKey.value === 'unread') return '未读文章'
  if (activeFilterKey.value === 'starred') return '收藏文章'
  return '全部文章'
})

const summaryClampStyle = computed(() => ({ WebkitLineClamp: String(store.summaryLineCount) }))

onMounted(async () => {
  window.addEventListener('rssreader:background-sync', handleBackgroundSync)
  await store.loadAll()
  await loadNote()
  ensureVisibleSelection()
})

onUnmounted(() => window.removeEventListener('rssreader:background-sync', handleBackgroundSync))

watch(() => store.selectedArticle?.id, loadNote)
watch(renderedArticleHtml, decorateArticleLinks, { flush: 'post' })
watch(filteredArticles, ensureVisibleSelection)
watch(
  () => route.query.panel,
  (panel) => {
    feedManagerOpen.value = panel === 'feeds'
  },
  { immediate: true }
)

async function handleBackgroundSync() {
  await store.loadAll()
  await loadNote()
}

async function loadNote() {
  if (!store.selectedArticle) return
  const data = await rssApi.note(store.selectedArticle.id)
  note.value = data.content_markdown
  fullTextEnabled.value = false
  fulltextHint.value = ''
}

async function decorateArticleLinks() {
  await nextTick()
  articleBodyRef.value?.querySelectorAll('a').forEach((link) => {
    link.setAttribute('target', '_blank')
    link.setAttribute('rel', 'noopener noreferrer')
  })
}

function ensureVisibleSelection() {
  if (!filteredArticles.value.length) {
    store.selectedArticle = null
    return
  }
  if (!filteredArticles.value.find((article) => article.id === store.selectedArticle?.id)) {
    store.selectedArticle = filteredArticles.value[0]
  }
}

function applyQuickFilter(key: 'all' | 'unread' | 'starred') {
  activeFilterKey.value = key
  activeFeedId.value = null
  activeTagId.value = null
  closeFeedManager()
}

function applyFeedFilter(feedId: number | null) {
  activeFeedId.value = feedId
  activeTagId.value = null
  activeFilterKey.value = 'all'
  closeFeedManager()
}

function openFeedManager() {
  feedManagerOpen.value = true
  if (route.query.panel !== 'feeds') {
    void router.replace({ path: '/', query: { ...route.query, panel: 'feeds' } })
  }
}

function closeFeedManager() {
  feedManagerOpen.value = false
  if (route.query.panel === 'feeds') {
    const nextQuery = { ...route.query }
    delete nextQuery.panel
    void router.replace({ path: '/', query: nextQuery })
  }
}

function tagArticleCount(tagId: number) {
  return store.articles.filter((article) => article.tag_ids.includes(tagId)).length
}

function tagName(tagId: number) {
  return store.tags.find((tag) => tag.id === tagId)?.name ?? '标签'
}

function articleThumbnail(article: Article) {
  const html = article.cleaned_html || article.raw_html || ''
  const matched = html.match(/<img[^>]+src=["']([^"']+)["']/i)
  return matched?.[1] ?? null
}

function formatArticleDate(article: Article) {
  const source = article.published_at || article.created_at
  if (!source) return ''
  const date = new Date(source)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date)
}

async function createTag() {
  const name = newTagName.value.trim()
  if (!name) return
  const created = await rssApi.createTag({ name, color: newTagColor.value })
  store.tags = [...store.tags, created]
  newTagName.value = ''
}

async function updateSelectedArticleTags(tagIds: number[]) {
  if (!store.selectedArticle) return
  await store.setArticleTags(store.selectedArticle.id, tagIds)
}

async function toggleSelectedArticleTag(tagId: number) {
  if (!store.selectedArticle) return
  const current = new Set(selectedArticleTagIds.value)
  if (current.has(tagId)) {
    current.delete(tagId)
  } else {
    current.add(tagId)
  }
  await updateSelectedArticleTags(Array.from(current))
}

async function saveNote() {
  if (!store.selectedArticle) return
  await rssApi.saveNote(store.selectedArticle.id, note.value)
  ElMessage.success('笔记已保存')
}

async function exportMarkdown() {
  if (!store.selectedArticle) return
  exportingMarkdown.value = true
  try {
    const blob = await rssApi.exportArticleMarkdown(store.selectedArticle.id)
    triggerBrowserDownload(blob, `${safeFilename(store.selectedArticle.title)}.md`)
  } finally {
    exportingMarkdown.value = false
  }
}

async function exportDigest() {
  if (!store.selectedArticle) return
  exportingMarkdown.value = true
  try {
    const data = await rssApi.exportBatchDigestMarkdown({
      article_ids: [store.selectedArticle.id],
      include_summary: true,
      include_note: true
    })
    const blob = new Blob([data.markdown], { type: 'text/markdown;charset=utf-8' })
    triggerBrowserDownload(blob, data.filename)
  } finally {
    exportingMarkdown.value = false
  }
}

async function refreshArticleContent() {
  if (!store.selectedArticle) return
  if (fullTextEnabled.value) {
    fullTextEnabled.value = false
    fulltextHint.value = '已切回摘要视图。'
    return
  }
  const current = store.selectedArticle
  if (hasSubstantialFullText(current)) {
    fullTextEnabled.value = true
    fulltextHint.value = '已切换到当前保存的全文版本。'
    return
  }
  refreshingArticleContent.value = true
  try {
    const updated = await rssApi.refreshArticleContent(store.selectedArticle.id)
    store.replaceArticle(updated)
    if (hasSubstantialFullText(updated)) {
      fullTextEnabled.value = true
      fulltextHint.value = '已加载更完整的正文内容。'
      ElMessage.success('已切换到全文')
    } else {
      fullTextEnabled.value = false
      fulltextHint.value = '当前来源暂时只提取到了摘要级内容。'
      ElMessage.warning('这篇文章目前还没有提取到更完整的正文')
    }
  } catch (error) {
    fullTextEnabled.value = false
    fulltextHint.value = '当前来源暂时不支持补全更完整的正文。'
    ElMessage.error('补全文失败')
  } finally {
    refreshingArticleContent.value = false
  }
}

function beginMultiExportMode() {
  ElMessage.info('批量导出入口已保留，后续可以继续细化交互。')
}

function handleArticleClick(articleId: number) {
  closeFeedManager()
  void store.selectArticle(articleId)
}

function handleExportCommand(command: string) {
  if (command === 'digest') void exportDigest()
  if (command === 'markdown') void exportMarkdown()
}

function handleListMenuCommand(command: string) {
  if (command === 'sync') void syncAll()
  if (command === 'batch-export') beginMultiExportMode()
  if (command === 'sort:newest') store.setArticleSortOrder('newest')
  if (command === 'sort:oldest') store.setArticleSortOrder('oldest')
  if (command === 'toggle:thumbnails') store.setShowThumbnails(!store.showThumbnails)
  if (command === 'unsubscribe') void unsubscribeCurrentFeed()
}

function handleFeedSectionCommand(command: string) {
  if (command === 'manage-feeds') openFeedManager()
  if (command === 'sync-feeds') void syncAll()
}

async function unsubscribeCurrentFeed() {
  const feed = activeFeedForMenu.value
  if (!feed) return
  await rssApi.deleteFeed(feed.id)
  await store.loadAll()
  activeFeedId.value = null
}

function decreaseSummaryLines() {
  store.setSummaryLineCount(Math.max(1, store.summaryLineCount - 1))
}

function increaseSummaryLines() {
  store.setSummaryLineCount(Math.min(5, store.summaryLineCount + 1))
}

function togglePinnedSelected() {
  if (!store.selectedArticle) return
  store.togglePinned(store.selectedArticle.id)
}

function hasSubstantialFullText(article: Article) {
  const html = article.cleaned_html?.trim() || ''
  if (!html) return false
  const summaryLength = (article.summary || '').trim().length
  const textLength = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().length
  return textLength > Math.max(summaryLength + 80, 220)
}

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function safeFilename(name: string) {
  return name.replace(/[\\/:*?"<>|]/g, '_').slice(0, 80) || 'article'
}

function escapeHtml(value: string) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

async function runSummary() {
  if (!store.selectedArticle) return
  const data = await rssApi.summary(store.selectedArticle.id)
  aiResult.value = data.result
}

async function runTranslate() {
  if (!store.selectedArticle) return
  const data = await rssApi.translate(store.selectedArticle.id)
  aiResult.value = data.result
}

async function syncAll() {
  const report = await rssApi.syncAll()
  await store.loadAll()
  ElMessage.success(`同步完成：${report.success} 个成功`)
}

function exportNote() {
  if (!store.selectedArticle) return
  const filename = `${safeFilename(store.selectedArticle.title)}-note.md`
  const content = note.value?.trim() ? note.value : ''
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  triggerBrowserDownload(blob, filename)
}
</script>

<style scoped>
.reader-shell {
  position: relative;
}

.sidebar-panel {
  padding: 10px 14px 16px;
  background: color-mix(in srgb, var(--app-surface-strong) 38%, var(--app-bg) 62%);
  border-color: color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 0;
  border-width: 0 1px 0 0;
  box-shadow: none;
  overflow: hidden;
}

.sidebar-header {
  position: sticky;
  top: 0;
  z-index: 2;
  margin: -10px -14px 8px;
  padding: 12px 14px 10px;
  background: color-mix(in srgb, var(--app-surface-strong) 70%, var(--app-bg) 30%);
  border-bottom: 1px solid color-mix(in srgb, var(--app-border) 68%, transparent 32%);
}

.sidebar-header h2,
.article-list-header h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
}

.sidebar-static-filters,
.sidebar-group-content {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
}

.sidebar-primary-link,
.sidebar-filter-button,
.sidebar-feed-button,
.sidebar-group-toggle {
  width: 100%;
  border: 0;
  border-radius: 12px;
  padding: 10px 11px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
}

.sidebar-primary-link.active,
.sidebar-filter-button.active,
.sidebar-feed-button.active {
  background: color-mix(in srgb, var(--theme-accent) 16%, var(--app-surface) 84%);
}

.sidebar-group-toggle {
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  margin-bottom: 8px;
}

.sidebar-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.sidebar-section-title {
  font-size: 15px;
  font-weight: 800;
}

.sidebar-section-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.sidebar-section-action {
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 10px;
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  color: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.sidebar-feed-list {
  margin-bottom: 0;
  overflow: hidden;
}

.sidebar-chevron {
  transition: transform 0.25s ease;
}

.sidebar-chevron.expanded {
  transform: rotate(90deg);
}

.sidebar-filter-count {
  min-width: 26px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-border) 72%, var(--app-surface) 28%);
  font-size: 12px;
  text-align: center;
}

.tag-create-row {
  display: grid;
  grid-template-columns: 1fr 46px auto;
  gap: 8px;
}

.tag-color-input {
  width: 46px;
  height: 32px;
  border: 1px solid color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  border-radius: 10px;
  background: transparent;
  padding: 2px;
}

.tag-filter-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.sidebar-feed-button {
  width: 100%;
  border: 0;
  border-radius: 14px;
  padding: 9px 10px;
  background: transparent;
  color: inherit;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  overflow: hidden;
}

.sidebar-feed-mark {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--theme-accent) 74%, white 26%);
  color: white;
  display: grid;
  place-items: center;
  font-weight: 800;
  flex: 0 0 auto;
}

.sidebar-feed-name {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}

.article-list-panel {
  overflow-x: hidden;
  background: color-mix(in srgb, var(--app-surface-strong) 38%, var(--app-bg) 62%);
  border-color: color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 0;
  border-width: 0 1px 0 0;
  box-shadow: none;
  padding: 16px 14px 20px;
}

.article-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.article-list-topbar-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.list-menu-button {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 12px;
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.article-card {
  margin-bottom: 8px;
  border: 1px solid color-mix(in srgb, var(--app-border) 74%, transparent 26%);
  border-radius: 16px;
  padding: 10px 12px;
  background: color-mix(in srgb, var(--app-surface-strong) 94%, var(--app-bg) 6%);
  cursor: pointer;
  min-height: 96px;
  overflow: hidden;
  transition: all 0.24s ease;
}

.article-card.active {
  background: color-mix(in srgb, var(--theme-accent) 14%, var(--app-surface) 86%);
  border-color: color-mix(in srgb, var(--theme-accent) 36%, var(--app-border) 64%);
}

.article-card-meta-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 76px;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  color: color-mix(in srgb, currentColor 52%, transparent 48%);
  font-size: 11px;
}

.article-card-source {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article-card-date {
  text-align: right;
  line-height: 1.25;
}

.article-card-main {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.article-card-main.with-thumbnail {
  grid-template-columns: minmax(0, 1fr) 68px;
  align-items: start;
}

.article-card-copy h3 {
  margin: 0 0 4px;
  font-size: 14px;
  line-height: 1.35;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.article-card-summary {
  margin: 0 0 7px;
  color: color-mix(in srgb, currentColor 66%, transparent 34%);
  font-size: 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.article-card-thumb {
  width: 68px;
  height: 68px;
  border-radius: 12px;
  overflow: hidden;
  justify-self: end;
}

.article-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.reader-detail-panel {
  background: color-mix(in srgb, var(--app-surface-strong) 94%, white 6%);
  border-color: color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  border-radius: 0;
  border-width: 0;
  box-shadow: none;
  padding: 18px 24px 24px;
}

:global(body.theme-dark) .reader-detail-panel {
  background: color-mix(in srgb, var(--app-surface-strong) 96%, black 4%);
}

.detail-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.toolbar-icon-button {
  width: 40px;
  min-width: 40px;
  height: 40px;
  padding: 0;
  --el-button-bg-color: color-mix(in srgb, var(--theme-accent) 18%, var(--app-surface) 82%);
  --el-button-border-color: color-mix(in srgb, var(--theme-accent) 24%, var(--app-border) 76%);
  --el-button-text-color: color-mix(in srgb, currentColor 88%, #435b84 12%);
  --el-button-hover-bg-color: color-mix(in srgb, var(--theme-accent) 28%, var(--app-surface-strong) 72%);
  --el-button-hover-border-color: color-mix(in srgb, var(--theme-accent) 42%, var(--app-border) 58%);
  --el-button-hover-text-color: inherit;
}

:deep(.toolbar-icon-button.active) {
  --el-button-bg-color: color-mix(in srgb, var(--theme-accent) 24%, var(--app-surface) 76%);
  --el-button-border-color: color-mix(in srgb, var(--theme-accent) 46%, var(--app-border) 54%);
  --el-button-text-color: color-mix(in srgb, var(--theme-accent) 82%, currentColor 18%);
}

.export-trigger {
  --el-button-bg-color: color-mix(in srgb, var(--theme-accent) 18%, var(--app-surface) 82%);
  --el-button-border-color: color-mix(in srgb, var(--theme-accent) 24%, var(--app-border) 76%);
  --el-button-text-color: color-mix(in srgb, currentColor 88%, #435b84 12%);
  --el-button-hover-bg-color: color-mix(in srgb, var(--theme-accent) 28%, var(--app-surface-strong) 72%);
  --el-button-hover-border-color: color-mix(in srgb, var(--theme-accent) 42%, var(--app-border) 58%);
}

.tag-popover-body {
  display: grid;
  gap: 10px;
}

.tag-selection-list {
  display: grid;
  gap: 8px;
  max-height: 220px;
  overflow: auto;
}

.tag-selection-item {
  width: 100%;
  border: 0;
  border-radius: 14px;
  padding: 14px 16px;
  background: color-mix(in srgb, var(--app-surface-strong) 90%, var(--app-bg) 10%);
  color: inherit;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-selection-item.active {
  background: color-mix(in srgb, var(--theme-accent) 14%, var(--app-surface) 86%);
}

.tag-selection-main {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
}

.tag-creator-card {
  padding-top: 10px;
  border-top: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
}

.dropdown-inline-control {
  padding: 10px 16px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dropdown-inline-label {
  color: color-mix(in srgb, currentColor 60%, transparent 40%);
  font-size: 13px;
  font-weight: 700;
}

.dropdown-inline-stepper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.stepper-button {
  width: 26px;
  height: 26px;
  border: 1px solid color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  color: color-mix(in srgb, currentColor 80%, transparent 20%);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.stepper-value {
  min-width: 18px;
  text-align: center;
  color: inherit;
  font-size: 14px;
  font-weight: 700;
}

.reader-inline-alert {
  margin-top: 14px;
}

.reader-title-link {
  color: inherit;
  text-decoration: none;
}

.reader-title-link:hover {
  text-decoration: underline;
}

.note-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
  margin-bottom: 12px;
}

.note-export-button {
  min-width: 96px;
}

.note-actions :deep(.el-button) {
  min-width: 112px;
  height: 42px;
  border-radius: 12px;
}

.note-actions :deep(.el-button--primary),
.note-export-button {
  --el-button-bg-color: var(--theme-accent);
  --el-button-border-color: color-mix(in srgb, var(--theme-accent) 74%, var(--app-border) 26%);
  --el-button-text-color: #ffffff;
  --el-button-hover-bg-color: color-mix(in srgb, var(--theme-accent) 86%, white 14%);
  --el-button-hover-border-color: color-mix(in srgb, var(--theme-accent) 86%, white 14%);
  --el-button-active-bg-color: color-mix(in srgb, var(--theme-accent) 74%, black 26%);
  --el-button-active-border-color: color-mix(in srgb, var(--theme-accent) 74%, black 26%);
}

.button-icon-right {
  margin-left: 6px;
}

.feed-manager-overlay {
  grid-column: 2 / 4;
  grid-row: 1;
  align-self: stretch;
  z-index: 4;
  margin: 0;
  border-radius: 0;
  border-width: 0;
  background: color-mix(in srgb, var(--app-bg) 90%, var(--app-surface) 10%);
  padding: 14px;
  overflow: auto;
  box-shadow: none;
}

:deep(.article-card-tags .el-tag) {
  border-radius: 999px;
}

:deep(.article-card-tags .el-tag),
:deep(.toolbar-tag-select .el-tag) {
  border-color: color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  color: inherit;
}

@media (max-width: 1200px) {
  .article-card-main.with-thumbnail {
    grid-template-columns: 1fr 64px;
  }

  .article-card-thumb {
    width: 64px;
    height: 64px;
  }
}

@media (max-width: 960px) {
  .article-list-header {
    align-items: center;
  }

  .feed-manager-overlay {
    grid-column: 1;
  }
}
</style>
