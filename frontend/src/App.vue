<template>
  <el-container class="app-shell">
    <el-aside class="nav">
      <div class="brand">
        <strong>RSSReader</strong>
        <span>Local-first</span>
      </div>
      <el-menu router :default-active="$route.path" class="nav-menu">
        <el-menu-item index="/">
          <el-icon><Reading /></el-icon>
          <span>阅读</span>
        </el-menu-item>
        <el-menu-item index="/feeds">
          <el-icon><Connection /></el-icon>
          <span>订阅</span>
        </el-menu-item>
        <el-menu-item index="/tags">
          <el-icon><CollectionTag /></el-icon>
          <span>标签</span>
        </el-menu-item>
        <el-menu-item index="/ai">
          <el-icon><MagicStick /></el-icon>
          <span>AI 设置</span>
        </el-menu-item>
        <el-menu-item index="/stats">
          <el-icon><DataAnalysis /></el-icon>
          <span>统计日志</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { CollectionTag, Connection, DataAnalysis, MagicStick, Reading, Setting } from '@element-plus/icons-vue'
</script>

