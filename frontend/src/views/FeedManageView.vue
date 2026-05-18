<template>
  <div>
    <div class="page-title">
      <h1>订阅管理</h1>
      <div class="toolbar">
        <el-button :icon="Refresh" @click="syncAll">同步全部</el-button>
        <el-button :icon="Upload">OPML 导入</el-button>
        <el-button tag="a" href="/api/opml/export" target="_blank" :icon="Download">OPML 导出</el-button>
      </div>
    </div>
    <section class="panel">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="标题">
          <el-input v-model="title" placeholder="可选" />
        </el-form-item>
        <el-form-item label="RSS URL">
          <el-input v-model="url" placeholder="https://example.com/feed.xml" class="url-input" />
        </el-form-item>
        <el-button type="primary" @click="addFeed">添加订阅</el-button>
      </el-form>
      <el-table :data="feeds" stripe>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="url" label="URL" />
        <el-table-column prop="last_sync_at" label="最后同步" />
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button size="small" @click="syncFeed(row.id)">同步</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Download, Refresh, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { Feed, rssApi } from '../api/client'

const feeds = ref<Feed[]>([])
const title = ref('')
const url = ref('')

onMounted(loadFeeds)

async function loadFeeds() {
  feeds.value = await rssApi.feeds()
}

async function addFeed() {
  if (!url.value) return
  await rssApi.createFeed({ title: title.value, url: url.value })
  title.value = ''
  url.value = ''
  await loadFeeds()
  ElMessage.success('订阅已添加到 Mock Repository')
}

async function syncFeed(id: number) {
  await rssApi.syncFeed(id)
  await loadFeeds()
  ElMessage.success('Mock 同步完成')
}

async function syncAll() {
  await rssApi.syncAll()
  await loadFeeds()
  ElMessage.success('全部订阅 Mock 同步完成')
}
</script>

<style scoped>
.url-input {
  width: 360px;
}
</style>

