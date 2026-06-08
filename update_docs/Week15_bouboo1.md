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

后续界面反馈修正中，又补充了两点：

- 当订阅源数量较多时，左栏中的订阅源列表恢复为列表区内部滚动，避免整个侧栏被裁切后无法继续下滑。
- 在小窗口高度下，阅读页主区域改为固定在视口内，由左栏、中栏、右栏各自承担滚动，避免必须拖动整页到底部才能看到文章列表或正文。

### 7. 订阅管理布局收敛

文件：

- `frontend/src/views/FeedManageView.vue`

根据嵌入式订阅管理面板的使用反馈，又对操作区做了进一步收敛：

- 移除“订阅管理”标题下方的冗余说明文案，减少顶部占高。
- 重排顶部操作按钮组，使按钮在较窄窗口下自动换行，不再出现右侧按钮被截断的问题。
- 将“已选 N 个”状态从顶部工具栏移到订阅列表区域下方，使其更贴近批量勾选语义。

### 8. 统计日志页面补渲染

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

---

## 补充修复：RSS 订阅抓取稳定性

文件：

- `backend/app/services/feed_parser.py`
- `backend/tests/test_feed_parser.py`

针对 `https://openai.com/news/rss.xml` 一类偶发无法订阅的问题，本次补充了后端 RSS 抓取稳定性修复：

- 不再只依赖 `feedparser.parse(url)` 直接抓取远端地址。
- 改为先使用显式 HTTP 请求拉取 XML，再把返回内容交给 `feedparser` 解析。
- 请求头增加更接近浏览器的 `User-Agent` 和 XML `Accept`，降低站点拒绝或异常断连概率。
- 对 `Remote end closed connection without response`、`URLError` 等临时网络错误加入最多 3 次重试。
- 对 `parsed.feed is None` 这类异常返回增加兜底，避免出现 `'NoneType' object has no attribute 'get'` 直接导致订阅失败。

本地通过 `python3 -m py_compile` 验证了相关文件语法；由于当前环境未安装 `feedparser` 依赖，单元测试未能在本机实际执行。

### 原文链接补正文说明

当前阅读页中的“从原文链接补正文”按钮，后端流程并不是简单重新读取 RSS，而是：

- 先重新解析该文章所属 RSS 条目。
- 再尝试访问文章原文链接并提取网页正文。
- 最后比较 RSS 内容和原文页内容，优先保存更完整的版本。

这对“RSS 只给摘要、但原网站有完整正文”的订阅源是有效的。

但经实际验证，`openai.com` 文章页当前启用了 Cloudflare 机器人防护：

- 即使已经补上证书校验失败时的抓取回退，服务端请求原文页时仍会收到 `HTTP 403 challenge`。
- 因此 OpenAI 新闻这类文章，当前仍可能只能显示 RSS 摘要，无法稳定补回完整正文。

如果后续要继续支持这类站点，需要考虑引入浏览器级抓取或渲染方案，而不是只依赖 Python 的 HTTP 请求。

### 阅读区补充优化

本日还补了两项阅读体验修正：

- 保持“默认展示 RSS 已保存内容，只有点击刷新正文后才尝试读取原文链接”的交互，不在初次进入文章时自动抓原网页。
- 对正文里无法直接展示的嵌入视频或播放器占位，改为保留“打开视频原链接”的超链接，避免阅读区里只剩空白框但无法操作。
- 同时放宽了右侧正文标题区域的宽度限制，减少标题过早换行的问题。

### 最终交互收束

在继续联调后，本轮又进一步收束了阅读页行为，最终版本不再保留“从阅读页补抓原文全文”的入口，而是回到更稳定的 RSS 阅读器语义：

- 右侧正文默认并最终只展示 RSS 已保存内容的渲染结果。
- 阅读区移除了“补全文/刷新正文”按钮和相关提示，不再从文章详情页触发原文抓取。
- 标题下方保留原文链接，用户仍可随时跳转到文章原网站查看完整页面。
- 左侧订阅源列表改为展示站点 favicon 和该源文章数量，减少仅用首字母头像带来的辨识度问题。
- 对部分 RSS 文本里出现的 `[Image: https://...]` 占位，前端渲染阶段会尽量转换为可显示图片，而不是原样显示为纯文本。

---

## 2026-06-06 补充：VS Code 工作区性能排查

本日另外处理了一个开发环境侧问题：在当前仓库中使用 VS Code 插件时，`Code Helper` 进程出现超过 `300% CPU` 的持续占用，导致插件响应明显变慢。

排查结果：

- 仓库当前文件数约为 `12,589`。
- `frontend/node_modules` 单目录约 `159 MB`，文件数约 `12,361`。
- 仓库还包含 `frontend/dist`、`backend/dist`、`backend/build`、`release` 等构建或生成目录。
- 工作区此前没有 `.vscode/settings.json`，VS Code 只能依赖默认规则，插件与编辑器更容易把依赖目录和产物目录纳入监听、搜索与上下文扫描范围。

本次处理：

- 新增 `.vscode/settings.json`。
- 为当前仓库补充 `files.exclude`、`files.watcherExclude`、`search.exclude`。
- 重点排除 `frontend/node_modules`、`frontend/dist`、`backend/dist`、`backend/build`、`release`、`__pycache__`、`.pytest_cache` 与 `.git` 相关监听对象。

预期效果：

- 降低 VS Code 文件系统监听与搜索索引开销。
- 降低 AI 插件在收集工作区上下文时误扫依赖目录的概率。
- 缓解 `Code Helper` 高 CPU 与插件卡顿问题，尤其是在当前这种前端依赖已安装的课程项目仓库里。

当前限制：

- 该修改主要优化本地工作区扫描范围，不改变插件服务端延迟。
- 如果后续仍偶发高 CPU，需要继续结合 VS Code 的 `Developer: Open Process Explorer` 确认是否为其他扩展、Webview 或终端任务导致。

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

---

## 2026-06-06 补充：Markdown 正文渲染

本日又补了一项阅读页兼容性修正：部分 RSS 条目正文实际是 Markdown 文本，而不是 HTML，原先会被直接当普通字符串渲染，导致标题、列表、链接、图片等 Markdown 结构无法正常显示。

本次处理：

- 在 `ReaderView.vue` 中补充正文内容类型判断。
- 若正文已经是 HTML，则继续按原有方式渲染。
- 若正文看起来是 Markdown，则在前端自动转换为 HTML 后再显示。
- 当前支持的 Markdown 结构包括：标题、无序列表、有序列表、引用、代码块、行内代码、粗体、斜体、链接和 Markdown 图片。

验证：

- 执行 `cd frontend && npm run build`，构建通过。

当前限制：

- 本次是轻量级 Markdown 渲染，不包含完整 CommonMark 全量特性。
- 若后续确认大量订阅源会直接提供 Markdown，可考虑将 Markdown 转 HTML 下沉到后端统一处理。
