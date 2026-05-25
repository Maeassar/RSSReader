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
            @click="router.push('/feeds')"
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
            @click="router.push('/settings')"
          />
        </el-tooltip>
      </div>
    </el-header>
    <el-main class="main">
      <router-view />
    </el-main>
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
import { useRouter } from "vue-router";

const router = useRouter();
</script>
