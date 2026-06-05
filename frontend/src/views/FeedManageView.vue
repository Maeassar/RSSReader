<template>
  <div class="feed-manage-page" :class="{ embedded }">
    <div class="page-title feed-manage-header" :class="{ embedded: embedded }">
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
          {{ syncingAll ? "正在同步..." : "同步全部" }}
        </el-button>
        <el-upload
          class="opml-upload"
          :show-file-list="false"
          accept=".opml,.xml"
          :http-request="importOpml"
          :disabled="isBusy"
        >
          <el-button class="feed-manage-action" :icon="Upload" :loading="importingOpml" :disabled="isBusy">
            OPML 导入
          </el-button>
        </el-upload>
        <el-button
          class="feed-manage-action"
          :loading="exportingOpml"
          :disabled="isBusy"
          :icon="Download"
          @click="exportOpml"
          >OPML 导出</el-button
        >
      </div>
    </div>
    <section class="panel feed-manage-panel" :class="{ embedded: embedded }">
      <el-form class="feed-form" :inline="!embedded" @submit.prevent>
        <el-form-item label="标题">
          <el-input v-model="title" placeholder="可选" />
        </el-form-item>
        <el-form-item label="RSS URL">
          <el-input
            v-model="url"
            placeholder="https://example.com/feed.xml"
            class="url-input"
          />
        </el-form-item>
        <el-button
          class="feed-submit-button"
          type="primary"
          :loading="addingFeed"
          :disabled="addingFeed || !url"
          @click="addFeed"
        >
          {{ addingFeed ? "正在添加..." : "添加订阅" }}
        </el-button>
      </el-form>
      <el-table :data="feeds" stripe table-layout="fixed" class="feed-table">
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="url" label="URL" min-width="320" show-overflow-tooltip />
        <el-table-column label="最后同步" width="180">
          <template #default="{ row }">
            {{ formatLastSyncAt(row.last_sync_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button
              size="small"
              :loading="syncingFeedId === row.id"
              :disabled="isBusy"
              @click="syncFeed(row.id)"
            >
              {{ syncingFeedId === row.id ? "正在同步..." : "同步" }}
            </el-button>
            <el-popconfirm
              title="确定删除当前订阅吗？"
              confirm-button-text="删除"
              cancel-button-text="取消"
              confirm-button-type="danger"
              @confirm="deleteFeed(row.id)"
            >
              <template #reference>
                <el-button
                  size="small"
                  type="danger"
                  plain
                  :loading="deletingFeedId === row.id"
                  :disabled="isBusy"
                >
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
import { Download, Refresh, Upload } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import type { UploadRequestOptions } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { Feed, rssApi } from "../api/client";

withDefaults(defineProps<{
  embedded?: boolean
}>(), {
  embedded: false,
});

const emit = defineEmits<{
  close: []
}>();

const feeds = ref<Feed[]>([]);
const title = ref("");
const url = ref("");
const addingFeed = ref(false);
const syncingAll = ref(false);
const syncingFeedId = ref<number | null>(null);
const deletingFeedId = ref<number | null>(null);
const importingOpml = ref(false);
const exportingOpml = ref(false);
const isBusy = computed(
  () =>
    syncingAll.value ||
    syncingFeedId.value !== null ||
    deletingFeedId.value !== null ||
    importingOpml.value ||
    exportingOpml.value,
);

onMounted(loadFeeds);

async function loadFeeds() {
  feeds.value = await rssApi.feeds();
}

function formatLastSyncAt(value?: string) {
  if (!value) return "未同步";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  const parts = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    hourCycle: "h23",
  }).formatToParts(date);
  const partMap = Object.fromEntries(
    parts.map((part) => [part.type, part.value]),
  );

  return `${partMap.year}/${partMap.month}/${partMap.day} ${partMap.hour}:${partMap.minute}:${partMap.second}`;
}

async function addFeed() {
  if (!url.value) return;
  addingFeed.value = true;
  try {
    await rssApi.createFeed({ title: title.value, url: url.value });
    title.value = "";
    url.value = "";
    await loadFeeds();
    ElMessage.success("订阅已添加");
  } catch (error) {
    ElMessage.error("添加订阅失败，请检查 RSS URL 或后端状态");
  } finally {
    addingFeed.value = false;
  }
}

async function syncFeed(id: number) {
  syncingFeedId.value = id;
  try {
    await rssApi.syncFeed(id);
    await loadFeeds();
    ElMessage.success("同步完成");
  } catch (error) {
    ElMessage.error("同步失败，请稍后重试");
  } finally {
    syncingFeedId.value = null;
  }
}

async function deleteFeed(id: number) {
  deletingFeedId.value = id;
  try {
    await rssApi.deleteFeed(id);
    await loadFeeds();
    ElMessage.success("订阅已删除");
  } catch (error) {
    ElMessage.error("删除订阅失败，请稍后重试");
  } finally {
    deletingFeedId.value = null;
  }
}

async function syncAll() {
  syncingAll.value = true;
  try {
    const report = await rssApi.syncAll();
    await loadFeeds();
    showSyncReportMessage(report);
  } catch (error) {
    ElMessage.error("同步全部失败，请稍后重试");
  } finally {
    syncingAll.value = false;
  }
}

async function importOpml(options: UploadRequestOptions) {
  importingOpml.value = true;
  try {
    const report = await rssApi.importOpml(options.file as File);
    await loadFeeds();
    if (report.failed > 0 && report.imported === 0) {
      ElMessage.error(`OPML 导入失败 ${report.failed} 个，跳过 ${report.skipped} 个`);
    } else if (report.failed > 0 || report.skipped > 0) {
      ElMessage.warning(`OPML 导入完成：新增 ${report.imported} 个，跳过 ${report.skipped} 个，失败 ${report.failed} 个`);
    } else {
      ElMessage.success(`OPML 导入完成：新增 ${report.imported} 个订阅`);
    }
  } catch (error) {
    ElMessage.error("OPML 导入失败，请检查文件格式或订阅源地址");
  } finally {
    importingOpml.value = false;
  }
}

async function exportOpml() {
  exportingOpml.value = true;
  try {
    const blob = await rssApi.exportOpml();
    triggerBrowserDownload(blob, "rssreader-subscriptions.opml");
    ElMessage.success("OPML 已导出");
  } catch (error) {
    ElMessage.error("OPML 导出失败，请确认后端已启动");
  } finally {
    exportingOpml.value = false;
  }
}

function showSyncReportMessage(report: { total: number; success: number; failed: number; skipped: number }) {
  if (report.total === 0) {
    ElMessage.warning("当前没有可同步的订阅");
    return;
  }
  if (report.failed > 0 && report.success === 0) {
    ElMessage.error(`同步失败：${report.failed} 个订阅失败`);
    return;
  }
  if (report.failed > 0) {
    ElMessage.warning(`同步完成：${report.success} 个成功，${report.failed} 个失败`);
    return;
  }
  ElMessage.success(`全部订阅同步完成：${report.success} 个成功`);
}

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
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

.opml-upload {
  display: inline-flex;
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
