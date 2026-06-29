<template>
  <div class="stats-page">
<!--    <div class="page-title">-->
<!--      <h1>统计日志</h1>-->
<!--    </div>-->
    <div class="stats-grid">
      <section class="panel stats-summary-panel">
        <div class="stats-panel-head">
          <span class="stats-panel-title">流量统计</span>
          <el-button text :icon="collapsed ? ArrowDown : ArrowUp" @click="collapsed = !collapsed" />
        </div>

        <template v-if="!collapsed">
          <div class="stats-controls">
            <div class="stats-range-tabs">
              <button
                v-for="opt in rangeOptions"
                :key="opt.value"
                class="range-tab"
                :class="{ active: trafficRange === opt.value }"
                @click="selectTrafficRange(opt.value)"
              >{{ opt.label }}</button>
              <el-button :icon="Refresh" text @click="loadTrafficStats" />
            </div>
            <div class="stats-controls-right">
              <el-select
                v-if="modelOptions.length > 1"
                v-model="selectedModel"
                size="small"
                style="width: 160px"
                placement="bottom-start"
                :fallback-placements="[]"
                :teleported="false"
                @change="loadTrafficStats"
              >
                <el-option label="全部模型" value="" />
                <el-option
                  v-for="opt in modelOptions"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                >
                  <div class="model-option">
                    <span class="model-option-label">{{ opt.label }}</span>
                    <span class="model-option-delete" title="删除此模型的统计记录" @click.stop="confirmDeleteModel(opt)">×</span>
                  </div>
                </el-option>
              </el-select>
              <div class="chart-mode-toggle">
                <button :class="{ active: chartMode === 'calls' }" @click="chartMode = 'calls'">请求次数</button>
                <button :class="{ active: chartMode === 'tokens' }" @click="chartMode = 'tokens'">TOKEN</button>
              </div>
            </div>
          </div>

          <div class="stats-cards">
            <div class="stats-card">
              <div class="stats-card-label">总请求</div>
              <div class="stats-card-value">{{ stats.total_calls ?? 0 }}</div>
            </div>
            <div class="stats-card">
              <div class="stats-card-label">输入 Token</div>
              <div class="stats-card-value">{{ formatTokens(stats.input_tokens) }}</div>
            </div>
            <div class="stats-card">
              <div class="stats-card-label">输出 Token</div>
              <div class="stats-card-value">{{ formatTokens(stats.output_tokens) }}</div>
            </div>
          </div>

          <div class="stats-chart-wrap">
            <Bar :data="chartData" :options="chartOptions" />
          </div>
        </template>
      </section>
      <section class="panel stats-log-panel">
        <div class="stats-panel-head">
          <div>
            <h2>同步日志</h2>
            <p class="muted">{{ logRangeLabel }}的同步记录与结果</p>
          </div>
          <div class="stats-range-tabs compact">
            <button
              v-for="opt in rangeOptions"
              :key="`logs-${opt.value}`"
              class="range-tab"
              :class="{ active: logRange === opt.value }"
              @click="selectLogRange(opt.value)"
            >{{ opt.label }}</button>
          </div>
        </div>
        <div class="stats-log-scroll">
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
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, ArrowUp, Refresh } from '@element-plus/icons-vue'
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js'
import { computed, onMounted, ref, watch } from 'vue'
import { Bar } from 'vue-chartjs'
import type { LLMTimeseriesBucket, StatsRange, SyncLog } from '../api/client'
import { rssApi } from '../api/client'
import { statusTagType, syncSuggestion } from '../utils/syncDiagnostics'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const collapsed = ref(false)
const trafficRange = ref<StatsRange>('today')
const logRange = ref<StatsRange>('today')
const chartMode = ref<'calls' | 'tokens'>('calls')
const selectedModel = ref('')
const stats = ref<Record<string, any>>({})
const timeseries = ref<LLMTimeseriesBucket[]>([])
const logs = ref<SyncLog[]>([])

const rangeOptions: { label: string; value: StatsRange }[] = [
  { label: '今天', value: 'today' },
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' },
  { label: '全部', value: 'all' },
]

const modelOptions = computed(() => {
  const rows: any[] = stats.value.by_provider ?? []
  return rows.map((r) => ({
    label: `${r.provider} / ${r.model}`,
    value: `${r.provider}\t${r.model}`,
    provider: r.provider,
    model: r.model,
  }))
})

function parseSelectedModel(): { provider?: string; model?: string } {
  if (!selectedModel.value) return {}
  const [provider, model] = selectedModel.value.split('\t')
  return { provider, model }
}

async function loadStats() {
  stats.value = await rssApi.llmStats(trafficRange.value, parseSelectedModel())
}
async function loadTimeseries() {
  timeseries.value = await rssApi.llmTimeseries(trafficRange.value, parseSelectedModel())
}
async function loadTrafficStats() {
  await Promise.all([loadStats(), loadTimeseries()])
}
async function loadAll() {
  await Promise.all([loadTrafficStats(), loadSyncLogs()])
}
async function loadSyncLogs() {
  logs.value = await rssApi.syncLogs(logRange.value)
}

async function confirmDeleteModel(opt: { label: string; value: string; provider: string; model: string }) {
  try {
    await ElMessageBox.confirm(
      `删除「${opt.label}」的所有统计记录？此操作不可撤销。`,
      '删除统计记录',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await rssApi.deleteModelStats(opt.provider, opt.model)
    if (selectedModel.value === opt.value) selectedModel.value = ''
    await loadTrafficStats()
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

function selectTrafficRange(range: StatsRange) {
  trafficRange.value = range
}
function selectLogRange(range: StatsRange) {
  logRange.value = range
}

watch(trafficRange, () => {
  loadTrafficStats()
})

watch(selectedModel, () => {
  loadTrafficStats()
})

watch(logRange, () => {
  loadSyncLogs()
})

onMounted(loadAll)

function formatTokens(n: number | undefined): string {
  if (!n) return '0'
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`
  return String(n)
}

const logRangeLabel = computed(() => rangeOptions.find((opt) => opt.value === logRange.value)?.label ?? '全部')

const chartData = computed(() => {
  const labels = timeseries.value.map((b) => b.time_label)
  if (chartMode.value === 'calls') {
    return {
      labels,
      datasets: [
        {
          label: '请求次数',
          data: timeseries.value.map((b) => b.calls),
          backgroundColor: 'rgba(239, 100, 97, 0.75)',
          hoverBackgroundColor: 'rgba(239, 100, 97, 1)',
          borderRadius: 6,
          borderSkipped: false,
          barPercentage: 0.5,
          categoryPercentage: 0.6,
        },
      ],
    }
  }
  return {
    labels,
    datasets: [
      {
        label: '输入 Token',
        data: timeseries.value.map((b) => b.input_tokens),
        backgroundColor: 'rgba(99, 102, 241, 0.75)',
        hoverBackgroundColor: 'rgba(99, 102, 241, 1)',
        borderRadius: 6,
        borderSkipped: false,
        barPercentage: 0.5,
        categoryPercentage: 0.6,
      },
      {
        label: '输出 Token',
        data: timeseries.value.map((b) => b.output_tokens),
        backgroundColor: 'rgba(52, 211, 153, 0.75)',
        hoverBackgroundColor: 'rgba(52, 211, 153, 1)',
        borderRadius: 6,
        borderSkipped: false,
        barPercentage: 0.5,
        categoryPercentage: 0.6,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: chartMode.value === 'tokens', align: 'end' as const },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      filter: (item: any) => {
        const data = item.chart.data.datasets.reduce(
          (sum: number, ds: any) => sum + ((ds.data[item.dataIndex] as number) || 0),
          0
        )
        return data > 0
      },
      callbacks: chartMode.value === 'calls'
        ? {
            afterBody: (items: any[]) => {
              if (!items.length) return []
              const idx = items[0].dataIndex
              const bucket = timeseries.value[idx]
              if (!bucket || !bucket.failed_calls) return []
              const pct = ((bucket.failed_calls / bucket.calls) * 100).toFixed(1)
              return [`请求异常: ${bucket.failed_calls} (${pct}%)`]
            },
          }
        : {},
    },
  },
  scales: {
    x: {
      grid: { display: false },
      border: { display: false },
      ticks: {
        font: { size: 11 },
        color: '#9ca3af',
        maxTicksLimit: trafficRange.value === 'today' ? 8 : undefined,
      },
    },
    y: {
      beginAtZero: true,
      border: { display: false, dash: [4, 4] },
      grid: { color: 'rgba(0,0,0,0.06)', lineWidth: 1 },
      ticks: { precision: 0, font: { size: 11 }, color: '#9ca3af' },
    },
  },
}))

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
  min-width: 0;
  overflow-x: hidden;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.stats-summary-panel,
.stats-log-panel {
  border-radius: 20px;
  min-width: 0;
}

.stats-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.stats-panel-title {
  font-size: 18px;
  font-weight: 800;
}

.stats-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 14px;
  gap: 8px;
}

.stats-range-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stats-range-tabs.compact {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.stats-range-tabs.compact .range-tab {
  padding: 3px 10px;
}

.range-tab {
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid var(--app-border);
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: var(--el-text-color-regular);
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.range-tab.active {
  background: var(--el-color-primary);
  color: #fff;
  border-color: var(--el-color-primary);
}

.chart-mode-toggle {
  display: flex;
  border: 1px solid var(--app-border);
  border-radius: 6px;
  overflow: hidden;
}

.chart-mode-toggle button {
  padding: 4px 14px;
  font-size: 13px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--el-text-color-regular);
  transition: background 0.15s, color 0.15s;
}

.chart-mode-toggle button.active {
  background: var(--el-color-primary);
  color: #fff;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 14px;
}

.stats-card {
  border: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 10px;
  padding: 6px 10px;
  background: color-mix(in srgb, var(--app-surface-strong) 94%, var(--app-bg) 6%);
  text-align: center;
}

.stats-card-label {
  color: #7a8799;
  font-size: 11px;
  font-weight: 600;
}

.stats-card-value {
  margin-top: 2px;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.stats-controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 4px;
}

.model-option-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-option-delete {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  transition: background 0.15s, color 0.15s;
}

.model-option-delete:hover {
  background: color-mix(in srgb, #f4b6b6 80%, white 20%);
  color: #8f2f2f;
}

.stats-chart-wrap {
  height: 220px;
  position: relative;
}

.stats-panel-head {
  margin-bottom: 0;
}

.stats-log-panel {
  border-radius: 20px;
}

.stats-log-scroll {
  max-height: min(560px, calc(100vh - 360px));
  min-height: 220px;
  overflow-y: auto;
  padding: 6px 8px 0 0;
  scrollbar-gutter: stable;
}

.stats-panel-head h2 {
  margin: 0 0 4px;
  font-size: 20px;
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

  .stats-cards {
    grid-template-columns: 1fr;
  }

  .stats-log-scroll {
    max-height: 420px;
  }
}
</style>
