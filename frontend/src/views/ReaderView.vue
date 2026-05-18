<template>
  <div class="reader-grid" v-loading="store.loading">
    <section class="panel scroll-panel">
      <h2>订阅与筛选</h2>
      <el-button class="filter-button" text @click="loadArticles()">全部文章</el-button>
      <el-button class="filter-button" text @click="loadArticles({ unread: true })">未读文章</el-button>
      <el-button class="filter-button" text @click="loadArticles({ starred: true })">收藏文章</el-button>
      <el-divider />
      <h3>订阅源</h3>
      <el-button v-for="feed in store.feeds" :key="feed.id" class="filter-button" text @click="loadArticles({ feed_id: feed.id })">
        {{ feed.title }}
      </el-button>
      <el-divider />
      <h3>标签</h3>
      <el-tag v-for="tag in store.tags" :key="tag.id" class="tag-filter" :color="tag.color" effect="dark" @click="loadArticles({ tag_id: tag.id })">
        {{ tag.name }}
      </el-tag>
    </section>

    <section class="panel scroll-panel">
      <div class="toolbar">
        <el-button :icon="Refresh" @click="syncAll">同步全部</el-button>
      </div>
      <article
        v-for="article in store.articles"
        :key="article.id"
        class="article-item"
        :class="{ active: store.selectedArticle?.id === article.id }"
        @click="store.selectArticle(article.id)"
      >
        <h3>{{ article.title }}</h3>
        <p class="muted">{{ article.feed_title }} · {{ article.summary }}</p>
        <el-tag v-if="!article.is_read" size="small">未读</el-tag>
        <el-tag v-if="article.is_starred" size="small" type="warning">收藏</el-tag>
      </article>
    </section>

    <section class="panel scroll-panel" v-if="store.selectedArticle">
      <div class="toolbar">
        <el-button :icon="Check" @click="store.toggleRead(store.selectedArticle)">
          {{ store.selectedArticle.is_read ? '标记未读' : '标记已读' }}
        </el-button>
        <el-button :icon="Star" @click="store.toggleStar(store.selectedArticle)">
          {{ store.selectedArticle.is_starred ? '取消收藏' : '收藏' }}
        </el-button>
        <el-button :icon="MagicStick" @click="runSummary">生成摘要</el-button>
        <el-button :icon="Switch" @click="runTranslate">翻译</el-button>
      </div>
      <h1>{{ store.selectedArticle.title }}</h1>
      <p class="muted">{{ store.selectedArticle.author }} · {{ store.selectedArticle.url }}</p>
      <div class="article-body" v-html="store.selectedArticle.cleaned_html"></div>
      <el-alert v-if="aiResult" :title="aiResult" type="success" show-icon :closable="false" />
      <el-divider />
      <h2>笔记</h2>
      <el-input v-model="note" type="textarea" :rows="6" placeholder="写下这篇文章的 Markdown 笔记" />
      <div class="toolbar">
        <el-button type="primary" @click="saveNote">保存笔记</el-button>
        <el-button tag="a" :href="`/api/export/articles/${store.selectedArticle.id}/markdown`" target="_blank">导出 Markdown</el-button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Check, MagicStick, Refresh, Star, Switch } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref, watch } from 'vue'
import { rssApi } from '../api/client'
import { useReaderStore } from '../stores/reader'

const store = useReaderStore()
const note = ref('')
const aiResult = ref('')

onMounted(async () => {
  await store.loadAll()
  await loadNote()
})

watch(() => store.selectedArticle?.id, loadNote)

async function loadArticles(params?: Record<string, unknown>) {
  store.articles = await rssApi.articles(params)
  store.selectedArticle = store.articles[0] ?? null
}

async function loadNote() {
  if (!store.selectedArticle) return
  const data = await rssApi.note(store.selectedArticle.id)
  note.value = data.content_markdown
  aiResult.value = ''
}

async function saveNote() {
  if (!store.selectedArticle) return
  await rssApi.saveNote(store.selectedArticle.id, note.value)
  ElMessage.success('笔记已保存到 Mock Repository')
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
  await rssApi.syncAll()
  ElMessage.success('Mock 同步已触发')
}
</script>

<style scoped>
.filter-button {
  width: 100%;
  justify-content: flex-start;
  margin: 2px 0;
}

.tag-filter {
  margin: 4px;
  cursor: pointer;
}
</style>

