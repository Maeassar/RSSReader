# Week14 Codex - 批量导出功能实现计划

## 任务背景

本次任务是为 RSSReader 实现一套对齐 Mercury 风格 `Export Multiple Digest` 的批量导出能力。实现目标参考前期整理出的需求分析结论，但不依赖仓库内额外的参考目录，需要直接适配当前项目的 `Vue 3 + FastAPI + Electron` 跨平台架构。

当前仓库已有：

- 单篇 Markdown 导出
- 文章列表与阅读页
- 笔记保存
- AI 摘要结果落库

当前仓库缺少：

- 文章列表多选导出模式
- 批量 digest 预览
- 批量 digest Markdown 生成接口
- Electron 端保存对话框与导出目录记忆

## 本次目标

实现一个可在 Web 和 Electron 桌面端共用的批量导出流程：

1. 用户从文章列表进入批量导出模式。
2. 用户勾选多篇文章，并保持导出顺序与当前列表顺序一致。
3. 用户在预览弹窗中选择是否包含 AI 摘要、是否包含笔记。
4. 后端生成符合 digest 格式的 Markdown。
5. Web 端通过浏览器下载文件。
6. Electron 端通过原生保存对话框导出文件，并记住上一次成功保存的目录。

## 设计决策

### 1. 后端只负责生成内容

后端新增专门的批量 digest 导出接口，返回：

- `markdown`
- `digest_title`
- `filename`
- `exported_article_ids`
- `skipped_article_ids`

后端不接收本地路径，不直接写客户端文件系统。

### 2. 摘要只取 AI Summary

当用户选择“包含摘要”时：

- 仅使用 `ai_results` 表中 `task_type = "summary"` 的最新一条结果
- 不回退到 RSS/Atom 自带的 `summary`

这与参考项目的 `loadLatestSummaryRecord(entryId:)` 语义保持一致。

### 3. 标题和文件名按参考项目规则

- `digest_title`: `Digest YY-MM-DD`
- `filename`: `YYYY-MM-DD-digest.md`

第一版不支持用户在导出弹窗中编辑 digest 标题和文件名。

### 4. 保存路径由客户端决定

为兼容 Web 和 Electron：

- Web：使用 `Blob` 下载
- Electron：调用原生 `showSaveDialog`

Electron 仅记忆“上一次成功保存的目录”，作为下次保存对话框的默认目录。

### 5. 缺失字段处理

对于批量导出：

- 无标题或无 URL 的文章不参与 digest 生成
- 不让整批请求失败
- 后端通过 `skipped_article_ids` 返回被跳过的文章

## 计划修改范围

### 后端

- `backend/app/schemas/rss.py`
  - 新增批量 digest 请求/响应模型
- `backend/app/routers/export.py`
  - 新增批量 digest 导出接口
- `backend/app/services/export_service.py`
  - 新增 digest Markdown 生成逻辑
- `backend/app/repositories/sqlite_repository.py`
  - 新增最新 AI 摘要读取能力

### 前端

- `frontend/src/api/client.ts`
  - 新增批量 digest API
- `frontend/src/views/ReaderView.vue`
  - 新增多选导出模式
  - 新增导出预览弹窗
  - 新增 Web/Electron 分支导出逻辑

### Electron

- `electron/main.js`
  - 新增保存 Markdown 的 IPC
  - 新增最近导出目录记忆
- `electron/preload.js`
  - 暴露窄接口给前端
- `frontend/src/types/electron.d.ts`
  - 补充桌面端类型声明

## 非目标

本次不做以下内容：

- 用户自定义 digest 模板
- 固定导出目录设置页
- 后端直接写入客户端本地目录
- 浏览器端持久化导出目录
- 多篇导出中的摘要生成或笔记编辑

## 预期结果

完成后，RSSReader 将具备一条完整的批量导出链路：

- 选择文章
- 预览 digest
- 按当前列表顺序导出 Markdown
- 在桌面端记住最近使用的导出目录

这样可以在不引入平台耦合后端逻辑的前提下，尽量贴近参考项目的使用体验和导出结构。

## 实际完成情况

已完成：

- 新增批量 digest 导出接口 `POST /api/export/digests/markdown`
- 新增批量导出请求/响应模型
- 后端实现 digest 标题、文件名和 Markdown 生成规则
- 后端实现“仅使用最新 AI 摘要结果”的摘要读取逻辑
- 阅读页新增批量导出模式与多选交互
- 阅读页新增 digest 预览弹窗、复制和导出动作
- Electron 新增 Markdown 保存 IPC
- Electron 新增最近导出目录记忆

本次实现后的行为：

- 批量导出顺序跟随当前文章列表顺序，而不是勾选顺序
- Digest 标题固定为 `Digest YY-MM-DD`
- 默认文件名固定为 `YYYY-MM-DD-digest.md`
- Web 端通过浏览器下载文件
- Electron 端通过保存对话框导出，并默认打开上次成功保存的目录
- 单篇文章导出入口调整为顶部工具栏中的 `导出` 下拉，区分 `导出文摘` 与 `导出 Markdown`
- 单篇文摘导出复用批量导出弹窗，只是以当前文章作为单元素选择集
- 旧版单篇 `导出 Markdown` 按钮恢复到笔记区右下角，保留原有直接导出习惯
- 修复桌面端首次运行时阅读字号默认值可能被写成 `0px` 的问题，避免标题和正文异常缩小
- 调整阅读页标题层级：文章主标题与“笔记”等小节标题不再共用完全相同的字号规则
- 调整阅读页工具栏按钮间距与导出按钮样式，避免导出入口与其它按钮出现视觉脱节

当前保留限制：

- 未实现 digest 模板自定义
- 未实现固定导出目录设置页
- 未实现批量导出中的摘要生成和笔记编辑
- Electron 目前仅做手动验证路径，未补自动化测试

## 后续可优化项

当前这版更偏“快速原型可用”，如果后续继续整理，优先建议优化以下几点：

1. 前端结构拆分

- `frontend/src/views/ReaderView.vue` 目前同时承担阅读页、批量选择模式、批量导出弹窗三部分职责
- 后续可拆为独立组件和 composable，例如：
  - `BatchSelectionToolbar.vue`
  - `BatchDigestExportDialog.vue`
  - `useBatchDigestExport.ts`

2. 批量导出 UI 打磨

- 继续优化文章列表进入多选模式时的视觉切换
- 优化弹窗内的元信息布局、提示文案和按钮层级
- 根据桌面端和浏览器端分别调整更贴合平台习惯的交互反馈

3. Electron 导出体验

- 增加桌面端真实手测覆盖
- 可考虑补充“最近导出目录”展示或“再次打开所在目录”能力
- 如后续需要，再评估是否引入可配置的默认导出目录

4. 批量摘要工作流

- 当前“包含 AI 摘要”只消费已有摘要记录
- 若后续接入真实 AI Provider，可考虑增加“为缺失摘要文章批量生成摘要”的独立动作
- 不建议直接把摘要生成逻辑塞进勾选框本身

5. 测试补强

- 为后端批量 digest 生成补更多用例：
  - 部分文章缺失 URL/标题
  - 部分文章无摘要
  - 多行笔记和多行摘要渲染
  - 文件名和标题日期规则

## 2026-06-14 当前 UI 恢复记录

阅读页在后续 Week16 UI 改版后，批量导出入口退化为占位提示。本次已按当前三栏阅读布局恢复前端交互，继续复用 Week14 已完成的后端接口和 Electron 保存能力。

恢复内容：

- 文章列表右上角菜单中的“批量文摘”进入批量选择模式。
- 当前列表文章卡片左侧显示选择圆点。
- 顶部批量工具条支持全选、清空、预览导出和退出。
- Digest 预览弹窗支持包含 AI 摘要、包含笔记两个选项。
- Digest 预览弹窗新增包含全文选项，和包含 AI 摘要、包含笔记并列。
- 预览弹窗展示后端生成的 Markdown，可复制或导出。
- Web 端走浏览器下载，Electron 端走 `window.rssReaderDesktop.saveMarkdown` 原生保存对话框。
- 后端批量 digest 请求体新增 `include_full_text` 字段；包含全文时优先使用清洗后的 `cleaned_markdown`，缺失时回退到文章摘要。

仍保留 Week14 原有非目标：

- 不支持自定义 digest 模板。
- 不支持固定导出目录设置。
- 不在批量导出流程内自动生成缺失摘要。
