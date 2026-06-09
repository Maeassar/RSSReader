<template>
  <div class="search-view">
    <div class="search-header">
      <el-input
        v-model="query"
        placeholder="搜索文章标题、内容..."
        clearable
        size="large"
        class="search-input"
        :prefix-icon="Search"
        @keyup.enter="doSearch"
        @clear="clearResults"
      />
      <el-button type="primary" size="large" :loading="loading" @click="doSearch">搜索</el-button>
    </div>

    <div v-if="searched && !loading" class="search-meta">
      <span v-if="results.length > 0">找到 {{ results.length }} 条结果</span>
      <span v-else class="no-results">未找到相关文章</span>
    </div>

    <div v-if="loading" class="search-skeleton">
      <el-skeleton :rows="4" animated v-for="i in 3" :key="i" class="skeleton-item" />
    </div>

    <el-scrollbar v-else class="results-scrollbar">
      <div class="results-list">
        <div
          v-for="item in results"
          :key="item.id"
          class="result-card"
          @click="openArticle(item.id)"
        >
          <div class="result-meta">
            <span class="feed-title">{{ item.feed_title }}</span>
            <span v-if="item.published_at" class="pub-date">{{ formatDate(item.published_at) }}</span>
            <el-tag v-if="item.is_starred" size="small" type="warning" class="tag-badge">收藏</el-tag>
            <el-tag v-if="!item.is_read" size="small" type="primary" class="tag-badge">未读</el-tag>
          </div>

          <h3
            class="result-title"
            v-html="item.title_snippet || item.title"
          />

          <p
            v-if="item.summary_snippet || item.content_snippet"
            class="result-snippet"
            v-html="item.summary_snippet || item.content_snippet"
          />

          <div class="result-footer">
            <span class="open-hint">点击打开文章 →</span>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { rssApi, type SearchResult } from '../api/client'

defineOptions({ name: 'SearchView' })

const router = useRouter()
const query = ref('')
const results = ref<SearchResult[]>([])
const loading = ref(false)
const searched = ref(false)

async function doSearch() {
  const q = query.value.trim()
  if (!q) return
  loading.value = true
  searched.value = false
  try {
    results.value = await rssApi.search(q)
    searched.value = true
  } catch {
    results.value = []
    searched.value = true
  } finally {
    loading.value = false
  }
}

function clearResults() {
  results.value = []
  searched.value = false
}

function openArticle(id: number) {
  router.push({ path: '/', query: { article: id } })
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.search-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
}

.search-header {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
}

.search-meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.no-results {
  color: var(--el-text-color-placeholder);
}

.search-skeleton {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-item {
  padding: 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}

.results-scrollbar {
  flex: 1;
  min-height: 0;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 24px;
}

.result-card {
  padding: 16px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-surface);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.result-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.feed-title {
  font-size: 12px;
  color: var(--el-color-primary);
  font-weight: 500;
}

.pub-date {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.tag-badge {
  line-height: 1;
}

.result-title {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.4;
}

.result-snippet {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Highlight matched terms from FTS5 snippet() */
:deep(mark) {
  background-color: #fff3a3;
  color: inherit;
  border-radius: 2px;
  padding: 0 1px;
}

.result-footer {
  margin-top: 8px;
}

.open-hint {
  font-size: 12px;
  color: var(--el-color-primary);
  opacity: 0;
  transition: opacity 0.15s;
}

.result-card:hover .open-hint {
  opacity: 1;
}
</style>

<style>
body.theme-dark .result-title {
  color: #e8eaed;
}

body.theme-dark .result-snippet,
body.theme-dark .result-footer .open-hint,
body.theme-dark .pub-date,
body.theme-dark .search-meta,
body.theme-dark .no-results {
  color: #9aa4b2;
}

body.theme-dark .result-card :deep(mark) {
  background-color: #4a4200;
  color: #ffe066;
}
</style>
