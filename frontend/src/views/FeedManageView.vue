<template>
  <div class="feed-manage-page" :class="{ embedded }">
    <div class="page-title feed-manage-header" :class="{ embedded }">
      <div class="feed-manage-title-group">
        <h1>订阅管理</h1>
        <p v-if="embedded" class="feed-manage-subtitle">在当前阅读页直接管理订阅，不跳转整页</p>
      </div>
      <div class="toolbar feed-manage-toolbar">
        <el-button v-if="embedded" class="feed-manage-action" @click="emit('close')">关闭</el-button>
        <el-button
          class="feed-manage-action"
          :icon="Refresh"
          :loading="syncingAll"
          :disabled="syncingAll || syncingFeedId !== null"
          @click="syncAll"
        >
          {{ syncingAll ? '正在同步...' : '同步全部' }}
        </el-button>
        <input
          ref="opmlFileInput"
          class="opml-file-input"
          type="file"
          accept=".opml,.xml"
          multiple
          @change="handleOpmlFilesSelected"
        />
        <el-button class="feed-manage-action" :icon="Upload" :loading="importingOpml" :disabled="isBusy" @click="openOpmlFileDialog">
          OPML 导入
        </el-button>
        <el-button class="feed-manage-action" :disabled="isBusy || feeds.length === 0" @click="selectAllFeeds">全选</el-button>
        <el-button class="feed-manage-action" :disabled="isBusy || selectedFeeds.length === 0" @click="clearFeedSelection">清空</el-button>
        <el-button
          class="feed-manage-action"
          :loading="exportingOpml && exportMode === 'selected'"
          :disabled="isBusy || selectedFeeds.length === 0"
          :icon="Download"
          @click="exportSelectedOpml"
        >
          导出选中
        </el-button>
        <el-button
          class="feed-manage-action"
          :loading="exportingOpml && exportMode === 'all'"
          :disabled="isBusy || feeds.length === 0"
          :icon="Download"
          @click="exportAllOpml"
        >
          导出全部
        </el-button>
        <span class="feed-selected-count">已选 {{ selectedFeeds.length }} 个</span>
      </div>
    </div>
    <section class="panel feed-manage-panel" :class="{ embedded }">
      <el-form class="feed-form" :inline="!embedded" @submit.prevent>
        <el-form-item label="标题">
          <el-input v-model="title" placeholder="可选" />
        </el-form-item>
        <el-form-item label="RSS URL">
          <el-input v-model="url" placeholder="https://example.com/feed.xml" class="url-input" />
        </el-form-item>
        <el-button
          class="feed-submit-button"
          type="primary"
          :loading="addingFeed"
          :disabled="addingFeed || !url"
          @click="addFeed"
        >
          {{ addingFeed ? '正在添加...' : '添加订阅' }}
        </el-button>
      </el-form>

      <section v-if="lastImportReport" class="result-block">
        <div class="result-block-header">
          <h2>OPML 导入结果</h2>
          <span>文件 {{ lastImportReport.files }} 个，新增 {{ lastImportReport.imported }} 个，跳过 {{ lastImportReport.skipped }} 个，失败 {{ lastImportReport.failed }} 个</span>
        </div>
        <el-table :data="lastImportReport.results" size="small" max-height="240" table-layout="fixed">
          <el-table-column prop="source_file" label="文件" min-width="150" show-overflow-tooltip />
          <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
          <el-table-column prop="url" label="URL" min-width="260" show-overflow-tooltip />
          <el-table-column label="状态" width="92">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="原因" min-width="260" show-overflow-tooltip />
        </el-table>
      </section>

      <section v-if="lastSyncReport" class="result-block">
        <div class="result-block-header">
          <h2>同步结果</h2>
          <span>成功 {{ lastSyncReport.success }} 个，失败 {{ lastSyncReport.failed }} 个</span>
          <el-button size="small" text @click="router.push('/stats')">查看同步日志</el-button>
        </div>
        <el-table :data="lastSyncReport.results" size="small" max-height="260" table-layout="fixed">
          <el-table-column prop="title" label="订阅源" min-width="160" show-overflow-tooltip />
          <el-table-column prop="url" label="URL" min-width="260" show-overflow-tooltip />
          <el-table-column label="状态" width="92">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="原因" min-width="260" show-overflow-tooltip />
          <el-table-column label="建议" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ syncSuggestion(row.message) }}</template>
          </el-table-column>
        </el-table>
      </section>

      <el-table
        ref="feedTableRef"
        :data="feeds"
        stripe
        table-layout="fixed"
        class="feed-table"
        @selection-change="handleFeedSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="url" label="URL" min-width="320" show-overflow-tooltip />
        <el-table-column label="最后同步" width="180">
          <template #default="{ row }">
            {{ formatLastSyncAt(row.last_sync_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" :loading="syncingFeedId === row.id" :disabled="isBusy" @click="syncFeed(row.id)">
              {{ syncingFeedId === row.id ? '正在同步...' : '同步' }}
            </el-button>
            <el-popconfirm
              title="确定删除当前订阅吗？"
              confirm-button-text="删除"
              cancel-button-text="取消"
              confirm-button-type="danger"
              @confirm="deleteFeed(row.id)"
            >
              <template #reference>
                <el-button size="small" type="danger" plain :loading="deletingFeedId === row.id" :disabled="isBusy">
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Download, Refresh, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { Feed, FeedSyncReport, OPMLImportReport } from '../api/client'
import { rssApi } from '../api/client'
import { apiErrorMessage, showSyncReportMessage, statusTagType, syncSuggestion } from '../utils/syncDiagnostics'

type FeedTableExpose = {
  clearSelection: () => void
  toggleRowSelection: (row: Feed, selected?: boolean) => void
}

withDefaults(
  defineProps<{
    embedded?: boolean
  }>(),
  {
    embedded: false
  }
)

const emit = defineEmits<{
  close: []
  changed: []
}>()

const router = useRouter()
const feeds = ref<Feed[]>([])
const selectedFeeds = ref<Feed[]>([])
const feedTableRef = ref<FeedTableExpose | null>(null)
const opmlFileInput = ref<HTMLInputElement | null>(null)
const title = ref('')
const url = ref('')
const addingFeed = ref(false)
const syncingAll = ref(false)
const syncingFeedId = ref<number | null>(null)
const deletingFeedId = ref<number | null>(null)
const importingOpml = ref(false)
const exportingOpml = ref(false)
const exportMode = ref<'all' | 'selected' | null>(null)
const lastImportReport = ref<OPMLImportReport | null>(null)
const lastSyncReport = ref<FeedSyncReport | null>(null)
const isBusy = computed(
  () =>
    syncingAll.value ||
    syncingFeedId.value !== null ||
    deletingFeedId.value !== null ||
    importingOpml.value ||
    exportingOpml.value
)

onMounted(loadFeeds)

async function loadFeeds() {
  feeds.value = await rssApi.feeds()
  selectedFeeds.value = selectedFeeds.value.filter((feed) => feeds.value.some((item) => item.id === feed.id))
}

function formatLastSyncAt(value?: string) {
  if (!value) return '未同步'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    hourCycle: 'h23'
  }).formatToParts(date)
  const partMap = Object.fromEntries(parts.map((part) => [part.type, part.value]))

  return `${partMap.year}/${partMap.month}/${partMap.day} ${partMap.hour}:${partMap.minute}:${partMap.second}`
}

async function addFeed() {
  if (!url.value) return
  addingFeed.value = true
  try {
    await rssApi.createFeed({ title: title.value, url: url.value })
    title.value = ''
    url.value = ''
    await loadFeeds()
    emit('changed')
    ElMessage.success('订阅已添加')
  } catch (error) {
    ElMessage.error(createFeedErrorMessage(error))
  } finally {
    addingFeed.value = false
  }
}

async function syncFeed(id: number) {
  const feed = feeds.value.find((item) => item.id === id)
  syncingFeedId.value = id
  try {
    await rssApi.syncFeed(id)
    lastSyncReport.value = null
    await loadFeeds()
    emit('changed')
    ElMessage.success('同步完成')
  } catch (error) {
    const message = apiErrorMessage(error, '同步失败，请稍后重试')
    lastSyncReport.value = {
      total: 1,
      success: 0,
      failed: 1,
      skipped: 0,
      results: [
        {
          feed_id: id,
          url: feed?.url,
          title: feed?.title,
          status: 'failed',
          message,
          feed: null
        }
      ]
    }
    ElMessage.error(message)
  } finally {
    syncingFeedId.value = null
  }
}

async function deleteFeed(id: number) {
  deletingFeedId.value = id
  try {
    await rssApi.deleteFeed(id)
    await loadFeeds()
    clearFeedSelection()
    emit('changed')
    ElMessage.success('订阅已删除')
  } catch (error) {
    ElMessage.error(apiErrorMessage(error, '删除订阅失败，请稍后重试'))
  } finally {
    deletingFeedId.value = null
  }
}

async function syncAll() {
  syncingAll.value = true
  try {
    const report = await rssApi.syncAll()
    lastSyncReport.value = report
    await loadFeeds()
    emit('changed')
    showSyncReportMessage(report)
  } catch (error) {
    ElMessage.error(apiErrorMessage(error, '同步全部失败，请稍后重试'))
  } finally {
    syncingAll.value = false
  }
}

function openOpmlFileDialog() {
  if (isBusy.value) return
  if (opmlFileInput.value) opmlFileInput.value.value = ''
  opmlFileInput.value?.click()
}

async function handleOpmlFilesSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (!files.length) return
  importingOpml.value = true
  try {
    const report = await rssApi.importOpml(files)
    lastImportReport.value = report
    await loadFeeds()
    emit('changed')
    showImportReportMessage(report)
  } catch (error) {
    ElMessage.error(apiErrorMessage(error, 'OPML 导入失败，请检查文件格式或订阅源地址'))
  } finally {
    importingOpml.value = false
    input.value = ''
  }
}

async function exportSelectedOpml() {
  if (selectedFeeds.value.length === 0) {
    ElMessage.warning('请先选择要导出的订阅源')
    return
  }
  await downloadOpml(
    selectedFeeds.value.map((feed) => feed.id),
    'rssreader-selected-subscriptions.opml',
    'selected'
  )
}

async function exportAllOpml() {
  await downloadOpml(undefined, 'rssreader-subscriptions.opml', 'all')
}

async function downloadOpml(feedIds: number[] | undefined, filename: string, mode: 'all' | 'selected') {
  exportingOpml.value = true
  exportMode.value = mode
  try {
    const blob = await rssApi.exportOpml(feedIds)
    triggerBrowserDownload(blob, filename)
    ElMessage.success('OPML 已导出')
  } catch (error) {
    ElMessage.error(apiErrorMessage(error, 'OPML 导出失败，请确认后端已启动或已选择有效订阅源'))
  } finally {
    exportingOpml.value = false
    exportMode.value = null
  }
}

function selectAllFeeds() {
  feedTableRef.value?.clearSelection()
  feeds.value.forEach((feed) => feedTableRef.value?.toggleRowSelection(feed, true))
  if (!feedTableRef.value) selectedFeeds.value = [...feeds.value]
}

function clearFeedSelection() {
  feedTableRef.value?.clearSelection()
  selectedFeeds.value = []
}

function handleFeedSelectionChange(selection: Feed[]) {
  selectedFeeds.value = selection
}

function showImportReportMessage(report: OPMLImportReport) {
  if (report.total === 0) {
    ElMessage.warning('OPML 文件中没有可导入的订阅源')
    return
  }
  if (report.failed > 0 && report.imported === 0) {
    ElMessage.error(`OPML 导入失败 ${report.failed} 个，跳过 ${report.skipped} 个`)
    return
  }
  if (report.failed > 0 || report.skipped > 0) {
    ElMessage.warning(`OPML 导入完成：新增 ${report.imported} 个，跳过 ${report.skipped} 个，失败 ${report.failed} 个`)
    return
  }
  ElMessage.success(`OPML 导入完成：新增 ${report.imported} 个订阅`)
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    imported: '新增',
    skipped: '跳过',
    failed: '失败',
    success: '成功',
    pending: '待同步'
  }
  return labels[status] || status
}

function createFeedErrorMessage(error: unknown) {
  const message = apiErrorMessage(error, '添加订阅失败，请检查 RSS URL 或后端状态')
  if (message.toLowerCase().includes('feed already exists')) {
    return '这条订阅已经存在，可以直接同步或在列表中查看'
  }
  return message
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
</script>

<style scoped>
.feed-manage-page {
  min-height: calc(100vh - 56px);
  padding: 20px;
  background: var(--app-bg);
}

.feed-manage-page.embedded {
  min-height: auto;
  padding: 0;
  display: grid;
  gap: 12px;
}

.feed-manage-header {
  align-items: flex-start;
  margin-bottom: 14px;
}

.feed-manage-title-group {
  display: grid;
  gap: 4px;
}

.feed-manage-title-group h1 {
  margin: 0;
}

.feed-manage-subtitle {
  margin: 0;
  color: #7a8799;
  font-size: 13px;
}

.page-title.embedded {
  margin-bottom: 0;
}

.feed-manage-toolbar {
  align-items: center;
  flex-wrap: wrap;
}

.feed-manage-panel {
  padding: 18px 20px;
  border-radius: 24px;
  box-shadow: none;
  background: color-mix(in srgb, var(--app-surface-strong) 94%, white 6%);
  border-color: color-mix(in srgb, var(--app-border) 78%, transparent 22%);
}

.feed-manage-panel.embedded {
  border-radius: 24px;
}

.feed-form {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr) auto;
  gap: 10px 12px;
  align-items: end;
  margin-bottom: 14px;
}

.feed-submit-button {
  margin: 0 0 18px;
}

.feed-manage-action {
  --el-button-bg-color: color-mix(in srgb, var(--app-surface-strong) 66%, var(--app-bg) 34%);
  --el-button-border-color: color-mix(in srgb, var(--app-border) 94%, #b5c7e6 6%);
  --el-button-text-color: color-mix(in srgb, currentColor 84%, #506483 16%);
  --el-button-hover-bg-color: color-mix(in srgb, var(--app-surface-strong) 48%, var(--theme-accent) 52%);
  --el-button-hover-border-color: color-mix(in srgb, var(--theme-accent) 44%, var(--app-border) 56%);
}

.feed-selected-count {
  color: #7a8799;
  font-size: 13px;
  font-weight: 700;
}

.opml-file-input {
  display: none;
}

.result-block {
  display: grid;
  gap: 10px;
  margin: 14px 0;
  padding-top: 14px;
  border-top: 1px solid color-mix(in srgb, var(--app-border) 72%, transparent 28%);
}

.result-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  color: #7a8799;
  font-size: 13px;
}

.result-block-header h2 {
  margin: 0;
  color: inherit;
  font-size: 15px;
  font-weight: 800;
}

.feed-table {
  border-radius: 18px;
  overflow: hidden;
}

.feed-table :deep(.el-table) {
  --el-table-bg-color: color-mix(in srgb, var(--app-surface) 96%, var(--app-bg) 4%);
  --el-table-tr-bg-color: color-mix(in srgb, var(--app-surface) 96%, var(--app-bg) 4%);
  --el-table-header-bg-color: color-mix(in srgb, var(--app-surface-strong) 82%, var(--app-bg) 18%);
  --el-table-border-color: color-mix(in srgb, var(--app-border) 74%, transparent 26%);
}

.feed-table :deep(.el-table th.el-table__cell) {
  font-weight: 800;
}

.feed-table :deep(.el-table__cell) {
  vertical-align: middle;
}

.url-input {
  width: 360px;
}

@media (max-width: 960px) {
  .feed-manage-page {
    padding: 14px;
  }

  .feed-form {
    grid-template-columns: 1fr;
  }

  .feed-submit-button {
    width: 100%;
    margin-bottom: 0;
  }

  .url-input {
    width: 100%;
  }
}
</style>
