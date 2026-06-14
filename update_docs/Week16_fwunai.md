# Week16 fwunai - AI 摘要前端展示系统

## 本周负责范围

- AI 摘要结果展示页面重构。
- 底部可交互摘要抽屉组件开发。
- 摘要 Markdown 渲染。
- 摘要语言输出修复（中文/英文标题模板分离）。
- 摘要生成过程可视化展示。
- 多语言选择器与系统语言自动检测。
- 生成失败/内容不完全红字警告居中展示。
- 拖拽无延迟优化与生成时抽屉高度自动调整。
- 生成状态图标与按钮交互优化。

## 主要实现

### 1. 底部摘要抽屉

将原有"正文下方展示摘要"的方式重构为固定在第三栏底部的可折叠抽屉栏。

- 抽屉默认收起，标题栏显示"AI 摘要"，箭头向上提示可展开。
- 点击标题栏展开/收起，展开后箭头向下。
- 抽屉内包含语言选择下拉菜单和生成摘要按钮。
- 生成失败时按钮文字变为"重新生成摘要"，标题栏边框变红提示。
- 切换文章时自动收起抽屉并清空上次结果。

### 2. 可拖拽调高

在抽屉顶部边框放置一条 8px 的透明拖拽条（`summary-drawer-resize-bar`）：

- 只在抽屉展开后显示，hover 时中间出现主题色小把手。
- 拖拽直接操作 DOM `style.setProperty('--drawer-height', ...)`，完全绕开 Vue 响应式，实现无延迟实时跟手。
- 高度范围限制在 120px–700px，mouseup 时再同步回 ref。
- 摘要生成完成后自动将抽屉高度弹升至第三栏面板高度的三分之一。

### 3. 摘要生成过程可视化

生成期间在抽屉内展示后端真实 SSE 事件步骤流：

- 当前活跃步骤显示呼吸动画圆点，已完成步骤沉淀为时间线记录并显示耗时。
- 步骤流仅在生成期间展示，生成完成后自动清空，只保留最终摘要内容。
- 生成完成立即展示摘要，不再有额外延迟。

### 4. 摘要 Markdown 渲染

摘要结果使用前端已有的 `markdownToHtml` 函数渲染，支持标题、列表、加粗、代码等格式，不再展示 Markdown 源码。

修复了 `renderMarkdownBlock` 函数在标题行后直接 return 导致同段落正文内容丢失的问题：标题匹配后现在会继续递归渲染剩余行。

### 5. 摘要语言输出修复

后端 `_mode_instruction` 函数原本硬编码中文标题模板（`## 一句话概览`、`## 关键要点`），导致选择英文生成时标题仍为中文。

修复方式：`_mode_instruction` 新增 `language` 参数，按语言分别返回中文和英文模板，两处调用点均传入 `options.language`。

英文模板示例：`## Overview`、`## Key Takeaways`、`## Keywords`。

### 6. 多语言选择器

将原有双选 `el-segmented`（仅中文/英文）改为 `el-select` 下拉菜单，支持 10 种语言：

| 语言代码 | 显示名称 |
|---|---|
| zh | 中文 |
| en | English |
| ja | 日本語 |
| ko | 한국어 |
| fr | Français |
| de | Deutsch |
| es | Español |
| pt | Português |
| ru | Русский |
| ar | العربية |

默认值通过 `navigator.language` 检测系统语言自动匹配，不支持的语言 code 回退到英文。

修复了非中英文语言始终生成失败的问题：根本原因是后端 `SummaryRequest` Pydantic 模型将 `language` 字段声明为 `Literal["zh", "en"]`，Pydantic 在请求进入服务层前就以 422 拒绝了其他语言代码。将字段类型放宽为 `str` 后恢复正常。

后端新增 `_language_display()` 映射函数，将语言代码转为完整语言名称写入 prompt（如 `日本語`、`Français`），使模型按所选语言输出内容。

### 7. 生成失败/内容不完全警告居中

标题栏原为 `flex + space-between` 布局，警告文字紧贴箭头左侧。

改为三列 grid 布局（`auto 1fr auto`）：左列为 AI 摘要图标和标题，中列为警告文字（`justify-content: center`），右列为箭头。红字警告始终水平居中于标题栏。

### 8. 拖拽无延迟优化

拖拽逻辑本身已绕开 Vue 响应式（直接写 DOM CSS 变量），但仍存在视觉延迟。

根本原因：`.summary-drawer-body` 有 `transition: height 0.35s cubic-bezier(...)`，每次 `--drawer-height` 变化都触发缓动，导致高度变化滞后于鼠标。

解决：拖拽开始（`mousedown`）时将 `body.style.transition = 'none'` 临时关闭过渡，`mouseup` 松手后清空恢复，展开/收起动画不受影响。

### 9. 生成时抽屉高度自动调整

点击"生成摘要"时，若当前抽屉高度低于 280px，自动提升至 280px（controls 约 60px + 3 条步骤约 180px + padding），确保步骤流内容完整可见，不被裁切。若用户已将抽屉拖得更高则不干预。

### 10. 生成状态图标与按钮交互优化

- 标题栏 MagicStick 图标不再旋转，始终静止；"AI 摘要"文字固定不变。
- 生成中在文字右侧条件渲染小转圈图标（Element Plus `Loading`，0.9s 匀速旋转），生成结束后消失。
- "生成摘要"按钮生成中改为 `disabled` 禁用状态，移除 `el-button` 的 `:loading` 转圈动画，按钮图标保持 MagicStick 静止。

### 11. 去除可信度输出

后端 prompt 中移除了"最后增加一行 `可信度：高/中/低`"的指令，前端 `renderedAiResult` 计算属性同时加了正则过滤作为保底，确保旧缓存结果也不展示可信度行。

## 实际测试记录

### 前端类型检查

```bash
cd frontend
./node_modules/.bin/vue-tsc --noEmit --pretty false
```

结果：通过，无类型错误。

### 前端构建

```bash
cd frontend
npm run build
```

结果：通过。

### 手动功能验证

- 启动前后端，订阅 `https://hnrss.org/frontpage`，选取文章点开摘要抽屉。
- 点击"生成摘要"，确认步骤流实时显示（读取文章上下文 → 评估预算 → 调用模型 → 保存结果）。
- 生成完成后步骤流消失，摘要以渲染后的富文本形式展示。
- 选择英文语言生成，确认标题为英文（`## Overview`、`## Key Takeaways`）。
- 选择日语/法语等语言生成，确认内容以对应语言输出，不再报生成失败。
- 拖拽顶部把手调整抽屉高度，确认实时跟手无延迟。
- 切换文章，确认抽屉自动收起并清空上次摘要。
- 模拟生成失败/内容不完全，确认红字警告显示在标题栏中央。

## 遇到的问题与解决

### 1. 摘要抽屉跟着正文滚动，不固定在底部

原因：第三栏 `reader-detail-panel` 使用 `overflow-y: auto` + `position: sticky`，抽屉无法真正固定在可视底部。

解决：将 `reader-detail-panel` 改为 `display: flex; flex-direction: column; overflow: hidden`，内部正文区新增 `reader-scroll-area`（`flex: 1; overflow-y: auto`）负责滚动，抽屉用 `flex-shrink: 0` 固定在 section 底部。

### 2. 拖拽有延迟，不跟手

原因：拖拽时更新 Vue `ref`，触发组件重新渲染，每次 `mousemove` 都走响应式调度，导致肉眼可见的延迟。

解决：`mousemove` 回调中直接调用 `el.style.setProperty('--drawer-height', ...)` 操作 DOM，完全绕开 Vue 响应式，只在 `mouseup` 时将最终值同步回 ref。

### 3. 标题后正文内容丢失

原因：`renderMarkdownBlock` 匹配到标题后直接 `return`，丢弃了同一段落内标题下方的正文行。

解决：标题匹配后继续 `renderMarkdownBlock(rest.join('\n'))` 递归渲染剩余行，同时为函数添加显式返回类型注解 `: string` 避免 TS 递归类型推断报错。

### 4. 英文摘要标题仍为中文

原因：`_mode_instruction` 硬编码中文占位模板，`output_language` 变量只影响 system prompt 里的语言说明，不影响格式模板。

解决：`_mode_instruction` 增加 `language` 参数，按 `zh`/`en` 分支返回对应语言的格式模板，两处调用点均传入 `options.language`。

### 5. 非中英文语言始终生成失败原因：后端 `SummaryRequest` Pydantic 模型 `language` 字段声明为 `Literal["zh", "en"]`，Pydantic 在请求进入服务层前就以 422 拒绝了其他语言代码，和提示词完全无关。

解决：将 `language` 字段类型改为 `str`；前端 `SummaryRequestPayload` 接口同步放宽；后端新增 `_language_display()` 映射函数，把语言代码转为完整语言名称写入 prompt。

### 6. CSS 语法错误（Unexpected }）

原因：编辑 `.summary-drawer-handle-label` 时，在结束花括号前插入新类块，导致原类的剩余属性行变成孤立语句，PostCSS 解析报 `Unexpected }`。

解决：将孤立的属性行提取为独立类规则，恢复合法的 CSS 块结构。

### 7. 拖拽仍有延迟

原因：拖拽 mousemove 回调已直接操作 DOM，但 `.summary-drawer-body` 的 `transition: height 0.35s` 在每次 CSS 变量变化时触发缓动，导致高度变化在视觉上滞后于鼠标。

解决：拖拽开始时 `body.style.transition = 'none'`，mouseup 后清空，只在展开/收起时保留过渡动画。

### 8. 抽屉拖到顶后右侧滚动条变长，底部摘要内容被截断

原因：`.reader-detail-panel` 是 `display: flex; flex-direction: column; overflow: hidden`，上方文章区 `reader-scroll-area` 设了 `flex: 1 1 auto; min-height: 0`，抽屉设了 `flex-shrink: 0`。当 `--drawer-height` 超出面板剩余空间时，抽屉不收缩，文章区被压缩至 0，抽屉底部被 `overflow: hidden` 截断，导致摘要底部内容不可见；同时因 flex 布局溢出，右侧出现多余滚动条。

解决：在所有涉及最大高度计算的地方，统一为：

```typescript
const maxH = Math.floor(panelHeight - handleHeight - 120)
```

为文章区预留至少 120px 可见空间，拖拽上限、生成时自动展开高度、摘要结果到达后的自动弹升高度三处均使用同一公式，杜绝抽屉完全覆盖文章区的情况。

## 本周新增：摘要内容美化

### 12. 摘要正文排版优化

调整摘要结果区正文样式，提升阅读舒适度：

- 正文字号 13.5px，行高 1.8
- h2 章节标题字号略大于正文，加粗，`letter-spacing: 0.01em`，与正文形成明显层级对比
- h2 标题上方间距 1.3em，下方 0.45em，视觉节奏更清晰

### 13. h2 标题前语义图标

`renderedAiResult` 计算属性在渲染后的 HTML 中，用正则替换所有 `<h2>` 标签，根据标题文字关键词注入对应 emoji 图标：

| 关键词（含多语言） | 图标 |
|---|---|
| 一句话、概览、概要、overview | 💬 |
| 核心、要点、关键要点、key、takeaway | 📌 |
| 关键词、keyword、キーワード、키워드 | 🏷️ |
| 背景、context | 📖 |
| 结论、conclusion | ✅ |
| 风险、警告、warning | ⚠️ |

无法匹配的标题使用 `▪` 作为默认前缀。图标通过 `<span class="summary-h2-icon">` 包裹，与标题文字 `gap: 6px` 对齐。

### 14. 关键词胶囊标签

在 `renderedAiResult` 中，用正则识别关键词章节（匹配多语言 h2 标题），将该节段下的 `<p>` 内容按 `；;、,，·` 及空白符切分为独立标签，渲染为胶囊形状的 `<span class="summary-tag">`。

样式使用 `color-mix()` 基于 `--theme-accent` 实现主题自适应：

```css
background: color-mix(in srgb, var(--theme-accent) 9%, var(--app-surface) 91%);
border: 1px solid color-mix(in srgb, var(--theme-accent) 35%, transparent 65%);
color: color-mix(in srgb, var(--theme-accent) 80%, var(--app-text) 20%);
border-radius: 999px;
padding: 3px 11px;
```

### 15. 生成摘要按钮升级

将原 Element Plus `el-button` 替换为自定义 `<button class="summary-generate-btn">`：

- 圆角 10px，高度 36px，`border + inset 阴影 + color-mix 主题色背景`
- 正常态：sparkle 闪光 SVG 图标（4 条射线 + 中心菱形）
- 生成中：切换为旋转圆弧 SVG（`stroke-dasharray` 模拟缺口圆），添加 `spin` CSS 动画，文字变为"生成中…"
- disabled 期间指针 `not-allowed`，透明度降低

### 16. 复制按钮与复制交互

将复制入口从标题栏移至摘要结果卡底部（`.summary-result-footer`），设计为浅描边风格按钮：

- 正常态：复制图标（两个叠置矩形 SVG）+ "复制摘要"文字
- 点击后：使用 `navigator.clipboard.writeText` 写入剪贴板，图标切换为绿色勾选 SVG，文字变为"已复制"
- 2 秒后 `copyDone.value = false` 自动复原
- 复制内容过滤掉可信度行（正则 `/^可信度[：:].+$/gm`）和多余空行

### 17. 标题栏文案与说明

- "AI 摘要"文字改为 `<strong>` 加粗
- 同行追加说明文字"由 AI 为你总结本篇文章核心内容"（`summary-drawer-desc`），字号 11px，`--el-text-color-secondary`，通过 `summary-drawer-title-wrap` 的 `align-items: baseline` 与标题对齐

### 18. 控制栏 sticky 固定

语言选择 + 生成按钮所在的 `.summary-drawer-controls` 改为 `position: sticky; top: 0; z-index: 1`，背景设为不透明（`color-mix` 混合 `--app-surface-strong`），使抽屉体内容滚动时控制栏始终可见。

## 本周新增：用量统计可视化

### 19. 用量统计面板重构

将原有纯文字的 LLM 用量统计区域重构为带时序柱状图的可视化面板。

**引入依赖：**`chart.js ^4.4.7`、`vue-chartjs ^5.3.2`

**面板功能：**
- 右上角折叠/展开箭头，可收起整个面板
- 时间跨度选择：今天 / 本周 / 本月 / 全部
- 本月范围从当月 1 日起算，不再跨月倒推 30 天
- 右上角请求次数 / TOKEN 切换按钮，切换柱状图数据集
- 刷新按钮同时刷新统计数据、时序数据和同步日志

**摘要卡片：**三列横排（总请求 / 输入 Token / 输出 Token），紧凑行内样式，文字居中，数值超过 1000 显示为 `K`。

**柱状图优化：**
- 圆角 6px，柱子 `barPercentage: 0.5` 变细，`borderSkipped: false` 四角均圆
- hover 时不透明度提升至 1
- y 轴虚线网格（`rgba(0,0,0,0.06)`，`dash: [4,4]`），去掉轴边框线
- 今天跨度 x 轴最多显示 8 个刻度（`maxTicksLimit: 8`），避免 24 个小时标签密集
- TOKEN 模式 legend 右对齐（`align: 'end'`）
- tooltip 在该时间点所有数据集均为 0 时不显示

### 20. 请求异常统计

**后端数据库：** `ai_results` 表新增 `status TEXT NOT NULL DEFAULT 'success'` 列，通过 `_migrate_ai_tables` migration 自动补列，存量数据默认为 `success`。

**后端写入：** `ai_service.summarize()` 在捕获 `SummaryAgentError` 时写入一条 `status='failed'` 的记录（prompt 为空，result 为错误信息，tokens 为 0），再 re-raise 不改变原有错误流程。

**后端统计：** `stats()` 和 `stats_timeseries()` 查询均加入 `failed_calls` 聚合（`SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END)`）。

**前端 tooltip：** 请求次数模式下，`afterBody` 在 `failed_calls > 0` 时追加"请求异常: N (X%)"一行。

### 21. 时区修复

**问题：** SQLite `CURRENT_TIMESTAMP` 存的是系统本地时间，但后端原先用 `datetime.now(timezone.utc)` 计算 cutoff，两者时区不一致，导致"今天"范围过滤和小时分桶均偏移 8 小时。

**修复：**
- `_range_cutoff` 和 `_fill_buckets` 统一改用 `datetime.now()`（无时区，本地时间）
- `stats_timeseries` SQL 分桶表达式通过 Python 计算本地与 UTC 的秒级偏移，以 `datetime(created_at, '+N seconds')` 转换后再 `strftime` 分桶
- cutoff 格式改为 `%Y-%m-%d %H:%M:%S`（空格分隔），与 SQLite `CURRENT_TIMESTAMP` 输出格式一致

### 22. 摘要生成按钮与圆点动画优化

**按钮：** 移除 `:icon="MagicStick"`，只保留"生成摘要"/"重新生成摘要"文字。

**active 圆点波纹动画：**
- 改用 `::before` 伪元素从圆点中心向外扩散（`scale: 1→2.8`，`opacity: 0.5→0`）
- 缓动曲线 `cubic-bezier(0.4, 0, 0.6, 1)`，持续 1.4s 无限循环
- 视觉效果：中心亮点稳定，波纹匀速扩散消失，更丝滑

**done 状态颜色：** accent 颜色混合比例从 70% 降至 35%，明显变浅，表示该步骤已完成。

## 后端接口变更

| 接口 | 变更 |
|---|---|
| `GET /api/stats/llm` | 新增 `range` query param（today/week/month/all），新增 `failed_calls` 字段 |
| `GET /api/stats/llm/timeseries` | 新增接口，返回时序分桶数据（`time_label`/`calls`/`failed_calls`/`input_tokens`/`output_tokens`） |

## 实际测试记录

### 前端类型检查

```bash
cd frontend
npx vue-tsc --noEmit
```

结果：通过，无类型错误。

### 手动功能验证

- 打开统计页，确认柱状图显示本地时间小时（今天跨度显示 10:xx 而非 02:xx）。
- 切换今天 / 本周 / 本月 / 全部，确认摘要卡片数值和图表同步刷新。
- 本月跨度确认从当月 1 日起算。
- 切换请求次数 / TOKEN，确认图表数据集和 legend 正确切换。
- 折叠/展开箭头功能正常。
- 点击生成摘要，确认按钮无 MagicStick 图标，步骤流 active 圆点有向外扩散波纹动画，done 步骤颜色变浅。

## 当前限制

- 时区处理依赖后端系统本地时区；若后端部署在不同时区的服务器上，需额外传入客户端时区偏移。
- 请求异常统计目前只覆盖摘要功能，translate 和 tag_suggestion 暂未接入 `status='failed'` 写入。
- 摘要步骤流圆点波纹动画为 CSS `::before` 伪元素实现，不支持在 `overflow: hidden` 父容器内显示完整波纹（需父容器 `overflow: visible`）。

