# Week16 specia1week - 阅读页笔记弹窗入口

## 本周负责范围

- 优化阅读页文章笔记入口。
- 将原本位于正文底部的笔记编辑区改为顶部工具栏弹出窗口。
- 保持现有笔记 API、SQLite 表结构和 Markdown 导出行为不变。

## 主要实现

### 1. 顶部工具栏新增笔记按钮

在阅读页详情栏顶部工具栏中，于导出按钮左侧新增笔记图标按钮。

- 按钮使用 Element Plus `EditPen` 图标。
- 点击后通过 `el-popover` 展示笔记小窗口。
- 按钮激活时沿用工具栏现有 active 样式。

### 2. 笔记编辑迁移到弹窗

将原本需要滚动到文章末尾才能操作的笔记区域迁移到弹窗中。

弹窗内容包括：

- Markdown 笔记 textarea。
- 自动保存状态提示和立即保存按钮。
- 导出笔记按钮。

底层仍复用现有笔记 API 和 `note` 响应式状态，因此不会改变用户已有笔记数据。

### 3. 移除正文底部旧入口

删除正文末尾的笔记标题、textarea 和操作按钮，避免同一篇文章出现两个笔记编辑入口。

### 4. 笔记自动保存

参考 Mercury 的笔记面板交互，将笔记保存从“必须点击保存按钮”调整为 debounce 自动保存。

- 用户输入后显示“保存中...”状态。
- 停止输入后自动调用 `PUT /api/articles/{id}/note` 保存。
- 弹窗关闭、切换文章、导出笔记或导出文摘前会立即 flush 当前草稿。
- 保留“立即保存”按钮，供用户主动触发保存。
- 保存失败时显示“保存失败”状态。
- 当前文章笔记非空时，顶部笔记按钮右上角显示蓝色圆点。

### 5. 保持后端与导出链路不变

本次没有新增或修改后端接口。

继续使用现有接口：

- `GET /api/articles/{id}/note`
- `PUT /api/articles/{id}/note`

继续使用现有数据表：

- `notes.entry_id`
- `notes.content`

继续保留笔记导出文件命名：

- `{文章标题}-note.md`

### 6. 恢复批量文摘导出入口

根据 Week14 批量导出计划，当前后端 `POST /api/export/digests/markdown` 和 Electron `saveMarkdown` 能力仍然存在，但阅读页 UI 改版后只保留了“批量文摘”占位提示。

本次在当前阅读页列表中补回批量导出流程：

- 从文章列表右上角菜单进入“批量文摘”模式。
- 当前列表文章卡片左侧显示选择圆点。
- 勾选顺序不影响导出顺序，导出顺序跟随当前列表顺序。
- 顶部批量工具条显示已选数量，支持全选、清空、预览导出和退出。
- 预览弹窗支持切换“包含 AI 摘要”和“包含笔记”。
- 预览弹窗新增“包含全文”选项，与“包含 AI 摘要”“包含笔记”并列。
- 预览弹窗展示后端生成的 Markdown，并显示可导出文章数、已有摘要文章数和跳过文章数。
- 支持复制预览 Markdown。
- Web 端使用浏览器下载，Electron 端继续调用原生保存对话框。

后端批量 digest 请求体新增 `include_full_text` 字段；数据库结构不变。包含全文时优先使用文章清洗后的 `cleaned_markdown`，缺失时回退到文章摘要。

## 修改文件

- `frontend/src/views/ReaderView.vue`
- `docs/AI_COLLABORATION.md`
- `update_docs/Week14_batch_export_plan.md`

## 实际测试记录

### 前端构建

```bash
cd frontend
npm run build
```

结果：通过。

构建过程中 Vite/Rollup 输出第三方依赖注释与 chunk size 警告，但不影响构建成功。

### 后端语法检查

```bash
cd backend
python -m py_compile app/schemas/rss.py app/services/export_service.py app/routers/export.py
```

结果：通过。

## 当前限制

- 本次只调整阅读页交互，没有新增自动化 UI 测试。
- 笔记自动保存采用前端 debounce，网络失败时会显示失败状态，但暂不做离线重试队列。
- 后端 API 和数据库结构未变化，因此不涉及迁移步骤。
