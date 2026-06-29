<template>
  <div class="ai-settings-page">
    <header class="ai-settings-header">
      <div>
        <p class="eyebrow">AI Workspace</p>
        <h1>AI 设置</h1>
        <p>管理摘要、标签、RAG 问答与翻译模型，所有 API Key 都会在本地加密保存。</p>
      </div>
      <div class="header-metrics">
        <div class="metric-card">
          <span>通用模型</span>
          <strong>{{ providers.length }}</strong>
        </div>
        <div class="metric-card">
          <span>翻译模型</span>
          <strong>{{ translationProviders.length }}</strong>
        </div>
      </div>
    </header>

    <section class="overview-grid">
      <div class="overview-item">
        <div class="overview-icon">
          <el-icon><MagicStick /></el-icon>
        </div>
        <div class="overview-copy">
          <span>摘要 / 标签 / RAG Chat</span>
          <strong>{{ defaultProvider?.name || '未选择 Provider' }}</strong>
          <small>{{ defaultProvider?.model || '请先新增并启用一个 Provider' }}</small>
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

      <div class="overview-item">
        <div class="overview-icon translation-icon">
          <el-icon><Connection /></el-icon>
        </div>
        <div class="overview-copy">
          <span>全文翻译</span>
          <strong>{{ defaultTranslationProvider?.name || '未选择翻译 Provider' }}</strong>
          <small>{{ defaultTranslationProvider?.model || '请新增并启用一个翻译 Provider' }}</small>
        </div>
      </div>
    </section>

    <section class="provider-workspace panel">
      <div class="provider-editor">
        <div class="section-heading">
          <div>
            <p>Provider</p>
            <h2>{{ editingProviderId ? '编辑通用 AI 模型' : '新增通用 AI 模型' }}</h2>
          </div>
          <el-tag round effect="plain">摘要 / 标签 / RAG</el-tag>
        </div>
        <p class="section-desc">文章摘要、AI 标签和 RAG Chat 共用当前选用的 Provider；编辑时 API Key 留空会保留原 Key。</p>
        <div v-if="editingProviderId" class="editing-banner">
          <div>
            <span>正在编辑</span>
            <strong>{{ editingProviderName }}</strong>
          </div>
          <el-button text type="primary" @click="resetProviderForm">切换为新建</el-button>
        </div>

        <el-form label-position="top" class="settings-form">
          <el-form-item label="快速模板">
            <el-segmented v-model="providerTemplate" :options="providerTemplates" @change="applyProviderTemplate" />
          </el-form-item>
          <div class="form-grid">
            <el-form-item label="Provider">
              <el-input v-model="provider.name" />
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="provider.provider_type">
                <el-option label="OpenAI Compatible" value="openai_compatible" />
                <el-option label="vLLM Local" value="vllm" />
                <el-option label="Ollama" value="ollama" />
                <el-option label="Custom" value="custom" />
              </el-select>
            </el-form-item>
          </div>
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
          <div class="form-footer">
            <div class="switch-row">
              <el-switch v-model="provider.enabled" active-text="启用" />
              <el-switch v-model="provider.isDefault" active-text="默认" />
            </div>
            <div class="button-row">
              <el-button @click="resetProviderForm">新建</el-button>
              <el-button type="primary" :loading="savingProvider" @click="saveProvider">{{ editingProviderId ? '保存修改' : '新增 Provider' }}</el-button>
            </div>
          </div>
        </el-form>
      </div>

      <aside class="provider-side-list">
        <div class="list-heading">
          <div>
            <h3>通用 Provider</h3>
            <span>{{ providers.length }} 个配置</span>
          </div>
        </div>
        <div class="provider-card-list">
          <article
            v-for="row in providers"
            :key="row.id"
            class="provider-card"
            :class="{ active: editingProviderId === row.id }"
          >
            <div class="provider-card-main">
              <div class="provider-card-title">
                <strong>{{ row.name }}</strong>
                <el-tag v-if="row.is_default" size="small">默认</el-tag>
              </div>
              <div class="provider-card-model">{{ row.model }}</div>
              <div class="provider-card-url">{{ row.base_url }}</div>
            </div>
            <div class="provider-card-meta">
              <el-tag size="small" effect="plain">{{ providerTypeLabel(row.provider_type) }}</el-tag>
              <el-tag v-if="row.has_api_key" size="small" type="warning" effect="plain">Key</el-tag>
              <el-tag v-if="row.enabled" size="small" type="success" effect="plain">启用</el-tag>
              <el-tag v-else size="small" type="info" effect="plain">停用</el-tag>
            </div>
            <div class="provider-card-actions">
              <el-button size="small" type="primary" plain @click="editProvider(row)">编辑配置</el-button>
              <el-button size="small" text type="success" :disabled="row.is_default || !row.enabled" @click="setDefaultProvider(row)">设为默认</el-button>
              <el-button size="small" text type="danger" @click="removeProvider(row.id)">删除</el-button>
            </div>
          </article>
          <el-empty v-if="!providers.length" description="暂无通用 Provider" :image-size="72" />
        </div>
      </aside>
    </section>

    <section class="provider-workspace panel">
      <div class="provider-editor">
        <div class="section-heading">
          <div>
            <p>Translation</p>
            <h2>{{ editingTranslationProviderId ? '编辑翻译模型' : '新增翻译模型' }}</h2>
          </div>
          <el-tag round effect="plain" type="success">独立配置</el-tag>
        </div>
        <p class="section-desc">翻译模型独立于摘要、标签和 RAG Chat，可配置 Qwen、Ollama 或任意 OpenAI-compatible 模型。</p>
        <div v-if="editingTranslationProviderId" class="editing-banner">
          <div>
            <span>正在编辑</span>
            <strong>{{ editingTranslationProviderName }}</strong>
          </div>
          <el-button text type="primary" @click="resetTranslationProviderForm">切换为新建</el-button>
        </div>

        <el-form label-position="top" class="settings-form">
          <el-form-item label="快速模板">
            <el-segmented v-model="translationTemplate" :options="translationTemplates" @change="applyTranslationTemplate" />
          </el-form-item>
          <div class="form-grid">
            <el-form-item label="Provider">
              <el-input v-model="translationProviderForm.name" />
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="translationProviderForm.provider_type">
                <el-option label="OpenAI Compatible" value="openai_compatible" />
                <el-option label="vLLM Local" value="vllm" />
                <el-option label="Ollama" value="ollama" />
                <el-option label="Custom" value="custom" />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="Base URL">
            <el-input v-model="translationProviderForm.baseUrl" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input
              v-model="translationProviderForm.apiKey"
              type="password"
              show-password
              :placeholder="editingTranslationProviderHasApiKey ? '已加密保存，留空则不修改' : '本地加密保存'"
            />
            <span class="field-hint">OpenAI-compatible API Key 可填在这里。</span>
          </el-form-item>
          <el-form-item label="Model">
            <el-input v-model="translationProviderForm.model" />
          </el-form-item>
          <div class="form-footer">
            <div class="switch-row">
              <el-switch v-model="translationProviderForm.enabled" active-text="启用" />
              <el-switch v-model="translationProviderForm.isDefault" active-text="默认" />
            </div>
            <div class="button-row">
              <el-button @click="resetTranslationProviderForm">新建</el-button>
              <el-button type="primary" :loading="savingTranslationProvider" @click="saveTranslationProvider">{{ editingTranslationProviderId ? '保存修改' : '新增翻译 Provider' }}</el-button>
            </div>
          </div>
        </el-form>
      </div>

      <aside class="provider-side-list">
        <div class="list-heading">
          <div>
            <h3>翻译 Provider</h3>
            <span>{{ translationProviders.length }} 个配置</span>
          </div>
        </div>
        <div class="provider-card-list">
          <article
            v-for="row in translationProviders"
            :key="row.id"
            class="provider-card"
            :class="{ active: editingTranslationProviderId === row.id }"
          >
            <div class="provider-card-main">
              <div class="provider-card-title">
                <strong>{{ row.name }}</strong>
                <el-tag v-if="row.is_default" size="small">默认</el-tag>
              </div>
              <div class="provider-card-model">{{ row.model }}</div>
              <div class="provider-card-url">{{ row.base_url }}</div>
            </div>
            <div class="provider-card-meta">
              <el-tag size="small" effect="plain">{{ providerTypeLabel(row.provider_type) }}</el-tag>
              <el-tag v-if="row.has_api_key" size="small" type="warning" effect="plain">Key</el-tag>
              <el-tag v-if="row.enabled" size="small" type="success" effect="plain">启用</el-tag>
              <el-tag v-else size="small" type="info" effect="plain">停用</el-tag>
            </div>
            <div class="provider-card-actions">
              <el-button size="small" type="primary" plain @click="editTranslationProvider(row)">编辑配置</el-button>
              <el-button size="small" text type="success" :disabled="row.is_default || !row.enabled" @click="setDefaultTranslationProvider(row)">设为默认</el-button>
              <el-button size="small" text type="danger" @click="removeTranslationProvider(row.id)">删除</el-button>
            </div>
          </article>
          <el-empty v-if="!translationProviders.length" description="暂无翻译 Provider" :image-size="72" />
        </div>
      </aside>
    </section>

    <section class="panel rag-panel">
      <div class="section-heading">
        <div>
          <p>Retrieval</p>
          <h2>RAG 问答配置</h2>
        </div>
        <div class="provider-pill">
          <span>Chat 使用</span>
          <strong>{{ rag.chat_provider_name || defaultProvider?.name || '未配置默认 Provider' }}</strong>
        </div>
      </div>
      <p class="section-desc">这里只配置向量检索 Embedding；Chat 生成会复用默认 AI Provider，Embedding API Key 同样加密保存。</p>

      <el-form label-position="top" class="settings-form rag-form">
        <div class="form-grid rag-form-grid">
          <el-form-item label="Embedding API Key">
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
            <el-input-number v-model="rag.embedding_dim" :min="64" :max="4096" :step="64" />
            <span class="field-hint">推荐 BAAI/bge-m3 或 text-embedding-v4，均为 1024 维。</span>
          </el-form-item>
        </div>
        <div class="rag-footer">
          <div class="provider-summary">
            <el-icon><Lock /></el-icon>
            <span>{{ rag.chat_provider_model || defaultProvider?.model || '请先新增并启用默认 Provider' }}</span>
          </div>
          <el-button type="primary" :loading="saving" @click="saveRag">保存 RAG 配置</el-button>
        </div>
      </el-form>
    </section>

  </div>
</template>

<script setup lang="ts">
import { Connection, Lock, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { rssApi, type LLMProvider, type LLMProviderType, type RagConfig, type TranslationProvider, getErrorMessage } from '../api/client'

const RAG_DEFAULTS = {
  siliconflow_base_url: 'e.g. https://api.siliconflow.cn/v1',
  embedding_model: 'e.g. BAAI/bge-m3',
}

const providerTemplates = ['vLLM Qwen3-8B', 'Ollama', 'OpenAI Compatible']
const providerTemplate = ref('vLLM Qwen3-8B')
const translationTemplates = ['vLLM Qwen3-8B', 'Ollama', 'OpenAI Compatible']
const translationTemplate = ref('vLLM Qwen3-8B')

const providers = ref<LLMProvider[]>([])
const translationProviders = ref<TranslationProvider[]>([])
const selectedProviderId = ref<number | null>(null)
const editingProviderId = ref<number | null>(null)
const editingProviderHasApiKey = ref(false)
const savingProvider = ref(false)
const switchingProvider = ref(false)
const editingTranslationProviderId = ref<number | null>(null)
const editingTranslationProviderHasApiKey = ref(false)
const savingTranslationProvider = ref(false)
const defaultProvider = computed(() => providers.value.find((item) => item.enabled && item.is_default) || providers.value.find((item) => item.enabled))
const defaultTranslationProvider = computed(() => translationProviders.value.find((item) => item.enabled && item.is_default) || translationProviders.value.find((item) => item.enabled))
const editingProviderName = computed(() => providers.value.find((item) => item.id === editingProviderId.value)?.name || provider.name)
const editingTranslationProviderName = computed(() => translationProviders.value.find((item) => item.id === editingTranslationProviderId.value)?.name || translationProviderForm.name)

const provider = reactive({
  name: 'Local vLLM Qwen3-8B',
  provider_type: 'vllm' as LLMProviderType,
  baseUrl: 'http://127.0.0.1:8001/v1',
  apiKey: '',
  model: 'Qwen/Qwen3-8B',
  enabled: true,
  isDefault: true
})

const translationProviderForm = reactive({
  name: 'Translation vLLM Qwen3-8B',
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
    await loadTranslationProviders()
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

async function loadTranslationProviders() {
  translationProviders.value = await rssApi.translationProviders()
}

function providerOptionLabel(item: LLMProvider) {
  const state = item.enabled ? (item.is_default ? '当前' : '可用') : '停用'
  return `${item.name} · ${item.model} · ${state}`
}

function providerTypeLabel(type: LLMProviderType) {
  const labels: Record<LLMProviderType, string> = {
    openai_compatible: 'OpenAI',
    vllm: 'vLLM',
    ollama: 'Ollama',
    custom: 'Custom',
  }
  return labels[type] || type
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
      is_default: provider.isDefault,
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


function applyTranslationTemplate() {
  if (translationTemplate.value === 'vLLM Qwen3-8B') {
    Object.assign(translationProviderForm, {
      name: 'Translation vLLM Qwen3-8B',
      provider_type: 'vllm',
      baseUrl: 'http://127.0.0.1:8001/v1',
      apiKey: '',
      model: 'Qwen/Qwen3-8B',
      enabled: true,
      isDefault: true
    })
  } else if (translationTemplate.value === 'Ollama') {
    Object.assign(translationProviderForm, {
      name: 'Translation Ollama',
      provider_type: 'ollama',
      baseUrl: 'http://127.0.0.1:11434/v1',
      apiKey: 'ollama',
      model: 'qwen3:8b',
      enabled: true,
      isDefault: true
    })
  } else {
    Object.assign(translationProviderForm, {
      name: 'Translation OpenAI Compatible',
      provider_type: 'openai_compatible',
      baseUrl: 'https://api.openai.com/v1',
      apiKey: '',
      model: 'gpt-4o-mini',
      enabled: true,
      isDefault: true
    })
  }
  editingTranslationProviderId.value = null
  editingTranslationProviderHasApiKey.value = false
}

function resetTranslationProviderForm() {
  applyTranslationTemplate()
}

function editTranslationProvider(row: TranslationProvider) {
  editingTranslationProviderId.value = row.id
  editingTranslationProviderHasApiKey.value = row.has_api_key
  Object.assign(translationProviderForm, {
    name: row.name,
    provider_type: row.provider_type,
    baseUrl: row.base_url,
    apiKey: '',
    model: row.model,
    enabled: row.enabled,
    isDefault: row.is_default
  })
}

async function setDefaultTranslationProvider(row: TranslationProvider) {
  savingTranslationProvider.value = true
  try {
    await rssApi.updateTranslationProvider(row.id, { is_default: true, enabled: true })
    await loadTranslationProviders()
    ElMessage.success(`翻译模型已选用 ${row.name}`)
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
  } finally {
    savingTranslationProvider.value = false
  }
}

async function removeTranslationProvider(id: number) {
  try {
    await rssApi.deleteTranslationProvider(id)
    await loadTranslationProviders()
    if (editingTranslationProviderId.value === id) resetTranslationProviderForm()
    ElMessage.success('翻译 Provider 已删除')
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
  }
}

async function saveTranslationProvider() {
  savingTranslationProvider.value = true
  try {
    const payload = {
      name: translationProviderForm.name,
      provider_type: translationProviderForm.provider_type,
      base_url: translationProviderForm.baseUrl,
      api_key: translationProviderForm.apiKey,
      model: translationProviderForm.model,
      enabled: translationProviderForm.enabled,
      is_default: translationProviderForm.isDefault
    }
    if (editingTranslationProviderId.value) {
      await rssApi.updateTranslationProvider(editingTranslationProviderId.value, payload)
      ElMessage.success('翻译 Provider 已更新')
      editingTranslationProviderHasApiKey.value = Boolean(translationProviderForm.apiKey || editingTranslationProviderHasApiKey.value)
    } else {
      await rssApi.createTranslationProvider(payload)
      ElMessage.success('翻译 Provider 已新增')
    }
    await loadTranslationProviders()
    translationProviderForm.apiKey = ''
  } catch (e: unknown) {
    ElMessage.error(getErrorMessage(e))
  } finally {
    savingTranslationProvider.value = false
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
  width: min(1180px, calc(100vw - 48px));
  margin: 0 auto;
  padding: 28px 0 40px;
  display: grid;
  gap: 18px;
}

.ai-settings-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
  padding: 6px 2px 2px;
}

.ai-settings-header h1 {
  margin: 2px 0 8px;
  font-size: 28px;
  line-height: 1.12;
  font-weight: 800;
  color: var(--el-text-color-primary);
}

.ai-settings-header p {
  margin: 0;
  max-width: 640px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.eyebrow,
.section-heading p {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  color: color-mix(in srgb, var(--theme-accent) 78%, var(--el-text-color-secondary) 22%);
  letter-spacing: 0;
  text-transform: uppercase;
}

.header-metrics {
  display: flex;
  gap: 10px;
  flex: 0 0 auto;
}

.metric-card {
  min-width: 96px;
  padding: 12px 14px;
  border: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 8px;
  background: color-mix(in srgb, var(--app-surface) 88%, var(--app-bg) 12%);
}

.metric-card span {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.metric-card strong {
  font-size: 24px;
  line-height: 1;
  color: var(--el-text-color-primary);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.overview-item {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--app-border) 72%, transparent 28%);
  border-radius: 8px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--theme-accent) 10%, transparent 90%), transparent 46%),
    color-mix(in srgb, var(--app-surface) 92%, var(--app-bg) 8%);
  box-shadow: 0 14px 30px color-mix(in srgb, #1f2937 8%, transparent 92%);
}

.overview-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: #ffffff;
  background: var(--theme-accent);
  box-shadow: 0 12px 24px color-mix(in srgb, var(--theme-accent) 26%, transparent 74%);
}

.overview-icon .el-icon {
  font-size: 22px;
}

.translation-icon {
  background: #0f8f72;
  box-shadow: 0 12px 24px rgba(15, 143, 114, 0.2);
}

.overview-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.overview-copy span {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
}

.overview-copy strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.overview-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.active-provider-select {
  width: min(320px, 34vw);
}

.provider-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(340px, 0.65fr);
  gap: 18px;
  align-items: start;
  padding: 18px;
}

.provider-editor {
  min-width: 0;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 8px;
}

.section-heading.compact {
  margin-bottom: 14px;
}

.section-heading h2 {
  margin: 3px 0 0;
  font-size: 18px;
  line-height: 1.2;
  color: var(--el-text-color-primary);
}

.section-desc {
  margin: 0 0 18px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.7;
}

.editing-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--theme-accent) 28%, var(--app-border) 72%);
  border-radius: 8px;
  background: color-mix(in srgb, var(--theme-accent) 8%, var(--app-surface) 92%);
}

.editing-banner div {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.editing-banner span {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.editing-banner strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
}

.settings-form {
  width: 100%;
}

.settings-form :deep(.el-form-item) {
  margin-bottom: 15px;
}

.settings-form :deep(.el-form-item__label) {
  margin-bottom: 6px;
  font-weight: 700;
  color: var(--el-text-color-regular);
}

.settings-form :deep(.el-select),
.settings-form :deep(.el-input-number) {
  width: 100%;
}

.settings-form :deep(.el-segmented) {
  max-width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(180px, 0.8fr);
  gap: 12px;
}

.form-footer,
.rag-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 2px;
}

.switch-row,
.button-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 10px;
}

.field-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.45;
  color: var(--el-text-color-placeholder);
}

.rag-panel {
  padding: 18px;
}

.rag-form-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.provider-pill,
.provider-summary {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 8px;
  background: color-mix(in srgb, var(--app-surface-strong) 88%, var(--app-bg) 12%);
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.provider-pill strong,
.provider-summary strong {
  color: var(--el-text-color-primary);
}

.provider-summary span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.provider-summary .el-icon {
  color: var(--theme-accent);
  flex: 0 0 auto;
}

.provider-side-list {
  min-width: 0;
  border: 1px solid color-mix(in srgb, var(--app-border) 74%, transparent 26%);
  border-radius: 8px;
  background: color-mix(in srgb, var(--app-surface-strong) 76%, var(--app-bg) 24%);
  overflow: hidden;
}

.list-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 14px;
  border-bottom: 1px solid color-mix(in srgb, var(--app-border) 70%, transparent 30%);
}

.list-heading h3 {
  margin: 0 0 2px;
  font-size: 15px;
  line-height: 1.2;
  color: var(--el-text-color-primary);
}

.list-heading span {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.provider-card-list {
  max-height: 520px;
  overflow-y: auto;
  padding: 10px;
  display: grid;
  gap: 10px;
}

.provider-card {
  min-width: 0;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 8px;
  background: var(--app-surface);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.provider-card:hover,
.provider-card.active {
  border-color: color-mix(in srgb, var(--theme-accent) 48%, var(--app-border) 52%);
  background: color-mix(in srgb, var(--theme-accent) 5%, var(--app-surface) 95%);
}

.provider-card.active {
  box-shadow: inset 3px 0 0 var(--theme-accent);
}

.provider-card-main {
  min-width: 0;
  display: grid;
  gap: 5px;
}

.provider-card-title {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-card-title strong,
.provider-card-model,
.provider-card-url {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.provider-card-title strong {
  color: var(--el-text-color-primary);
}

.provider-card-model {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.provider-card-url {
  font-family: "JetBrains Mono", "Cascadia Mono", Consolas, monospace;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.provider-card-meta,
.provider-card-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.provider-card-actions {
  gap: 2px;
  justify-content: flex-end;
}

.provider-card-actions .el-button {
  margin-left: 0;
}

@media (max-width: 1100px) {
  .overview-grid,
  .provider-workspace {
    grid-template-columns: 1fr;
  }

  .active-provider-select {
    width: min(320px, 42vw);
  }

  .rag-form-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .provider-card-list {
    max-height: 360px;
  }
}

@media (max-width: 760px) {
  .ai-settings-page {
    width: min(100vw - 24px, 1180px);
    padding: 18px 0 28px;
  }

  .ai-settings-header,
  .form-footer,
  .rag-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .header-metrics,
  .button-row {
    width: 100%;
  }

  .metric-card,
  .button-row .el-button {
    flex: 1 1 0;
  }

  .overview-item {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .active-provider-select {
    grid-column: 1 / -1;
    width: 100%;
  }

  .form-grid,
  .rag-form-grid {
    grid-template-columns: 1fr;
  }

  .editing-banner {
    align-items: stretch;
    flex-direction: column;
  }

  .provider-card-actions {
    justify-content: flex-start;
  }
}
</style>
