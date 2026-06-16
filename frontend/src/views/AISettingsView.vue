<template>
  <div class="ai-settings-page">
<!--    <div class="page-title">-->
<!--      <h1>AI 设置</h1>-->
<!--    </div>-->

    <section class="panel">
      <h2 class="section-title">AI Provider</h2>
      <el-alert
        title="文章摘要、AI 标签和 RAG Chat 共用当前选用的 Provider；API Key 会加密保存，编辑时留空则保留原 Key。"
        type="info"
        :closable="false"
      />
      <div class="active-provider-bar">
        <div class="active-provider-copy">
          <span class="active-provider-label">当前使用</span>
          <strong>{{ defaultProvider?.name || '未选择 Provider' }}</strong>
          <span>{{ defaultProvider?.model || '请先新增并启用一个 Provider' }}</span>
        </div>
        <el-select
          v-model="selectedProviderId"
          placeholder="选择 AI Provider"
          class="active-provider-select"
          :disabled="!providers.length || switchingProvider"
          @change="selectActiveProvider"
        >
          <el-option
            v-for="item in providers"
            :key="item.id"
            :label="providerOptionLabel(item)"
            :value="item.id"
            :disabled="!item.enabled"
          />
        </el-select>
      </div>
      <el-form label-width="120px" class="settings-form">
        <el-form-item label="快速模板">
          <el-segmented v-model="providerTemplate" :options="providerTemplates" @change="applyProviderTemplate" />
        </el-form-item>
        <el-form-item label="Provider">
          <el-input v-model="provider.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="provider.provider_type" style="width: 220px">
            <el-option label="OpenAI Compatible" value="openai_compatible" />
            <el-option label="vLLM Local" value="vllm" />
            <el-option label="Ollama" value="ollama" />
            <el-option label="Custom" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="provider.baseUrl" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="provider.apiKey"
            type="password"
            show-password
            :placeholder="editingProviderHasApiKey ? '已加密保存，留空则不修改' : '本地加密保存'"
          />
          <span class="field-hint">保存后数据库仅记录加密值，列表不会回显明文。</span>
        </el-form-item>
        <el-form-item label="Model">
          <el-input v-model="provider.model" />
        </el-form-item>
        <el-form-item>
          <el-switch v-model="provider.enabled" active-text="启用" />
          <el-switch v-model="provider.isDefault" active-text="默认" style="margin-left: 18px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingProvider" @click="saveProvider">{{ editingProviderId ? '更新 Provider' : '新增 Provider' }}</el-button>
          <el-button @click="resetProviderForm">新建</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="providers" size="small" class="provider-table">
        <el-table-column prop="name" label="Provider" min-width="160" />
        <el-table-column prop="provider_type" label="类型" width="150" />
        <el-table-column prop="model" label="模型" min-width="180" show-overflow-tooltip />
        <el-table-column prop="base_url" label="Base URL" min-width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="220">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" size="small">默认</el-tag>
            <el-tag v-if="row.has_api_key" size="small" type="warning">Key 已加密</el-tag>
            <el-tag v-if="row.enabled" size="small" type="success">启用</el-tag>
            <el-tag v-else size="small" type="info">停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editProvider(row)">编辑</el-button>
            <el-button link type="success" :disabled="row.is_default || !row.enabled" @click="setDefaultProvider(row)">选用</el-button>
            <el-button link type="danger" @click="removeProvider(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="panel rag-panel">
      <h2 class="section-title">RAG 问答配置</h2>
      <el-alert
        title="这里只配置向量检索 Embedding；Chat 生成会复用上方默认 AI Provider，Embedding API Key 同样加密保存。"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-form label-width="120px" class="settings-form">
        <div class="config-group-title">Embedding</div>
        <el-form-item label="API Key">
          <el-input
            v-model="rag.siliconflow_api_key"
            type="password"
            show-password
            :placeholder="rag.has_siliconflow_api_key ? '已加密保存，留空则不修改' : 'sk-...'"
          />
          <span class="field-hint">Embedding Key 保存后会加密，接口不会回传明文。</span>
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="rag.siliconflow_base_url" :placeholder="RAG_DEFAULTS.siliconflow_base_url" />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="rag.embedding_model" :placeholder="RAG_DEFAULTS.embedding_model" />
        </el-form-item>
        <el-form-item label="向量维度">
          <el-input-number v-model="rag.embedding_dim" :min="64" :max="4096" :step="64" style="width: 160px" />
          <span class="field-hint">推荐：BAAI/bge-m3（硅基流动）或 text-embedding-v4（千问），均为 1024 维</span>
        </el-form-item>

        <div class="config-group-title" style="margin-top: 24px">Chat 生成</div>
        <el-form-item label="使用 Provider">
          <div class="provider-summary">
            <strong>{{ rag.chat_provider_name || defaultProvider?.name || '未配置默认 Provider' }}</strong>
            <span>{{ rag.chat_provider_model || defaultProvider?.model || '请先新增并启用默认 Provider' }}</span>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveRag">保存 RAG 配置</el-button>
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { rssApi, type LLMProvider, type LLMProviderType, type RagConfig, getErrorMessage } from '../api/client'

const RAG_DEFAULTS = {
  siliconflow_base_url: 'e.g. https://api.siliconflow.cn/v1',
  embedding_model: 'e.g. BAAI/bge-m3',
}

const providerTemplates = ['vLLM Qwen3-8B', 'Ollama', 'OpenAI Compatible']
const providerTemplate = ref('vLLM Qwen3-8B')

const providers = ref<LLMProvider[]>([])
const selectedProviderId = ref<number | null>(null)
const editingProviderId = ref<number | null>(null)
const editingProviderHasApiKey = ref(false)
const savingProvider = ref(false)
const switchingProvider = ref(false)
const defaultProvider = computed(() => providers.value.find((item) => item.enabled && item.is_default) || providers.value.find((item) => item.enabled))

const provider = reactive({
  name: 'Local vLLM Qwen3-8B',
  provider_type: 'vllm' as LLMProviderType,
  baseUrl: 'http://127.0.0.1:8001/v1',
  apiKey: '',
  model: 'Qwen/Qwen3-8B',
  enabled: true,
  isDefault: true
})

const rag = reactive<RagConfig>({
  siliconflow_api_key: '',
  siliconflow_base_url: '',
  embedding_model: '',
  embedding_dim: 1024,
  chat_provider_name: '',
  chat_provider_model: '',
  has_siliconflow_api_key: false,
})

const saving = ref(false)

onMounted(async () => {
  try {
    await loadProviders()
    const cfg = await rssApi.getRagConfig()
    Object.assign(rag, cfg)
  } catch (e: unknown) {
    ElMessage.warning(getErrorMessage(e))
  }
})

async function loadProviders() {
  providers.value = await rssApi.llmProviders()
  const current = defaultProvider.value
  selectedProviderId.value = current?.id ?? null
  rag.chat_provider_name = current?.name || rag.chat_provider_name
  rag.chat_provider_model = current?.model || rag.chat_provider_model
}

function providerOptionLabel(item: LLMProvider) {
  const state = item.enabled ? (item.is_default ? '当前' : '可用') : '停用'
  return `${item.name} · ${item.model} · ${state}`
}

async function selectActiveProvider(value: number | string | boolean | undefined) {
  const providerId = Number(value)
  const item = providers.value.find((candidate) => candidate.id === providerId)
  if (!item || item.is_default) return
  await setDefaultProvider(item)
}

async function setDefaultProvider(row: LLMProvider) {
  switchingProvider.value = true
  try {
    await rssApi.updateLLMProvider(row.id, { is_default: true, enabled: true })
    await loadProviders()
    const cfg = await rssApi.getRagConfig()
    Object.assign(rag, cfg)
    ElMessage.success(`已选用 ${row.name}`)
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
    selectedProviderId.value = defaultProvider.value?.id ?? null
  } finally {
    switchingProvider.value = false
  }
}

function applyProviderTemplate() {
  if (providerTemplate.value === 'vLLM Qwen3-8B') {
    Object.assign(provider, {
      name: 'Local vLLM Qwen3-8B',
      provider_type: 'vllm',
      baseUrl: 'http://127.0.0.1:8001/v1',
      apiKey: '',
      model: 'Qwen/Qwen3-8B',
      enabled: true,
      isDefault: true
    })
  } else if (providerTemplate.value === 'Ollama') {
    Object.assign(provider, {
      name: 'Local Ollama',
      provider_type: 'ollama',
      baseUrl: 'http://127.0.0.1:11434/v1',
      apiKey: 'ollama',
      model: 'qwen3:8b',
      enabled: true,
      isDefault: true
    })
  } else {
    Object.assign(provider, {
      name: 'OpenAI Compatible',
      provider_type: 'openai_compatible',
      baseUrl: 'https://api.openai.com/v1',
      apiKey: '',
      model: 'gpt-4o-mini',
      enabled: true,
      isDefault: true
    })
  }
  editingProviderId.value = null
  editingProviderHasApiKey.value = false
}

function resetProviderForm() {
  applyProviderTemplate()
}

function editProvider(row: LLMProvider) {
  editingProviderId.value = row.id
  editingProviderHasApiKey.value = row.has_api_key
  Object.assign(provider, {
    name: row.name,
    provider_type: row.provider_type,
    baseUrl: row.base_url,
    apiKey: '',
    model: row.model,
    enabled: row.enabled,
    isDefault: row.is_default
  })
}

async function removeProvider(id: number) {
  try {
    await rssApi.deleteLLMProvider(id)
    await loadProviders()
    if (editingProviderId.value === id) resetProviderForm()
    const cfg = await rssApi.getRagConfig()
    Object.assign(rag, cfg)
    ElMessage.success('Provider 已删除')
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
  }
}

async function saveProvider() {
  savingProvider.value = true
  try {
    const payload = {
      name: provider.name,
      provider_type: provider.provider_type,
      base_url: provider.baseUrl,
      api_key: provider.apiKey,
      model: provider.model,
      enabled: provider.enabled,
      is_default: provider.isDefault
    }
    if (editingProviderId.value) {
      await rssApi.updateLLMProvider(editingProviderId.value, payload)
      ElMessage.success('Provider 已更新')
      editingProviderHasApiKey.value = Boolean(provider.apiKey || editingProviderHasApiKey.value)
    } else {
      await rssApi.createLLMProvider(payload)
      ElMessage.success('Provider 已新增')
    }
    await loadProviders()
    const cfg = await rssApi.getRagConfig()
    Object.assign(rag, cfg)
    provider.apiKey = ''
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
  } finally {
    savingProvider.value = false
  }
}

async function saveRag() {
  saving.value = true
  try {
    await rssApi.saveRagConfig({ ...rag })
    ElMessage.success('RAG 配置已保存')
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.ai-settings-page {
  padding: 24px;
}

.settings-form {
  width: 100%;
  margin-top: 16px;
}

.active-provider-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  background: var(--el-fill-color-lighter);
}

.active-provider-copy {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  color: var(--el-text-color-secondary);
}

.active-provider-copy strong {
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.active-provider-label {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.active-provider-select {
  width: min(360px, 44vw);
  flex: 0 0 auto;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--el-text-color-primary);
}

.rag-panel {
  margin-top: 24px;
}

.provider-table {
  margin-top: 18px;
}

.field-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-left: 10px;
}

.config-group-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid var(--el-color-primary);
}

.provider-summary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-secondary);
}

.provider-summary strong {
  color: var(--el-text-color-primary);
}
</style>
