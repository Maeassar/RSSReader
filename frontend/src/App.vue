<template>
  <el-container class="app-shell">
    <el-header class="top-nav">
      <div class="brand" style="display: flex; align-items: center; gap: 4px">
        <strong>RSSReader</strong>
      </div>
      <div class="top-actions">
        <el-tooltip content="阅读" placement="bottom">
          <el-button
            :icon="Reading"
            text
            circle
            aria-label="阅读"
            @click="router.push('/')"
          />
        </el-tooltip>
        <el-tooltip content="订阅" placement="bottom">
          <el-button
            :icon="Connection"
            text
            circle
            aria-label="订阅"
            @click="openSubscriptionPanel"
          />
        </el-tooltip>
        <el-tooltip content="统计日志" placement="bottom">
          <el-button
            :icon="DataAnalysis"
            text
            circle
            aria-label="统计日志"
            @click="router.push('/stats')"
          />
        </el-tooltip>
        <el-tooltip content="AI 设置" placement="bottom">
          <el-button
            :icon="MagicStick"
            text
            circle
            aria-label="AI 设置"
            @click="router.push('/ai')"
          />
        </el-tooltip>
        <el-tooltip content="设置" placement="bottom">
          <el-button
            :icon="Setting"
            text
            circle
            aria-label="设置"
            @click="settingsDrawerOpen = true"
          />
        </el-tooltip>
      </div>
    </el-header>
    <el-main class="main">
      <router-view />
    </el-main>
    <el-drawer
      v-model="settingsDrawerOpen"
      direction="rtl"
      size="460px"
      class="settings-drawer"
      append-to-body
      :with-header="false"
    >
      <SettingsView embedded />
    </el-drawer>
  </el-container>
</template>

<script setup lang="ts">
import {
  Connection,
  DataAnalysis,
  MagicStick,
  Reading,
  Setting,
} from "@element-plus/icons-vue";
import { onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { rssApi } from "./api/client";
import { usePreferencesStore } from "./stores/preferences";
import SettingsView from "./views/SettingsView.vue";

const router = useRouter();
const preferences = usePreferencesStore();
const settingsDrawerOpen = ref(false);
let timedSyncTimer: number | undefined;
let backgroundSyncRunning = false;

onMounted(() => {
  preferences.applyPreferences();
  triggerStartupSync();
  configureTimedSync();
});

onUnmounted(() => {
  clearTimedSync();
});

watch(
  () => [preferences.timedSyncEnabled, preferences.timedSyncIntervalMinutes] as const,
  configureTimedSync,
);

function triggerStartupSync() {
  if (!preferences.startupSyncEnabled || !preferences.shouldRunStartupSync()) {
    return;
  }
  preferences.recordStartupSync();
  void runBackgroundSync("startup");
}

function configureTimedSync() {
  clearTimedSync();
  if (!preferences.timedSyncEnabled) {
    return;
  }
  timedSyncTimer = window.setInterval(
    () => void runBackgroundSync("timer"),
    preferences.timedSyncIntervalMinutes * 60 * 1000,
  );
}

function clearTimedSync() {
  if (timedSyncTimer !== undefined) {
    window.clearInterval(timedSyncTimer);
    timedSyncTimer = undefined;
  }
}

async function runBackgroundSync(reason: "startup" | "timer") {
  if (backgroundSyncRunning) {
    return;
  }
  backgroundSyncRunning = true;
  try {
    const report = await rssApi.syncAll();
    window.dispatchEvent(new CustomEvent("rssreader:background-sync", { detail: report }));
    if (report.failed > 0) {
      console.warn(`Background ${reason} sync finished with ${report.failed} failed feed(s).`, report);
    }
  } catch (error) {
    console.warn(`Background ${reason} sync failed.`, error);
  } finally {
    backgroundSyncRunning = false;
  }
}

function openSubscriptionPanel() {
  void router.push({ path: '/', query: { panel: 'feeds' } })
}
</script>
