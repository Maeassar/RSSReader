<template>
  <div class="tag-manage-page" :class="{ embedded }">
    <div class="page-title tag-manage-header" :class="{ embedded }">
      <div class="tag-manage-title-group">
        <h1>标签管理</h1>
        <p v-if="embedded" class="tag-manage-subtitle">在当前阅读页直接管理标签，不跳转整页</p>
      </div>
      <div class="toolbar tag-manage-toolbar">
        <el-button v-if="embedded" class="tag-manage-action" @click="emit('close')">关闭</el-button>
      </div>
    </div>
    <section class="panel tag-manage-panel" :class="{ embedded }">
      <el-form class="tag-form" :inline="!embedded" @submit.prevent>
        <el-form-item label="名称">
          <el-input v-model="name" placeholder="例如 AI / 设计 / 学习" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="color" />
        </el-form-item>
        <el-button class="tag-submit-button" type="primary" @click="addTag">创建标签</el-button>
      </el-form>
      <div class="tag-grid">
        <div v-for="tag in tags" :key="tag.id" class="tag-card">
          <span class="tag-card-dot" :style="{ background: tag.color }"></span>
          <span class="tag-card-name">{{ tag.name }}</span>
          <el-tag size="small" effect="plain">已创建</el-tag>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { rssApi, Tag } from '../api/client'

withDefaults(defineProps<{
  embedded?: boolean
}>(), {
  embedded: false
})

const emit = defineEmits<{
  close: []
}>()

const tags = ref<Tag[]>([])
const name = ref('')
const color = ref('#409eff')

onMounted(loadTags)

async function loadTags() {
  tags.value = await rssApi.tags()
}

async function addTag() {
  if (!name.value) return
  await rssApi.createTag({ name: name.value, color: color.value })
  name.value = ''
  await loadTags()
  ElMessage.success('标签已创建')
}
</script>

<style scoped>
.tag-manage-page {
  min-height: calc(100vh - 56px);
  padding: 20px;
  background: var(--app-bg);
}

.tag-manage-page.embedded {
  min-height: auto;
  padding: 0;
}

.tag-manage-header {
  margin-bottom: 14px;
}

.tag-manage-title-group {
  display: grid;
  gap: 4px;
}

.tag-manage-title-group h1 {
  margin: 0;
}

.tag-manage-subtitle {
  margin: 0;
  color: #7a8799;
  font-size: 13px;
}

.tag-manage-panel {
  padding: 18px 20px;
  border-radius: 24px;
  background: color-mix(in srgb, var(--app-surface-strong) 94%, white 6%);
  border-color: color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  box-shadow: none;
}

.tag-form {
  display: grid;
  grid-template-columns: minmax(220px, 360px) 180px auto;
  gap: 10px 12px;
  align-items: end;
  margin-bottom: 18px;
}

.tag-submit-button {
  margin-bottom: 18px;
}

.tag-manage-action {
  --el-button-bg-color: color-mix(in srgb, var(--theme-accent) 18%, var(--app-surface) 82%);
  --el-button-border-color: color-mix(in srgb, var(--theme-accent) 24%, var(--app-border) 76%);
  --el-button-text-color: color-mix(in srgb, currentColor 88%, #435b84 12%);
}

.tag-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.tag-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid color-mix(in srgb, var(--app-border) 74%, transparent 26%);
  background: color-mix(in srgb, var(--app-surface) 96%, var(--app-bg) 4%);
}

.tag-card-dot {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  flex: 0 0 auto;
}

.tag-card-name {
  flex: 1;
  min-width: 0;
  font-size: 15px;
  font-weight: 800;
}

@media (max-width: 960px) {
  .tag-manage-page {
    padding: 14px;
  }

  .tag-form {
    grid-template-columns: 1fr;
  }

  .tag-submit-button {
    width: 100%;
    margin-bottom: 0;
  }
}
</style>
