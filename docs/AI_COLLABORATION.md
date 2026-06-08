# AI 协作记录

## 2026-05-18

本项目开发过程中使用 Coding Agent 辅助完成需求拆解、架构规划和代码骨架生成。

## 协作内容

- 根据 `demand.png` 提取 Mercury Features 和 Technical Constraints。
- 将桌面端 Mercury 功能转换为 Vue + FastAPI Web 应用方案。
- 设计 Mock-first 后端架构，保留 SQLite Repository 替换点。
- 生成 FastAPI 路由、Pydantic Schema、Service 和 Repository。
- 生成 Vue 页面、API Client、Pinia Store 和基础样式。
- 编写项目 README 和设计文档。

## 当前限制

- 当前版本已接入 SQLite 持久化，但标签关联、全文搜索索引、LLM Provider 配置和迁移机制仍需继续完善。
- AI 摘要、翻译、标签推荐仍以 Mock 结果或预留接口为主。
- RSS、OPML 和 Sync 流程已有接口基础，后续需要继续完善自动同步、订阅迁移和异常处理。

## 2026-05-19

本日使用 AI Coding Agent 辅助完成项目早期文档写作、需求拆解和技术方案整理，主要用于将课程项目需求转换为可协作开发的工程说明。

### 协作与整理内容

- 根据项目需求梳理 RSSReader 的核心功能边界，包括订阅源管理、文章阅读、笔记、搜索、导出、AI 摘要和 AI 翻译等模块。
- 辅助整理 Vue 3 + Vite、FastAPI、SQLite 的技术栈说明，并将其写入项目规划和说明文档。
- 辅助生成后端 API、数据库设计、前端页面结构和协作流程的初版文档。
- 辅助撰写 README、开发计划、贡献说明和 AI 协作记录，使后续成员可以快速理解项目目标与分工。
- 将原始需求中的功能点拆分为更适合 GitHub Issues、周任务和 Pull Request 的开发条目。

### AI 参与方式

- AI 主要承担需求归纳、文档草拟、结构优化和技术表达润色。
- 人工负责确认课程要求、项目范围、最终技术选型和文档是否符合团队协作习惯。
- AI 生成内容经过人工审阅后再纳入仓库，避免直接提交未经确认的设计假设。

### 当日产出

- 项目 README 和功能概览草稿。
- 后端 API 与数据库设计说明草稿。
- Vue/FastAPI/SQLite 项目结构规划。
- Mock-first 开发思路和后续 SQLite Repository 替换说明。
- AI 协作记录初版。

## 2026-05-20

- 使用 Coding Agent 梳理项目协作规则，将开发阶段的集成分支调整为 `develop`，并明确 `main` 在开发结束前仅作为助教查看 README 和项目概览的文档分支。
- 补充 Agent 协作记录要求：后续与 AI Agent 协作后，需要在本文件追加带日期的协作内容、产出和限制。
- 修正 `Plan.md` 中过期的当前功能和数据库接入说明，使其与现有 SQLite Repository、`schema.sql`、`app.db` 和 README 功能规划保持一致。

## 2026-05-22

- Used AI Coding Agent to implement the Electron desktop packaging plan for cross-platform RSSReader delivery.
- Added an Electron main process and preload bridge, plus root scripts for desktop development and installer builds.
- Added a FastAPI desktop server entry and PyInstaller build helper so the backend can run as a bundled local executable.
- Updated SQLite configuration to support `RSSREADER_DB_PATH`, allowing desktop runtime data to live in the OS user data directory.
- Updated frontend API configuration so the desktop app can inject the local backend URL while browser development keeps the Vite `/api` proxy.
- Remaining limitations: platform installer signing/notarization is not configured, and macOS/Linux package verification still needs to be run on those systems.

## 2026-05-25

- 使用 AI Coding Agent 协助重新整理项目说明文档。
- 将 `INIT.md` 重写为英文项目需求与架构说明，覆盖 RSSReader 功能、跨平台桌面端目标和 Vue/FastAPI/SQLite/Electron/PyInstaller 技术栈。
- 将 `docs/NOTES.md` 重写为中文开发说明，补充功能设计、启动方式、桌面端数据库位置、接口测试和 PR 流程。
- 在 README 中追加唐益 Week13/Week14 macOS 桌面端功能测试职责，以及成员分工概览修订说明。
- 当前限制：README 原有中文内容存在历史编码显示问题，本次采用追加修订小节而不是整体重写，以减少对原始 README 的破坏。

## 2026-05-28

- 使用 AI Coding Agent 协助优化订阅管理页面。
- 将订阅列表中的最后同步时间按 UTC+8 展示为 `yyyy/M/d HH:mm:ss` 格式。
- 在订阅操作栏新增删除按钮，调用现有 `DELETE /api/feeds/{feed_id}` 接口，并在删除前进行二次确认。
- 当前限制：本次只调整订阅管理页展示和删除交互，未扩展订阅删除后的阅读页状态联动测试。

## 2026-05-30

- 使用 AI Coding Agent 设计并实现批量 digest 导出功能，目标是对齐 Mercury 风格的多篇导出流程，并适配当前 RSSReader 的 Web/Electron 架构。
- 在 `update_docs/Week14_batch_export_plan.md` 中先写明任务目标、范围、接口方案和跨平台保存策略，再据此推进实现。
- 后端新增 `POST /api/export/digests/markdown`，统一生成批量 digest Markdown，支持可选 AI 摘要、可选笔记、按当前列表顺序导出，以及跳过缺少标题或链接的文章。
- 前端阅读页新增批量导出模式、文章多选、Digest 预览弹窗、复制和导出动作；Web 端使用浏览器下载，Electron 端调用原生保存对话框。
- Electron 新增保存 Markdown 的 IPC 能力，并在桌面端记忆上一次成功保存的导出目录。
- 当前限制：本次未实现 digest 模板自定义、固定导出目录设置页和桌面端自动化测试；Electron 导出目录记忆目前仅记录最近一次成功保存的目录。
- 后续优化建议：继续收敛批量导出 UI，必要时把 `ReaderView.vue` 中的批量选择工具条和导出弹窗拆为独立组件，并补充桌面端手测记录与批量导出测试用例。
- 后续迭代中又补充了单篇导出入口的语义区分：将当前文章顶部工具栏中的导出入口整理为 `导出文摘 / 导出全文` 下拉，避免把全文导出与 digest 导出混在一起。
- 同时修复了桌面端首次运行时阅读字号默认值可能被错误初始化为 `0px` 的问题，并重新调整了阅读页标题与小节标题的字号层级，改善 Electron 客户端的可读性。

## 2026-05-31

- 使用 AI Coding Agent 继续微调阅读页导出相关交互，修正工具栏按钮间距、批量导出按钮宽度预算和导出入口层级。
- 恢复旧版单篇 `导出 Markdown` 入口到笔记区右下角，同时保留顶部导出菜单中的文摘导出能力。

## 2026-06-02

- 使用 AI Coding Agent 协助补齐 Week14 的 OPML 与 Feed 同步系统。
- 后端将 OPML 导入从 Mock 改为真实 XML 解析，支持递归读取 `outline` 中的 `xmlUrl`，并在导入后立即创建订阅、同步文章和写入 SQLite。
- 后端将 OPML 导出改为读取当前 SQLite `feeds` 表生成 OPML 2.0 XML。
- `POST /api/feeds/sync-all` 改为返回同步汇总对象，单个 Feed 失败不会阻断其它 Feed，并保留失败结果供前端提示和日志排查。
- 前端订阅管理页新增 OPML 文件上传、真实 OPML 导出和同步结果分级提示。
- 设置页新增 Feed 同步偏好：启动时自动同步默认开启，定时同步默认关闭，默认间隔 60 分钟；同步偏好先保存在前端本地存储。
- 当前限制：定时同步只在应用运行期间生效，不提供系统级后台任务；OPML 导入即同步会受到慢速订阅源影响。

## 2026-06-04

- 使用 AI Coding Agent 协助推进 Week15 的“内容清洗与阅读优化系统”任务。
- 后端重写 `content_cleaner`，补充正文节点选择、危险标签移除、懒加载图片归一化、空链接展开和 Markdown 转换逻辑。
- 将清洗流程正式接入 SQLite 文章入库链路，使 `cleaned_html` 与 `cleaned_markdown` 不再只是预留字段，而会随文章同步自动生成。
- 前端扩展阅读偏好设置，新增阅读纸张、行距、正文宽度，并在应用启动时立即应用对应样式变量。
- 阅读页补充正文渲染降级逻辑和新的阅读卡片样式，改善文章详情页的稳定性与可读性。
- 新增内容清洗测试文件，并补充 `update_docs/Week15_bouboo1.md` 说明本周接口影响、实现范围和后续限制。
- 当前限制：尚未在仓库内补充实际 macOS 手测截图或详细记录，若课程汇报要求展示平台测试过程，仍需后续人工补充。

## 2026-06-05

- 使用 AI Coding Agent 继续推进 Week15 的阅读交互细化与界面收纳。
- 将设置页中过大的“外观”模块压缩为更小的“主题”折叠卡片，并保留浅色、深色、设备模式与配色切换能力。
- 在阅读页左侧新增可折叠的 `筛选`、`标签`、`订阅源` 分组，统一整理 `全部`、`未读文章`、`收藏` 等入口。
- 为阅读页补充标签创建、文章标签分配、标签筛选，并在后端标签关联能力不足时增加前端本地持久化兜底。
- 在文章列表顶部新增菜单式入口，支持时间排序、摘要行数、缩略图显示和退订当前订阅源。
- 在文章详情工具栏新增 `置顶`，并让置顶文章优先显示，改善高频文章的回看效率。
- 将“加载全文”文案和反馈调整为更保守的“尝试补全文”，避免误导为稳定全文抓取能力。
- 当日验证：执行 `cd frontend && npm run build`，构建通过。
- 当前限制：文章标签的后端持久化和按标签过滤目前仍以本地交互为主，若后续要支持跨设备一致性，需要继续完善 SQLite 标签关联实现与查询接口。

## 2026-06-05（第二轮界面收敛）

- 使用 AI Coding Agent 持续细化 Week15 的阅读页、设置页和订阅管理页视觉交互。
- 将阅读页右侧工具按钮、底部笔记按钮、订阅管理操作按钮统一到同一套主题色和按钮语义。
- 重构阅读页中的订阅管理入口：左侧订阅源区域和右上角导航中的“订阅”最终统一为“保留左栏，在中右区域打开订阅管理”的交互，不再保留风格割裂的独立普通页面。
- 继续压缩设置页主题区域，补充黑白灰基础主题，并拉开前几组主题色卡的视觉差异。
- 优化文章详情区：默认先展示摘要，再按需尝试补全文，并保留返回摘要视图的切换逻辑。
- 调整左侧导航区为更稳定的信息栏：移除单独滚动条，订阅源名称超出时使用省略号，悬停可查看完整名称。
- 修复正文区标签按钮点击不稳定的问题，保留标签的轻交互方式，不再将标签管理做成大页面切换。
- 同步更新 `update_docs/Week15_bouboo1.md`，整理本周内容处理、主题系统、订阅管理、导出语义和本地验证结果。
- 当日验证：多次执行 `cd frontend && npm run build`，构建通过。
- 当前限制：标签分配与标签筛选虽然已可在前端使用，但后端的标签关联查询与跨设备一致性仍需后续完善。

## 2026-06-06

- 使用 AI Coding Agent 对阅读页文章详情头部做小幅对齐修正。
- 将标题、来源、作者与发布时间所在的 `reader-hero` 区域从居中块布局改回左对齐，贴近此前阅读页的视觉习惯。
- 本次改动仅调整前端样式，不涉及接口、数据结构或业务逻辑变更。
- 使用 AI Coding Agent 收紧“加载全文”的正文提取与清洗规则。
- 提取阶段新增更具体的正文容器优先级，并对 `sidebar`、`related`、`share` 一类噪音区块做预裁剪，尽量避免把右侧插图或推荐内容带入阅读页。
- 清洗阶段补充对侧栏、分享区和高链接密度推荐块的移除逻辑，目标是保留主图、正文段落和正文内嵌图片。
- 使用 AI Coding Agent 排查 VS Code 中 `Code Helper` CPU 异常升高与插件响应缓慢问题。
- 确认当前工作区总文件数约 `12,589`，其中 `frontend/node_modules` 约 `159 MB`、`12,361` 个文件，且仓库此前缺少工作区级 `.vscode/settings.json`，导致 VS Code 与插件容易对依赖目录和构建产物持续监听、搜索与索引。
- 新增工作区级排除配置，收紧 `files.exclude`、`files.watcherExclude` 与 `search.exclude`，重点排除 `frontend/node_modules`、`frontend/dist`、`backend/dist`、`backend/build`、`release`、`__pycache__` 与 `.pytest_cache`。
- 当前限制：该修复只降低 VS Code 及插件对无关目录的扫描开销，不会影响插件本身的远端响应速度；若后续仍有高 CPU，需要继续结合 VS Code 进程管理器检查是否有特定扩展或 Webview 卡住。
- 使用 AI Coding Agent 为阅读页补充 Markdown 正文渲染兼容。
- 当文章正文不是 HTML 而是 Markdown 文本时，前端现在会自动识别并渲染标题、列表、引用、代码块、链接、强调和 Markdown 图片，而不是直接把原始 Markdown 当普通文本显示。
- 本次仅调整前端阅读页渲染逻辑，不修改后端接口和数据库字段。
- 当日验证：`cd frontend && npm run build` 通过。
- 使用 AI Coding Agent 排查 OpenAI RSS 订阅失败问题，目标地址为 `https://openai.com/news/rss.xml`。
- 实测确认该地址在 2026-06-06 仍返回 `HTTP 200`，且后端当前使用的 `feedparser.parse(...)` 可以正常解析出 `OpenAI News` 和 992 篇文章；本地数据库中也已存在该订阅。
- 本次修复聚焦于订阅管理页的错误提示：当后端返回 `Feed already exists` 时，前端现在会明确提示“这条订阅已经存在，可以直接同步或在列表中查看”，并对 URL 校验失败、Feed 解析失败等情况显示更具体的错误信息，而不是统一显示笼统失败提示。

## 2026-06-06

- 使用 AI Coding Agent 再次排查 `https://openai.com/news/rss.xml` 仍偶发无法订阅的问题。
- 结合本地 `feed_fetch_logs` 记录，确认失败并非单一 URL 校验问题，而是后端抓取链路存在两类真实异常：`Remote end closed connection without response` 与 `'NoneType' object has no attribute 'get'`。
- 已将 `backend/app/services/feed_parser.py` 调整为先显式发起 HTTP 请求拉取 RSS/XML，再交给 `feedparser` 解析；请求头补充浏览器化 `User-Agent` 与 XML `Accept`，并对临时网络错误增加最多 3 次重试。
- 同时新增 `parsed.feed` 为空时的兜底逻辑，避免异常解析结果直接触发 `NoneType` 崩溃。
- 新增 `backend/tests/test_feed_parser.py` 的回归测试，覆盖“临时网络失败后重试成功”和“feed 元数据对象缺失但条目仍可解析”两种场景。
- 当前限制：本地执行环境未安装 `feedparser` 依赖，因此本次仅完成 `python3 -m py_compile` 语法检查，未在本机完成单元测试实际运行。
- 当日验证：再次执行 `cd frontend && npm run build`，构建通过。

## 2026-06-06

- 使用 AI Coding Agent 继续排查“点击刷新 RSS 正文时，是否可以通过原文链接补回完整正文”这一链路，重点验证 OpenAI 新闻订阅。
- 确认当前 `POST /api/articles/{id}/refresh-content` 已具备“同时比较 RSS 条目内容和原文页提取结果，再选更完整正文”的后端流程。
- 新增 `backend/app/services/webpage_extractor.py` 的 SSL 证书校验失败回退逻辑，避免部分站点因本机证书链不完整而直接无法抓取原文页。
- 新增 `backend/tests/test_webpage_extractor.py` 的回归测试，覆盖“证书校验失败后使用不校验证书上下文重试”的场景。
- 将阅读页按钮和提示文案从“刷新 RSS 正文”调整为“从原文链接补正文”，避免用户误以为该功能只会重读 RSS 内容。
- 实测结论：对于普通可抓取网页，该入口可以把原文页正文补回到阅读区；但 `openai.com` 当前返回 Cloudflare `403 challenge`，后端服务端抓取仍拿不到可读正文，因此 OpenAI 文章暂时只能保留 RSS 摘要。
- 当前限制：若要对 OpenAI 这类启用机器人防护的站点稳定补全文，后续需要引入浏览器级抓取方案，例如 Playwright/WebView 渲染后提取正文，而不是仅依赖服务器侧 HTTP 请求。

## 2026-06-06

- 使用 AI Coding Agent 调整阅读页正文体验，保持“首次进入时只显示 RSS 已保存内容，只有点击刷新正文后才尝试读取原文链接”的交互语义。
- 将阅读区按钮提示和刷新结果提示改得更明确，避免误解为页面初次打开时就会自动抓原文。
- 更新 `backend/app/services/content_cleaner.py`：对于正文中无法直接显示的 `iframe`、`embed`、`object`、`video`，不再简单移除，而是替换为“打开视频原链接”的超链接，至少保留可访问入口。
- 新增 `backend/tests/test_content_cleaner.py` 回归测试，覆盖嵌入视频替换为链接的行为。
- 调整 `frontend/src/styles.css` 中的阅读区标题宽度约束，让标题区域不再和正文列完全共用同一窄宽度，减少过早换行。
- 使用 AI Coding Agent 继续增强“刷新 RSS 正文”行为，面向只提供摘要的 RSS/Atom 源补充原文页正文抓取。
- 当前刷新动作不再只依赖重新解析 feed 项内容，而是会同时尝试从文章原文链接提取正文，并在 `RSS 内容` 与 `原文页提取结果` 之间选择更完整的一份保存回数据库。
- 新增 `backend/tests/test_refresh_content.py`，覆盖“原文页正文优先于简短摘要”的选择逻辑，以及根据原文链接构建清洗后正文载荷的行为。
- 当前限制：本地执行 `python3 -m unittest tests.test_refresh_content` 时，当前 Python 环境缺少 `beautifulsoup4` 依赖，因此后端测试未能直接跑通；前端构建验证已通过。

## 2026-06-06

- 使用 AI Coding Agent 收束阅读页交互，放弃“点击后再补抓原文全文”的方案，最终保留“右侧正文只展示 RSS 已保存内容”的实现。
- 阅读页移除了“刷新/补全文”按钮与相关提示，文章详情默认直接渲染数据库中的 RSS 内容，不再从阅读区触发原文抓取。
- 对 RSS 文本里形如 `[Image: https://...]` 的占位内容补充前端转换逻辑，渲染时会尽量转成图片而不是裸文本。
- 左侧订阅源列表改为显示站点 favicon 和该源文章数量；右侧正文头部移除了站点图标，只保留订阅源名称、标题及标题下方的原文链接。
- 阅读页交互改为“点击文章即自动标记为已读，再次点击已读按钮可切回未读”，并保留手动切换能力。
- 当日验证：执行 `npm run build --prefix frontend`，构建通过。

## 2026-06-07

- 使用 AI Coding Agent 优化 OPML 导入、导出、同步反馈和桌面端 RSS 添加体验。
- OPML 导入改为支持一次选择多个 `.opml`/`.xml` 文件，并在导入阶段只创建订阅元数据，不再立即联网同步文章，避免订阅源较多时前端等待后端长时间处理。
- OPML 导出新增订阅源勾选、全选、清空、导出选中和导出全部能力，方便只迁移部分订阅源。
- 同步失败反馈补充订阅源标题、URL、失败原因和处理建议；首页“同步全部”和订阅管理页都会展示逐项同步结果。
- 后端 RSS 抓取补充浏览器化请求头、XML `Accept`、超时控制和临时网络失败重试，并把 HTTP、DNS、SSL、无效 RSS 等问题转成更可读的错误消息。
- 修复 BBC News 同步时同一批 RSS 条目中重复 `link` 触发 `UNIQUE constraint failed: entries.feed_id, entries.link` 的问题，保存前会按 `guid`/`link` 做批内去重。
- 修复 OpenAI RSS 在桌面端重复添加和重新添加时的超时体验：添加前先检查订阅 URL 是否已存在，已存在会直接提示；RSS 同步阶段不再逐篇抓取原文页，只保存 RSS/Atom 自带内容。
- 为手工验证准备了 `manual-opml-test-a.opml`、`manual-opml-test-b.opml`、`manual-opml-test-broken.opml` 和 `manual-opml-test-c-many.opml`，分别覆盖正常导入、重复/无效 URL、破损 XML 和多订阅源导入场景。
- 新增或更新后端回归测试，覆盖多 OPML 文件导入、选中导出、同步不中断、RSS 抓取重试、重复条目去重和已存在订阅先查重。
- 当日验证：执行 `..\.venv\Scripts\python.exe -m unittest tests.test_feed_parser tests.test_opml_sync` 通过，执行 `node_modules\.bin\vue-tsc.cmd --noEmit` 通过；临时数据库完整添加 `https://openai.com/news/rss.xml` 用时约 9.2 秒。
- 当前限制：同步仍是同步请求流程，没有新增持久化后台任务队列；若源站本身拒绝访问或网络环境不可达，仍需要用户查看同步日志并按建议处理。

## 2026-06-08（首次同步恢复）

- 使用 AI Coding Agent 根据反馈恢复“添加订阅后立即首次同步”的体验，同时保留失败原因展示。
- 后端 `POST /api/feeds` 返回 `FeedCreateResult`，区分 `success` 和 `partial`：首次同步失败时订阅源仍保留，响应和同步日志会包含失败原因。
- OPML 导入新增 `partial` 结果和计数，表示“订阅源已添加但首次同步失败”，不会阻断其它订阅继续导入和同步。
- 前端订阅管理页适配新的添加结果，手动添加 partial 会显示 warning 和同步结果表；OPML 结果表也会显示 partial 状态、失败原因和建议。

## 2026-06-08（布局适配修正）

- 使用 AI Coding Agent 根据界面反馈继续收敛阅读页与订阅管理页布局。
- 修复左侧“订阅源”列表在订阅较多时无法继续下滑的问题，将滚动限定到列表区内部。
- 优化订阅管理页顶部按钮组的布局与换行策略，解决小窗口下右侧操作按钮溢出截断的问题。
- 移除“订阅管理”标题下方的冗余说明文案，并将“已选 N 个”状态标签移到订阅列表下方，使批量选择反馈位置更合理。
- 调整主应用容器高度与滚动约束，让小窗口下的左栏、文章列表和正文详情都在各自面板内滚动，避免必须滚动整页到底部才能继续阅读。
- 当日验证：执行 `cd frontend && npm run build`，构建通过。
- 当前限制：本次仅收敛前端布局与滚动行为，没有新增自动化 UI 测试；桌面端与不同窗口尺寸仍建议后续继续人工巡检。

## 2026-06-08（周报回退）

- 使用 AI Coding Agent 按要求撤回 `update_docs/Week14_handingna.md` 中本次关于“添加订阅后首次同步”的周报修改。
- 本次仅调整周报记录范围，不改变后端、前端、测试或数据库清空结果。
