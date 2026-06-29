<template>
  <div class="ask-view">
    <div class="ask-header">
      <h2 class="ask-title">AI 问答</h2>
      <p class="ask-subtitle">用自然语言提问，从你的订阅文章中找答案</p>
    </div>

    <div class="ask-input-row">
      <el-input
        v-model="question"
        type="textarea"
        :rows="2"
        placeholder="例如：最近有哪些关于 AI Agent 的文章？总结一下过去一周的技术趋势。"
        resize="none"
        @keydown.enter.ctrl="doAsk"
        @keydown.enter.meta="doAsk"
      />
      <div class="ask-input-actions">
        <span class="ask-hint">Ctrl+Enter 发送</span>
        <el-button type="primary" :loading="loading" @click="doAsk">提问</el-button>
        <el-tooltip content="对订阅文章建立向量索引（首次使用或新增文章后需要执行）" placement="top">
          <el-button :loading="indexing" @click="doIndex">建立索引</el-button>
        </el-tooltip>
      </div>
    </div>

    <div v-if="error" class="ask-error">
      <el-alert :title="error" type="error" :closable="false" />
    </div>

    <div v-if="result" class="ask-result">
      <div class="answer-box">
        <div class="answer-label">回答</div>
        <div class="answer-text" v-html="renderedAnswer" />
      </div>

      <div v-if="result.sources.length > 0" class="sources-box">
        <div class="sources-label">引用来源（{{ result.sources.length }}）</div>
        <div class="sources-list">
          <div
            v-for="(src, i) in result.sources"
            :key="src.id"
            class="source-card"
            @click="openArticle(src.id)"
          >
            <div class="source-index">[{{ i + 1 }}]</div>
            <div class="source-body">
              <div class="source-meta">
                <span class="source-feed">{{ src.feed_title }}</span>
                <span v-if="src.published_at" class="source-date">{{ formatDate(src.published_at) }}</span>
              </div>
              <div class="source-title">{{ src.title }}</div>
              <div v-if="src.snippet" class="source-snippet">{{ src.snippet }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!result && !loading && !error" class="ask-empty">
      <el-icon class="ask-empty-icon"><ChatDotRound /></el-icon>
      <p>提问前请先点击「建立索引」，对已同步的文章建立向量索引</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getErrorMessage } from '../api/client'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { rssApi, type AskResponse } from '../api/client'

defineOptions({ name: 'AskView' })

const router = useRouter()
const question = ref('')
const result = ref<AskResponse | null>(null)
const loading = ref(false)
const indexing = ref(false)
const error = ref('')

async function doAsk() {
  const q = question.value.trim()
  if (!q) return
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await rssApi.ragAsk(q)
  } catch (e: unknown) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function doIndex() {
  indexing.value = true
  try {
    const res = await rssApi.ragIndex()
    if (res.status === 'already_running') {
      ElMessage.info('索引正在进行中，请稍候')
      return
    }
    ElMessage.info('索引已在后台启动，完成后可以开始提问')
    // 轮询直到索引完成
    const poll = setInterval(async () => {
      try {
        const status = await rssApi.ragIndexStatus()
        if (!status.running) {
          clearInterval(poll)
          indexing.value = false
          if (status.error) {
            ElMessage.error(status.error)
          } else {
            const parts = []
            if (status.last_added > 0) parts.push(`新增 ${status.last_added} 篇`)
            if (status.last_removed > 0) parts.push(`删除 ${status.last_removed} 篇`)
            const detail = parts.length > 0 ? `（${parts.join('，')}）` : '（无变化）'
            ElMessage.success(`索引完成 ${detail}`)
          }
        }
      } catch {
        clearInterval(poll)
        indexing.value = false
      }
    }, 2000)
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
    indexing.value = false
  }
}

function openArticle(id: number) {
  router.push({ path: '/', query: { article: id } })
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  })
}

// Simple markdown-like rendering: newlines → <br>, **bold**
const renderedAnswer = computed(() => {
  if (!result.value?.answer) return ''
  return result.value.answer
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
})
</script>

<style scoped>
.ask-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
  gap: 20px;
}

.ask-header {
  flex-shrink: 0;
}

.ask-title {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 600;
}

.ask-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.ask-input-row {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ask-input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: flex-end;
}

.ask-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-right: auto;
}

.ask-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.answer-box {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 16px;
  color: inherit;
}

.answer-label,
.sources-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.answer-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--el-text-color-primary);
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-card {
  display: flex;
  gap: 10px;
  padding: 12px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 8px;
  cursor: pointer;
  color: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.source-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.source-index {
  font-size: 13px;
  font-weight: 700;
  color: var(--el-color-primary);
  flex-shrink: 0;
  padding-top: 1px;
}

.source-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}

.source-feed {
  font-size: 12px;
  color: var(--el-color-primary);
  font-weight: 500;
}

.source-date {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.source-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.source-snippet {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ask-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}

.ask-empty-icon {
  font-size: 48px;
  opacity: 0.3;
}
</style>

<style>
body.theme-dark .ask-title,
body.theme-dark .ask-subtitle,
body.theme-dark .answer-text,
body.theme-dark .answer-label,
body.theme-dark .sources-label,
body.theme-dark .source-title,
body.theme-dark .source-snippet,
body.theme-dark .source-date,
body.theme-dark .ask-hint {
  color: #e8eaed;
}

body.theme-dark .ask-subtitle,
body.theme-dark .answer-label,
body.theme-dark .sources-label,
body.theme-dark .source-snippet,
body.theme-dark .source-date,
body.theme-dark .ask-hint {
  color: #9aa4b2;
}
</style>