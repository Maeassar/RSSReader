# Week15 bouboo1 - 内容清洗与阅读优化

## 本周完成内容概览

本周围绕“内容清洗与阅读优化系统”完成了从后端正文处理到前端阅读界面收纳的一整轮迭代，重点包括：

- 后端补齐 HTML 内容清洗、Markdown 转换和链接型文章正文补抓。
- 入库时统一生成 `cleaned_html` 与 `cleaned_markdown`，供阅读页、导出和 AI 能力复用。
- 前端阅读页重构为更接近阅读器产品的三栏结构，并持续压缩交互层级。
- 新增主题模式、主题配色、字号、行距、正文宽度等阅读偏好设置。
- 新增标签交互、订阅管理嵌入式页面、文章置顶、排序/视图菜单、缩略图开关等阅读增强能力。
- 结合 macOS 本地运行，对前端页面在 Electron/Web 共用场景下做了功能验证与样式调整。

---

## 后端部分

### 1. HTML 内容清洗模块

文件：

- `backend/app/services/content_cleaner.py`

本轮清洗逻辑主要做了这些事：

- 移除 `script`、`style`、`iframe`、`form`、`svg`、`canvas` 等不适合阅读或存在风险的标签。
- 优先识别 `article`、`main`、`.post-content`、`.entry-content` 等正文节点，减少页面壳层和广告噪声。
- 处理懒加载图片，优先把 `data-src`、`data-original`、`data-lazy-src` 等地址补到 `src`。
- 清理无意义属性、空块元素和空链接，保留更干净的正文结构。
- 在清洗后的 HTML 基础上生成适合导出的 Markdown 内容。

### 2. 链接型文章正文补抓

文件：

- `backend/app/services/webpage_extractor.py`
- `backend/app/services/feed_parser.py`

为了解决部分 RSS 源正文很短、只有摘要和原文链接的问题，新增了保守的网页正文补抓流程：

- 当 RSS 提供的摘要内容过短且存在原文链接时，尝试访问原网页。
- 使用 `readability-lxml` 提取网页主正文。
- 将相对路径补成绝对链接。
- 再交给现有 `clean_html()` 流程统一生成 `cleaned_html` 和 `cleaned_markdown`。

这一点对后续 AI 摘要、文章详情展示和导出 Markdown 都有帮助。

### 3. 入库链路接入清洗结果

文件：

- `backend/app/repositories/sqlite_repository.py`

当前文章写入 `entries` 表时，会同时保存：

- `raw_html`
- `cleaned_html`
- `cleaned_markdown`

这样前端阅读、导出和 AI 处理都可以直接复用已经清洗好的内容，不需要重复清洗。

### 4. 相关后端联动文件

本轮阅读优化还联动调整了：

- `backend/app/services/article_service.py`
- `backend/app/routers/articles.py`

主要用于支持阅读页“尝试补全文”以及文章详情刷新后的内容回填。

---

## 前端部分

### 1. 阅读页整体结构重构

文件：

- `frontend/src/views/ReaderView.vue`
- `frontend/src/styles.css`
- `frontend/src/stores/reader.ts`

阅读页目前采用三栏结构：

- 左栏：订阅与筛选
- 中栏：文章列表
- 右栏：文章详情与笔记

在此基础上，本周逐步完成了这些交互优化：

- 左栏固定展示 `全部文章 / 未读文章 / 收藏`。
- `标签` 改为轻交互模式，只负责展开/收起标签列表，不再切换整页。
- `订阅源` 支持在左栏直接切换当前订阅过滤。
- 中栏新增菜单式操作入口，支持排序、摘要行数、缩略图展示和退订当前订阅源。
- 文章支持 `置顶`，置顶文章会在当前排序基础上优先显示。
- 文章卡片补充来源、日期、摘要和可选缩略图，层级更接近 RSS 阅读器风格。

### 2. 订阅管理页面统一

文件：

- `frontend/src/views/FeedManageView.vue`
- `frontend/src/App.vue`
- `frontend/src/views/ReaderView.vue`

本轮将订阅管理统一成两种一致的打开方式：

- 左栏订阅源区域点击 `+` 或 `... -> 管理订阅源`
- 右上角导航点击 `订阅`

它们都会回到阅读页，并在保留最左栏的前提下，在中间和右侧区域打开订阅管理面板，而不是跳成一张完全独立、风格不一致的普通页面。

当前订阅管理面板支持：

- 添加订阅
- 同步全部
- OPML 导入
- OPML 导出
- 单个订阅同步
- 单个订阅删除

### 3. 标签交互

文件：

- `frontend/src/views/ReaderView.vue`
- `frontend/src/views/TagsView.vue`

本轮实际保留下来的标签能力是“轻交互”方案：

- 左栏支持新建标签和按标签筛选文章。
- 正文工具栏中的标签按钮支持给当前文章分配标签。
- 正文区标签按钮修复了点击无效的问题。
- 当前实现还带有前端本地持久化兜底，避免后端标签关联能力不完整时完全不可用。

### 4. 主题与阅读设置

文件：

- `frontend/src/views/SettingsView.vue`
- `frontend/src/stores/preferences.ts`

当前设置项包括：

- 主题模式：浅色 / 深色
- 主题配色：多组颜色卡片切换
- 新增基础 `黑白灰` 默认主题
- 自定义主题色
- 阅读字号
- 行距
- 正文宽度
- 启动同步 / 定时同步 / 同步间隔

本轮又继续压缩了设置区交互：

- 将“主题”做成折叠卡片，避免占用过大空间。
- 缩小色卡尺寸和间距，减少空白感。
- 增加黑白灰默认主题，避免只有彩色系主题可选。

### 5. 阅读正文与笔记区

文件：

- `frontend/src/views/ReaderView.vue`
- `frontend/src/styles.css`

正文区目前的逻辑：

- 默认优先显示摘要视图。
- 点击“尝试补全文 / 加载网页原文”后，再切换到全文视图。
- 再次点击可回到摘要视图。

笔记区目前支持：

- 保存当前 Markdown 笔记
- 单独导出“导出笔记”

本轮还对右侧工具栏和底部按钮做了统一：

- 工具按钮配色、边框和填充更统一。
- `保存笔记` 和 `导出笔记` 改为同一套主按钮风格。

### 6. 左栏细节优化

文件：

- `frontend/src/views/ReaderView.vue`

为了让左侧更像稳定导航区而不是可滚动内容区，本轮做了这些处理：

- 左栏去掉单独滚动条，不再作为滚动面板。
- 订阅源名称超出宽度时使用省略号。
- 鼠标悬停在订阅源名称上时，显示完整标题。

### 7. 统计日志页面补渲染

文件：

- `frontend/src/views/StatsView.vue`

虽然这不是 Week15 的核心任务，但在本轮联调中顺手修整了统计日志页：

- 将统计页整理为更完整的卡片化布局。
- 显示 LLM 调用次数、输入 Token、输出 Token。
- 同步日志改为更清晰的时间线展示。

---

## 导出相关影响

文件：

- `backend/app/services/export_service.py`
- `frontend/src/views/ReaderView.vue`

当前导出相关的语义已经调整为：

- 顶部导出菜单：导出文摘 / 导出清洗后 Markdown
- 底部笔记区：导出笔记

其中：

- “导出清洗后 Markdown” 依赖后端保存的 `cleaned_markdown`
- “导出笔记” 导出的是当前笔记框内的 Markdown 内容

---

## 测试与验证

相关测试文件：

- `backend/tests/test_content_cleaner.py`

建议执行：

```bash
cd backend
python -m unittest discover -s tests

cd ../frontend
npm run build
```

本轮前端样式和交互多次调整后，已反复执行：

```bash
cd frontend
npm run build
```

构建通过。

---

## macOS 端功能测试说明

按照分工，Week15/Week17 需要补充 Mac 端功能测试。本轮实际验证重点在本地运行与页面交互层，已覆盖：

- 前端在 macOS 本地 `npm run dev` 环境下可正常启动。
- 后端文档页 `http://127.0.0.1:8000/docs` 可正常访问。
- 阅读页主题、布局和按钮交互在本地浏览器环境可用。
- 订阅管理、标签分配、导出笔记、正文切换等前端交互已做多轮本地验证。

如果后续课程汇报需要更正式的 Mac 桌面端测试记录，建议补充：

- Electron 启动与关闭测试
- 设置持久化测试
- 深浅色主题切换测试
- 导出与同步流程测试

---

## 当前限制

- 对于摘要极短但带原文链接的文章，系统会尝试补抓正文，但抓取结果仍受目标站点限制、动态渲染方式和网页结构复杂度影响。
- 标签交互当前已可在前端稳定使用，但后端标签关联查询能力仍有继续补强空间。
- 阅读页的很多样式细节已经较大程度收敛，但若后续继续追求更像成熟产品的视觉层次，建议把 `ReaderView.vue` 再拆分成更小的组件维护。
- 当前仓库内仍存在 `frontend/dist/` 等生成物变更风险，提交前应注意只提交源码与文档，不提交构建产物。
