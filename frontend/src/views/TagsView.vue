<template>
  <div>
    <div class="page-title">
      <h1>标签管理</h1>
    </div>
    <section class="panel">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="名称">
          <el-input v-model="name" placeholder="例如 AI" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="color" />
        </el-form-item>
        <el-button type="primary" @click="addTag">创建标签</el-button>
      </el-form>
      <div class="tag-list">
        <el-tag v-for="tag in tags" :key="tag.id" :color="tag.color" effect="dark" size="large">{{ tag.name }}</el-tag>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { rssApi, Tag } from '../api/client'

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
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}
</style>

