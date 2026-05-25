<template>
  <div class="reader-grid" v-loading="store.loading">
    <section class="panel scroll-panel article-list-panel">
      <h2>订阅与筛选</h2>
      <el-button class="filter-button" text @click="loadArticles()"
        >全部文章</el-button
      >
      <el-button
        class="filter-button"
        text
        @click="loadArticles({ unread: true })"
        >未读文章</el-button
      >
      <el-button
        class="filter-button"
        text
        @click="loadArticles({ starred: true })"
        >收藏文章</el-button
      >
      <el-divider />
      <h3>订阅源</h3>
      <el-button
        v-for="feed in store.feeds"
        :key="feed.id"
        class="filter-button"
        text
        @click="loadArticles({ feed_id: feed.id })"
      >
        {{ feed.title }}
      </el-button>
    </section>

    <section class="panel scroll-panel">
      <div class="toolbar">
        <el-button :icon="Refresh" @click="syncAll">同步全部</el-button>
      </div>
      <article
        v-for="article in store.articles"
        :key="article.id"
        class="article-item"
        :class="{ active: store.selectedArticle?.id === article.id }"
        @click="store.selectArticle(article.id)"
      >
        <h3>{{ article.title }}</h3>
        <p class="muted">{{ article.feed_title }}</p>
        <el-tag v-if="!article.is_read" size="small">未读</el-tag>
        <el-tag v-if="article.is_starred" size="small" type="warning"
          >收藏</el-tag
        >
      </article>
    </section>

    <section class="panel scroll-panel" v-if="store.selectedArticle">
      <div class="toolbar">
        <el-button
          :icon="Check"
          @click="store.toggleRead(store.selectedArticle)"
        >
          {{ store.selectedArticle.is_read ? "标记未读" : "标记已读" }}
        </el-button>
        <el-button
          :icon="Star"
          @click="store.toggleStar(store.selectedArticle)"
        >
          {{ store.selectedArticle.is_starred ? "取消收藏" : "收藏" }}
        </el-button>
        <el-button :icon="MagicStick" @click="runSummary">生成摘要</el-button>
        <el-button :icon="Switch" @click="runTranslate">翻译</el-button>
      </div>
      <h1 class="reader-title">{{ store.selectedArticle.title }}</h1>
      <p class="muted">
        <span v-if="store.selectedArticle.author"
          >{{ store.selectedArticle.author }} ·
        </span>
        <a
          class="article-source-link"
          :href="store.selectedArticle.url"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ store.selectedArticle.url }}
        </a>
      </p>
      <div
        ref="articleBodyRef"
        class="article-body"
        v-html="store.selectedArticle.cleaned_html"
      ></div>
      <el-alert
        v-if="aiResult"
        :title="aiResult"
        type="success"
        show-icon
        :closable="false"
      />
      <el-divider />
      <h2 class="reader-section-title">笔记</h2>
      <el-input
        v-model="note"
        type="textarea"
        :rows="6"
        placeholder="写下这篇文章的 Markdown 笔记"
      />
      <div class="note-actions">
        <el-button type="primary" @click="saveNote">保存笔记</el-button>
        <el-button :loading="exportingMarkdown" @click="exportMarkdown">
          {{ exportingMarkdown ? "正在导出..." : "导出 Markdown" }}
        </el-button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  Check,
  MagicStick,
  Refresh,
  Star,
  Switch,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { nextTick, onMounted, ref, watch } from "vue";
import { rssApi } from "../api/client";
import { useReaderStore } from "../stores/reader";

const store = useReaderStore();
const note = ref("");
const aiResult = ref("");
const articleBodyRef = ref<HTMLElement | null>(null);
const exportingMarkdown = ref(false);

onMounted(async () => {
  await store.loadAll();
  await loadNote();
});

watch(() => store.selectedArticle?.id, loadNote);
watch(() => store.selectedArticle?.cleaned_html, decorateArticleLinks, {
  flush: "post",
});

async function loadArticles(params?: Record<string, unknown>) {
  store.articles = await rssApi.articles(params);
  store.selectedArticle = store.articles[0] ?? null;
}

async function loadNote() {
  if (!store.selectedArticle) return;
  const data = await rssApi.note(store.selectedArticle.id);
  note.value = data.content_markdown;
  aiResult.value = "";
}

async function decorateArticleLinks() {
  await nextTick();
  articleBodyRef.value?.querySelectorAll("a").forEach((link) => {
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
  });
}

async function saveNote() {
  if (!store.selectedArticle) return;
  await rssApi.saveNote(store.selectedArticle.id, note.value);
  ElMessage.success("笔记已保存");
}

async function exportMarkdown() {
  if (!store.selectedArticle) return;
  exportingMarkdown.value = true;
  try {
    const blob = await rssApi.exportArticleMarkdown(store.selectedArticle.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${safeFilename(store.selectedArticle.title)}.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    ElMessage.success("Markdown 已导出");
  } catch (error) {
    ElMessage.error("导出失败，请确认后端已启动");
  } finally {
    exportingMarkdown.value = false;
  }
}

function safeFilename(name: string) {
  return name.replace(/[\\/:*?"<>|]/g, "_").slice(0, 80) || "article";
}

async function runSummary() {
  if (!store.selectedArticle) return;
  const data = await rssApi.summary(store.selectedArticle.id);
  aiResult.value = data.result;
}

async function runTranslate() {
  if (!store.selectedArticle) return;
  const data = await rssApi.translate(store.selectedArticle.id);
  aiResult.value = data.result;
}

async function syncAll() {
  await rssApi.syncAll();
  ElMessage.success("Mock 同步已触发");
}
</script>

<style scoped>
.filter-button {
  width: 100%;
  justify-content: flex-start;
  margin: 2px 0;
}

.tag-filter {
  margin: 4px;
  cursor: pointer;
}
</style>
