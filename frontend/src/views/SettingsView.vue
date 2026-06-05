<template>
  <div class="settings-page" :class="{ embedded }" :data-mode="resolvedPreviewMode">
    <div class="page-title" v-if="!embedded">
      <h1>设置</h1>
    </div>
    <div class="drawer-title" v-else>
      <h2>设置</h2>
    </div>

    <section class="panel settings-theme-panel">
      <button type="button" class="appearance-summary" @click="toggleAppearanceExpanded">
        <div class="appearance-summary-copy">
          <div class="appearance-summary-title">主题</div>
          <div class="appearance-summary-value">{{ selectedModeLabel }} · {{ selectedPaletteLabel }}</div>
        </div>
        <span class="appearance-summary-arrow" :class="{ expanded: appearanceExpanded }">›</span>
      </button>

      <div v-if="appearanceExpanded" class="appearance-card">
        <div class="mode-switcher" role="tablist" aria-label="外观模式">
          <button
            v-for="option in modeOptions"
            :key="option.value"
            type="button"
            class="mode-option"
            :class="{ active: appearanceMode === option.value }"
            :aria-selected="appearanceMode === option.value"
            @click="appearanceMode = option.value"
          >
            <span class="mode-icon">{{ option.icon }}</span>
            <span>{{ option.label }}</span>
          </button>
        </div>

        <div class="palette-grid">
          <button
            v-for="palette in paletteOptions"
            :key="palette.value"
            type="button"
            class="palette-tile"
            :class="{ active: appearancePalette === palette.value }"
            :aria-label="palette.label"
            @click="selectPalette(palette.value)"
          >
            <span v-if="appearancePalette === palette.value" class="palette-check">✓</span>
            <span class="palette-preview">
              <span
                v-for="(color, index) in palette.quadrants"
                :key="`${palette.value}-${index}`"
                class="palette-quadrant"
                :style="{ background: color }"
              ></span>
            </span>
          </button>

          <button
            type="button"
            class="palette-tile custom-tile"
            :class="{ active: appearancePalette === 'custom' }"
            aria-label="自定义主题"
            @click="selectPalette('custom')"
          >
            <span v-if="appearancePalette === 'custom'" class="palette-check">✓</span>
            <span class="custom-icon">✎</span>
          </button>
        </div>

        <div v-if="appearancePalette === 'custom'" class="custom-palette-editor">
          <div class="custom-palette-row">
            <label class="custom-color-field">
              <span>背景</span>
              <input :value="customPalette.appBg" type="color" @input="updateCustomColor('appBg', $event)" />
            </label>
            <label class="custom-color-field">
              <span>面板</span>
              <input :value="customPalette.appSurface" type="color" @input="updateCustomColor('appSurface', $event)" />
            </label>
            <label class="custom-color-field">
              <span>描边</span>
              <input :value="customPalette.appBorder" type="color" @input="updateCustomColor('appBorder', $event)" />
            </label>
            <label class="custom-color-field">
              <span>高亮</span>
              <input :value="customPalette.accentLight" type="color" @input="updateCustomColor('accentLight', $event)" />
            </label>
          </div>
          <div class="custom-palette-preview">
            <div class="custom-preview-card">
              <div class="custom-preview-chip"></div>
              <div class="custom-preview-line is-strong"></div>
              <div class="custom-preview-line"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="panel settings-secondary-panel">
      <el-form label-width="120px">
        <el-form-item label="阅读字号">
          <el-slider v-model="fontSize" :min="14" :max="24" show-input />
        </el-form-item>
        <el-form-item label="行距">
          <el-slider v-model="readerLineHeight" :min="1.4" :max="2.2" :step="0.05" show-input />
        </el-form-item>
        <el-form-item label="正文宽度">
          <el-slider v-model="readerContentWidth" :min="640" :max="1040" :step="20" show-input />
        </el-form-item>
        <el-form-item label="启动时同步">
          <el-switch v-model="startupSyncEnabled" />
        </el-form-item>
        <el-form-item label="定时同步">
          <el-switch v-model="timedSyncEnabled" />
        </el-form-item>
        <el-form-item label="同步间隔">
          <el-input-number
            v-model="timedSyncIntervalMinutes"
            :min="5"
            :step="5"
            :disabled="!timedSyncEnabled"
          />
          <span class="interval-unit">分钟</span>
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  AppearanceMode,
  AppearancePalette,
  CustomPalette,
  usePreferencesStore
} from '../stores/preferences'

defineProps<{
  embedded?: boolean
}>()

const preferences = usePreferencesStore()
const appearanceExpanded = computed({
  get: () => preferences.appearanceExpanded,
  set: (value: boolean) => preferences.setAppearanceExpanded(value)
})

const modeOptions: Array<{ label: string; value: AppearanceMode; icon: string }> = [
  { label: '浅色', value: 'light', icon: '☼' },
  { label: '深色', value: 'dark', icon: '☾' }
]

const paletteOptions: Array<{ label: string; value: AppearancePalette; quadrants: [string, string, string, string] }> = [
  { label: '黑白灰', value: 'mono', quadrants: ['#f1f3f5', '#d6d9de', '#4b5563', '#a7afb9'] },
  { label: '晨曦蓝', value: 'blue', quadrants: ['#d9e7ff', '#f3f7ff', '#2f6fe4', '#b5cbff'] },
  { label: '经典蓝', value: 'classic', quadrants: ['#d4dbec', '#eef2f8', '#4b648f', '#aab8d1'] },
  { label: '靛青', value: 'indigo', quadrants: ['#cfd5ff', '#e7e9ff', '#5a54c4', '#9a94ef'] },
  { label: '石板', value: 'slate', quadrants: ['#d7dde7', '#eef2f6', '#66788d', '#a8b7c8'] },
  { label: '云雾', value: 'fog', quadrants: ['#d5e7ec', '#d8e7ec', '#596d74', '#b5cad0'] },
  { label: '海盐绿', value: 'teal', quadrants: ['#88e1d7', '#8addd3', '#0d7b74', '#75cbc4'] },
  { label: '草木绿', value: 'green', quadrants: ['#b6ee9d', '#b0dd93', '#3e7630', '#9ace87'] },
  { label: '鼠尾草', value: 'sage', quadrants: ['#d2dec4', '#dce5cf', '#66715f', '#bcc7b4'] },
  { label: '琥珀黄', value: 'gold', quadrants: ['#ffe587', '#ffe587', '#887600', '#e4cf68'] },
  { label: '落日橙', value: 'amber', quadrants: ['#ffd4b6', '#ffb784', '#a35c1e', '#ffb784'] },
  { label: '陶土粉', value: 'peach', quadrants: ['#f8d3bd', '#f0cfbc', '#816658', '#ddbea9'] },
  { label: '莓果粉', value: 'rose', quadrants: ['#f7cad6', '#f6a1b4', '#9b4d66', '#f5a0b2'] },
  { label: '樱雾', value: 'blush', quadrants: ['#f3d0d8', '#e3c4cc', '#7a6167', '#d9bcc4'] },
  { label: '兰调', value: 'orchid', quadrants: ['#f0c6eb', '#e39ddc', '#8c4f8f', '#df9cde'] },
  { label: '紫晶', value: 'violet', quadrants: ['#d8c7f2', '#c2abf0', '#6c54a1', '#bca3f0'] }
]

const fontSize = computed({
  get: () => preferences.readerFontSize,
  set: (value: number) => preferences.setReaderFontSize(value)
})

const appearanceMode = computed({
  get: () => preferences.appearanceMode,
  set: (value: AppearanceMode) => preferences.setAppearanceMode(value)
})

const appearancePalette = computed({
  get: () => preferences.appearancePalette,
  set: (value: AppearancePalette) => preferences.setAppearancePalette(value)
})

const customPalette = computed(() => preferences.customPalette)

const readerLineHeight = computed({
  get: () => preferences.readerLineHeight,
  set: (value: number) => preferences.setReaderLineHeight(value)
})

const readerContentWidth = computed({
  get: () => preferences.readerContentWidth,
  set: (value: number) => preferences.setReaderContentWidth(value)
})

const startupSyncEnabled = computed({
  get: () => preferences.startupSyncEnabled,
  set: (value: boolean) => preferences.setStartupSyncEnabled(value)
})

const timedSyncEnabled = computed({
  get: () => preferences.timedSyncEnabled,
  set: (value: boolean) => preferences.setTimedSyncEnabled(value)
})

const timedSyncIntervalMinutes = computed({
  get: () => preferences.timedSyncIntervalMinutes,
  set: (value: number) => preferences.setTimedSyncIntervalMinutes(value)
})

const resolvedPreviewMode = computed(() => preferences.resolveReaderTheme())
const selectedModeLabel = computed(() => modeOptions.find((option) => option.value === appearanceMode.value)?.label ?? '浅色')
const selectedPaletteLabel = computed(() => {
  if (appearancePalette.value === 'custom') return '自定义'
  return paletteOptions.find((palette) => palette.value === appearancePalette.value)?.label ?? '黑白灰'
})
const customPreviewSurface = computed(() => resolvedPreviewMode.value === 'dark' ? customPalette.value.darkAppSurface : customPalette.value.appSurface)
const customPreviewBorder = computed(() => resolvedPreviewMode.value === 'dark' ? customPalette.value.darkAppBorder : customPalette.value.appBorder)
const customPreviewAccent = computed(() => resolvedPreviewMode.value === 'dark' ? customPalette.value.accentDark : customPalette.value.accentLight)

function toggleAppearanceExpanded() {
  appearanceExpanded.value = !appearanceExpanded.value
}

function selectPalette(value: AppearancePalette) {
  appearancePalette.value = value
}

function updateCustomColor(field: keyof CustomPalette, event: Event) {
  const value = (event.target as HTMLInputElement).value
  const patch: Partial<CustomPalette> = { [field]: value }
  if (field === 'appSurface') {
    patch.appSurfaceStrong = value
  }
  if (field === 'accentLight') {
    patch.accentDark = value
  }
  preferences.setCustomPalette(patch)
}
</script>

<style scoped>
.settings-page {
  display: grid;
  gap: 14px;
  align-content: start;
}

.settings-page.embedded {
  min-height: 100%;
  padding-right: 0;
}

.drawer-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
}

.settings-theme-panel,
.settings-secondary-panel {
  border-radius: 18px;
  padding: 12px 14px;
  align-self: start;
}

.settings-page[data-mode="dark"] .settings-theme-panel,
.settings-page[data-mode="dark"] .settings-secondary-panel {
  background: color-mix(in srgb, var(--app-surface) 94%, black 6%);
  border-color: color-mix(in srgb, var(--app-border) 82%, transparent 18%);
  box-shadow: none;
}

.appearance-summary {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  color: inherit;
  cursor: pointer;
}

.appearance-summary-copy {
  display: grid;
  gap: 2px;
}

.appearance-summary-title {
  font-size: 15px;
  font-weight: 800;
}

.appearance-summary-value {
  font-size: 12px;
  font-weight: 600;
  color: #738095;
}

.settings-page[data-mode="dark"] .appearance-summary-value {
  color: #aab4c3;
}

.appearance-summary-arrow {
  font-size: 22px;
  line-height: 1;
  transform: rotate(90deg);
  transition: transform 0.3s ease;
}

.appearance-summary-arrow.expanded {
  transform: rotate(-90deg);
}

.appearance-card {
  margin-top: 10px;
  display: grid;
  gap: 10px;
}

.mode-switcher {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--theme-accent) 22%, var(--app-border) 78%);
  background: color-mix(in srgb, var(--app-surface-strong) 82%, var(--app-bg) 18%);
}

.settings-page[data-mode="dark"] .mode-switcher {
  background: color-mix(in srgb, var(--app-surface-strong) 88%, black 12%);
  border-color: color-mix(in srgb, var(--app-border) 82%, transparent 18%);
}

.mode-option {
  border: 0;
  border-radius: 999px;
  min-height: 36px;
  background: transparent;
  color: #556172;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s ease;
}

.settings-page[data-mode="dark"] .mode-option {
  color: #e8eaed;
}

.mode-option.active {
  background: var(--theme-accent);
  color: #202124;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--theme-accent) 18%, transparent 82%);
}

.mode-icon {
  font-size: 15px;
}

.palette-grid {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 6px;
}

.palette-tile {
  position: relative;
  min-height: 34px;
  border: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 14px;
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.settings-page[data-mode="dark"] .palette-tile {
  background: color-mix(in srgb, var(--app-surface-strong) 92%, black 8%);
  border-color: color-mix(in srgb, var(--app-border) 82%, transparent 18%);
}

.palette-tile:hover,
.palette-tile.active {
  border-color: color-mix(in srgb, var(--theme-accent) 42%, var(--app-border) 58%);
  background: color-mix(in srgb, var(--theme-accent) 14%, var(--app-surface) 86%);
}

.palette-preview {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.palette-check {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 10px;
  color: white;
  background: var(--theme-accent);
}

.custom-tile {
  font-size: 15px;
  color: #546172;
}

.settings-page[data-mode="dark"] .custom-tile {
  color: #c4c7c5;
}

.custom-palette-editor {
  border-top: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  padding-top: 10px;
  display: grid;
  gap: 10px;
}

.custom-palette-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.custom-color-field {
  display: grid;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #627083;
}

.custom-color-field input {
  width: 100%;
  height: 32px;
  border: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 10px;
  background: transparent;
  padding: 2px;
}

.custom-palette-preview {
  padding: 10px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--app-bg) 88%, var(--app-surface) 12%);
  border: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
}

.settings-page[data-mode="dark"] .custom-palette-preview {
  background: color-mix(in srgb, var(--app-surface) 88%, black 12%);
  border-color: color-mix(in srgb, var(--app-border) 82%, transparent 18%);
}

.custom-preview-card {
  padding: 12px;
  border-radius: 14px;
  background: v-bind(customPreviewSurface);
  border: 1px solid v-bind(customPreviewBorder);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}

.custom-preview-chip {
  width: 48px;
  height: 8px;
  border-radius: 999px;
  background: v-bind(customPreviewAccent);
  margin-bottom: 12px;
}

.custom-preview-line {
  height: 8px;
  border-radius: 999px;
  background: color-mix(in srgb, v-bind(customPreviewBorder) 60%, white 40%);
  margin-bottom: 8px;
}

.custom-preview-line.is-strong {
  width: 70%;
}

.custom-preview-line:not(.is-strong) {
  width: 92%;
}

.interval-unit {
  margin-left: 8px;
  color: var(--el-text-color-secondary);
}

@media (max-width: 900px) {
  .palette-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }

  .custom-palette-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
