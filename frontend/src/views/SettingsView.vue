<template>
  <div>
    <div class="page-title">
      <h1>设置</h1>
    </div>
    <section class="panel">
      <el-form label-width="120px">
        <el-form-item label="界面语言">
          <el-segmented v-model="language" :options="['中文', 'English']" />
        </el-form-item>
        <el-form-item label="阅读字号">
          <el-slider v-model="fontSize" :min="14" :max="22" show-input />
        </el-form-item>
        <el-form-item label="本地优先">
          <el-switch v-model="localFirst" active-text="已启用" disabled />
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const language = ref('中文')
const fontSize = ref(16)
const localFirst = ref(true)
</script>

