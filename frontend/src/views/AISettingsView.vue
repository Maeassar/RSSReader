<template>
  <div>
    <div class="page-title">
      <h1>AI 设置</h1>
    </div>
    <section class="panel">
      <el-alert title="当前阶段保留 OpenAI-compatible Provider 配置界面，后端 AI 接口返回 Mock 结果。" type="info" :closable="false" />
      <el-form label-width="120px" class="settings-form">
        <el-form-item label="Provider">
          <el-input v-model="provider.name" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="provider.baseUrl" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="provider.apiKey" type="password" show-password />
        </el-form-item>
        <el-form-item label="Model">
          <el-input v-model="provider.model" />
        </el-form-item>
        <el-form-item>
          <el-switch v-model="provider.enabled" active-text="启用" />
        </el-form-item>
        <el-button type="primary" @click="save">保存配置</el-button>
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive } from 'vue'

const provider = reactive({
  name: 'OpenAI Compatible Demo',
  baseUrl: 'https://api.example.com/v1',
  apiKey: '',
  model: 'gpt-compatible-demo',
  enabled: true
})

function save() {
  ElMessage.success('Provider 配置界面已预留，后续接入 llm_providers 表')
}
</script>

<style scoped>
.settings-form {
  max-width: 720px;
  margin-top: 16px;
}
</style>

