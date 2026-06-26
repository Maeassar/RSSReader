<template>
  <div class="reader-shell" :class="readerShellClass">
    <div class="reader-grid" :style="readerGridStyle">
      <section class="panel sidebar-panel">
<!--        <div class="sidebar-header">-->
<!--          <h2>订阅与筛选</h2>-->
<!--        </div>-->

        <div class="sidebar-static-filters">
          <button
            v-for="item in quickFilters"
            :key="item.key"
            type="button"
            class="sidebar-primary-link"
            :class="{ active: activeFilterKey === item.key }"
            @click="applyQuickFilter(item.key)"
          >
            <span>{{ item.label }}</span>
            <span class="sidebar-filter-count">{{ item.count }}</span>
          </button>
        </div>

        <button type="button" class="sidebar-group-toggle" @click="store.setTagPanelExpanded(!store.tagPanelExpanded)">
          <span>标签</span>
          <span class="sidebar-chevron" :class="{ expanded: store.tagPanelExpanded }">›</span>
        </button>
        <el-scrollbar v-show="store.tagPanelExpanded" class="sidebar-tag-scrollbar">
          <div class="sidebar-group-content sidebar-tag-list">
            <div class="tag-create-row">
              <el-input
                v-model="newTagName"
                size="small"
                placeholder="新建标签"
                @keyup.enter="createTag"
              />
              <input v-model="newTagColor" class="tag-color-input" type="color" aria-label="选择标签颜色" />
              <el-button size="small" @click="createTag">添加</el-button>
            </div>
            <button
              v-for="tag in store.tags"
              :key="tag.id"
              type="button"
              class="sidebar-filter-button"
              :class="{ active: activeTagId === tag.id }"
              @click="applyTagFilter(activeTagId === tag.id ? null : tag.id)"
            >
              <span class="tag-filter-label">
                <span class="tag-dot" :style="{ background: tag.color }"></span>
                <span>{{ tag.name }}</span>
              </span>
              <span class="tag-filter-actions">
                <span class="sidebar-filter-count">{{ tagArticleCount(tag.id) }}</span>
                <span
                  role="button"
                  tabindex="0"
                  class="tag-delete-action"
                  :aria-label="`删除标签 ${tag.name}`"
                  title="删除标签"
                  @click.stop="deleteTag(tag.id)"
                  @keydown.enter.stop.prevent="deleteTag(tag.id)"
                  @keydown.space.stop.prevent="deleteTag(tag.id)"
                >
                  <el-icon><Delete /></el-icon>
                </span>
              </span>
            </button>
          </div>
        </el-scrollbar>

        <div class="sidebar-section-header">
<!--          <span class="sidebar-section-title">订阅源</span>-->
<!--          <div class="sidebar-section-actions">-->
<!--            <button type="button" class="sidebar-section-action" aria-label="添加订阅源" @click="openFeedManager">-->
<!--              <el-icon><Plus /></el-icon>-->
<!--            </button>-->
<!--            <el-dropdown trigger="click" @command="handleFeedSectionCommand">-->
<!--              <button type="button" class="sidebar-section-action" aria-label="订阅源更多操作">-->
<!--                <el-icon><MoreFilled /></el-icon>-->
<!--              </button>-->
<!--              <template #dropdown>-->
<!--                <el-dropdown-menu>-->
<!--                  <el-dropdown-item command="manage-feeds">管理订阅源</el-dropdown-item>-->
<!--                  <el-dropdown-item command="sync-feeds" :disabled="syncingAllFeeds">-->
<!--                    {{ syncingAllFeeds ? '正在同步全部' : '同步全部订阅' }}-->
<!--                  </el-dropdown-item>-->
<!--                </el-dropdown-menu>-->
<!--              </template>-->
<!--            </el-dropdown>-->
<!--          </div>-->
        </div>
        <el-scrollbar class="sidebar-feed-scrollbar">
          <div class="sidebar-group-content sidebar-feed-list">
            <button
              v-for="feed in store.feeds"
              :key="feed.id"
              type="button"
              class="sidebar-feed-button"
              :class="{ active: activeFeedId === feed.id }"
              @click="applyFeedFilter(feed.id)"
            >
              <span class="sidebar-feed-mark">
                <img
                  v-if="feedFaviconUrl(feed)"
                  :src="feedFaviconUrl(feed) || ''"
                  :alt="`${feed.title} logo`"
                  class="sidebar-feed-icon"
                  @error="handleFeedIconError(feed.id)"
                />
                <span v-else class="sidebar-feed-icon-fallback"></span>
              </span>
              <span class="sidebar-feed-name" :title="feed.title">{{ feed.title }}</span>
              <span class="sidebar-feed-article-count">{{ feedArticleCount(feed.id) }}</span>
            </button>
          </div>
        </el-scrollbar>
      </section>

      <div
        class="reader-resizer sidebar-resizer"
        role="separator"
        aria-orientation="vertical"
        :aria-label="store.leftSidebarVisible ? '调整或隐藏订阅栏' : '显示订阅栏'"
        @pointerdown="startSidebarResize"
      >
        <button type="button" class="reader-resizer-toggle" @click.stop="toggleSidebarFromResizer">
          {{ store.leftSidebarVisible ? '<' : '>' }}
        </button>
      </div>

      <section v-if="!feedManagerOpen" class="panel scroll-panel article-list-panel" @scroll.passive="handleArticleListScroll">
        <div class="article-list-header">
          <h2>{{ currentListTitle }}</h2>
          <div class="article-list-topbar-right">
            <el-dropdown trigger="click" @command="handleListMenuCommand">
              <button type="button" class="list-menu-button" aria-label="列表设置">
                <el-icon><MoreFilled /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="sync" :disabled="syncingAllFeeds">
                    <el-icon><Refresh /></el-icon>
                    <span>{{ syncingAllFeeds ? '正在同步全部' : '同步全部' }}</span>
                  </el-dropdown-item>
                  <el-dropdown-item command="batch-export">
                    <el-icon><Files /></el-icon>
                    <span>批量文摘</span>
                  </el-dropdown-item>
                  <el-dropdown-item disabled>排序</el-dropdown-item>
                  <el-dropdown-item command="sort:newest">
                    {{ store.articleSortOrder === 'newest' ? '✓ ' : '' }}从新到旧
                  </el-dropdown-item>
                  <el-dropdown-item command="sort:oldest">
                    {{ store.articleSortOrder === 'oldest' ? '✓ ' : '' }}从旧到新
                  </el-dropdown-item>
                  <el-dropdown-item divided disabled>视图</el-dropdown-item>
                  <div class="dropdown-inline-control" @click.stop>
                    <span class="dropdown-inline-label">摘要行数</span>
                    <div class="dropdown-inline-stepper">
                      <button type="button" class="stepper-button" @click.stop="decreaseSummaryLines">-</button>
                      <span class="stepper-value">{{ store.summaryLineCount }}</span>
                      <button type="button" class="stepper-button" @click.stop="increaseSummaryLines">+</button>
                    </div>
                  </div>
                  <el-dropdown-item command="toggle:thumbnails">
                    {{ store.showThumbnails ? '✓ ' : '' }}显示缩略图
                  </el-dropdown-item>
                  <el-dropdown-item divided command="unsubscribe" :disabled="!activeFeedForMenu">
                    退订
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <div v-if="batchExportMode" class="batch-export-bar">
          <div class="batch-export-status">
            <strong>批量文摘</strong>
            <span>已选 {{ batchSelectedArticles.length }} / {{ filteredArticles.length }}</span>
          </div>
          <div class="batch-export-actions">
            <el-button size="small" :icon="Check" @click="selectAllBatchArticles">全选</el-button>
            <el-button size="small" @click="clearBatchSelection">清空</el-button>
            <el-button
              size="small"
              type="primary"
              :icon="Files"
              :disabled="batchSelectedArticles.length === 0"
              @click="openBatchDigestDialog"
            >
              预览导出
            </el-button>
            <el-button size="small" :icon="Close" @click="exitBatchExportMode">退出</el-button>
          </div>
        </div>

        <div v-if="store.loading && filteredArticles.length === 0" class="article-list-loading">
          <el-icon class="article-list-loading-icon"><Loading /></el-icon>
          <span>正在加载文章</span>
        </div>
        <article
          v-for="article in filteredArticles"
          :key="article.id"
          class="article-card"
          :class="{
            active: !batchExportMode && store.selectedArticle?.id === article.id,
            pinned: store.isPinned(article.id),
            'batch-mode': batchExportMode,
            'batch-selected': isBatchArticleSelected(article.id)
          }"
          @click="handleArticleClick(article.id)"
        >
          <button
            v-if="batchExportMode"
            type="button"
            class="article-select-control"
            :class="{ checked: isBatchArticleSelected(article.id) }"
            :aria-label="`选择 ${article.title}`"
            @click.stop="toggleBatchArticle(article.id)"
          >
            <el-icon v-if="isBatchArticleSelected(article.id)"><Check /></el-icon>
          </button>
          <div class="article-card-meta-row">
            <span class="article-card-source">{{ article.feed_title }}</span>
            <div class="article-card-meta-right">
              <span class="article-card-date">{{ formatArticleDate(article) }}</span>
              <div class="article-card-actions">
                <el-tooltip :content="article.is_read ? '标记未读' : '标记已读'" placement="top">
                  <button
                    type="button"
                    class="article-action-button"
                    :class="{ active: article.is_read }"
                    @click.stop="toggleArticleRead(article)"
                  >
                    <el-icon><Check /></el-icon>
                  </button>
                </el-tooltip>
                <el-tooltip :content="store.isPinned(article.id) ? '取消置顶' : '置顶'" placement="top">
                  <button
                    type="button"
                    class="article-action-button"
                    :class="{ active: store.isPinned(article.id) }"
                    @click.stop="store.togglePinned(article.id)"
                  >
                    <el-icon><Top /></el-icon>
                  </button>
                </el-tooltip>
                <el-tooltip :content="article.is_starred ? '取消收藏' : '收藏'" placement="top">
                  <button
                    type="button"
                    class="article-action-button"
                    :class="{ active: article.is_starred }"
                    @click.stop="toggleArticleStar(article)"
                  >
                    <el-icon><Star /></el-icon>
                  </button>
                </el-tooltip>
              </div>
            </div>
          </div>

          <div class="article-card-main" :class="{ 'with-thumbnail': Boolean(store.showThumbnails && articleThumbnail(article)) }">
            <div class="article-card-copy">
              <h3 class="article-card-title" :class="{ unread: !article.is_read }" v-html="renderTitleInlineHtml(article.title)"></h3>
              <p v-if="articleListSummary(article)" class="article-card-summary" :style="summaryClampStyle">
                {{ articleListSummary(article) }}
              </p>
              <div class="article-card-tags">
                <el-tag v-if="article.is_starred" size="small" type="warning">收藏</el-tag>
                <el-tag v-if="store.isPinned(article.id)" size="small" effect="plain">置顶</el-tag>
                <el-tag
                  v-for="tagId in article.tag_ids"
                  :key="`${article.id}-${tagId}`"
                  size="small"
                  effect="plain"
                >
                  {{ tagName(tagId) }}
                </el-tag>
              </div>
            </div>

            <div v-if="store.showThumbnails && articleThumbnail(article)" class="article-card-thumb">
              <img
                :src="articleThumbnail(article) || ''"
                alt=""
                class="article-thumbnail"
                @error="handleThumbnailError(article)"
              />
            </div>
          </div>
        </article>
        <div v-if="store.pagination.hasMore || store.loadingMore" class="article-list-load-more">
          <el-button :loading="store.loadingMore" @click="loadMoreArticles">
            {{ store.loadingMore ? '正在加载' : '加载更多' }}
          </el-button>
        </div>
        <div v-else-if="!store.loading && filteredArticles.length === 0" class="article-list-empty">
          当前列表没有文章
        </div>
      </section>

      <div
        v-if="!feedManagerOpen"
        class="reader-resizer article-list-resizer"
        role="separator"
        aria-orientation="vertical"
        :aria-label="store.articleListVisible ? '调整或隐藏文章列表' : '显示文章列表'"
        @pointerdown="startArticleListResize"
      >
        <button type="button" class="reader-resizer-toggle" @click.stop="toggleArticleListFromResizer">
          {{ store.articleListVisible ? '<' : '>' }}
        </button>
      </div>

      <section v-if="store.selectedArticle && !feedManagerOpen" class="panel reader-detail-panel">
        <div class="toolbar detail-toolbar">
          <el-popover placement="bottom" :width="380" trigger="click" popper-class="tag-popover">
            <template #reference>
              <el-button class="toolbar-icon-button" :icon="CollectionTag" circle aria-label="标签" title="标签" />
            </template>
            <div class="tag-popover-body">
              <el-input
                v-model="tagSearchQuery"
                class="tag-search-input"
                size="small"
                clearable
                placeholder="搜索标签"
                @keyup.enter="createAndAssignTagFromSearch"
              />
              <div class="ai-tag-panel">
                <div class="ai-tag-panel-header">
                  <span class="ai-tag-panel-title">AI 推荐标签</span>
                  <el-button size="small" :loading="aiTagLoading" :icon="MagicStick" @click="generateAiTags">
                    AI 生成
                  </el-button>
                </div>
                <div v-if="aiTagError" class="ai-tag-error">{{ aiTagError }}</div>
                <div v-if="aiTagCandidates.length" class="ai-tag-candidate-list">
                  <button
                    v-for="candidate in aiTagCandidates"
                    :key="aiTagCandidateKey(candidate)"
                    type="button"
                    class="ai-tag-candidate"
                    :class="{
                      active: isAiTagCandidateSelected(candidate),
                      assigned: isAiTagCandidateAssigned(candidate)
                    }"
                    :title="candidate.reason || candidate.name"
                    @click="toggleAiTagCandidate(candidate)"
                  >
                    <span>{{ candidate.name }}</span>
                    <span class="ai-tag-badge">{{ candidate.tag_id ? '已有' : '新建' }}</span>
                  </button>
                </div>
                <div v-if="aiTagCandidates.length" class="ai-tag-actions">
                  <el-button size="small" @click="clearAiTagCandidates">清空</el-button>
                  <el-button size="small" type="primary" :loading="aiTagApplying" @click="applyAiTagCandidates">
                    应用所选
                  </el-button>
                </div>
              </div>
              <div v-if="filteredTagOptions.length" class="tag-selection-list">
                <button
                  v-for="tag in filteredTagOptions"
                  :key="tag.id"
                  type="button"
                  class="tag-selection-item"
                  :class="{ active: selectedArticleTagIds.includes(tag.id) }"
                  @click="toggleSelectedArticleTag(tag.id)"
                >
                  <span class="tag-selection-main">
                    <span class="tag-dot" :style="{ background: tag.color }"></span>
                    <span>{{ tag.name }}</span>
                  </span>
                  <span class="tag-selection-actions">
                    <el-icon v-if="selectedArticleTagIds.includes(tag.id)"><Check /></el-icon>
                    <span
                      role="button"
                      tabindex="0"
                      class="tag-delete-action"
                      :aria-label="`删除标签 ${tag.name}`"
                      title="删除标签"
                      @click.stop="deleteTag(tag.id)"
                      @keydown.enter.stop.prevent="deleteTag(tag.id)"
                      @keydown.space.stop.prevent="deleteTag(tag.id)"
                    >
                      <el-icon><Delete /></el-icon>
                    </span>
                  </span>
                </button>
              </div>
              <div v-else class="tag-selection-empty">没有匹配标签</div>
              <div class="tag-creator-card">
                <div class="tag-create-row">
                  <el-input
                    v-model="newTagName"
                    size="small"
                    placeholder="创建标签"
                    @keyup.enter="createTag"
                  />
                  <input v-model="newTagColor" class="tag-color-input" type="color" aria-label="选择标签颜色" />
                  <el-button size="small" @click="createTag">+</el-button>
                </div>
              </div>
            </div>
          </el-popover>
          <div class="toolbar-translate-group">
            <el-tooltip :content="translatingAll ? '翻译中…' : `翻译全文 (${currentTranslationLanguageLabel})`" placement="top">
              <el-button class="toolbar-icon-button" :icon="Switch" circle :loading="translatingAll" @click="runTranslate" />
            </el-tooltip>
            <el-dropdown trigger="click" @command="handleTranslationCommand">
              <el-button class="toolbar-icon-button toolbar-translate-caret" circle>
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled>目标语言</el-dropdown-item>
                  <el-dropdown-item v-for="opt in summaryLanguageOptions" :key="opt.value" :command="`lang:${opt.value}`">
                    {{ translationLanguage === opt.value ? '✓ ' : '' }}{{ opt.label }}
                  </el-dropdown-item>
                  <el-dropdown-item divided command="toggle-all-mode" :disabled="!hasAnyTranslation">
                    {{ allTranslatedInComparisonMode ? '全部切换为仅译文' : '全部切换为双语对照' }}
                  </el-dropdown-item>
                  <el-dropdown-item divided command="clear-all" :disabled="!hasAnyTranslation">清除全部翻译</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <el-popover
            v-model:visible="notePopoverOpen"
            placement="bottom"
            :width="420"
            trigger="click"
            popper-class="note-popover"
            :teleported="false"
          >
            <template #reference>
              <el-button
                class="toolbar-icon-button note-toolbar-button"
                :class="{ active: notePopoverOpen, 'has-note': hasCurrentNote }"
                :icon="EditPen"
                circle
                aria-label="笔记"
                title="笔记"
              />
            </template>
            <div class="note-popover-body">
              <div class="note-popover-header">
                <span class="note-popover-title">笔记</span>
                <span class="note-popover-meta" :class="noteSaveState">{{ noteSaveStatusText }}</span>
              </div>
              <el-input
                v-model="note"
                class="note-popover-input"
                type="textarea"
                :rows="8"
                resize="none"
                placeholder="写下这篇文章的 Markdown 笔记"
              />
              <div class="note-actions note-popover-actions">
                <el-button type="primary" :loading="noteSaveState === 'saving'" @click="saveNoteNow">立即保存</el-button>
                <el-button class="note-export-button" @click="exportNote">
                  导出笔记
                  <el-icon class="button-icon-right"><Download /></el-icon>
                </el-button>
              </div>
            </div>
          </el-popover>
          <el-dropdown trigger="click" @command="handleExportCommand">
            <el-button class="toolbar-icon-button export-trigger" :loading="exportingMarkdown" circle aria-label="导出">
              <el-icon><Download /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="digest">导出文摘</el-dropdown-item>
                <el-dropdown-item command="markdown">导出清洗后 Markdown</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="reader-scroll-area">
          <div class="reader-content-frame">
            <header class="reader-hero">
              <div class="reader-source-row">
                <span class="reader-source-name">{{ store.selectedArticle.feed_title }}</span>
              </div>
              <!-- 原文标题：有译文且仅译文模式时隐藏 -->
              <h1
                v-if="!titleTranslation || titleTranslation.mode !== 'translation' || !titleTranslation.text"
                class="reader-title"
                v-html="renderTitleInlineHtml(store.selectedArticle.title)"
              ></h1>
              <!-- 标题译文（仅译文模式：只显示译文替代原文） -->
              <h1
                v-if="titleTranslation && titleTranslation.mode === 'translation'"
                class="reader-title reader-title-translated"
                v-html="renderTitleInlineHtml(titleTranslation.text)"
              ></h1>
              <!-- 标题译文（对照模式：原文下方显示译文） -->
              <div v-if="titleTranslation && titleTranslation.mode === 'comparison'" class="title-translation-row">
                <div class="title-translation-text" v-html="renderedTitleTranslation(titleTranslation.text)"></div>
              </div>
              <!-- 标题操作栏：hover 标题区域浮现 -->
              <div class="title-translate-bar">
                <div class="title-translate-actions">
                  <template v-if="titleTranslation && titleTranslation.text">
                    <span class="title-translate-status">
                      <el-icon><Switch /></el-icon>
                      <span v-if="titleTranslation.loading">翻译中…</span>
                      <span v-else>已翻译</span>
                    </span>
                    <button class="para-translate-btn" :disabled="titleTranslation.loading || translatingAll" @click.stop="translateTitle()">
                      <span>重新翻译</span>
                    </button>
                    <button class="para-translate-btn mode-btn" @click.stop="toggleTitleMode()">
                      <span v-if="titleTranslation.mode === 'translation'">双语对照</span>
                      <span v-else>仅译文</span>
                    </button>
                    <button class="para-translate-btn mode-btn" @click.stop="restoreTitleOriginal()">
                      <span>恢复原文</span>
                    </button>
                  </template>
                  <template v-else>
                    <button class="para-translate-btn" :disabled="translatingAll" @click.stop="translateTitle()">
                      <el-icon><Switch /></el-icon>
                      <span>翻译标题</span>
                    </button>
                  </template>
                </div>
              </div>
              <div class="reader-source-link-row">
                <a class="reader-source-link" :href="store.selectedArticle.url" target="_blank" rel="noopener noreferrer" @click="handleExternalLinkClick">
                  {{ store.selectedArticle.url }}
                </a>
              </div>
              <div class="reader-meta">
                <span v-if="store.selectedArticle.author">{{ store.selectedArticle.author }}</span>
                <span v-if="readerPublishedAt(store.selectedArticle)">{{ readerPublishedAt(store.selectedArticle) }}</span>
              </div>
            </header>
            <div ref="articleBodyRef" class="article-body article-body-blocks" @click="handleArticleContentClick">
              <div
                v-for="(block, idx) in articleRenderedBlocks"
                :key="idx"
                class="article-block"
                :class="{ 'article-block-translatable': block.translatable }"
              >
                <template v-if="block.translatable">
                  <!-- 有译文且替换模式：直接显示译文 -->
                  <div
                    v-if="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.text && paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]!.mode === 'translation'"
                    class="article-block-content article-block-translated"
                  >
                    <button
                      type="button"
                      class="translation-badge translation-badge-button"
                      title="点击恢复原文"
                      @click.stop="restoreParagraphOriginal(store.selectedArticle!.id, idx)"
                    >
                      <el-icon><Switch /></el-icon>
                      <span>译文</span>
                      <span class="translation-badge-hint">恢复原文</span>
                    </button>
                    <div v-html="renderedParagraphTranslation(paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]!.text)"></div>
                  </div>
                  <!-- 双语对照模式：原文 + 译文两行 -->
                  <div
                    v-else-if="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.text && paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]!.mode === 'comparison'"
                    class="article-block-comparison"
                  >
                    <div class="comparison-row">
                      <span class="comparison-label original-label">原文</span>
                      <div class="article-block-content article-block-original" v-html="block.html"></div>
                    </div>
                    <div class="comparison-divider"></div>
                    <div class="comparison-row">
                      <button
                        type="button"
                        class="comparison-label translation-label translation-label-button"
                        title="点击恢复原文"
                        @click.stop="restoreParagraphOriginal(store.selectedArticle!.id, idx)"
                      >
                        译文
                        <span class="translation-badge-hint">恢复原文</span>
                      </button>
                      <div class="para-translation article-body" v-html="renderedParagraphTranslation(paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]!.text)"></div>
                    </div>
                  </div>
                  <!-- 无译文：显示原文 -->
                  <div v-else class="article-block-content" v-html="block.html"></div>
                  <!-- 操作按钮区 -->
                  <div class="article-block-translate">
                    <button
                      v-if="!paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.text"
                      class="para-translate-btn"
                      :class="{ loading: paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.loading }"
                      :disabled="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.loading || translatingAll"
                      @click.stop="translateParagraph(store.selectedArticle!.id, idx, block.text, block.isHtml)"
                    >
                      <el-icon v-if="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.loading" class="is-loading"><Loading /></el-icon>
                      <el-icon v-else><Switch /></el-icon>
                      <span v-if="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.loading">翻译中…</span>
                      <span v-else>翻译</span>
                    </button>
                    <template v-else>
                      <button
                        class="para-translate-btn"
                        :class="{ loading: paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.loading }"
                        :disabled="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.loading || translatingAll"
                        @click.stop="translateParagraph(store.selectedArticle!.id, idx, block.text, block.isHtml)"
                      >
                        <el-icon v-if="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.loading" class="is-loading"><Loading /></el-icon>
                        <el-icon v-else><Refresh /></el-icon>
                        <span v-if="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]?.loading">翻译中…</span>
                        <span v-else>重新翻译</span>
                      </button>
                      <button
                        class="para-translate-btn mode-btn"
                        @click.stop="toggleParagraphMode(store.selectedArticle!.id, idx)"
                      >
                        <el-icon><CopyDocument /></el-icon>
                        <span v-if="paragraphTranslations[paragraphKey(store.selectedArticle!.id, idx)]!.mode === 'translation'">双语对照</span>
                        <span v-else>仅译文</span>
                      </button>
                    </template>
                  </div>
                </template>
                <div v-else class="article-block-content" v-html="block.html"></div>
              </div>
            </div>
            </div>
        </div>

        <!-- 底部摘要抽屉 -->
        <div ref="summaryDrawerRef" class="summary-drawer" :class="{ expanded: summaryDrawerOpen, failed: summaryFailed }" :style="summaryDrawerOpen ? { '--drawer-height': summaryDrawerHeight + 'px' } : {}">
          <div v-if="summaryDrawerOpen" class="summary-drawer-resize-bar" @mousedown.prevent="onDrawerDragStart"></div>
          <button type="button" class="summary-drawer-handle" @click="toggleSummaryDrawer" :aria-expanded="summaryDrawerOpen">
            <span class="summary-drawer-handle-label">
              <el-icon class="summary-drawer-icon"><MagicStick /></el-icon>
              <span class="summary-drawer-title-wrap">
                <strong>AI 摘要</strong>
                <span class="summary-drawer-desc">由 AI 为你总结本篇文章核心内容</span>
              </span>
            </span>
            <span class="summary-drawer-handle-center">
              <span v-if="summaryFailed && !summaryRunning" class="summary-warning summary-warning-inline">摘要生成失败，请重新生成...</span>
              <span v-else-if="summaryIncomplete && !summaryRunning" class="summary-warning summary-warning-inline">摘要内容展示不完全，请重新生成...</span>
            </span>
            <span class="summary-drawer-handle-right">
              <span class="summary-drawer-arrow" :class="{ up: !summaryDrawerOpen }">›</span>
            </span>
          </button>
          <div class="summary-drawer-body">
            <div class="summary-drawer-controls">
              <div class="summary-drawer-control-row">
                <span class="summary-drawer-label">语言</span>
                <el-select v-model="summaryLanguage" size="small" style="width: 110px" :teleported="false">
                  <el-option v-for="opt in summaryLanguageOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </div>
              <button
                class="summary-generate-btn"
                :class="{ loading: summaryRunning }"
                :disabled="summaryRunning"
                @click="runSummary"
              >
                <span class="summary-generate-btn-icon">
                  <svg v-if="!summaryRunning" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 1c.3 0 .54.22.58.51l.01.1L9 4.5a.5.5 0 0 1-.41.49l-.09.01H7.5a.5.5 0 0 1-.1-.99l.1-.01.36-.01-.28-2.49A.58.58 0 0 1 8 1ZM4.22 2.78a.58.58 0 0 1 .76-.07l.08.07 1.77 1.77a.5.5 0 0 1-.63.77l-.07-.06L4.36 3.49a.58.58 0 0 1-.14-.71ZM11.78 2.78c.2.2.23.5.07.73l-.07.08-1.77 1.77a.5.5 0 0 1-.77-.63l.06-.07 1.77-1.77c.22-.22.57-.22.71-.11ZM2.78 4.22c.2-.2.5-.23.73-.07l.08.07 1.77 1.77a.5.5 0 0 1-.63.77l-.07-.06-1.77-1.77a.58.58 0 0 1-.11-.71ZM8 5a3 3 0 1 1 0 6A3 3 0 0 1 8 5Zm5.22-.22c.22.22.22.57.11.71l-.07.08-1.77 1.77a.5.5 0 0 1-.77-.63l.06-.07 1.77-1.77a.58.58 0 0 1 .67-.09ZM1 8c0-.3.22-.54.51-.58l.1-.01 3-.01a.5.5 0 0 1 .09.99l-.09.01H1.61A.58.58 0 0 1 1 8Zm10.41-.59 3-.01a.5.5 0 0 1 .1.99l-.1.01-3 .01a.5.5 0 0 1-.1-.99l.1-.01ZM5.32 10.32a.5.5 0 0 1 .63.77l-.06.07-1.77 1.77a.58.58 0 0 1-.85-.78l.07-.08 1.98-1.75Zm5.36 0 1.98 1.75a.58.58 0 0 1-.71.86l-.08-.07-1.77-1.77a.5.5 0 0 1 .58-.77ZM8 11.5c.3 0 .54.22.58.51l.01.1.01 2.28a.58.58 0 0 1-1.16.07V14.4l-.01-2.28A.58.58 0 0 1 8 11.5Z"/>
                  </svg>
                  <svg v-else class="spin" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5" stroke-dasharray="28" stroke-dashoffset="10" stroke-linecap="round"/>
                  </svg>
                </span>
                <span>{{ summaryRunning ? '生成中…' : (summaryFailed ? '重新生成' : '生成摘要') }}</span>
              </button>
            </div>
            <div v-if="summaryRunning && summaryStepItems.length === 0" class="summary-drawer-loading">
              <span class="summary-drawer-loading-dots">摘要生成中，请稍等</span>
            </div>
            <transition-group v-if="summaryRunning" name="summary-stream" tag="div" class="summary-drawer-stream">
              <div
                v-for="step in summaryStepItems"
                :key="step.id"
                class="summary-thought-item"
                :class="step.status"
              >
                <span class="summary-thought-line"></span>
                <span class="summary-thought-dot"></span>
                <div class="summary-thought-copy">
                  <div class="summary-thought-row">
                    <strong>{{ step.title }}</strong>
                    <span v-if="step.elapsedMs !== undefined" class="summary-thought-time">{{ formatElapsed(step.elapsedMs) }}</span>
                  </div>
                  <p>{{ step.detail }}</p>
                </div>
              </div>
            </transition-group>
            <div v-if="summaryResultVisible && !summaryRunning" class="summary-drawer-result">
              <div class="summary-result-body article-body" v-html="renderedAiResult" @click="handleArticleContentClick"></div>
              <div class="summary-result-footer">
                <button class="summary-copy-btn" :class="{ copied: copyDone }" @click="copySummary">
                  <svg viewBox="0 0 16 16" fill="none">
                    <rect v-if="!copyDone" x="5" y="5" width="8" height="9" rx="1.5" stroke="currentColor" stroke-width="1.4"/>
                    <path v-if="!copyDone" d="M3 11V3.5A1.5 1.5 0 0 1 4.5 2H10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                    <path v-else d="M3 8l3.5 3.5L13 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>{{ copyDone ? '已复制' : '复制摘要' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section v-else-if="!feedManagerOpen" class="panel reader-detail-panel reader-empty-panel">
        <div class="reader-empty-state">
        </div>
      </section>

      <section v-if="feedManagerOpen" class="panel feed-manager-overlay">
        <FeedManageView embedded @close="closeFeedManager" @changed="handleFeedManagerChanged" />
      </section>

      <el-dialog v-model="homeSyncDialogOpen" title="同步结果" width="720px">
        <el-table :data="homeSyncResults" size="small" max-height="320" table-layout="fixed">
          <el-table-column prop="title" label="订阅源" min-width="160" show-overflow-tooltip />
          <el-table-column prop="url" label="URL" min-width="260" show-overflow-tooltip />
          <el-table-column label="状态" width="92">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="原因" min-width="260" show-overflow-tooltip />
          <el-table-column label="建议" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ syncSuggestion(row.message) }}</template>
          </el-table-column>
        </el-table>
      </el-dialog>
      <el-dialog
        v-model="batchDigestDialogOpen"
        title="批量导出文摘"
        width="760px"
        class="batch-digest-dialog"
        append-to-body
      >
        <div class="batch-digest-body">
          <div class="batch-digest-options">
            <el-checkbox v-model="batchIncludeSummary" @change="loadBatchDigestPreview">包含 AI 摘要</el-checkbox>
            <el-checkbox v-model="batchIncludeNote" @change="loadBatchDigestPreview">包含笔记</el-checkbox>
            <el-checkbox v-model="batchIncludeFullText" @change="loadBatchDigestPreview">包含全文</el-checkbox>
          </div>
          <div class="batch-digest-meta">
            <span>已选择 {{ batchSelectedArticles.length }} 篇</span>
            <span v-if="batchDigestPreview">可导出 {{ batchDigestPreview.exported_article_ids.length }} 篇</span>
            <span v-if="batchDigestPreview && batchIncludeSummary">包含摘要 {{ batchDigestPreview.summary_available_count }} 篇</span>
          </div>
          <el-alert
            v-if="batchDigestPreview?.skipped_article_ids.length"
            type="warning"
            :closable="false"
            show-icon
            class="batch-digest-alert"
            :title="`${batchDigestPreview.skipped_article_ids.length} 篇文章缺少标题或链接，已跳过。`"
          />
          <el-input
            v-loading="batchPreviewLoading"
            class="batch-digest-preview"
            type="textarea"
            resize="none"
            readonly
            :rows="18"
            :model-value="batchDigestPreview?.markdown || ''"
            placeholder="正在生成文摘预览..."
          />
        </div>
        <template #footer>
          <div class="batch-digest-footer">
            <el-button :icon="CopyDocument" :disabled="!batchDigestPreview" @click="copyBatchDigestPreview">复制</el-button>
            <el-button @click="batchDigestDialogOpen = false">取消</el-button>
            <el-button
              type="primary"
              :icon="Download"
              :loading="batchSavingDigest"
              :disabled="!batchDigestPreview || batchPreviewLoading"
              @click="exportBatchDigest"
            >
              导出 Markdown
            </el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowDown, Check, Close, CollectionTag, CopyDocument, Delete, Download, EditPen, Files, Loading, MagicStick, MoreFilled, Plus, Refresh, Star, Switch, Top } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Article, ArticleListItem, BatchDigestExportResponse, FeedSyncReport, LLMProvider, SummaryStreamEvent, TagSuggestionCandidate } from '../api/client'
import { getErrorMessage, rssApi } from '../api/client'
import type { ArticleListQuery } from '../stores/reader'
import { useReaderStore } from '../stores/reader'
import { apiErrorMessage, showSyncReportMessage, statusTagType, syncSuggestion } from '../utils/syncDiagnostics'
import FeedManageView from './FeedManageView.vue'

const store = useReaderStore()
const route = useRoute()
const router = useRouter()
const SIDEBAR_WIDTH_KEY = 'rssreader.sidebarWidth'
const ARTICLE_LIST_WIDTH_KEY = 'rssreader.articleListWidth'
const SIDEBAR_MIN_WIDTH = 156
const SIDEBAR_MAX_WIDTH = 360
const ARTICLE_LIST_MIN_WIDTH = 172
const ARTICLE_LIST_MAX_WIDTH = 560
const RESIZER_WIDTH = 20
const note = ref('')
const lastSavedNote = ref('')
const notePopoverOpen = ref(false)
const noteSaveState = ref<'idle' | 'saving' | 'saved' | 'failed'>('idle')
const noteLoading = ref(false)
const aiResult = ref('')
const summaryUsage = ref('')
const summaryRunning = ref(false)
const summaryStepsExpanded = ref(false)
const summaryActiveArticleId = ref<number | null>(null)
const summaryProviders = ref<LLMProvider[]>([])
const summaryProviderId = ref<number | null>(null)
const summaryMode = ref<'brief' | 'structured' | 'deep'>('structured')
const summaryLanguageOptions = [
  { label: '中文', value: 'zh' },
  { label: 'English', value: 'en' },
  { label: '日本語', value: 'ja' },
  { label: '한국어', value: 'ko' },
  { label: 'Français', value: 'fr' },
  { label: 'Deutsch', value: 'de' },
  { label: 'Español', value: 'es' },
  { label: 'Português', value: 'pt' },
  { label: 'Русский', value: 'ru' },
  { label: 'العربية', value: 'ar' },
]
function detectSystemLanguage(): string {
  const lang = navigator.language || 'zh'
  const prefix = lang.split('-')[0].toLowerCase()
  const supported = summaryLanguageOptions.map(o => o.value)
  return supported.includes(prefix) ? prefix : 'en'
}
const summaryLanguage = ref<string>(detectSystemLanguage())
const summaryMaxWords = ref(450)
const summaryModeOptions = [
  { label: '简短', value: 'brief' },
  { label: '结构化', value: 'structured' },
  { label: '深入', value: 'deep' }
]
type SummaryThoughtStep = {
  id: string
  title: string
  detail: string
  status: 'active' | 'done' | 'error'
  startedAt: number
  elapsedMs?: number
  eventType: string
}

const summaryDrawerOpen = ref(false)
const summaryDrawerHeight = ref(320)
const summaryFailed = ref(false)
const summaryStepItems = ref<SummaryThoughtStep[]>([])
const summaryDrawerRef = ref<HTMLElement | null>(null)
const summaryResultVisible = ref(false)
const copyDone = ref(false)

// 翻译相关状态
const paragraphTranslations = ref<Record<string, { text: string; loading: boolean; mode: 'translation' | 'comparison' }>>({})
const translatingAll = ref(false)

// 标题翻译
const titleTranslation = computed(() => {
  const articleId = store.selectedArticle?.id
  if (!articleId) return null
  const key = `${articleId}:title`
  return paragraphTranslations.value[key] || null
})

function translateTitle() {
  const article = store.selectedArticle
  if (!article) return
  const key = `${article.id}:title`
  translateParagraphWithKey(key, article.title)
}

function toggleTitleMode() {
  const article = store.selectedArticle
  if (!article) return
  const key = `${article.id}:title`
  const entry = paragraphTranslations.value[key]
  if (!entry) return
  paragraphTranslations.value = {
    ...paragraphTranslations.value,
    [key]: { ...entry, mode: entry.mode === 'translation' ? 'comparison' : 'translation' },
  }
}

function restoreTitleOriginal() {
  const article = store.selectedArticle
  if (!article) return
  const key = `${article.id}:title`
  const next = { ...paragraphTranslations.value }
  delete next[key]
  paragraphTranslations.value = next
}
const translationLanguage = ref<string>(detectSystemLanguage())

type SummaryCacheEntry = { result: string; usage: string; language: string }

const SUMMARY_LANGUAGE_DISPLAY_TO_CODE: Record<string, string> = {
  '中文': 'zh', 'English': 'en', '日本語': 'ja', '한국어': 'ko',
  'Français': 'fr', 'Deutsch': 'de', 'Español': 'es', 'Português': 'pt',
  'Русский': 'ru', 'العربية': 'ar',
}

function extractSummaryLanguage(prompt: string): string | null {
  const m = prompt.match(/输出语言[：:]\s*(\S+)/)
  if (!m) return null
  return SUMMARY_LANGUAGE_DISPLAY_TO_CODE[m[1]] ?? null
}
const summaryCache = new Map<number, SummaryCacheEntry>()

async function copySummary() {
  if (!aiResult.value) return
  const text = aiResult.value.replace(/^可信度[：:].+$/gm, '').replace(/\n{3,}/g, '\n\n').trim()
  await navigator.clipboard.writeText(text)
  copyDone.value = true
  setTimeout(() => { copyDone.value = false }, 2000)
}

function onDrawerDragStart(e: MouseEvent) {
  const el = summaryDrawerRef.value
  if (!el) return
  const startY = e.clientY
  const startHeight = summaryDrawerHeight.value

  const panelEl = el.closest('.reader-detail-panel') as HTMLElement | null
  const handleEl = el.querySelector('.summary-drawer-handle') as HTMLElement | null
  const panelHeight = panelEl?.clientHeight ?? window.innerHeight
  const handleHeight = handleEl?.offsetHeight ?? 44
  // reserve at least 120px for the article scroll area above the drawer
  const maxHeight = Math.floor(panelHeight - handleHeight - 120)

  const body = el.querySelector('.summary-drawer-body') as HTMLElement | null
  if (body) body.style.transition = 'none'

  const onMove = (me: MouseEvent) => {
    const next = Math.min(maxHeight, Math.max(120, startHeight + (startY - me.clientY)))
    el.style.setProperty('--drawer-height', `${next}px`)
  }
  const onUp = (me: MouseEvent) => {
    const next = Math.min(maxHeight, Math.max(120, startHeight + (startY - me.clientY)))
    summaryDrawerHeight.value = next
    if (body) body.style.transition = ''
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

const summaryDrawerTitle = computed(() => 'AI 摘要')

function toggleSummaryDrawer() {
  summaryDrawerOpen.value = !summaryDrawerOpen.value
}


const articleBodyRef = ref<HTMLElement | null>(null)
const exportingMarkdown = ref(false)
const feedManagerOpen = ref(false)
const activeFilterKey = ref<'all' | 'unread' | 'starred'>('all')
const activeFeedId = ref<number | null>(null)
const activeTagId = ref<number | null>(null)
const batchExportMode = ref(false)
const batchDigestDialogOpen = ref(false)
const batchPreviewLoading = ref(false)
const batchSavingDigest = ref(false)
const batchIncludeSummary = ref(true)
const batchIncludeNote = ref(true)
const batchDigestPreview = ref<BatchDigestExportResponse | null>(null)
const selectedBatchArticleIds = ref<number[]>([])
const batchIncludeFullText = ref(false)
const newTagName = ref('')
const newTagColor = ref('#5b8def')
const tagSearchQuery = ref('')
const aiTagLoading = ref(false)
const aiTagApplying = ref(false)
const aiTagError = ref('')
const aiTagCandidates = ref<TagSuggestionCandidate[]>([])
const selectedAiTagNames = ref<string[]>([])
const failedThumbnailKeys = ref<Set<string>>(new Set())
const failedFeedIconIds = ref<Set<number>>(new Set())
const syncingAllFeeds = ref(false)
const homeSyncDialogOpen = ref(false)
const lastHomeSyncReport = ref<FeedSyncReport | null>(null)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440)
const sidebarWidth = ref(storedPanelWidth(SIDEBAR_WIDTH_KEY, 244, SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH))
const articleListWidth = ref(storedPanelWidth(ARTICLE_LIST_WIDTH_KEY, 392, ARTICLE_LIST_MIN_WIDTH, ARTICLE_LIST_MAX_WIDTH))
const suppressNextSidebarToggle = ref(false)
const suppressNextArticleListToggle = ref(false)
const NOTE_AUTOSAVE_DELAY_MS = 900
let noteSaveTimer: number | undefined

function clampNumber(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function storedPanelWidth(key: string, fallback: number, min: number, max: number) {
  const raw = localStorage.getItem(key)
  const value = raw ? Number(raw) : fallback
  return Number.isFinite(value) ? clampNumber(value, min, max) : fallback
}

const renderedArticleHtml = computed(() => {
  const article = store.selectedArticle
  if (!article) return ''
  const primaryContent = article.cleaned_html?.trim() || article.raw_html?.trim() || ''
  if (primaryContent) return renderRichArticleContent(primaryContent, article.cleaned_markdown)
  if (article.summary?.trim()) return `<p>${escapeHtml(article.summary)}</p>`
  return '<p>这篇文章暂时没有可展示的正文内容。</p>'
})

// 正文渲染块：分块 v-for 渲染（保留原 v-html 整体效果，同时支持逐段翻译）
const articleRenderedBlocks = computed(() => {
  const article = store.selectedArticle
  if (!article) return [] as { html: string; text: string; translatable: boolean; isHtml: boolean }[]
  const primaryContent = article.cleaned_html?.trim() || article.raw_html?.trim() || ''
  const hasImages = /<img[^>]+src=/i.test(primaryContent)

  // 有图片的 HTML：从 HTML 中提取文本段和图片段混合排列
  if (primaryContent && hasImages) {
    return parseHtmlBlocks(primaryContent, article.cleaned_markdown?.trim())
  }

  // 无图片 HTML：没有 markdown 时退化为单块
  if (primaryContent && !article.cleaned_markdown?.trim()) {
    const text = htmlToPlainText(primaryContent) || article.summary?.trim() || ''
    return [{ html: primaryContent, text, translatable: !!text, isHtml: true }]
  }

  // markdown 路径
  const md = article.cleaned_markdown?.trim() || article.summary?.trim() || ''
  if (!md) return [{ html: '<p>这篇文章暂时没有可展示的正文内容。</p>', text: '', translatable: false, isHtml: false }]
  const normalized = md.replace(/\r\n/g, '\n').trim()
  const blocks = normalized.split(/\n{2,}/).filter(Boolean)
  return blocks.map((block) => {
    const isCodeFence = block.startsWith('```')
    const isHr = /^[-*_]{3,}\s*$/.test(block.trim())
    const isImageOnly = !block.replace(/!\[[^\]]*]\([^)]+\)/g, '').trim()
    const translatable = !isCodeFence && !isHr && !isImageOnly && block.trim().length > 0
    return { html: renderMarkdownBlock(block), text: block, translatable, isHtml: false }
  })
})

const currentTranslationLanguageLabel = computed(() => {
  return summaryLanguageOptions.find((o: { label: string; value: string }) => o.value === translationLanguage.value)?.label ?? translationLanguage.value
})

const hasAnyTranslation = computed(() => {
  if (!store.selectedArticle) return false
  const articleId = store.selectedArticle.id
  return Object.keys(paragraphTranslations.value).some((key) => {
    return key.startsWith(`${articleId}:`) && paragraphTranslations.value[key]?.text
  })
})

const selectedArticleTagIds = computed(() => store.selectedArticle?.tag_ids ?? [])
const filteredTagOptions = computed(() => {
  const keyword = tagSearchQuery.value.trim().toLowerCase()
  if (!keyword) return store.tags
  return store.tags.filter((tag) => tag.name.toLowerCase().includes(keyword))
})
const quickFilters = computed(() => [
  { key: 'all' as const, label: '全部文章', count: store.articleCounts.total },
  { key: 'unread' as const, label: '未读文章', count: store.articleCounts.unread },
  { key: 'starred' as const, label: '收藏', count: store.articleCounts.starred }
])

const activeFeedForMenu = computed(() => {
  if (activeFeedId.value !== null) return store.feeds.find((feed) => feed.id === activeFeedId.value) ?? null
  if (store.selectedArticle) return store.feeds.find((feed) => feed.id === store.selectedArticle?.feed_id) ?? null
  return null
})

const activeArticleQuery = computed<ArticleListQuery>(() => {
  const query: ArticleListQuery = { sort_order: store.articleSortOrder }
  if (activeFeedId.value !== null) query.feed_id = activeFeedId.value
  if (activeTagId.value !== null) query.tag_id = activeTagId.value
  if (activeFilterKey.value === 'unread') query.unread = true
  if (activeFilterKey.value === 'starred') query.starred = true
  return query
})

const filteredArticles = computed(() => store.articleItems)

const selectedBatchArticleIdSet = computed(() => new Set(selectedBatchArticleIds.value))
const batchSelectedArticles = computed(() =>
  filteredArticles.value.filter((article) => selectedBatchArticleIdSet.value.has(article.id))
)

const currentListTitle = computed(() => {
  if (activeFeedId.value !== null) return store.feeds.find((feed) => feed.id === activeFeedId.value)?.title ?? '当前订阅'
  if (activeTagId.value !== null) return `标签 · ${tagName(activeTagId.value)}`
  if (activeFilterKey.value === 'unread') return '未读文章'
  if (activeFilterKey.value === 'starred') return '收藏文章'
  return '全部文章'
})

const renderedAiResult = computed(() => {
  if (!aiResult.value) return ''
  const cleaned = aiResult.value.replace(/^可信度[：:].+$/gm, '').replace(/\n{3,}/g, '\n\n').trim()
  let html = markdownToHtml(cleaned)

  // h2 加图标
  const h2Icons: Record<string, string> = {
    // 中文
    '一句话': '💬', '概览': '💬', '概要': '💬',
    '核心': '📌', '要点': '📌', '关键要点': '📌', '重要': '📌',
    '关键词': '🏷️', '키워드': '🏷️', 'キーワード': '🏷️', 'mots-clés': '🏷️', 'schlüssel': '🏷️', 'palabras': '🏷️', 'palavras': '🏷️', 'ключев': '🏷️', 'الكلمات': '🏷️',
    '背景': '📖', '结论': '✅', '风险': '⚠️', '建议': '💡',
    '追踪': '🔍', '继续': '🔍',
    // 英文及其他语言通用词
    'overview': '💬', 'résumé': '💬', 'zusammenfassung': '💬', 'resumen': '💬', 'resumo': '💬', 'резюме': '💬', 'ملخص': '💬', '요약': '💬',
    'key': '📌', 'takeaway': '📌', 'puntos': '📌', 'points': '📌', 'wichtig': '📌', 'моменты': '📌', 'النقاط': '📌', '포인트': '📌', 'ポイント': '📌',
    'keyword': '🏷️',
    'background': '📖', 'contexte': '📖', 'hintergrund': '📖', 'contexto': '📖', 'контекст': '📖', 'الخلفية': '📖', '배경': '📖',
    'follow': '🔍', 'suivre': '🔍', 'verfolgung': '🔍', 'acompanhar': '🔍', 'следить': '🔍', '追う': '🔍', '추적': '🔍',
  }
  html = html.replace(/<h2>(.*?)<\/h2>/g, (_, text) => {
    const icon = Object.entries(h2Icons).find(([k]) => text.toLowerCase().includes(k))?.[1] ?? '▪'
    return `<h2><span class="summary-h2-icon">${icon}</span>${text}</h2>`
  })

  // 关键词段落转标签：跟在含各语言"关键词"的 h2 后面的 <p>
  html = html.replace(
    /(<h2>(?:(?!<\/h2>).)*(?:关键词|keyword|キーワード|키워드|mots-clés|schlüsselwörter|palabras\sclave|palavras-chave|ключевые\sслова|الكلمات\sالمفتاحية)(?:(?!<\/h2>).)*<\/h2>)\s*<p>([\s\S]*?)<\/p>/i,
    (_, h2, content) => {
      const tags = content.split(/[；;、,，·\s]+/).map((t: string) => t.trim()).filter(Boolean)
      const tagHtml = tags.map((t: string) => `<span class="summary-tag">${t}</span>`).join('')
      return `${h2}<div class="summary-tags">${tagHtml}</div>`
    }
  )

  return html
})

const summaryIncomplete = computed(() => {
  if (!aiResult.value) return false
  const text = aiResult.value.replace(/^可信度[：:].+$/gm, '').trim()
  // 只有明确的截断迹象才报警：末尾是省略号、逗号、分号、冒号，或以空格结尾
  return /([,，;；:：。、]|\.{2,}|…+|\s)$/.test(text)
})

const summaryClampStyle = computed(() => ({ WebkitLineClamp: String(store.summaryLineCount) }))
const hasCurrentNote = computed(() => note.value.trim().length > 0 || lastSavedNote.value.trim().length > 0)
const noteSaveStatusText = computed(() => {
  if (noteSaveState.value === 'saving') return '保存中...'
  if (noteSaveState.value === 'saved') return '已保存'
  if (noteSaveState.value === 'failed') return '保存失败'
  return '自动保存'
})
const homeSyncResults = computed(() => lastHomeSyncReport.value?.results ?? [])
const isSidebarHidden = computed(() => !store.leftSidebarVisible || viewportWidth.value <= 1220)
const isArticleListHidden = computed(() =>
  !store.articleListVisible || (viewportWidth.value <= 900 && Boolean(store.selectedArticle) && !feedManagerOpen.value)
)
const readerGridStyle = computed(() => ({
  gridTemplateColumns: [
    isSidebarHidden.value ? '0px' : `${sidebarWidth.value}px`,
    `${RESIZER_WIDTH}px`,
    isArticleListHidden.value || feedManagerOpen.value ? '0px' : `${articleListWidth.value}px`,
    feedManagerOpen.value ? '0px' : `${RESIZER_WIDTH}px`,
    'minmax(0, 1fr)'
  ].join(' ')
}))
const readerShellClass = computed(() => ({
  'sidebar-hidden': isSidebarHidden.value,
  'article-list-hidden': isArticleListHidden.value,
  'sidebar-compact': !isSidebarHidden.value && sidebarWidth.value < 210,
  'article-list-compact': !isArticleListHidden.value && articleListWidth.value < 260,
  'article-list-micro': !isArticleListHidden.value && articleListWidth.value < 210
}))

onMounted(async () => {
  window.addEventListener('rssreader:background-sync', handleBackgroundSync)
  window.addEventListener('resize', handleWindowResize)
  handleWindowResize()
  await reloadArticleList()
  await loadSummaryProviders()
  const articleId = route.query.article
  if (articleId) {
    await store.selectArticle(Number(articleId))
    void router.replace({ path: '/', query: { ...route.query, article: undefined } })
  }
  await loadNote()
  await ensureVisibleSelection()
})

onUnmounted(() => {
  clearNoteSaveTimer()
  void flushNote().catch(() => undefined)
  window.removeEventListener('rssreader:background-sync', handleBackgroundSync)
  window.removeEventListener('resize', handleWindowResize)
})

watch(
  () => store.selectedArticle?.id,
  async (newId, oldId) => {
    if (oldId !== undefined) {
      saveSummaryToCache(oldId)
      try {
        await flushNote({ articleId: oldId, content: note.value })
      } catch {
        if (store.hasArticle(oldId)) {
          ElMessage.error('保存上一条文章笔记失败')
        }
      }
    }
    clearSummaryResult()
    summaryDrawerOpen.value = false
    await loadNote()
    if (newId !== undefined) {
      const cached = summaryCache.get(newId)
      if (cached) {
        aiResult.value = cached.result
        summaryUsage.value = cached.usage
        summaryLanguage.value = cached.language
        summaryResultVisible.value = true
      } else {
        const remote = await rssApi.getCachedSummary(newId)
        if (remote?.result) {
          aiResult.value = remote.result
          summaryUsage.value = `${remote.input_tokens} 输入 / ${remote.output_tokens} 输出 tokens`
          const detectedLang = extractSummaryLanguage(remote.prompt ?? '')
          if (detectedLang) summaryLanguage.value = detectedLang
          summaryResultVisible.value = true
          summaryCache.set(newId, { result: aiResult.value, usage: summaryUsage.value, language: summaryLanguage.value })
        }
      }
    }
  }
)
watch(note, () => {
  if (noteLoading.value) return
  scheduleNoteAutoSave()
})
watch(notePopoverOpen, (open) => {
  if (!open) {
    void flushNote().catch(() => undefined)
  }
})
watch(articleRenderedBlocks, decorateArticleLinks, { flush: 'post' })
watch(filteredArticles, () => {
  void ensureVisibleSelection()
})
watch(filteredArticles, (articles) => {
  if (!batchExportMode.value) return
  const articleIds = new Set(articles.map((article) => article.id))
  selectedBatchArticleIds.value = selectedBatchArticleIds.value.filter((id) => articleIds.has(id))
  if (batchDigestDialogOpen.value) {
    void loadBatchDigestPreview()
  }
})
watch(
  () => route.query.panel,
  (panel) => {
    feedManagerOpen.value = panel === 'feeds'
  },
  { immediate: true }
)

async function handleBackgroundSync() {
  await reloadArticleList()
  await loadNote()
}

function handleWindowResize() {
  viewportWidth.value = window.innerWidth
}

function toggleSidebarVisible() {
  store.setLeftSidebarVisible(!store.leftSidebarVisible)
}

function toggleArticleListVisible() {
  if (store.articleListVisible && !store.selectedArticle && filteredArticles.value[0]) {
    void store.selectArticle(filteredArticles.value[0].id)
  }
  store.setArticleListVisible(!store.articleListVisible)
}

function toggleSidebarFromResizer() {
  if (suppressNextSidebarToggle.value) {
    suppressNextSidebarToggle.value = false
    return
  }
  toggleSidebarVisible()
}

function toggleArticleListFromResizer() {
  if (suppressNextArticleListToggle.value) {
    suppressNextArticleListToggle.value = false
    return
  }
  toggleArticleListVisible()
}

function startSidebarResize(event: PointerEvent) {
  if (isArticleListHidden.value && isSidebarHidden.value) {
    startPanelResize('article-list', event)
    return
  }
  startPanelResize('sidebar', event)
}

function startArticleListResize(event: PointerEvent) {
  startPanelResize('article-list', event)
}

function startPanelResize(kind: 'sidebar' | 'article-list', event: PointerEvent) {
  if (event.button !== 0) return
  event.preventDefault()

  const startX = event.clientX
  const startWidth = kind === 'sidebar'
    ? (store.leftSidebarVisible ? sidebarWidth.value : 0)
    : (store.articleListVisible ? articleListWidth.value : 0)
  let moved = false
  const previousCursor = document.body.style.cursor
  const previousUserSelect = document.body.style.userSelect
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  const onMove = (moveEvent: PointerEvent) => {
    const delta = moveEvent.clientX - startX
    if (Math.abs(delta) > 3) moved = true
    const next = startWidth + delta
    if (kind === 'sidebar') {
      if (next < 80) {
        store.setLeftSidebarVisible(false)
        return
      }
      const width = clampNumber(next, SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH)
      sidebarWidth.value = width
      localStorage.setItem(SIDEBAR_WIDTH_KEY, String(width))
      store.setLeftSidebarVisible(true)
      return
    }

    if (next < 100) {
      store.setArticleListVisible(false)
      return
    }
    const width = clampNumber(next, ARTICLE_LIST_MIN_WIDTH, ARTICLE_LIST_MAX_WIDTH)
    articleListWidth.value = width
    localStorage.setItem(ARTICLE_LIST_WIDTH_KEY, String(width))
    store.setArticleListVisible(true)
  }

  const onUp = () => {
    document.body.style.cursor = previousCursor
    document.body.style.userSelect = previousUserSelect
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
    if (moved) {
      if (kind === 'sidebar') suppressNextSidebarToggle.value = true
      else suppressNextArticleListToggle.value = true
      window.setTimeout(() => {
        suppressNextSidebarToggle.value = false
        suppressNextArticleListToggle.value = false
      }, 0)
    }
  }

  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp, { once: true })
}

async function handleFeedManagerChanged(options?: { reload?: boolean }) {
  if (options?.reload !== false) {
    await reloadArticleList()
  } else {
    await store.loadCounts()
  }
  await loadNote()
  if (activeFeedId.value !== null && !store.feeds.some((feed) => feed.id === activeFeedId.value)) {
    activeFeedId.value = null
  }
}

async function reloadArticleList() {
  await store.loadAll(activeArticleQuery.value)
}

async function loadMoreArticles() {
  await store.loadMore(activeArticleQuery.value)
}

function handleArticleListScroll(event: Event) {
  const target = event.currentTarget as HTMLElement | null
  if (!target || store.loadingMore || !store.pagination.hasMore) return
  const remaining = target.scrollHeight - target.scrollTop - target.clientHeight
  if (remaining < 240) {
    void loadMoreArticles()
  }
}

async function loadNote() {
  clearNoteSaveTimer()
  if (!store.selectedArticle) {
    note.value = ''
    lastSavedNote.value = ''
    noteSaveState.value = 'idle'
    return
  }
  noteLoading.value = true
  try {
    const data = await rssApi.note(store.selectedArticle.id)
    note.value = data.content_markdown
    lastSavedNote.value = data.content_markdown
    noteSaveState.value = data.content_markdown.trim() ? 'saved' : 'idle'
    await nextTick()
  } catch (error) {
    console.warn('Failed to load note', error)
    note.value = ''
    lastSavedNote.value = ''
    noteSaveState.value = 'idle'
  } finally {
    noteLoading.value = false
  }
}

async function loadSummaryProviders() {
  try {
    summaryProviders.value = await rssApi.llmProviders()
  } catch (error) {
    console.warn('Failed to load LLM providers.', error)
  }
}

async function decorateArticleLinks() {
  await nextTick()
  articleBodyRef.value?.querySelectorAll('a').forEach((link) => {
    link.setAttribute('target', '_blank')
    link.setAttribute('rel', 'noopener noreferrer')
  })
  articleBodyRef.value?.querySelectorAll('img').forEach((image) => {
    image.addEventListener(
      'error',
      () => {
        image.classList.add('image-load-failed')
      },
      { once: true }
    )
  })
}

async function ensureVisibleSelection() {
  if (!filteredArticles.value.length) {
    store.selectedArticle = null
    return
  }
  if (!filteredArticles.value.find((article) => article.id === store.selectedArticle?.id)) {
    await store.selectArticle(filteredArticles.value[0].id, { markRead: false })
  }
}

function applyQuickFilter(key: 'all' | 'unread' | 'starred') {
  exitBatchExportMode()
  activeFilterKey.value = key
  activeFeedId.value = null
  activeTagId.value = null
  closeFeedManager()
  void reloadArticleList()
}

function applyFeedFilter(feedId: number | null) {
  exitBatchExportMode()
  activeFeedId.value = feedId
  activeTagId.value = null
  activeFilterKey.value = 'all'
  closeFeedManager()
  void reloadArticleList()
}

function applyTagFilter(tagId: number | null) {
  exitBatchExportMode()
  activeTagId.value = tagId
  activeFeedId.value = null
  activeFilterKey.value = 'all'
  closeFeedManager()
  void reloadArticleList()
}

function openFeedManager() {
  exitBatchExportMode()
  feedManagerOpen.value = true
  if (route.query.panel !== 'feeds') {
    void router.replace({ path: '/', query: { ...route.query, panel: 'feeds' } })
  }
}

function closeFeedManager() {
  feedManagerOpen.value = false
  if (route.query.panel === 'feeds') {
    const nextQuery = { ...route.query }
    delete nextQuery.panel
    void router.replace({ path: '/', query: nextQuery })
  }
}

function tagArticleCount(tagId: number) {
  return store.articleCounts.by_tag[tagId] ?? 0
}

function tagName(tagId: number) {
  return store.tags.find((tag) => tag.id === tagId)?.name ?? '标签'
}

function articleThumbnail(article: ArticleListItem) {
  const src = extractImageSrc(article.summary || '')
  if (!src || failedThumbnailKeys.value.has(thumbnailKey(article, src))) return null
  return src
}

function handleThumbnailError(article: ArticleListItem) {
  const src = articleThumbnail(article)
  if (!src) return
  failedThumbnailKeys.value = new Set([...failedThumbnailKeys.value, thumbnailKey(article, src)])
}

function thumbnailKey(article: ArticleListItem, src: string) {
  return `${article.id}:${src}`
}

function handleFeedIconError(feedId: number) {
  failedFeedIconIds.value = new Set([...failedFeedIconIds.value, feedId])
}

function feedArticleCount(feedId: number) {
  return store.articleCounts.by_feed[feedId] ?? 0
}

function feedFaviconUrl(feed: { id: number; site_url?: string; url: string }) {
  if (failedFeedIconIds.value.has(feed.id)) return null
  const target = feed.site_url || feed.url
  return `https://www.google.com/s2/favicons?sz=64&domain_url=${encodeURIComponent(target)}`
}

function extractImageSrc(html: string) {
  const matched = html.match(/<img[^>]+src=["']([^"']+)["']/i)
  return matched?.[1] ?? null
}

function articleListSummary(article: ArticleListItem) {
  const source = article.summary || ''
  const text = htmlToPlainText(source)
  return text.length > 180 ? `${text.slice(0, 180).trim()}...` : text
}

function htmlToPlainText(value: string) {
  if (!value.trim()) return ''
  const withoutScripts = value.replace(/<(script|style)[^>]*>[\s\S]*?<\/\1>/gi, ' ')
  const withBreaks = withoutScripts
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|h[1-6]|li|blockquote|section|article)>/gi, '\n')
  const withoutTags = withBreaks.replace(/<[^>]+>/g, ' ')
  const parser = new DOMParser()
  const document = parser.parseFromString(withoutTags, 'text/html')
  return (document.body.textContent || withoutTags)
    .replace(/\u00a0/g, ' ')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n\s+/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function formatArticleDate(article: ArticleListItem) {
  const source = article.published_at || article.created_at
  if (!source) return ''
  const date = new Date(source)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date)
}

function readerPublishedAt(article: Article) {
  const source = article.published_at || article.created_at
  if (!source) return ''
  const date = new Date(source)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

async function createTag() {
  const name = newTagName.value.trim()
  if (!name) return
  try {
    const tag = await store.createTag({ name, color: newTagColor.value })
    newTagName.value = ''
    return tag
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '创建标签失败'))
  }
}

async function updateSelectedArticleTags(tagIds: number[]) {
  if (!store.selectedArticle) return
  await store.setArticleTags(store.selectedArticle.id, tagIds)
  if (activeTagId.value !== null) {
    await reloadArticleList()
  }
}

async function toggleSelectedArticleTag(tagId: number) {
  if (!store.selectedArticle) return
  const current = new Set(selectedArticleTagIds.value)
  if (current.has(tagId)) {
    current.delete(tagId)
  } else {
    current.add(tagId)
  }
  await updateSelectedArticleTags(Array.from(current))
}

async function createAndAssignTagFromSearch() {
  const name = tagSearchQuery.value.trim()
  if (!name || !store.selectedArticle) return
  const matchedTag = store.tags.find((tag) => tag.name.trim().toLowerCase() === name.toLowerCase())
  const tag = matchedTag ?? await store.createTag({ name, color: newTagColor.value })
  if (!selectedArticleTagIds.value.includes(tag.id)) {
    await updateSelectedArticleTags([...selectedArticleTagIds.value, tag.id])
  }
  tagSearchQuery.value = ''
}

function normalizeAiTagName(name: string) {
  return name.trim().toLowerCase()
}

function aiTagCandidateKey(candidate: TagSuggestionCandidate) {
  return `${normalizeAiTagName(candidate.name)}-${candidate.tag_id ?? 'new'}`
}

function isAiTagCandidateSelected(candidate: TagSuggestionCandidate) {
  return selectedAiTagNames.value.includes(normalizeAiTagName(candidate.name))
}

function isAiTagCandidateAssigned(candidate: TagSuggestionCandidate) {
  if (candidate.tag_id && selectedArticleTagIds.value.includes(candidate.tag_id)) return true
  const matched = store.tags.find((tag) => normalizeAiTagName(tag.name) === normalizeAiTagName(candidate.name))
  return Boolean(matched && selectedArticleTagIds.value.includes(matched.id))
}

function toggleAiTagCandidate(candidate: TagSuggestionCandidate) {
  const key = normalizeAiTagName(candidate.name)
  if (!key) return
  const next = new Set(selectedAiTagNames.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  selectedAiTagNames.value = Array.from(next)
}

function clearAiTagCandidates() {
  aiTagCandidates.value = []
  selectedAiTagNames.value = []
  aiTagError.value = ''
}

async function generateAiTags() {
  const articleId = store.selectedArticle?.id
  if (!articleId) return
  aiTagLoading.value = true
  aiTagError.value = ''
  try {
    const response = await rssApi.suggestTags(articleId)
    if (store.selectedArticle?.id !== articleId) return
    const seen = new Set<string>()
    aiTagCandidates.value = response.candidates.filter((candidate) => {
      const key = normalizeAiTagName(candidate.name)
      if (!key || seen.has(key)) return false
      seen.add(key)
      return true
    })
    selectedAiTagNames.value = aiTagCandidates.value.map((candidate) => normalizeAiTagName(candidate.name))
    if (!aiTagCandidates.value.length) {
      aiTagError.value = 'AI 没有返回可用的候选标签'
    }
  } catch (error) {
    aiTagError.value = getErrorMessage(error, 'AI 标签生成失败，请检查 Provider 配置')
    ElMessage.error(aiTagError.value)
  } finally {
    aiTagLoading.value = false
  }
}

async function applyAiTagCandidates() {
  if (!store.selectedArticle || !aiTagCandidates.value.length) return
  aiTagApplying.value = true
  try {
    const selected = new Set(selectedAiTagNames.value)
    const tagIds = new Set(selectedArticleTagIds.value)
    for (const candidate of aiTagCandidates.value) {
      if (!selected.has(normalizeAiTagName(candidate.name))) continue
      const existing = candidate.tag_id
        ? store.tags.find((tag) => tag.id === candidate.tag_id)
        : store.tags.find((tag) => normalizeAiTagName(tag.name) === normalizeAiTagName(candidate.name))
      const tag = existing ?? await store.createTag({ name: candidate.name, color: newTagColor.value })
      tagIds.add(tag.id)
    }
    await updateSelectedArticleTags(Array.from(tagIds))
    ElMessage.success('AI 标签已应用')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '应用 AI 标签失败'))
  } finally {
    aiTagApplying.value = false
  }
}

async function deleteTag(tagId: number) {
  const deletingActiveTag = activeTagId.value === tagId
  await store.deleteTag(tagId)
  if (deletingActiveTag) {
    activeTagId.value = null
    await reloadArticleList()
  } else if (activeTagId.value !== null) {
    await reloadArticleList()
  }
}

function clearNoteSaveTimer() {
  if (noteSaveTimer !== undefined) {
    window.clearTimeout(noteSaveTimer)
    noteSaveTimer = undefined
  }
}

function scheduleNoteAutoSave() {
  clearNoteSaveTimer()
  if (!store.selectedArticle) return
  if (note.value === lastSavedNote.value) {
    noteSaveState.value = note.value.trim() ? 'saved' : 'idle'
    return
  }
  noteSaveState.value = 'saving'
  noteSaveTimer = window.setTimeout(() => {
    void flushNote().catch(() => undefined)
  }, NOTE_AUTOSAVE_DELAY_MS)
}

async function saveNoteNow() {
  try {
    await flushNote({ showSuccess: true })
  } catch {
    // flushNote already updates state and shows an error for explicit saves.
  }
}

async function flushNote(options: { articleId?: number; content?: string; showSuccess?: boolean } = {}) {
  clearNoteSaveTimer()
  const articleId = options.articleId ?? store.selectedArticle?.id
  if (!articleId) return
  const content = options.content ?? note.value
  if (content === lastSavedNote.value) {
    noteSaveState.value = content.trim() ? 'saved' : 'idle'
    if (options.showSuccess) ElMessage.success('笔记已保存')
    return
  }
  noteSaveState.value = 'saving'
  try {
    await rssApi.saveNote(articleId, content)
    if (store.selectedArticle?.id === articleId && note.value === content) {
      lastSavedNote.value = content
      noteSaveState.value = content.trim() ? 'saved' : 'idle'
    }
    if (options.showSuccess) ElMessage.success('笔记已保存')
  } catch (error) {
    if (store.selectedArticle?.id === articleId && note.value === content) {
      noteSaveState.value = 'failed'
    }
    if (options.showSuccess) {
      ElMessage.error(getErrorMessage(error, '保存笔记失败'))
    }
    throw error
  }
}

async function exportMarkdown() {
  if (!store.selectedArticle) return
  exportingMarkdown.value = true
  try {
    const blob = await rssApi.exportArticleMarkdown(store.selectedArticle.id)
    triggerBrowserDownload(blob, `${safeFilename(store.selectedArticle.title)}.md`)
  } finally {
    exportingMarkdown.value = false
  }
}

async function exportDigest() {
  if (!store.selectedArticle) return
  exportingMarkdown.value = true
  try {
    await flushNote()
    const data = await rssApi.exportBatchDigestMarkdown({
      article_ids: [store.selectedArticle.id],
      include_summary: true,
      include_note: true,
      include_full_text: false
    })
    await saveMarkdownContent(data.markdown, data.filename)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '导出文摘失败'))
  } finally {
    exportingMarkdown.value = false
  }
}

function beginMultiExportMode() {
  if (!filteredArticles.value.length) {
    ElMessage.info('当前列表没有可选择的文章')
    return
  }
  batchExportMode.value = true
  batchDigestDialogOpen.value = false
  batchDigestPreview.value = null
  selectedBatchArticleIds.value = []
}

function handleArticleClick(articleId: number) {
  if (batchExportMode.value) {
    toggleBatchArticle(articleId)
    return
  }
  closeFeedManager()
  void store.selectArticle(articleId, { markRead: true })
}

function toggleArticleRead(article: ArticleListItem) {
  void store
    .toggleRead(article)
    .then(() => {
      if (activeFilterKey.value === 'unread') void reloadArticleList()
    })
    .catch((error) => {
      ElMessage.error(getErrorMessage(error, '更新已读状态失败'))
    })
}

function toggleArticleStar(article: ArticleListItem) {
  void store
    .toggleStar(article)
    .then(() => {
      if (activeFilterKey.value === 'starred') void reloadArticleList()
    })
    .catch((error) => {
      ElMessage.error(getErrorMessage(error, '更新收藏状态失败'))
    })
}

function handleExportCommand(command: string) {
  if (command === 'digest') void exportDigest()
  if (command === 'markdown') void exportMarkdown()
}

function isBatchArticleSelected(articleId: number) {
  return selectedBatchArticleIdSet.value.has(articleId)
}

function toggleBatchArticle(articleId: number) {
  const selected = new Set(selectedBatchArticleIds.value)
  if (selected.has(articleId)) {
    selected.delete(articleId)
  } else {
    selected.add(articleId)
  }
  selectedBatchArticleIds.value = Array.from(selected)
  if (batchDigestDialogOpen.value) {
    void loadBatchDigestPreview()
  }
}

function selectAllBatchArticles() {
  selectedBatchArticleIds.value = filteredArticles.value.map((article) => article.id)
  if (batchDigestDialogOpen.value) {
    void loadBatchDigestPreview()
  }
}

function clearBatchSelection() {
  selectedBatchArticleIds.value = []
  batchDigestPreview.value = null
}

function exitBatchExportMode() {
  batchExportMode.value = false
  batchDigestDialogOpen.value = false
  batchDigestPreview.value = null
  selectedBatchArticleIds.value = []
}

function selectedBatchArticleIdsInListOrder() {
  return batchSelectedArticles.value.map((article) => article.id)
}

async function openBatchDigestDialog() {
  if (!batchSelectedArticles.value.length) {
    ElMessage.warning('请先选择要导出的文章')
    return
  }
  try {
    await flushNote()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '保存当前笔记失败，请稍后重试'))
    return
  }
  batchDigestDialogOpen.value = true
  await loadBatchDigestPreview()
}

async function loadBatchDigestPreview() {
  const articleIds = selectedBatchArticleIdsInListOrder()
  if (!articleIds.length) {
    batchDigestPreview.value = null
    return
  }
  batchPreviewLoading.value = true
  try {
    batchDigestPreview.value = await rssApi.exportBatchDigestMarkdown({
      article_ids: articleIds,
      include_summary: batchIncludeSummary.value,
      include_note: batchIncludeNote.value,
      include_full_text: batchIncludeFullText.value
    })
  } catch (error) {
    batchDigestPreview.value = null
    ElMessage.error(getErrorMessage(error, '生成批量文摘失败'))
  } finally {
    batchPreviewLoading.value = false
  }
}

async function copyBatchDigestPreview() {
  const markdown = batchDigestPreview.value?.markdown
  if (!markdown) return
  try {
    await copyText(markdown)
    ElMessage.success('文摘已复制')
  } catch {
    ElMessage.error('复制失败，请手动选择预览内容复制')
  }
}

async function exportBatchDigest() {
  if (!batchDigestPreview.value) return
  batchSavingDigest.value = true
  try {
    await saveMarkdownContent(batchDigestPreview.value.markdown, batchDigestPreview.value.filename)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '导出批量文摘失败'))
  } finally {
    batchSavingDigest.value = false
  }
}

async function saveMarkdownContent(markdown: string, filename: string) {
  if (window.rssReaderDesktop?.saveMarkdown) {
    const result = await window.rssReaderDesktop.saveMarkdown({
      content: markdown,
      suggestedFilename: filename
    })
    if (!result.canceled) {
      ElMessage.success('Markdown 已导出')
    }
    return
  }
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  triggerBrowserDownload(blob, filename)
  ElMessage.success('Markdown 已开始下载')
}

async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  textarea.remove()
}

function handleListMenuCommand(command: string) {
  if (command === 'sync') void syncAll()
  if (command === 'batch-export') beginMultiExportMode()
  if (command === 'sort:newest') {
    store.setArticleSortOrder('newest')
    void reloadArticleList()
  }
  if (command === 'sort:oldest') {
    store.setArticleSortOrder('oldest')
    void reloadArticleList()
  }
  if (command === 'toggle:thumbnails') store.setShowThumbnails(!store.showThumbnails)
  if (command === 'unsubscribe') void unsubscribeCurrentFeed()
}

function handleFeedSectionCommand(command: string) {
  if (command === 'manage-feeds') openFeedManager()
  if (command === 'sync-feeds') void syncAll()
}

async function unsubscribeCurrentFeed() {
  const feed = activeFeedForMenu.value
  if (!feed) return
  await rssApi.deleteFeed(feed.id)
  activeFeedId.value = null
  await reloadArticleList()
}

function decreaseSummaryLines() {
  store.setSummaryLineCount(Math.max(1, store.summaryLineCount - 1))
}

function increaseSummaryLines() {
  store.setSummaryLineCount(Math.min(5, store.summaryLineCount + 1))
}

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function isBrowserExternalUrl(url: string) {
  try {
    const parsed = new URL(url.trim())
    return ['http:', 'https:', 'mailto:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

async function openExternalLink(url: string) {
  if (!isBrowserExternalUrl(url)) return false

  try {
    if (window.rssReaderDesktop?.openExternal) {
      const result = await window.rssReaderDesktop.openExternal(url)
      if (!result.ok) {
        ElMessage.error(result.message || '无法打开链接')
        return false
      }
      return true
    }

    const opened = window.open(url, '_blank', 'noopener,noreferrer')
    if (!opened) {
      ElMessage.error('无法打开链接')
      return false
    }
    return true
  } catch {
    ElMessage.error('无法打开链接')
    return false
  }
}

function handleExternalLinkClick(event: MouseEvent) {
  const link = event.currentTarget as HTMLAnchorElement | null
  const href = link?.getAttribute('href') || link?.href
  if (!href || !isBrowserExternalUrl(href)) return
  event.preventDefault()
  void openExternalLink(href)
}

function handleArticleContentClick(event: MouseEvent) {
  const target = event.target as Element | null
  const link = target?.closest('a[href]') as HTMLAnchorElement | null
  const href = link?.getAttribute('href') || ''
  if (!href || !isBrowserExternalUrl(href)) return
  event.preventDefault()
  void openExternalLink(href)
}

function safeFilename(name: string) {
  return name.replace(/[\\/:*?"<>|]/g, '_').slice(0, 80) || 'article'
}

function escapeHtml(value: string) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

function renderRichArticleContent(primaryContent: string, cleanedMarkdown?: string) {
  if (looksLikeHtml(primaryContent)) return primaryContent
  const markdownSource = normalizeRssTextPlaceholders(cleanedMarkdown?.trim() || primaryContent)
  if (looksLikeMarkdown(markdownSource)) return markdownToHtml(markdownSource)
  return `<p>${renderMarkdownInline(markdownSource).replace(/\n/g, '<br />')}</p>`
}

function renderTitleInlineHtml(value: string) {
  return renderMarkdownInline(value, { allowLinks: false })
}

function normalizeRssTextPlaceholders(value: string) {
  return value.replace(/\[Image:\s*(https?:\/\/[^\]\s]+)\]/g, '![]($1)')
}

function looksLikeHtml(value: string) {
  return /<\/?[a-z][\s\S]*>/i.test(value)
}

function looksLikeMarkdown(value: string) {
  return /(^|\n)\s{0,3}(#{1,6}\s|[-*+]\s|\d+\.\s|>\s)|(```|`[^`]+`|\*\*[^*]+\*\*|!\[[^\]]*]\([^)]+\)|\[[^\]]+\]\([^)]+\)|\[Image:\s*https?:\/\/[^\]]+\])/m.test(value)
}

function markdownToHtml(markdown: string) {
  const normalized = markdown.replace(/\r\n/g, '\n').trim()
  const blocks = normalized.split(/\n{2,}/).filter(Boolean)
  return blocks.map(renderMarkdownBlock).join('')
}

function renderMarkdownBlock(block: string): string {
  const lines = block.split('\n')
  if (lines[0]?.startsWith('```') && lines[lines.length - 1]?.startsWith('```')) {
    const code = lines.slice(1, -1).join('\n')
    return `<pre><code>${escapeHtml(code)}</code></pre>`
  }

  const heading = lines[0]?.match(/^\s*(#{1,6})\s+(.+)$/)
  if (heading) {
    const level = heading[1].length
    const headingHtml = `<h${level}>${renderMarkdownInline(heading[2])}</h${level}>`
    const rest = lines.slice(1).filter(Boolean)
    if (!rest.length) return headingHtml
    return headingHtml + renderMarkdownBlock(rest.join('\n'))
  }

  if (lines.every((line) => /^\s*[-*+]\s+/.test(line))) {
    const items = lines.map((line) => `<li>${renderMarkdownInline(line.replace(/^\s*[-*+]\s+/, ''))}</li>`)
    return `<ul>${items.join('')}</ul>`
  }

  if (lines.every((line) => /^\s*\d+\.\s+/.test(line))) {
    const items = lines.map((line) => `<li>${renderMarkdownInline(line.replace(/^\s*\d+\.\s+/, ''))}</li>`)
    return `<ol>${items.join('')}</ol>`
  }

  if (lines.every((line) => /^\s*>\s?/.test(line))) {
    const content = lines.map((line) => line.replace(/^\s*>\s?/, '')).join('<br />')
    return `<blockquote>${renderMarkdownInline(content)}</blockquote>`
  }

  return `<p>${lines.map((line) => renderMarkdownInline(line)).join('<br />')}</p>`
}

// 从含图片的 HTML 中提取混合块：图片段单独展示，文本段可翻译
function parseHtmlBlocks(html: string, markdownFallback?: string): { html: string; text: string; translatable: boolean; isHtml: boolean }[] {
  // 用 <img> 标签切分 HTML
  const imgRegex = /(<img[^>]+src="[^"]+"[^>]*\/?>)/gi
  const segments = html.split(imgRegex)
  const result: { html: string; text: string; translatable: boolean; isHtml: boolean }[] = []
  const mdText = markdownFallback || htmlToPlainText(html)

  for (const segment of segments) {
    if (!segment.trim()) continue
    if (/^<img[^>]+>/i.test(segment.trim())) {
      // 图片段：直接渲染，不可翻译
      result.push({ html: segment.trim(), text: '', translatable: false, isHtml: true })
    } else {
      // 文本段：可翻译，保留完整 HTML 原文发送给翻译 agent
      const plainText = htmlToPlainText(segment)
      if (!plainText.trim()) continue
      // 用原始 HTML（保留链接/粗体/排版）作为翻译输入
      result.push({ html: segment.trim(), text: segment.trim(), translatable: true, isHtml: true })
    }
  }
  return result.length ? result : [{ html, text: mdText, translatable: !!mdText, isHtml: true }]
}

// 简易 Markdown 块解析：按双换行切块，识别代码块/ hr 不可翻译
function parseTranslatableBlocks(markdown: string): { text: string; translatable: boolean }[] {
  const normalized = markdown.replace(/\r\n/g, '\n').trim()
  if (!normalized) return []
  const blocks = normalized.split(/\n{2,}/).filter(Boolean)
  return blocks.map((block) => {
    const isCodeFence = block.startsWith('```')
    const isHr = /^[-*_]{3,}\s*$/.test(block.trim())
    const isImageOnly = !block.replace(/!\[[^\]]*]\([^)]+\)/g, '').trim()
    const translatable = !isCodeFence && !isHr && !isImageOnly && block.trim().length > 0
    return { text: block, translatable }
  }).filter((b) => b.translatable || b.text.trim())
}

function renderMarkdownInline(value: string, options: { allowLinks?: boolean } = {}) {
  let html = escapeHtml(value)
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')
  if (options.allowLinks !== false) {
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
  } else {
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1')
  }
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  return html
}

function saveSummaryToCache(articleId: number) {
  if (aiResult.value) {
    summaryCache.set(articleId, { result: aiResult.value, usage: summaryUsage.value, language: summaryLanguage.value })
  }
}

function clearSummaryResult() {
  aiResult.value = ''
  summaryUsage.value = ''
  summaryStepItems.value = []
  summaryStepsExpanded.value = false
  summaryRunning.value = false
  summaryActiveArticleId.value = null
  summaryFailed.value = false
  summaryResultVisible.value = false
}

async function runSummary() {
  const articleId = store.selectedArticle?.id
  if (!articleId) return
  summaryRunning.value = true
  summaryFailed.value = false
  summaryDrawerOpen.value = true
  summaryActiveArticleId.value = articleId
  summaryStepsExpanded.value = true
  aiResult.value = ''
  summaryUsage.value = ''
  summaryStepItems.value = []

  // 确保抽屉有足够高度展示步骤流（controls ~60px + 3条步骤 ~180px + padding）
  const MIN_RUNNING_HEIGHT = 280
  if (summaryDrawerHeight.value < MIN_RUNNING_HEIGHT) {
    const panelEl = summaryDrawerRef.value?.closest('.reader-detail-panel') as HTMLElement | null
    const panelHeight = panelEl?.clientHeight ?? window.innerHeight
    const handleH = (summaryDrawerRef.value?.querySelector('.summary-drawer-handle') as HTMLElement | null)?.offsetHeight ?? 44
    const maxH = Math.floor(panelHeight - handleH - 120)
    summaryDrawerHeight.value = Math.min(maxH, Math.max(MIN_RUNNING_HEIGHT, summaryDrawerHeight.value))
    summaryDrawerRef.value?.style.setProperty('--drawer-height', `${summaryDrawerHeight.value}px`)
  }

  // 检查文章是否无正文或正文过短，如果是则先尝试拉取原文
  const article = store.selectedArticle
  const contentText = article?.cleaned_html?.trim() || article?.raw_html?.trim() || article?.cleaned_markdown?.trim() || ''
  const MIN_CONTENT_LENGTH = 280
  const hasEnoughContent = contentText.length >= MIN_CONTENT_LENGTH
  if (!hasEnoughContent && article?.url) {
    appendSummaryStep({
      type: 'fetch_content',
      title: '拉取原文',
      detail: '文章暂无正文，正在从源网页抓取完整内容...'
    })
    try {
      const refreshed = await rssApi.refreshArticleContent(articleId)
      store.replaceArticle(refreshed)
      appendSummaryStep({
        type: 'fetch_done',
        title: '原文拉取完成',
        detail: '已成功获取原文内容，开始生成摘要。'
      })
    } catch (error) {
      appendSummaryStep({
        type: 'fetch_failed',
        title: '原文拉取失败',
        detail: getErrorMessage(error, '无法从源网页获取内容，将基于标题生成摘要')
      })
    }
  }

  try {
    await rssApi.streamSummary(articleId, {
      provider_id: summaryProviderId.value,
      refresh: true,
      mode: summaryMode.value,
      language: summaryLanguage.value,
      max_words: summaryMaxWords.value
    }, (event) => {
      if (summaryActiveArticleId.value !== articleId || store.selectedArticle?.id !== articleId) return
      handleSummaryStreamEvent(event)
    })
    ElMessage.success('摘要已生成')
  } catch (error) {
    summaryFailed.value = true
    failSummarySteps(getErrorMessage(error, '摘要生成失败，请检查 Provider 配置'))
    ElMessage.error(getErrorMessage(error, '摘要生成失败，请检查 Provider 配置'))
  } finally {
    if (summaryActiveArticleId.value === articleId) {
      summaryRunning.value = false
      summaryActiveArticleId.value = null
    }
  }
}

function handleSummaryStreamEvent(event: SummaryStreamEvent) {
  if (event.type === 'result' && event.result) {
    const resultText = event.result.result
    const usage = `${event.result.input_tokens} 输入 / ${event.result.output_tokens} 输出 tokens`
    markSummaryStepsDone()
    aiResult.value = resultText
    summaryUsage.value = usage
    if (!summaryResultVisible.value) {
      const panelEl = summaryDrawerRef.value?.closest('.reader-detail-panel') as HTMLElement | null
      const panelH = panelEl?.clientHeight ?? window.innerHeight
      const handleH = (summaryDrawerRef.value?.querySelector('.summary-drawer-handle') as HTMLElement | null)?.offsetHeight ?? 44
      const maxH = Math.floor(panelH - handleH - 120)
      const targetHeight = Math.round(panelH / 3)
      if (summaryDrawerHeight.value < targetHeight) {
        summaryDrawerHeight.value = Math.min(maxH, Math.max(120, targetHeight))
      }
    }
    summaryResultVisible.value = true
    summaryStepItems.value = []
    return
  }
  if (event.type === 'done') {
    markSummaryStepsDone()
    return
  }
  if (event.type === 'error') {
    summaryFailed.value = true
    failSummarySteps(event.detail || '摘要生成失败，请检查 Provider 配置、Ollama 服务或网络连接后重试。')
    return
  }
  appendSummaryStep(event)
}

function appendSummaryStep(event: SummaryStreamEvent) {
  const now = Date.now()
  summaryStepItems.value = summaryStepItems.value.map((step) => (
    step.status === 'active'
      ? { ...step, status: 'done' as const, elapsedMs: now - step.startedAt }
      : step
  ))
  summaryStepItems.value.push({
    id: `${event.type}-${summaryStepItems.value.length}-${now}`,
    title: event.title || summaryEventTitle(event.type),
    detail: event.detail || summaryEventDetail(event),
    status: 'active',
    startedAt: now,
    eventType: event.type
  })
}

function markSummaryStepsDone() {
  const now = Date.now()
  summaryStepItems.value = summaryStepItems.value.map((step) => (
    step.status === 'active'
      ? { ...step, status: 'done' as const, elapsedMs: now - step.startedAt }
      : step
  ))
}

function failSummarySteps(detail: string) {
  const now = Date.now()
  summaryStepItems.value = [
    ...summaryStepItems.value.map((step) => (
      step.status === 'active'
        ? { ...step, status: 'done' as const, elapsedMs: now - step.startedAt }
        : step
    )),
    {
      id: `error-${now}`,
      title: '生成失败',
      detail,
      status: 'error',
      startedAt: now,
      eventType: 'error'
    }
  ]
  summaryStepsExpanded.value = true
}

function summaryEventTitle(type: string) {
  const titles: Record<string, string> = {
    prepare: '读取文章上下文',
    budget: '评估上下文预算',
    chunk_plan: '切分长文上下文',
    chunk_start: '提取片段事实',
    chunk_done: '片段事实完成',
    compact_plan: '规划上下文压缩',
    compact_start: '压缩中间笔记',
    compact_done: '中间笔记压缩完成',
    final_start: '合成最终摘要',
    final_done: '最终摘要完成',
    save_start: '保存摘要结果',
    save_done: '摘要结果已保存',
    cache_hit: '读取已有摘要'
  }
  return titles[type] || '处理摘要任务'
}

function summaryEventDetail(event: SummaryStreamEvent) {
  if (event.usage) return `${event.usage.input_tokens} 输入 / ${event.usage.output_tokens} 输出 tokens`
  if (event.estimated_tokens && event.input_budget) return `约 ${event.estimated_tokens} tokens，预算 ${event.input_budget} tokens。`
  return '后端已推进到该步骤。'
}

function formatElapsed(value: number) {
  if (value < 1000) return `${value}ms`
  return `${(value / 1000).toFixed(value < 10000 ? 1 : 0)}s`
}

// 段落键：按文章 id + 段落索引生成
function paragraphKey(articleId: number, index: number) {
  return `${articleId}:${index}`
}

// 渲染单段译文为 HTML（HTML 保真模式直接返回原文，否则 markdown 转 HTML）
function renderedParagraphTranslation(text: string): string {
  if (!text) return ''
  // 译文含 HTML 标签则直接渲染
  if (looksLikeHtml(text)) return text
  return markdownToHtml(text)
}

// 渲染标题译文
function renderedTitleTranslation(text: string): string {
  if (!text) return ''
  if (looksLikeHtml(text)) return text
  return renderTitleInlineHtml(text)
}

// 翻译正文中的单一段落（通过指定 key）
async function translateParagraphWithKey(key: string, sourceText: string, isHtml: boolean = false) {
  const prev = paragraphTranslations.value[key]
  if (prev?.loading) return
  paragraphTranslations.value = {
    ...paragraphTranslations.value,
    [key]: { text: prev?.text ?? '', loading: true, mode: prev?.mode ?? 'comparison' },
  }
  try {
    const res = await rssApi.translateSegment({
      text: sourceText,
      target_language: translationLanguage.value,
      source_language: 'auto',
      preserve_html: isHtml,
      preserve_markdown: !isHtml,
    })
    paragraphTranslations.value = {
      ...paragraphTranslations.value,
      [key]: { text: res.text, loading: false, mode: 'comparison' },
    }
  } catch (error) {
    paragraphTranslations.value = {
      ...paragraphTranslations.value,
      [key]: { text: prev?.text ?? '', loading: false, mode: prev?.mode ?? 'translation' },
    }
    ElMessage.error(getErrorMessage(error, '该段翻译失败，请检查 Provider 配置'))
  }
}

// 翻译正文中的单一段落
async function translateParagraph(articleId: number, index: number, sourceText: string, isHtml: boolean = false) {
  const key = paragraphKey(articleId, index)
  translateParagraphWithKey(key, sourceText, isHtml)
}

// 切换某段译文的展示模式
function toggleParagraphMode(articleId: number, index: number) {
  const key = paragraphKey(articleId, index)
  const entry = paragraphTranslations.value[key]
  if (!entry) return
  paragraphTranslations.value = {
    ...paragraphTranslations.value,
    [key]: { ...entry, mode: entry.mode === 'translation' ? 'comparison' : 'translation' },
  }
}

function restoreParagraphOriginal(articleId: number, index: number) {
  const key = paragraphKey(articleId, index)
  const next = { ...paragraphTranslations.value }
  delete next[key]
  paragraphTranslations.value = next
}

// 清除当前文章的所有翻译
function clearAllTranslations() {
  if (!store.selectedArticle) return
  const articleId = store.selectedArticle.id
  const next: typeof paragraphTranslations.value = {}
  for (const [key, value] of Object.entries(paragraphTranslations.value)) {
    if (!key.startsWith(`${articleId}:`)) {
      next[key] = value
    }
  }
  paragraphTranslations.value = next
  ElMessage.success('已清除全部翻译')
}

const allTranslatedInComparisonMode = computed(() => {
  if (!store.selectedArticle) return false
  const articleId = store.selectedArticle.id
  const keys = Object.keys(paragraphTranslations.value).filter(k => k.startsWith(`${articleId}:`))
  if (!keys.length) return false
  return keys.every(k => paragraphTranslations.value[k]?.mode === 'comparison')
})

// 处理翻译下拉菜单命令
function handleTranslationCommand(command: string) {
  if (command.startsWith('lang:')) {
    translationLanguage.value = command.slice(5)
    const label = summaryLanguageOptions.find((o: { label: string; value: string }) => o.value === translationLanguage.value)?.label ?? translationLanguage.value
    ElMessage.success(`目标语言已设为 ${label}`)
  } else if (command === 'clear-all') {
    clearAllTranslations()
  } else if (command === 'toggle-all-mode') {
    const targetMode = allTranslatedInComparisonMode.value ? 'translation' : 'comparison'
    const articleId = store.selectedArticle?.id
    if (!articleId) return
    const next = { ...paragraphTranslations.value }
    for (const key of Object.keys(next)) {
      if (key.startsWith(`${articleId}:`) && next[key]?.text) {
        next[key] = { ...next[key], mode: targetMode as 'translation' | 'comparison' }
      }
    }
    paragraphTranslations.value = next
    ElMessage.success(targetMode === 'comparison' ? '已全部切换为双语对照' : '已全部切换为仅译文')
  }
}

// 顶部"翻译全文"按钮：逐段翻译所有可翻译段落
async function runTranslate() {
  const article = store.selectedArticle
  if (!article) return
  const blocks = articleRenderedBlocks.value
  if (!blocks.length) {
    ElMessage.warning('当前文章没有可翻译的正文段落')
    return
  }
  if (translatingAll.value) return
  translatingAll.value = true
  try {
    // 先翻译标题（始终重新翻译以匹配新语言）
    const titleKey = `${article.id}:title`
    if (article.title) {
      await translateParagraphWithKey(titleKey, article.title)
    }
    for (let i = 0; i < blocks.length; i++) {
      const b = blocks[i]
      if (!b.translatable || !b.text.trim()) continue
      await translateParagraph(article.id, i, b.text, b.isHtml)
    }
    ElMessage.success('全文翻译完成')
  } finally {
    translatingAll.value = false
  }
}

async function syncAll() {
  if (syncingAllFeeds.value) return
  syncingAllFeeds.value = true
  try {
    const report = await rssApi.syncAll()
    lastHomeSyncReport.value = report
    await reloadArticleList()
    await loadNote()
    showSyncReportMessage(report)
    if (report.failed > 0) {
      homeSyncDialogOpen.value = true
    }
  } catch (error) {
    ElMessage.error(apiErrorMessage(error, '同步全部失败，请稍后重试'))
  } finally {
    syncingAllFeeds.value = false
  }
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    success: '成功',
    failed: '失败',
    skipped: '跳过',
    pending: '待同步'
  }
  return labels[status] || status
}

async function exportNote() {
  if (!store.selectedArticle) return
  try {
    await flushNote()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '保存笔记失败，请稍后重试'))
    return
  }
  const filename = `${safeFilename(store.selectedArticle.title)}-note.md`
  const content = note.value?.trim() ? note.value : ''
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  triggerBrowserDownload(blob, filename)
}
</script>

<style scoped>
.reader-shell {
  position: relative;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.reader-shell.sidebar-hidden .sidebar-panel {
  display: none;
}

.reader-shell.article-list-hidden .article-list-panel {
  display: none;
}

.reader-shell.sidebar-hidden .feed-manager-overlay {
  grid-column: 3 / 6;
}

.sidebar-panel {
  grid-column: 1;
  grid-row: 1;
}

.sidebar-resizer {
  grid-column: 2;
  grid-row: 1;
}

.article-list-panel {
  grid-column: 3;
  grid-row: 1;
}

.article-list-resizer {
  grid-column: 4;
  grid-row: 1;
}

.reader-detail-panel {
  grid-column: 5;
  grid-row: 1;
}

.reader-resizer {
  position: relative;
  z-index: 5;
  height: 100%;
  min-width: 20px;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    linear-gradient(
      to right,
      transparent 0,
      transparent calc(50% - 0.5px),
      color-mix(in srgb, var(--app-border) 86%, transparent 14%) calc(50% - 0.5px),
      color-mix(in srgb, var(--app-border) 86%, transparent 14%) calc(50% + 0.5px),
      transparent calc(50% + 0.5px),
      transparent 100%
    );
  transition: background-color 0.18s ease;
}

.reader-resizer:hover {
  background-color: color-mix(in srgb, var(--theme-accent) 6%, transparent 94%);
}

.reader-resizer-toggle {
  width: 28px;
  height: 42px;
  border: 1px solid color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-strong) 94%, var(--app-bg) 6%);
  color: color-mix(in srgb, currentColor 62%, transparent 38%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  font-size: 17px;
  font-weight: 800;
  line-height: 1;
  cursor: pointer;
  box-shadow: 0 6px 18px color-mix(in srgb, var(--app-text) 6%, transparent 94%);
  transition: border-color 0.18s ease, color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.reader-resizer-toggle:hover {
  border-color: color-mix(in srgb, var(--theme-accent) 46%, var(--app-border) 54%);
  background: color-mix(in srgb, var(--theme-accent) 10%, var(--app-surface) 90%);
  color: var(--theme-accent);
  transform: scale(1.04);
}

.sidebar-panel {
  height: 100%;
  min-height: 0;
  padding: 10px 14px 16px;
  background: color-mix(in srgb, var(--app-surface-strong) 38%, var(--app-bg) 62%);
  border-color: color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 0;
  border-width: 0 1px 0 0;
  box-shadow: none;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  position: sticky;
  top: 0;
  z-index: 2;
  margin: 0 0 8px;
  padding: 4px 0 6px;
  background: transparent;
  border-bottom: 0;
}

.sidebar-header h2,
.article-list-header h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
}

.sidebar-static-filters,
.sidebar-group-content {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
  flex: 0 0 auto;
}

.sidebar-tag-scrollbar {
  flex: 0 1 auto;
  max-height: min(34vh, 320px);
  min-height: 0;
  margin-bottom: 14px;
}

.sidebar-tag-list {
  margin-bottom: 0;
  align-content: start;
  padding-right: 4px;
  padding-bottom: 4px;
}

.sidebar-primary-link,
.sidebar-filter-button,
.sidebar-feed-button,
.sidebar-group-toggle {
  width: 100%;
  border: 0;
  border-radius: 12px;
  padding: 10px 11px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
}

.sidebar-primary-link.active,
.sidebar-filter-button.active,
.sidebar-feed-button.active {
  background: color-mix(in srgb, var(--theme-accent) 16%, var(--app-surface) 84%);
}

.sidebar-group-toggle {
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  margin-bottom: 8px;
}

.sidebar-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.sidebar-section-title {
  font-size: 15px;
  font-weight: 800;
}

.sidebar-section-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.sidebar-section-action {
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 10px;
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  color: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.sidebar-feed-scrollbar {
  flex: 1 1 auto;
  min-height: 0;
}

.sidebar-feed-list {
  margin-bottom: 0;
  align-content: start;
  padding-bottom: 8px;
  padding-right: 4px;
}

.reader-shell.sidebar-compact .sidebar-panel {
  padding-inline: 8px;
}

.reader-shell.sidebar-compact .sidebar-header h2,
.reader-shell.sidebar-compact .sidebar-section-title {
  font-size: 14px;
}

.reader-shell.sidebar-compact .sidebar-primary-link,
.reader-shell.sidebar-compact .sidebar-filter-button,
.reader-shell.sidebar-compact .sidebar-feed-button,
.reader-shell.sidebar-compact .sidebar-group-toggle {
  padding-inline: 8px;
  gap: 6px;
}

.sidebar-chevron {
  transition: transform 0.25s ease;
}

.sidebar-chevron.expanded {
  transform: rotate(90deg);
}

.sidebar-filter-count {
  min-width: 26px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-border) 72%, var(--app-surface) 28%);
  font-size: 12px;
  text-align: center;
}

.tag-create-row {
  display: grid;
  grid-template-columns: 1fr 46px auto;
  gap: 8px;
}

.tag-color-input {
  width: 46px;
  height: 32px;
  border: 1px solid color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  border-radius: 10px;
  background: transparent;
  padding: 2px;
}

.tag-filter-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.tag-filter-label span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex: 0 0 auto;
}

.tag-filter-actions,
.tag-selection-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
}

.tag-delete-action {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: color-mix(in srgb, currentColor 42%, transparent 58%);
  cursor: pointer;
  transition: all 0.16s ease;
}

.tag-delete-action:hover,
.tag-delete-action:focus-visible {
  outline: none;
  background: color-mix(in srgb, var(--el-color-danger) 12%, var(--app-surface) 88%);
  color: color-mix(in srgb, var(--el-color-danger) 86%, currentColor 14%);
}

.sidebar-feed-button {
  width: 100%;
  border: 0;
  border-radius: 14px;
  padding: 9px 10px;
  background: transparent;
  color: inherit;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  overflow: hidden;
  flex: 0 0 auto;
}

.sidebar-feed-mark {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  overflow: hidden;
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  border: 1px solid color-mix(in srgb, var(--app-border) 78%, transparent 22%);
}

.sidebar-feed-icon {
  width: 14px;
  height: 14px;
  object-fit: contain;
}

.sidebar-feed-icon-fallback,
.reader-source-icon-fallback {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--theme-accent) 72%, white 28%);
}

.sidebar-feed-name {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
  display: block;
}

.sidebar-feed-article-count {
  min-width: 28px;
  margin-left: auto;
  text-align: right;
  color: color-mix(in srgb, currentColor 56%, transparent 44%);
  font-size: 12px;
  font-weight: 700;
}

.article-list-panel {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-y;
  background: color-mix(in srgb, var(--app-surface-strong) 38%, var(--app-bg) 62%);
  border-color: color-mix(in srgb, var(--app-border) 76%, transparent 24%);
  border-radius: 0;
  border-width: 0 1px 0 0;
  box-shadow: none;
  padding: 16px 14px 20px;
}

.reader-shell.article-list-compact .article-list-panel {
  padding-inline: 10px;
}

.reader-shell.article-list-compact .article-list-header {
  gap: 8px;
}

.reader-shell.article-list-compact .article-list-header h2 {
  font-size: 15px;
}

.reader-shell.article-list-compact .article-card {
  min-height: 74px;
  padding: 9px 10px;
}

.reader-shell.article-list-compact .article-card-main.with-thumbnail {
  grid-template-columns: 1fr;
}

.reader-shell.article-list-compact .article-card-thumb {
  display: none;
}

.reader-shell.article-list-compact .article-card-summary,
.reader-shell.article-list-micro .article-card-tags,
.reader-shell.article-list-micro .article-card-source {
  display: none;
}

.reader-shell.article-list-compact .article-card-meta-row {
  grid-template-columns: 1fr;
  gap: 4px;
}

.reader-shell.article-list-compact .article-card-meta-right {
  justify-content: space-between;
}

.reader-shell.article-list-compact .article-card-copy h3 {
  font-size: 13px;
}

.reader-shell.article-list-compact .article-action-button {
  width: 22px;
  height: 22px;
}

.reader-shell.article-list-micro .article-card-date {
  text-align: left;
}

.summary-result-alert {
  margin: 18px 0 0;
}

.summary-thought-panel {
  max-width: 860px;
  margin: 20px auto 0;
  padding: 16px 18px 14px;
  border: 1px solid color-mix(in srgb, var(--app-border) 84%, transparent 16%);
  border-radius: 8px;
  background: color-mix(in srgb, var(--app-surface-strong) 78%, var(--app-bg) 22%);
  box-shadow: 0 10px 24px color-mix(in srgb, var(--app-text) 5%, transparent 95%);
}

.summary-thought-header,
.summary-result-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.summary-thought-title-group {
  display: grid;
  gap: 2px;
}

.summary-thought-kicker {
  color: color-mix(in srgb, var(--theme-accent) 78%, var(--app-text) 22%);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
}

.summary-thought-title-group strong {
  color: var(--app-text);
  font-size: 14px;
  line-height: 1.35;
}

.summary-thought-title-group small {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.summary-thought-toggle {
  flex: 0 0 auto;
}

.summary-thought-stream {
  display: grid;
  gap: 0;
  margin-top: 16px;
}

.summary-thought-item {
  position: relative;
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr);
  gap: 10px;
  min-height: 50px;
  padding: 0 0 14px;
  color: var(--el-text-color-secondary);
}

.summary-thought-item:last-child {
  min-height: 0;
  padding-bottom: 0;
}

.summary-thought-line {
  position: absolute;
  left: 6px;
  top: 19px;
  bottom: 0;
  width: 1px;
  background: color-mix(in srgb, var(--app-border) 70%, transparent 30%);
}

.summary-thought-item:last-child .summary-thought-line {
  display: none;
}

.summary-thought-dot {
  position: relative;
  z-index: 1;
  width: 13px;
  height: 13px;
  margin-top: 3px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--theme-accent) 34%, var(--app-border) 66%);
  background: var(--app-surface);
}

.summary-thought-copy {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.summary-thought-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.summary-thought-row strong {
  min-width: 0;
  color: inherit;
  font-size: 13px;
  line-height: 1.35;
}

.summary-thought-time {
  flex: 0 0 auto;
  color: var(--el-text-color-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  line-height: 1;
}

.summary-thought-item.done,
.summary-thought-item.active {
  color: var(--app-text);
}

.summary-thought-item.done .summary-thought-dot {
  background: color-mix(in srgb, var(--theme-accent) 35%, var(--app-surface) 65%);
  border-color: color-mix(in srgb, var(--theme-accent) 38%, var(--app-border) 62%);
}

.summary-thought-item.active .summary-thought-dot {
  background: var(--theme-accent);
  border-color: var(--theme-accent);
  overflow: visible;
}

.summary-thought-item.active .summary-thought-dot::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--theme-accent);
  opacity: 0.5;
  animation: summary-ripple 1.4s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.summary-thought-item.error .summary-thought-dot {
  background: var(--el-color-danger);
  border-color: var(--el-color-danger);
}

.summary-thought-item.error {
  color: var(--el-color-danger);
}

.summary-thought-item p {
  margin: 0;
  line-height: 1.55;
  font-size: 13px;
}

.summary-stream-enter-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.summary-stream-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}

@keyframes summary-ripple {
  0% {
    transform: scale(1);
    opacity: 0.5;
  }
  100% {
    transform: scale(2.8);
    opacity: 0;
  }
}

.summary-popover-body {
  display: grid;
  gap: 8px;
}

.summary-generate-button {
  width: 100%;
  margin-top: 4px;
}

.summary-result-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.summary-usage {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 500;
}

.summary-result-body {
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--app-text);
}

.summary-result-body :deep(h1) {
  font-size: 1.05em;
  font-weight: 700;
  margin: 1em 0 0.4em;
}

.summary-result-body :deep(h2) {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 1.35em;
  font-weight: 700;
  letter-spacing: 0.01em;
  margin: 1.3em 0 0.45em;
  padding: 0;
  border-left: none;
  color: var(--app-text);
}

.summary-result-body :deep(h3) {
  font-size: 0.88em;
  font-weight: 600;
  margin: 0.9em 0 0.3em;
  color: color-mix(in srgb, var(--app-text) 85%, transparent 15%);
}

.summary-result-body :deep(p) {
  margin: 0 0 0.75em;
  line-height: 1.8;
  color: color-mix(in srgb, var(--app-text) 88%, transparent 12%);
}

.summary-result-body :deep(.summary-h2-icon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  font-size: 12px;
  border-radius: 5px;
  background: color-mix(in srgb, var(--theme-accent) 12%, var(--app-surface) 88%);
  flex-shrink: 0;
}

.summary-result-body :deep(.summary-tags) {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin: 6px 0 14px;
}

.summary-result-body :deep(.summary-tag) {
  display: inline-block;
  padding: 3px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.01em;
  background: color-mix(in srgb, var(--theme-accent) 9%, var(--app-surface) 91%);
  border: 1px solid color-mix(in srgb, var(--theme-accent) 35%, transparent 65%);
  color: color-mix(in srgb, var(--theme-accent) 80%, var(--app-text) 20%);
  transition: background 0.15s, border-color 0.15s;
}

.summary-result-body :deep(li) {
  line-height: 1.75;
  color: color-mix(in srgb, var(--app-text) 88%, transparent 12%);
}

.summary-result-body :deep(li + li) { margin-top: 5px; }

.summary-result-body :deep(ul),
.summary-result-body :deep(ol) { padding-left: 1.4em; margin: 0 0 0.9em; }

.article-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.article-list-topbar-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.batch-export-bar {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
  padding: 10px;
  border: 1px solid color-mix(in srgb, var(--theme-accent) 26%, var(--app-border) 74%);
  border-radius: 8px;
  background: color-mix(in srgb, var(--theme-accent) 10%, var(--app-surface-strong) 90%);
}

.batch-export-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.batch-export-status strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.batch-export-status span {
  flex: 0 0 auto;
  color: color-mix(in srgb, currentColor 62%, transparent 38%);
  font-size: 12px;
  font-weight: 700;
}

.batch-export-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.batch-export-actions :deep(.el-button) {
  margin-left: 0;
}

.list-menu-button {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 12px;
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.article-card {
  position: relative;
  margin-bottom: 8px;
  border: 1px solid color-mix(in srgb, var(--app-border) 74%, transparent 26%);
  border-radius: 16px;
  padding: 10px 12px;
  background: color-mix(in srgb, var(--app-surface-strong) 94%, var(--app-bg) 6%);
  cursor: pointer;
  min-height: 96px;
  overflow: hidden;
  transition: all 0.24s ease;
}

.article-card.pinned {
  border-color: color-mix(in srgb, var(--theme-accent) 38%, var(--app-border) 62%);
}

.article-card.active {
  background: color-mix(in srgb, var(--theme-accent) 14%, var(--app-surface) 86%);
  border-color: color-mix(in srgb, var(--theme-accent) 36%, var(--app-border) 64%);
}

.article-card.batch-mode {
  padding-left: 46px;
}

.article-card.batch-selected {
  background: color-mix(in srgb, var(--theme-accent) 16%, var(--app-surface) 84%);
  border-color: color-mix(in srgb, var(--theme-accent) 44%, var(--app-border) 56%);
}

.article-select-control {
  position: absolute;
  left: 12px;
  top: 14px;
  width: 24px;
  height: 24px;
  border: 1px solid color-mix(in srgb, var(--app-border) 82%, transparent 18%);
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface) 94%, var(--app-bg) 6%);
  color: #ffffff;
  display: inline-grid;
  place-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.article-select-control.checked {
  border-color: color-mix(in srgb, var(--theme-accent) 76%, var(--app-border) 24%);
  background: var(--theme-accent);
}

.article-select-control :deep(.el-icon) {
  font-size: 14px;
}

.article-card-meta-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  color: color-mix(in srgb, currentColor 52%, transparent 48%);
  font-size: 11px;
}

.article-card-source {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article-card-date {
  text-align: right;
  line-height: 1.25;
}

.article-card-meta-right {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-width: 0;
}

.article-card-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.article-action-button {
  width: 24px;
  height: 24px;
  border: 1px solid color-mix(in srgb, var(--app-border) 70%, transparent 30%);
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-strong) 82%, var(--app-bg) 18%);
  color: color-mix(in srgb, currentColor 48%, transparent 52%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  cursor: pointer;
  transition: all 0.18s ease;
}

.article-action-button:hover,
.article-action-button.active {
  border-color: color-mix(in srgb, var(--theme-accent) 52%, var(--app-border) 48%);
  background: color-mix(in srgb, var(--theme-accent) 14%, var(--app-surface) 86%);
  color: color-mix(in srgb, var(--theme-accent) 86%, currentColor 14%);
}

.article-action-button :deep(.el-icon) {
  font-size: 13px;
}

.article-card-main {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.article-card-main.with-thumbnail {
  grid-template-columns: minmax(0, 1fr) 68px;
  align-items: start;
}

.article-card-copy h3 {
  margin: 0 0 4px;
  font-size: 14px;
  line-height: 1.35;
  font-weight: 650;
  letter-spacing: 0;
  color: color-mix(in srgb, currentColor 70%, transparent 30%);
}

.article-card-title.unread {
  font-weight: 850;
  color: color-mix(in srgb, var(--app-text) 94%, var(--theme-accent) 6%);
}

.article-card-summary {
  margin: 0 0 7px;
  color: color-mix(in srgb, currentColor 66%, transparent 34%);
  font-size: 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.article-list-load-more,
.article-list-empty,
.article-list-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 64px;
  padding: 12px 0 18px;
  color: color-mix(in srgb, currentColor 58%, transparent 42%);
  font-size: 13px;
  font-weight: 700;
}

.article-list-loading {
  gap: 8px;
}

.article-list-loading-icon {
  animation: summary-icon-spin 0.9s linear infinite;
}

.article-list-load-more :deep(.el-button) {
  min-width: 112px;
}

.article-card-thumb {
  width: 68px;
  height: 68px;
  border-radius: 12px;
  overflow: hidden;
  justify-self: end;
}

.article-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.reader-detail-panel {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: color-mix(in srgb, var(--app-surface-strong) 94%, white 6%);
  border-color: color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  border-radius: 0;
  border-width: 0;
  box-shadow: none;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.reader-scroll-area {
  flex: 1 1 auto;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-y;
  padding: 18px clamp(18px, 4vw, 48px) 24px;
}

.reader-content-frame {
  width: min(100%, 760px);
  margin: 0 auto;
}

:global(body.theme-dark) .reader-detail-panel {
  background: color-mix(in srgb, var(--app-surface-strong) 96%, black 4%);
}

.detail-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex-shrink: 0;
  width: min(100%, 760px);
  padding: 16px 0 0;
  margin: 0 auto;
  justify-content: flex-end;
}

.toolbar-icon-button {
  width: 34px;
  min-width: 34px;
  height: 34px;
  padding: 0;
  --el-button-bg-color: color-mix(in srgb, var(--app-surface-strong) 72%, transparent 28%);
  --el-button-border-color: color-mix(in srgb, var(--app-border) 72%, transparent 28%);
  --el-button-text-color: color-mix(in srgb, currentColor 58%, transparent 42%);
  --el-button-hover-bg-color: color-mix(in srgb, var(--theme-accent) 12%, var(--app-surface) 88%);
  --el-button-hover-border-color: color-mix(in srgb, var(--theme-accent) 34%, var(--app-border) 66%);
  --el-button-hover-text-color: color-mix(in srgb, var(--theme-accent) 82%, currentColor 18%);
  --el-button-active-bg-color: color-mix(in srgb, var(--theme-accent) 16%, var(--app-surface) 84%);
  box-shadow: none;
}

.toolbar-icon-button :deep(.el-icon) {
  font-size: 15px;
}

:deep(.toolbar-icon-button.active) {
  --el-button-bg-color: color-mix(in srgb, var(--theme-accent) 13%, var(--app-surface) 87%);
  --el-button-border-color: color-mix(in srgb, var(--theme-accent) 38%, var(--app-border) 62%);
  --el-button-text-color: color-mix(in srgb, var(--theme-accent) 82%, currentColor 18%);
}

.export-trigger {
  margin-left: 4px;
}

.note-toolbar-button {
  position: relative;
}

.note-toolbar-button.has-note::after {
  content: '';
  position: absolute;
  top: 3px;
  right: 3px;
  width: 7px;
  height: 7px;
  border: 2px solid var(--app-surface);
  border-radius: 999px;
  background: var(--theme-accent);
}

.tag-popover-body {
  display: grid;
  gap: 10px;
}

.tag-search-input {
  width: 100%;
}

.ai-tag-panel {
  display: grid;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--app-border) 70%, transparent 30%);
}

.ai-tag-panel-header,
.ai-tag-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ai-tag-panel-title {
  font-size: 12px;
  font-weight: 800;
  color: color-mix(in srgb, currentColor 58%, transparent 42%);
}

.ai-tag-error {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-color-danger);
}

.ai-tag-candidate-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-tag-candidate {
  max-width: 100%;
  border: 1px solid color-mix(in srgb, var(--app-border) 74%, transparent 26%);
  border-radius: 999px;
  padding: 6px 8px 6px 10px;
  background: color-mix(in srgb, var(--app-surface-strong) 90%, var(--app-bg) 10%);
  color: inherit;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 750;
  transition: all 0.18s ease;
}

.ai-tag-candidate.active {
  border-color: color-mix(in srgb, var(--theme-accent) 48%, var(--app-border) 52%);
  background: color-mix(in srgb, var(--theme-accent) 14%, var(--app-surface) 86%);
  color: color-mix(in srgb, var(--theme-accent) 82%, var(--app-text) 18%);
}

.ai-tag-candidate.assigned {
  opacity: 0.74;
}

.ai-tag-badge {
  padding: 2px 5px;
  border-radius: 999px;
  background: color-mix(in srgb, currentColor 10%, transparent 90%);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}

.tag-selection-list {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 8px;
  max-height: 220px;
  overflow: auto;
  padding: 2px 2px 4px;
}

.tag-selection-item {
  max-width: 100%;
  border: 0;
  border-radius: 999px;
  padding: 7px 8px 7px 10px;
  background: color-mix(in srgb, var(--app-surface-strong) 90%, var(--app-bg) 10%);
  color: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 7px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-selection-item.active {
  background: color-mix(in srgb, var(--theme-accent) 14%, var(--app-surface) 86%);
}

.tag-selection-main {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  font-weight: 700;
  font-size: 13px;
}

.tag-selection-main span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-selection-actions {
  gap: 4px;
}

.tag-selection-actions .tag-delete-action {
  width: 20px;
  height: 20px;
}

.tag-selection-empty {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: color-mix(in srgb, var(--app-surface-strong) 78%, var(--app-bg) 22%);
  color: color-mix(in srgb, currentColor 48%, transparent 52%);
  font-size: 12px;
  font-weight: 700;
}

.tag-creator-card {
  padding-top: 10px;
  border-top: 1px solid color-mix(in srgb, var(--app-border) 76%, transparent 24%);
}

:deep(.note-popover) {
  max-width: calc(100vw - 32px);
  border-radius: 8px;
}

.note-popover-body {
  display: grid;
  gap: 12px;
}

.note-popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.note-popover-title {
  font-size: 15px;
  font-weight: 700;
}

.note-popover-meta {
  color: color-mix(in srgb, currentColor 52%, transparent 48%);
  font-size: 12px;
  font-weight: 700;
}

.note-popover-input :deep(.el-textarea__inner) {
  min-height: 190px;
  border-radius: 10px;
  line-height: 1.6;
}

.note-actions.note-popover-actions {
  margin: 0;
}

.note-actions.note-popover-actions :deep(.el-button) {
  flex: 1 1 0;
  min-width: 0;
}

.batch-digest-body {
  display: grid;
  gap: 12px;
}

.batch-digest-options,
.batch-digest-meta,
.batch-digest-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.batch-digest-options {
  flex-wrap: wrap;
}

.batch-digest-meta {
  flex-wrap: wrap;
  color: color-mix(in srgb, currentColor 62%, transparent 38%);
  font-size: 13px;
  font-weight: 700;
}

.batch-digest-alert {
  margin: 0;
}

.batch-digest-preview :deep(.el-textarea__inner) {
  min-height: 360px;
  border-radius: 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
}

.batch-digest-footer {
  justify-content: flex-end;
  flex-wrap: wrap;
}

.batch-digest-footer :deep(.el-button) {
  margin-left: 0;
}

.dropdown-inline-control {
  padding: 10px 16px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dropdown-inline-label {
  color: color-mix(in srgb, currentColor 60%, transparent 40%);
  font-size: 13px;
  font-weight: 700;
}

.dropdown-inline-stepper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.stepper-button {
  width: 26px;
  height: 26px;
  border: 1px solid color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  color: color-mix(in srgb, currentColor 80%, transparent 20%);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.stepper-value {
  min-width: 18px;
  text-align: center;
  color: inherit;
  font-size: 14px;
  font-weight: 700;
}

.reader-inline-alert {
  margin-top: 14px;
}

.reader-source-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.note-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
  margin-bottom: 12px;
}

.note-export-button {
  min-width: 96px;
}

.note-actions :deep(.el-button) {
  min-width: 112px;
  height: 42px;
  border-radius: 12px;
}

.note-actions :deep(.el-button--primary),
.note-export-button {
  --el-button-bg-color: var(--theme-accent);
  --el-button-border-color: color-mix(in srgb, var(--theme-accent) 74%, var(--app-border) 26%);
  --el-button-text-color: #ffffff;
  --el-button-hover-bg-color: color-mix(in srgb, var(--theme-accent) 86%, white 14%);
  --el-button-hover-border-color: color-mix(in srgb, var(--theme-accent) 86%, white 14%);
  --el-button-active-bg-color: color-mix(in srgb, var(--theme-accent) 74%, black 26%);
  --el-button-active-border-color: color-mix(in srgb, var(--theme-accent) 74%, black 26%);
}

.button-icon-right {
  margin-left: 6px;
}

.feed-manager-overlay {
  grid-column: 3 / 6;
  grid-row: 1;
  align-self: stretch;
  height: 100%;
  min-height: 0;
  z-index: 4;
  margin: 0;
  border-radius: 0;
  border-width: 0;
  background: color-mix(in srgb, var(--app-bg) 90%, var(--app-surface) 10%);
  padding: 14px;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-y;
  box-shadow: none;
}

:deep(.article-card-tags .el-tag) {
  border-radius: 999px;
}

:deep(.article-card-tags .el-tag),
:deep(.toolbar-tag-select .el-tag) {
  border-color: color-mix(in srgb, var(--app-border) 78%, transparent 22%);
  background: color-mix(in srgb, var(--app-surface-strong) 92%, var(--app-bg) 8%);
  color: inherit;
}

@media (max-width: 1200px) {
  .article-card-main.with-thumbnail {
    grid-template-columns: 1fr 64px;
  }

  .article-card-thumb {
    width: 64px;
    height: 64px;
  }
}

.reader-hero {
  margin-bottom: 16px;
  padding-top: 16px;
}

.reader-title-translated {
  color: color-mix(in srgb, var(--theme-accent) 70%, var(--app-text) 30%);
}

.title-translation-row {
  margin: 6px 0 0;
}

.title-translation-text {
  font-size: clamp(20px, calc(var(--reader-font-size) + 6px), 28px);
  line-height: 1.35;
  letter-spacing: -0.04em;
  color: color-mix(in srgb, var(--theme-accent) 75%, var(--app-text) 25%);
  text-wrap: pretty;
  padding: 8px 14px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--theme-accent) 22%, var(--app-border) 78%);
  background: color-mix(in srgb, var(--theme-accent) 6%, var(--app-surface) 94%);
}

/* 标题翻译操作栏 */
.title-translate-bar {
  margin: 4px 0 2px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.reader-hero:hover .title-translate-bar {
  opacity: 1;
}

.title-translate-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.title-translate-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: color-mix(in srgb, var(--theme-accent) 80%, var(--app-text) 20%);
}

.title-translate-status .el-icon {
  font-size: 12px;
}

.summary-drawer {
  flex-shrink: 0;
  position: relative;
  background: color-mix(in srgb, var(--app-surface-strong) 96%, var(--app-bg) 4%);
  border-top: 1px solid color-mix(in srgb, var(--app-border) 80%, transparent 20%);
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -4px 20px color-mix(in srgb, var(--app-text) 6%, transparent 94%);
  transition: box-shadow 0.2s ease;
}

.summary-drawer.expanded {
  box-shadow: 0 -6px 28px color-mix(in srgb, var(--app-text) 10%, transparent 90%);
}

.summary-drawer.failed .summary-drawer-handle {
  border-top-color: color-mix(in srgb, var(--el-color-danger) 30%, var(--app-border) 70%);
}

.summary-drawer-handle {
  width: 100%;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  padding: 10px 18px;
  border: 0;
  background: transparent;
  cursor: pointer;
  color: inherit;
  gap: 10px;
  user-select: none;
}

.summary-drawer-resize-bar {
  position: absolute;
  top: -4px;
  left: 0;
  right: 0;
  height: 8px;
  cursor: ns-resize;
  z-index: 1;
}

.summary-drawer-resize-bar::before {
  content: '';
  position: absolute;
  top: 3px;
  left: 50%;
  transform: translateX(-50%);
  width: 32px;
  height: 3px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-border) 80%, transparent 20%);
  transition: background 0.15s;
}

.summary-drawer-resize-bar:hover::before {
  background: var(--theme-accent);
}

.summary-drawer-handle-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.summary-drawer-title-wrap {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.summary-drawer-desc {
  font-size: 11px;
  font-weight: 400;
  color: var(--el-text-color-secondary);
}

.summary-drawer-handle-center {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 50px;
}

.summary-drawer-handle-label-text {
  font-size: 13px;
  font-weight: 700;
  color: color-mix(in srgb, var(--theme-accent) 80%, var(--app-text) 20%);
}

.summary-drawer-icon {
  font-size: 15px;
}

.summary-drawer-loading-icon {
  font-size: 13px;
  animation: summary-icon-spin 0.9s linear infinite;
}

@keyframes summary-icon-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.summary-drawer-handle-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.summary-drawer-arrow {
  font-size: 18px;
  color: color-mix(in srgb, currentColor 50%, transparent 50%);
  transition: transform 0.25s ease;
  transform: rotate(90deg);
  line-height: 1;
  display: inline-block;
}

.summary-drawer-arrow.up {
  transform: rotate(-90deg);
}

.summary-drawer-body {
  overflow: hidden;
  height: 0;
  transition: height 0.35s cubic-bezier(0.4, 0, 0.2, 1), padding 0.32s ease;
  padding: 0 18px;
}

.summary-drawer.expanded .summary-drawer-body {
  height: var(--drawer-height, 320px);
  padding: 0 18px 32px;
  overflow-y: auto;
  scroll-padding-bottom: 32px;
}

.summary-drawer-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 0 12px;
  border-bottom: 1px solid color-mix(in srgb, var(--app-border) 60%, transparent 40%);
  margin-bottom: 12px;
  position: sticky;
  top: 0;
  z-index: 1;
  background: color-mix(in srgb, var(--app-surface-strong) 96%, var(--app-bg) 4%);
}

.summary-drawer-control-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 auto;
}

.summary-drawer-label {
  font-size: 12px;
  font-weight: 700;
  color: color-mix(in srgb, currentColor 60%, transparent 40%);
  white-space: nowrap;
}

.summary-generate-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 36px;
  padding: 0 16px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--theme-accent) 55%, transparent 45%);
  background: color-mix(in srgb, var(--theme-accent) 10%, var(--app-surface) 90%);
  color: color-mix(in srgb, var(--theme-accent) 85%, var(--app-text) 15%);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  letter-spacing: 0.01em;
  box-shadow: 0 1px 4px color-mix(in srgb, var(--theme-accent) 18%, transparent 82%),
              inset 0 1px 0 color-mix(in srgb, white 30%, transparent 70%);
  transition: background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, transform 0.1s ease;
}

.summary-generate-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--theme-accent) 16%, var(--app-surface) 84%);
  border-color: color-mix(in srgb, var(--theme-accent) 70%, transparent 30%);
  box-shadow: 0 2px 10px color-mix(in srgb, var(--theme-accent) 22%, transparent 78%),
              inset 0 1px 0 color-mix(in srgb, white 25%, transparent 75%);
}

.summary-generate-btn:active:not(:disabled) {
  background: color-mix(in srgb, var(--theme-accent) 22%, var(--app-surface) 78%);
  box-shadow: 0 1px 3px color-mix(in srgb, var(--theme-accent) 15%, transparent 85%);
  transform: translateY(1px);
}

.summary-generate-btn:disabled {
  background: color-mix(in srgb, var(--theme-accent) 5%, var(--app-surface) 95%);
  border-color: color-mix(in srgb, var(--theme-accent) 20%, transparent 80%);
  color: color-mix(in srgb, var(--theme-accent) 35%, transparent 65%);
  box-shadow: none;
  cursor: not-allowed;
}

.summary-generate-btn-icon {
  display: inline-flex;
  align-items: center;
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.summary-generate-btn-icon svg {
  width: 14px;
  height: 14px;
}

.summary-generate-btn-icon .spin {
  animation: summary-btn-spin 0.9s linear infinite;
}

@keyframes summary-btn-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.summary-result-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid color-mix(in srgb, var(--app-border) 50%, transparent 50%);
}

.summary-copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid var(--app-border);
  background: transparent;
  color: var(--el-text-color-regular);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, color 0.15s ease;
}

.summary-copy-btn svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.summary-copy-btn:hover {
  background: color-mix(in srgb, var(--app-surface-strong) 80%, var(--app-bg) 20%);
  border-color: color-mix(in srgb, var(--app-border) 80%, var(--theme-accent) 20%);
  box-shadow: 0 1px 4px color-mix(in srgb, var(--app-text) 8%, transparent 92%);
}

.summary-copy-btn:active {
  transform: translateY(1px);
  box-shadow: none;
}

.summary-copy-btn.copied {
  color: color-mix(in srgb, var(--theme-accent) 85%, black 15%);
  border-color: color-mix(in srgb, var(--theme-accent) 35%, var(--app-border) 65%);
  background: color-mix(in srgb, var(--theme-accent) 8%, var(--app-surface) 92%);
}

.summary-drawer-loading {
  padding: 10px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.summary-drawer-loading-dots::after {
  content: '';
  display: inline-block;
  animation: loading-dots 1.2s steps(4, end) infinite;
}

@keyframes loading-dots {
  0%   { content: ''; }
  25%  { content: '.'; }
  50%  { content: '..'; }
  75%  { content: '...'; }
  100% { content: ''; }
}

.summary-drawer-stream {
  display: grid;
  gap: 0;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid color-mix(in srgb, var(--app-border) 50%, transparent 50%);
}

.summary-warning {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-danger);
}

.summary-warning-inline {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
}

.summary-drawer-result {
  padding-top: 4px;
  padding: 12px 14px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--app-surface-strong) 60%, var(--app-bg) 40%);
  border: 1px solid color-mix(in srgb, var(--app-border) 55%, transparent 45%);
}

.summary-drawer-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.summary-drawer-result-label {
  font-size: 13px;
  font-weight: 700;
  color: color-mix(in srgb, var(--theme-accent) 80%, var(--app-text) 20%);
}

@media (max-width: 960px) {
  .article-list-header {
    align-items: center;
  }

  .feed-manager-overlay {
    grid-column: 1 / -1;
  }
}

/* ===== Translation UI (参考现有设计风格统一优化) ===== */

/* ---- 正文分块布局 ---- */
.article-body-blocks {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.article-block {
  position: relative;
  padding: 0;
  border-radius: 12px;
  transition: background 0.2s ease, box-shadow 0.2s ease;
}

/* 可翻译段落：hover 时像 article-card 一样有微妙的背景变化 */
.article-block-translatable {
  padding: 8px 12px;
  margin: 0 -12px;
}

.article-block-translatable:hover {
  background: color-mix(in srgb, var(--app-surface-strong) 60%, var(--app-bg) 40%);
  box-shadow: 0 2px 12px color-mix(in srgb, var(--app-text) 4%, transparent 96%);
}

/* ---- 译文替换模式：翻译标识徽章 ---- */
/* 参考 .summary-tag 风格：pill 形状、细边框、主题色点缀 */
.article-block-translated {
  position: relative;
}

.translation-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  margin-bottom: 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: color-mix(in srgb, var(--theme-accent) 80%, var(--app-text) 20%);
  background: color-mix(in srgb, var(--theme-accent) 8%, var(--app-surface) 92%);
  border: 1px solid color-mix(in srgb, var(--theme-accent) 30%, var(--app-border) 70%);
  border-radius: 999px;
}

.translation-badge-button,
.translation-label-button {
  cursor: pointer;
  font-family: inherit;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.translation-badge-button:hover,
.translation-label-button:hover {
  color: color-mix(in srgb, var(--theme-accent) 92%, var(--app-text) 8%);
  background: color-mix(in srgb, var(--theme-accent) 16%, var(--app-surface) 84%);
  border-color: color-mix(in srgb, var(--theme-accent) 45%, var(--app-border) 55%);
}

.translation-badge-hint {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0;
  opacity: 0.68;
}

.translation-badge .el-icon {
  font-size: 13px;
}

/* ---- 双语对照模式：卡片式分隔 ---- */
/* 参考 article-card 的卡片风格，原文译文各自成卡 */
.article-block-comparison {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 0;
}

.comparison-row {
  position: relative;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--app-border) 60%, transparent 40%);
  background: color-mix(in srgb, var(--app-surface-strong) 50%, var(--app-bg) 50%);
}

.comparison-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.03em;
  border-radius: 999px;
  line-height: 1.4;
}

.original-label {
  color: color-mix(in srgb, var(--app-text) 50%, transparent 50%);
  background: color-mix(in srgb, var(--app-border) 15%, var(--app-surface) 85%);
  border: 1px solid color-mix(in srgb, var(--app-border) 45%, transparent 55%);
}

.translation-label {
  color: color-mix(in srgb, var(--theme-accent) 85%, var(--app-text) 15%);
  background: color-mix(in srgb, var(--theme-accent) 10%, var(--app-surface) 90%);
  border: 1px solid color-mix(in srgb, var(--theme-accent) 30%, var(--app-border) 70%);
}

/* 去掉简单横线，用间距和卡片背景自然分隔 */
.comparison-divider {
  display: none;
}

/* ---- 翻译操作按钮区 ---- */
/* 参考 .sidebar-primary-link 风格：pill 形状、hover 背景变化 */
.article-block-translate {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  align-items: center;
  opacity: 0;
  transform: translateY(4px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.article-block-translatable:hover .article-block-translate {
  opacity: 1;
  transform: translateY(0);
}

.para-translate-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: color-mix(in srgb, var(--app-text) 60%, transparent 40%);
  background: color-mix(in srgb, var(--app-surface-strong) 90%, var(--app-bg) 10%);
  border: 1px solid color-mix(in srgb, var(--app-border) 55%, transparent 45%);
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.para-translate-btn:hover:not(:disabled) {
  color: color-mix(in srgb, var(--theme-accent) 90%, var(--app-text) 10%);
  border-color: color-mix(in srgb, var(--theme-accent) 50%, var(--app-border) 50%);
  background: color-mix(in srgb, var(--theme-accent) 12%, var(--app-surface) 88%);
}

.para-translate-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.para-translate-btn .el-icon {
  font-size: 13px;
}

/* 模式切换按钮：更 subtle 的样式 */
.para-translate-btn.mode-btn {
  color: color-mix(in srgb, var(--app-text) 45%, transparent 55%);
  background: transparent;
  border-color: color-mix(in srgb, var(--app-border) 40%, transparent 60%);
}

.para-translate-btn.mode-btn:hover {
  color: color-mix(in srgb, var(--theme-accent) 80%, var(--app-text) 20%);
  border-color: color-mix(in srgb, var(--theme-accent) 45%, var(--app-border) 55%);
  background: color-mix(in srgb, var(--theme-accent) 6%, transparent 94%);
}

/* ---- 译文显示区域 ---- */
/* 参考 article-card 风格：圆角卡片、边框、柔和背景 */
.para-translation {
  margin: 0;
  padding: 12px 16px;
  color: inherit;
  background: color-mix(in srgb, var(--theme-accent) 5%, var(--app-surface-strong) 95%);
  border: 1px solid color-mix(in srgb, var(--theme-accent) 18%, var(--app-border) 82%);
  border-radius: 10px;
}

/* 清除原文和译文内部的末段边距 */
.article-block-original :deep(p:last-child),
.article-block-original :deep(ul:last-child),
.article-block-original :deep(ol:last-child),
.article-block-original :deep(blockquote:last-child),
.para-translation :deep(p:last-child),
.para-translation :deep(ul:last-child),
.para-translation :deep(ol:last-child),
.para-translation :deep(blockquote:last-child) {
  margin-bottom: 0;
}

.para-translation :deep(p:first-child),
.para-translation :deep(ul:first-child),
.para-translation :deep(ol:first-child),
.para-translation :deep(blockquote:first-child) {
  margin-top: 0;
}

/* ---- 工具栏翻译按钮组 ---- */
.toolbar-translate-group {
  display: inline-flex;
  align-items: center;
}

.toolbar-translate-caret {
  width: 22px;
  min-width: 22px;
  height: 22px;
  margin-left: 2px;
  padding: 0;
  --el-button-bg-color: transparent;
  --el-button-border-color: transparent;
  --el-button-text-color: color-mix(in srgb, currentColor 45%, transparent 55%);
  --el-button-hover-bg-color: color-mix(in srgb, var(--app-border) 25%, transparent 75%);
  --el-button-hover-border-color: transparent;
  --el-button-hover-text-color: color-mix(in srgb, var(--app-text) 75%, transparent 25%);
}

.toolbar-translate-caret :deep(.el-icon) {
  font-size: 11px;
}

/* ---- 响应式：移动端按钮始终可见 ---- */
@media (max-width: 768px) {
  .article-block-translate {
    opacity: 0.85;
    transform: translateY(0);
  }
}
</style>
