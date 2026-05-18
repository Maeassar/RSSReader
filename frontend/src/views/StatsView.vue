<template>
  <div>
    <div class="page-title">
      <h1>统计日志</h1>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>
    <div class="form-grid">
      <section class="panel">
        <h2>LLM 用量统计</h2>
        <el-statistic title="调用次数" :value="stats.total_calls || 0" />
        <el-statistic title="输入 Token" :value="stats.input_tokens || 0" />
        <el-statistic title="输出 Token" :value="stats.output_tokens || 0" />
      </section>
      <section class="panel">
        <h2>同步日志</h2>
        <el-timeline>
          <el-timeline-item v-for="log in logs" :key="log.id" :timestamp="log.created_at" :type="log.status === 'success' ? 'success' : 'info'">
            {{ log.message }}
          </el-timeline-item>
        </el-timeline>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { rssApi } from '../api/client'

const stats = ref<Record<string, any>>({})
const logs = ref<any[]>([])

onMounted(load)

async function load() {
  stats.value = await rssApi.llmStats()
  logs.value = await rssApi.syncLogs()
}
</script>

