# Week13 gloriaaa0312 - 前端阅读系统、文章展示、设置与笔记功能

## 完成范围

本周负责 RSSReader 的前端阅读系统与笔记功能开发，主要完成以下内容：

- 完成基础阅读页面，支持订阅筛选、文章列表和文章详情三栏阅读布局。
- 完成 Feed 列表与文章展示 UI，支持按全部文章、未读文章、收藏文章和订阅源筛选。
- 完成文章详情展示，支持标题、作者、原文链接、正文内容和正文内链接展示。
- 完成文章已读/未读、收藏/取消收藏的前端交互。
- 完成文章笔记输入与保存功能，对接后端笔记 API。
- 完成单篇文章 Markdown 导出按钮，并修复 Electron 桌面端随机端口下导出失败的问题。
- 完成设置页中的阅读字号和白天/黑夜阅读模式功能。
- 删除设置页中暂不需要的界面语言、本地优先开关。
- 优化 Electron 桌面端导航布局，将导航入口集中到顶部栏。
- 修正一些细节问题，提高用户体验。

## 关键页面

### 阅读页面

文件：

```text
frontend/src/views/ReaderView.vue
```

当前阅读页面包含三部分：

- 左侧：订阅与筛选，包括全部文章、未读文章、收藏文章和 Feed 订阅源。
- 中间：文章选择列表，每篇文章显示文章标题和所属订阅源。
- 右侧：文章详情阅读区，包括文章标题、作者、原文链接、正文、笔记输入框和导出按钮。

文章详情中的原文 URL 已改为可点击链接：

```text
target="_blank"
rel="noopener noreferrer"
```

### 设置页面

文件：

```text
frontend/src/views/SettingsView.vue
frontend/src/stores/preferences.ts
```

设置页当前保留并实现了：

- 阅读字号：范围为 14px 到 24px。
- 阅读模式：白天 / 黑夜。

阅读字号和阅读模式会保存到浏览器或 Electron 渲染进程的 `localStorage` 中，重启应用后仍会保留。

文章正文字号使用用户选择的字号，文章标题和“笔记”标题会比正文字号大 3px。

### 顶部导航

文件：

```text
frontend/src/App.vue
frontend/src/styles.css
```

当前已取消侧边栏，将主要入口放到顶部导航栏右侧：

- 阅读
- 订阅
- 统计日志
- AI 设置
- 设置

顶部导航按钮只显示图标，鼠标悬浮时显示名称。

## 使用到的前端 API

统一 API 封装文件：

```text
frontend/src/api/client.ts
```

本模块主要使用以下接口：

- `GET /api/feeds`
- `POST /api/feeds`
- `POST /api/feeds/{id}/sync`
- `POST /api/feeds/sync-all`
- `GET /api/articles`
- `GET /api/articles/{id}`
- `PATCH /api/articles/{id}/read`
- `PATCH /api/articles/{id}/star`
- `GET /api/articles/{id}/note`
- `PUT /api/articles/{id}/note`
- `GET /api/export/articles/{id}/markdown`

其中 Markdown 导出在前端通过 Axios 获取 `Blob` 后触发本地下载，避免 Electron 桌面端随机后端端口导致 `/api/...` 相对链接被错误代理到 `127.0.0.1:8000`。

## 主要交互说明

### 添加订阅与同步

订阅管理页面中：

- 点击“添加订阅”后，按钮会进入 loading 状态并显示“正在添加...”。
- 点击单个 Feed 的“同步”后，对应按钮会显示“正在同步...”。
- 点击“同步全部”后，会禁用其它同步按钮，避免重复请求。

相关文件：

```text
frontend/src/views/FeedManageView.vue
```

### 文章阅读

用户可以在阅读页完成以下操作：

1. 按筛选条件查看文章。
2. 点击中间栏文章标题切换文章。
3. 查看文章详情和原文链接。
4. 点击正文内链接并在新页面打开。
5. 标记已读/未读。
6. 收藏/取消收藏。
7. 编写并保存文章笔记。
8. 导出当前文章 Markdown。

### 阅读设置

用户可以在设置页完成以下操作：

1. 调整阅读字号。
2. 切换白天/黑夜阅读模式。

黑夜模式下已优化：

- 页面背景
- 顶部导航栏
- 内容面板
- 按钮
- 笔记输入框
- 阅读字号输入框
- 分段选择器
- 正文链接颜色
- 滚动条滑块

## 运行与验证

### Electron 桌面端开发模式

推荐使用桌面端模式验证本模块：

```bash
npm run dev:desktop
```

该命令会启动：

- Vite 前端
- Electron 桌面窗口
- 本地 FastAPI 后端

### 前端构建验证

已执行：

```bash
npm.cmd run build:frontend
```

构建结果通过。

### 建议手动测试流程

1. 启动桌面端应用。
2. 进入订阅管理页面，添加一个 RSS Feed。
3. 点击同步或同步全部。
4. 回到阅读页，查看 Feed 筛选和文章列表。
5. 点击文章，确认右侧文章详情正常显示。
6. 点击文章原文链接和正文内链接，确认会在新页面打开。
7. 切换已读/未读和收藏状态。
8. 输入笔记并保存，切换文章后再切回确认笔记仍存在。
9. 点击导出 Markdown，确认可以下载 `.md` 文件。
10. 进入设置页，调整字号和阅读模式，确认阅读页样式同步变化。

## 当前限制与后续建议

- 当前文章正文内容依赖 RSS Feed 提供的内容。如果 Feed 只提供摘要，阅读页也只能显示摘要。
- 标签功能目前不属于本次前端阅读主流程，且后端标签持久化仍待后续完善。
- AI 摘要和翻译按钮已保留在阅读页，但当前后端仍以 mock 或预留逻辑为主，后续需要由 AI 功能负责同学继续接入真实模型。
- OPML 导入/导出按钮仍属于后续订阅迁移功能范围，不是本次阅读与笔记模块的核心完成内容。
- 笔记保存已有基础功能，后续可以继续扩展自动保存、未保存提醒和 Markdown 预览。

## 关键文件

- `frontend/src/views/ReaderView.vue`：阅读页、文章详情、笔记、Markdown 导出。
- `frontend/src/views/FeedManageView.vue`：订阅添加与同步按钮 loading 状态。
- `frontend/src/views/SettingsView.vue`：阅读字号和白天/黑夜模式设置。
- `frontend/src/stores/preferences.ts`：阅读偏好设置持久化。
- `frontend/src/api/client.ts`：前端 API 封装。
- `frontend/src/App.vue`：顶部导航布局。
- `frontend/src/styles.css`：阅读布局、主题、滚动条、链接和控件样式。
