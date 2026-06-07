<template>
  <div class="stats-page">
    <div class="page-title">
      <h1>统计日志</h1>
      <el-button class="stats-refresh-button" :icon="Refresh" @click="load">刷新</el-button>
    </div>
    <div class="stats-grid">
      <section class="panel stats-summary-panel">
        <div class="stats-panel-head">
          <h2>LLM 用量统计</h2>
          <p class="muted">当前 AI 功能的调用与 Token 消耗概览</p>
        </div>
        <div class="stats-cards">
          <div class="stats-card">
            <div class="stats-card-label">调用次数</div>
            <div class="stats-card-value">{{ stats.total_calls || 0 }}</div>
          </div>
          <div class="stats-card">
            <div class="stats-card-label">输入 Token</div>
            <div class="stats-card-value">{{ stats.input_tokens || 0 }}</div>
          </div>
          <div class="stats-card">
            <div class="stats-card-label">输出 Token</div>
            <div class="stats-card-value">{{ stats.output_tokens || 0 }}</div>
          </div>
        </div>
      </section>
      <section class="panel stats-log-panel">
        <div class="stats-panel-head">
          <h2>同步日志</h2>
          <p class="muted">最近的同步记录与结果</p>
        </div>
        <el-empty v-if="!logs.length" description="还没有同步日志" />
        <el-timeline v-else class="stats-timeline">
          <el-timeline-item
            v-for="log in logs"
            :key="log.id"
            :timestamp="formatLogTime(log.created_at)"
            :type="statusTagType(log.status)"
          >
            <div class="stats-log-item">
              <div class="stats-log-main">
                <div class="stats-log-title">{{ log.feed_title || log.url || '未关联订阅源' }}</div>
                <div v-if="log.url" class="stats-log-url">{{ log.url }}</div>
                <div class="stats-log-message">{{ log.message }}</div>
                <div v-if="log.status === 'failed'" class="stats-log-suggestion">{{ syncSuggestion(log.message) }}</div>
              </div>
              <div class="stats-log-status" :class="log.status">{{ statusLabel(log.status) }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import type { SyncLog } from '../api/client'
import { rssApi } from '../api/client'
import { statusTagType, syncSuggestion } from '../utils/syncDiagnostics'

const stats = ref<Record<string, any>>({})
const logs = ref<SyncLog[]>([])

onMounted(load)

async function load() {
  stats.value = await rssApi.llmStats()
  logs.value = await rssApi.syncLogs()
}

function formatLogTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    success: '成功',
    failed: '失败',
    pending: '待同步'
  }
  return labels[status] || status
}
</script>

<style scoped>
.stats-page {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 16px;
}

.stats-summary-panel,
.stats-log-panel {
  border-radius: 20px;
}

.stats-panel-head {
  margin-bottom: 16px;
}

.stats-panel-head h2 {
  margin: 0 0 4px;
  font-size: 20px;
}

.stats-cards {
  display: grid;
  gap: 12px;
}

.stats-card {
  border: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 18px;
  padding: 16px;
  background: color-mix(in srgb, var(--app-surface-strong) 94%, var(--app-bg) 6%);
}

.stats-card-label {
  color: #7a8799;
  font-size: 13px;
  font-weight: 700;
}

.stats-card-value {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.stats-timeline {
  padding-top: 6px;
}

.stats-log-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.stats-log-main {
  min-width: 0;
}

.stats-log-title {
  font-weight: 800;
  line-height: 1.5;
}

.stats-log-url,
.stats-log-suggestion {
  color: #7a8799;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-all;
}

.stats-log-message {
  line-height: 1.6;
  word-break: break-word;
}

.stats-log-status {
  flex: 0 0 auto;
  min-width: 64px;
  padding: 3px 10px;
  border-radius: 999px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  text-transform: capitalize;
  background: color-mix(in srgb, var(--app-border) 66%, var(--app-surface) 34%);
}

.stats-log-status.success {
  background: color-mix(in srgb, #a7efc0 72%, white 28%);
  color: #21633a;
}

.stats-log-status.failed,
.stats-log-status.error,
.stats-log-status.danger {
  background: color-mix(in srgb, #f4b6b6 76%, white 24%);
  color: #8f2f2f;
}

@media (max-width: 960px) {
  .stats-page {
    padding: 14px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
