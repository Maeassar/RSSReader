## 2026-06-26

- 使用 AI Coding Agent 协助排查并修正统计页模型用量交互问题。
- 统计页模型下拉中的删除按钮原先依赖展示字符串拆分 `provider / model`，导致某些模型统计记录删除失败；现已改为直接传递结构化 `provider`、`model` 参数给现有 `/api/stats/llm` 删除接口。
- 为避免下拉弹层偶发出现在控件左侧，前端进一步为统计页 `el-select` 显式固定 `placement="bottom-start"`，关闭 fallback placements 和 teleport，使弹层稳定从控件下方展开。
- 同步补充 `backend/tests/test_llm_provider_repository.py` 回归测试，覆盖按 `provider + model` 删除统计记录的场景。
- 当前限制：本地 shell 直接执行 `python -m unittest` 时仍存在 `app` 模块路径未注入的问题，因此这次只完成了代码修正和测试用例补充，未在当前命令环境下完整跑通该测试文件。

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

## 2026-06-11

- 使用 AI Coding Agent 完成 Week16 Summary Agent 模块，接入 `llm_providers` 配置、OpenAI-compatible Chat Completions、vLLM/Ollama/OpenAI-compatible provider 模板和摘要用量统计。
- 继续强化 Summary Agent：摘要请求支持 `brief`、`structured`、`deep` 三种模式，支持中文/英文输出和长度预算；prompt 参考 coding agent workflow，要求先理解约束、提取事实、再自检忠实性，并输出可信度。
- 根据“类似 opencode 的 agent 强化”反馈，补充长文上下文循环：短文单轮摘要，长文自动按 token budget 切块，逐块生成事实笔记；中间笔记超预算时继续 compaction；最后 final merge 得到整篇文章摘要，避免只截断并总结开头。
- 为 Qwen3 兼容增加输出清洗：移除 `<think>...</think>` 与 `最终答案：` 前缀；对 Ollama provider 自动传入 `reasoning_effort: "none"`，避免 Qwen3 通过 OpenAI-compatible API 时把内容放入 reasoning 字段而正文为空。
- 前端阅读页的摘要下拉菜单新增 provider 选择、摘要模式、语言和长度设置；AI 设置页支持本地 vLLM Qwen3-8B、Ollama 和通用 OpenAI-compatible provider 配置。
- 实际安装并运行 Ollama `qwen3:8b`，订阅 `https://hnrss.org/frontpage`、`https://feeds.bbci.co.uk/news/technology/rss.xml` 和 `https://hnrss.org/newest?q=AI` 后，用 BBC Technology 的真实文章执行摘要，成功写入 `ai_results` 并统计为 `348` input tokens / `194` output tokens。
- 使用真实 Ollama `qwen3:8b` 对强制小上下文长文执行多轮摘要验证，触发 `7` 个 chunk 调用和 final merge，累计 `7737` input tokens / `2764` output tokens。
- 排查到 Homebrew formula 版 `ollama 0.30.7` 缺少 `llama-server`，真实推理时报 `llama-server binary not found`；改用 `brew install --cask ollama-app` 后通过 `/Applications/Ollama.app/Contents/Resources/ollama serve` 启动完整运行时。
- 当日验证：后端 `python3 -m unittest discover -s backend/tests` 通过，前端 `./node_modules/.bin/vue-tsc --noEmit --pretty false` 通过，真实 Ollama/Qwen3 API 摘要和 `/api/stats/llm` 用量聚合通过。
- 当前限制：vLLM 模板和 OpenAI-compatible 调用链路已完成，但本次真实本地推理使用的是 Ollama `qwen3:8b`；若需要演示 vLLM 权重加载，还需要在具备足够 GPU/内存的机器上单独启动 vLLM。
- 根据人工验收反馈继续优化摘要交互：provider 不再承担“开始生成”的动作，摘要面板新增明确的 `生成摘要` 按钮；摘要运行时展示贴合阅读页风格的内嵌思考流，步骤按时间顺序逐条向下追加，完成后自动折叠，用户可重新展开查看思考过程；切换文章时清空上一篇摘要，避免结果串页。
- 根据进一步反馈修正“思考流”实现：移除前端 `setInterval` 固定步骤和 prompt 事后解析，改为后端 Summary Agent 在真实执行节点发出 `prepare`、`budget`、`chunk_start`、`chunk_done`、`final_start`、`final_done`、`save_done` 等事件。
- 新增 `POST /api/ai/summary/{article_id}/stream`，使用 `StreamingResponse` 输出 SSE；前端 `streamSummary()` 用 `fetch` POST 请求读取流，阅读页只渲染真实后端事件，并展示当前步骤实际停留时间。
- 对本地 Ollama `qwen3:8b` 执行真实长文流式摘要验证：文章约 `15008` 输入 tokens，正文切成 `4` 个 chunk，最终合成并保存，累计用量 `14145` input tokens / `863` output tokens。
- 为避免最后结果帧过大，流式 `result` 事件不再携带完整 prompt trace；数据库中的 `ai_results.prompt` 仍保留完整多轮 trace，便于开发排查。
- 更新 `update_docs/Week16_GentleCold.md`，记录真实事件流实现、Ollama 测试、前端假进度问题和解决方案。

## 2026-06-26

- 使用 AI Coding Agent 协助推进 Week17 Translation Agent 的稳定性修复。
- 将翻译链路从自然语言格式输出升级为结构化 JSON 队列协议：后端先把可翻译内容整理成 `[{id, text}]`，再要求模型返回 `[{id, translation}]`，最后按 id 顺序回填原文结构。
- 为兼容历史 provider，后端仍保留旧版 `|1|` 行号格式解析作为 fallback，同时为单段翻译增加 JSON 解析、清洗和空译文兜底。
- 新增/更新翻译相关单测，覆盖 JSON 输出、代码块包裹、缺项失败、旧格式兼容和 SSE 翻译流。
- 当日验证：`python -m pytest tests/test_translation_agent.py tests/test_translation_stream.py -q` 通过，`python -m py_compile app/services/translation_agent.py tests/test_translation_agent.py tests/test_translation_stream.py` 通过。
- 当前限制：虽然 JSON 队列协议明显降低了格式解析失败概率，但模型仍可能返回字段缺失；单段翻译已对空译文增加自动重试，后续如果某些 provider 仍不稳定，可以继续引入更强的 schema 校验。

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

## 2026-06-11（Week16 Summary Agent）

- 使用 AI Coding Agent 协助完成朱文韬负责的 Week16 Summary Agent 后端系统。
- 后端新增 Summary Agent、LLM Provider CRUD、OpenAI-compatible Chat Completions 调用、vLLM/Ollama provider 类型和摘要用量统计。
- 前端 AI 设置页由“Provider 预留界面”改为真实配置管理，新增 vLLM Qwen3-8B、Ollama、OpenAI-compatible 快速模板；阅读页摘要按钮支持选择 provider 并展示输入/输出 token；统计页展示按功能和按 provider 的用量明细。
- 实测通过本地 OpenAI-compatible 服务模拟 Qwen3-8B，验证 vLLM 与 Ollama provider 类型均可生成摘要并写入 `ai_results`。
- 实际打开 Electron 应用验证桌面端链路：Electron 主进程启动 FastAPI 后端，前端通过 preload 注入的 `apiBaseUrl` 调用后端；实际订阅 `https://hnrss.org/frontpage` 成功同步 21 篇文章，并对真实订阅文章完成摘要生成与用量统计。
- 新增 `update_docs/Week16_GentleCold.md`，记录功能、接口、测试、ModelScope/vLLM 与 Ollama 使用方式、遇到的问题和解决方案。

## 2026-06-13（Week16 AI 摘要前端展示系统）

- 使用 AI Coding Agent 协助完成徐治平负责的 Week16 AI 摘要前端展示系统。
- 将原有"正文下方平铺摘要"的方式重构为固定在第三栏底部的可折叠摘要抽屉，支持展开/收起、语言选择、生成按钮和失败重试。
- 新增顶部透明拖拽条，抽屉展开后用户可拖拽自由调整高度；拖拽直接操作 DOM CSS 变量绕开 Vue 响应式；修复拖拽仍有延迟的问题：根本原因是 `.summary-drawer-body` 存在 `transition: height 0.35s`，拖拽开始时临时设为 `none`，mouseup 后恢复，彻底消除缓动干扰。
- 摘要生成完成后自动弹升至第三栏高度三分之一处（仅首次生成触发）。
- 点击"生成摘要"时若抽屉高度不足以展示步骤流，自动提升至 280px，确保步骤内容完整可见。
- 生成期间在抽屉内展示后端真实 SSE 事件步骤流，步骤完成后自动清空，只保留渲染后的摘要富文本。
- 标题栏生成状态改为：MagicStick 图标静止，"AI 摘要"文字固定不变，文字右侧条件渲染小转圈图标（`Loading`）；生成中按钮改为 `disabled` 禁用，移除 `el-button` 的 `:loading` 转圈动画。
- 修复摘要 Markdown 渲染中 `renderMarkdownBlock` 标题行后直接 return 导致正文内容丢失的问题，改为递归渲染剩余行。
- 修复后端 `_mode_instruction` 硬编码中文格式模板导致英文摘要标题仍为中文的问题，增加 `language` 参数按语言分支返回对应模板。
- 后端 prompt 中移除"可信度：高/中/低"输出指令，前端同步加正则过滤作为保底。
- 将语言选择从双选 `el-segmented`（仅中/英）改为下拉菜单 `el-select`，新增日语、韩语、法语、德语、西班牙语、葡萄牙语、俄语、阿拉伯语共 10 种语言，默认值通过 `navigator.language` 检测系统语言自动匹配。
- 修复其他语言生成失败的根本原因：后端 `SummaryRequest` Pydantic 模型 `language` 字段声明为 `Literal["zh", "en"]`，导致其他语言代码在进入服务层前被 Pydantic 以 422 直接拒绝；将字段类型放宽为 `str`。
- 后端新增 `_language_display()` 映射函数，将语言代码转为完整语言名称（如 `日本語`、`Français`）写入提示词，使模型按所选语言输出。
- 将标题栏布局从 `flex + space-between` 改为三列 grid（`auto 1fr auto`），红字警告放入独立中间列，始终水平居中于标题栏。
- 对摘要正文富文本做系列视觉美化：调整正文字号为 13.5px、行高 1.8，使阅读更舒适；h2 章节标题加大字号并加粗，与正文形成层级对比；为每个 h2 标题前根据关键词映射添加语义图标（💬 概览、📌 要点、🏷️ 关键词等），支持中日韩英法等多语言标题匹配。
- 关键词章节自动渲染为胶囊标签：`renderedAiResult` 计算属性用正则识别关键词 h2 节段，将下方 `<p>` 内容按分隔符切分为独立 `<span class="summary-tag">` 标签，胶囊样式使用 `color-mix()` 基于 `--theme-accent` 实现主题自适应配色（浅色填充 + 描边 + 主题色文字）。
- 生成摘要按钮升级为自定义样式：带 border、inset 阴影、主题色背景，圆角 10px，高度 36px；按钮前置 sparkle 闪光 SVG 图标，生成中切换为旋转圆弧 SVG（`spin` 动画），文字同步切换为"生成中…"。
- 将复制按钮从标题栏移入摘要结果卡底部，设计为浅描边风格（`summary-copy-btn`）；点击后使用 `navigator.clipboard.writeText` 写入剪贴板，同时切换为绿色勾选图标和"已复制"文字，2 秒后自动复原。
- "AI 摘要"标题改为加粗，后方同行追加浅色说明文字"由 AI 为你总结本篇文章核心内容"（11px，`--el-text-color-secondary`），在标题栏同一行展示，不另起一行。
- 控制栏（语言选择 + 生成按钮）改用 `position: sticky; top: 0` 使其在抽屉体内滚动时始终可见。
- 当日验证：前端 `vue-tsc --noEmit` 通过，手动验证多语言摘要生成、拖拽无延迟、步骤流高度自动调整、警告居中显示均符合预期。
- 当前限制：抽屉高度未持久化，刷新后重置为默认值；拖拽仅支持鼠标，未适配触摸屏；语言修复需重启后端生效。

## 2026-06-14（Week16 用量统计可视化）

- 使用 AI Coding Agent 协助完成徐治平负责的 Week16 用量统计可视化模块。
- 将原有纯文字的 LLM 用量统计面板重构为带时序柱状图的可视化面板，引入 `chart.js` 和 `vue-chartjs`。
- 面板新增右上角折叠/展开箭头，时间跨度选择（今天 / 本周 / 本月 / 全部），右上角请求次数 / TOKEN 切换按钮，刷新按钮。
- 摘要卡片压缩为紧凑行内样式，三列横排（总请求 / 输入 Token / 输出 Token），文字居中。
- 柱状图优化：圆角加大、柱子变细（`barPercentage: 0.5`）、hover 加深、y 轴虚线网格、x 轴今天跨度最多显示 8 个刻度、TOKEN 模式 legend 右对齐。
- tooltip 在请求次数为 0 时不显示；请求次数模式下 tooltip `afterBody` 附加"请求异常: N (X%)"，仅在 `failed_calls > 0` 时出现。
- 后端 `ai_results` 表新增 `status TEXT DEFAULT 'success'` 列，通过 migration 自动补列；`create_ai_result` 新增 `status` 参数。
- `ai_service.py` 在 `SummaryAgentError` 时写入 `status='failed'` 记录再 re-raise，不影响原有错误流程。
- 后端新增 `GET /api/stats/llm/timeseries` 接口，支持 `range` 参数（today/week/month/all），按小时或天分桶返回时序数据，同时统计 `failed_calls`；`GET /api/stats/llm` 同步支持 `range` 过滤。
- 修复时区问题：数据库 `CURRENT_TIMESTAMP` 存本地时间，cutoff 和分桶统一改用 `datetime.now()`（无时区），SQL 分桶表达式通过 Python 计算偏移量后以 `datetime(created_at, '+N seconds')` 转换，x 轴显示本地小时。
- 本月跨度改为从当月 1 日到今天，不再跨月倒推 30 天。
- 摘要生成按钮移除 `MagicStick` 图标，只保留文字。
- 摘要步骤流 active 圆点动画改为从中心向四周扩散的波纹（`::before` 伪元素，scale 1→2.8，opacity 0.5→0，`cubic-bezier(0.4,0,0.6,1)`）；done 状态颜色变浅（accent 混合比例 70%→35%）。
- 当日验证：前端 `vue-tsc --noEmit` 通过，手动验证时序图正确显示本地时间、折叠/展开、时间跨度切换、请求异常 tooltip 均符合预期。
- 当前限制：时区处理依赖后端系统本地时区，若后端部署在与用户不同时区的服务器上需额外处理；请求异常统计仅覆盖摘要功能（translate/tag_suggestion 暂未接入失败记录）。
- 修复摘要抽屉拖到顶时底部内容无法查看的问题：根本原因是抽屉高度无上限导致文章区被压缩至 0，同时抽屉底部被第三栏 `overflow: hidden` 截断。在拖拽、生成时自动展开、结果弹升三处高度计算中，统一为面板高度减去标题栏高度再减去 120px，为文章区始终保留至少 120px 可见空间。

## 2026-06-14（Week16 阅读页笔记弹窗入口）

- 使用 AI Coding Agent 阅读项目结构、定位阅读页工具栏、正文底部笔记区域、前端笔记 API 和后端 notes 数据流，并制定实现计划。
- 将阅读页笔记入口从文章正文底部迁移到顶部工具栏导出按钮左侧，新增 `EditPen` 图标按钮，通过 `el-popover` 打开笔记小窗口。
- 弹窗复用现有 `note` 状态和笔记 API，保留 Markdown 编辑、立即保存和导出笔记能力。
- 删除正文末尾旧笔记编辑区，避免同一篇文章出现两个笔记入口。
- 笔记保存参考 Mercury 的自动 flush 行为：输入后 debounce 自动保存，关闭弹窗、切换文章、导出笔记或导出文摘前会立即保存当前草稿；保存状态在弹窗头部显示。
- 当前文章笔记非空时，顶部笔记按钮右上角显示蓝色圆点。
- 本次未修改后端接口、数据库表结构或导出服务，继续使用 `GET/PUT /api/articles/{id}/note` 和 `notes` 表。
- 新增 `update_docs/Week16_specia1week.md` 记录本次任务范围、实现内容、验证结果和限制。
- 当日验证：执行 `cd frontend && npm run build`，构建通过；Vite/Rollup 仅输出第三方依赖注释和 chunk size 警告。
- 当前限制：本次未新增自动化 UI 测试；笔记自动保存失败时会显示失败状态，但暂不做离线重试队列。

## 2026-06-14（Week16 批量文摘导出 UI 恢复）

- 使用 AI Coding Agent 复查 `update_docs/Week14_batch_export_plan.md`、当前导出 API、Electron 保存 IPC 和阅读页列表菜单，确认后端 `POST /api/export/digests/markdown`、前端 `rssApi.exportBatchDigestMarkdown()` 与桌面端 `saveMarkdown` 能力仍存在。
- 恢复阅读页“批量文摘”入口：从文章列表右上角菜单进入批量选择模式，不再只显示占位提示。
- 在当前列表文章卡片左侧新增选择圆点，点击卡片即可勾选/取消；导出顺序按当前列表顺序计算，不按勾选顺序。
- 新增批量工具条，展示已选数量，并提供全选、清空、预览导出和退出。
- 新增批量文摘预览弹窗，支持切换“包含 AI 摘要”和“包含笔记”，展示可导出数量、摘要数量、跳过数量和后端生成的 Markdown 预览。
- 根据追加需求，批量文摘预览弹窗新增“包含全文”选项，与“包含 AI 摘要”“包含笔记”并列；后端请求体新增 `include_full_text`，导出时优先写入文章清洗后的 Markdown 正文，缺失时回退到文章摘要。
- 新增复制预览 Markdown 和导出 Markdown 操作；Web 端触发浏览器下载，Electron 端复用原生保存对话框。
- 更新 `update_docs/Week14_batch_export_plan.md`，记录 Week16 UI 改版后的恢复内容；同步扩展 `update_docs/Week16_specia1week.md`。
- 当日验证：执行 `cd backend && python -m py_compile app/schemas/rss.py app/services/export_service.py app/routers/export.py` 通过；执行 `cd frontend && npm run build`，构建通过；Vite/Rollup 仍仅输出第三方依赖注释和 chunk size 警告。
- 当前限制：本次未新增自动化 UI 测试；仍不支持自定义 digest 模板、固定导出目录设置，也不会在导出流程中自动生成缺失摘要。

## 2026-06-15（OPML 导入逐条显示）

- 使用 AI Coding Agent 协助优化批量上传 Feed 的前端反馈流程。
- 后端新增 `POST /api/opml/import/stream` SSE 接口，复用 OPML 导入逻辑，在每个 Feed 处理完成后立即推送单条导入结果和当前汇总。
- 前端订阅管理页改为监听流式导入事件，收到 `imported` 或 `partial` 结果时立即把对应 Feed 合并到订阅列表，同时逐条更新 OPML 导入结果表。
- 保留原有 `POST /api/opml/import` 汇总接口，降低对旧调用方的影响。
- 当前限制：本次未新增端到端 UI 自动化测试；最终仍会在导入结束后重新加载一次 Feed 列表，用于和后端状态对齐。

## 2026-06-15（订阅批量删除）

- 使用 AI Coding Agent 协助补充订阅管理页的批量删除功能。
- 后端新增 `POST /api/feeds/batch-delete` 接口，接收 `feed_ids` 列表并返回逐条删除结果汇总；单个 Feed 删除失败或重复 ID 不会中断整批操作。
- 前端订阅管理页在现有多选、全选、清空能力基础上新增“删除选中”按钮，并通过确认弹窗降低误删风险。
- 删除完成后前端会刷新订阅列表、清空当前选择，并按成功、失败、跳过数量给出反馈。
- 当前限制：本次未新增端到端 UI 自动化测试；批量删除仍复用现有单个 Feed 删除逻辑和数据库级联清理能力。

## 2026-06-15（OPML 导入排队状态）

- 使用 AI Coding Agent 继续修复 OPML 批量导入体验。
- 后端流式导入接口改为先解析上传文件并推送 `parsed` 事件，前端收到后立即显示所有待导入订阅为 `pending` 状态。
- 前端新增本地 OPML 预解析：用户选中文件后先用浏览器解析 OPML 并立即把所有 Feed 显示为“待同步”，后端流式事件随后逐行覆盖最终状态。
- 后端随后逐个导入和同步 Feed，每完成一个就推送该行最终状态；前端按文件名和 URL 替换对应行，并在成功或部分成功时立即通知阅读页刷新订阅列表。
- 前端新增共享 OPML 导入进度 store，导入过程中切换页面再回到订阅管理页时仍保留当前结果表和状态。
- 阅读页 store 新增 Feed 即时 upsert/remove 能力，OPML 导入成功、手动添加、同步和删除订阅后，阅读界面订阅源列表会立即更新。
- OPML 解析器补充兼容 `feedUrl`、`rssUrl`、`atomUrl`、`url`、`href` 以及文本本身是 URL 的常见导出格式，避免出现文件有效但结果表为空。
- 当前限制：本次未新增端到端 UI 自动化测试；如果 OPML 文件本身不包含可识别 Feed URL，会以失败行提示而不是静默显示 0 条。

## 2026-06-15（OPML 导入文章即时可读）

- 使用 AI Coding Agent 继续修复 OPML 导入后的阅读状态刷新问题。
- 阅读页 store 新增按 Feed 合并文章与刷新单个 Feed 文章的能力，避免导入成功后侧边栏只显示订阅源、文章计数仍为 0。
- OPML 流式导入每收到一个成功或部分成功的 Feed 后，前端会立即把该 Feed 插入订阅列表，并异步拉取该 Feed 的文章合并到阅读页文章池。
- 手动添加订阅和单个订阅同步也接入同样的文章刷新路径，减少需要重启或整页重载才能看到文章的情况。
- 修复 OPML 逐条导入期间的全量刷新竞态：单条完成时不再触发父组件 `loadAll()` 覆盖文章池，`loadAll()` 返回时如果检测到期间已有文章合并，会改为合并而不是替换。
- OPML 上传初始状态文案改为“上传中”，原因改为“正在上传”，后端 `parsed` 事件和前端本地预解析保持一致。
- OPML 导入流结束后会主动执行一次阅读 store 全量加载，用后端最终文章状态对齐侧边栏计数和文章列表，避免早完成 Feed 仍显示 0 并需要重启。
- 为满足“每完成一个同步就更新在前端”的严格要求，OPML 单条 SSE 结果现在会携带该 Feed 同步后读取到的文章列表；前端收到单条 `item` 事件后直接把文章合并进阅读 store，不再依赖额外 `/articles?feed_id=...` 请求的异步时序。
- 当前限制：本次仍未新增端到端 UI 自动化测试；文章即时刷新依赖后端同步完成后 `/api/articles?feed_id=...` 能返回该 Feed 的文章。

## 2026-06-15（同步日志时间范围过滤）

- 使用 AI Coding Agent 为统计日志页的同步日志补充时间范围过滤。
- 后端 `GET /api/logs/sync` 新增 `range` 查询参数，支持与 LLM 流量统计一致的 `today`、`week`、`month`、`all` 范围。
- SQLite repository 的同步日志查询复用现有统计 cutoff 逻辑，按 `feed_fetch_logs.fetched_at` 过滤后再倒序返回。
- 前端统计页的同步日志加载会跟随当前范围切换，并在同步日志面板内提供同样的“今天 / 本周 / 本月 / 全部”切换入口。
- 新增 repository 测试覆盖同步日志 `today` 与 `all` 过滤结果；当前限制是同步日志仍为列表视图，暂未增加按天分组或图表。
- 后续根据反馈将流量统计范围与同步日志范围拆分为两个独立状态，二者不再联动；同步日志列表改为面板内固定高度滚动，避免日志过多时无限拉长页面。

## 2026-06-15（OPML 导入文章刷新竞态修复）

- 使用 AI Coding Agent 继续定位 OPML 逐条导入时只有最后完成的 Feed 能即时显示文章的问题。
- 根因是每条导入成功后虽然会刷新单个 Feed 的文章，但同时触发父级阅读页全量 `loadAll()`，导致刚合并进阅读状态的文章被默认文章列表覆盖，异步时序下最后完成的 Feed 最容易保留下来。
- 订阅管理页现在会收集每个成功导入 Feed 的文章刷新任务，并在导入流结束前等待这些刷新完成；同时通过 `changed` 事件告诉父级不再进行全量 reload。
- 阅读页 `handleFeedManagerChanged` 支持轻量刷新模式，避免 OPML 导入期间反复覆盖文章池。
- OPML 初始 pending 行的状态文案改为“上传中”，原因改为“正在上传”，并在本地预解析和后端 `parsed` 事件两条路径中保持一致。

## 2026-06-15 (Ripple branding and installer icon)

- Used AI Coding Agent to update the desktop and frontend branding from RSSReader to Ripple.
- Generated `build/icon.ico`, `build/icon.png`, and `frontend/public/ripple-logo.png` from `docs/brand/ripple-logo-concept.png`.
- Updated Electron Builder metadata so packaged desktop builds use `productName: Ripple` and the NSIS installer/uninstaller use `build/icon.ico`.
- Updated the Electron window title/name/icon and frontend title, favicon, header logo, and i18n app name to Ripple.
- Verification: frontend type check passed; frontend build passed with existing Vite/Rollup warnings; a lightweight Electron Builder directory package produced `Ripple.exe` and was cleaned afterward.

## 2026-06-15 (Reader layout polish)

- Used AI Coding Agent to refine the reader page layout and reduce detail-toolbar density.
- Moved read, pin, and favorite quick actions from the article detail toolbar into each article card.
- Changed unread/read distinction in the article list to title color and weight instead of relying on a separate unread tag.
- Added persistent sidebar and article-list visibility toggles so the three reader columns can be collapsed and restored.
- Constrained the article detail content to a centered fixed reading width while keeping the full-height reading panel.
- Replaced the floating layout buttons with draggable column splitters between subscription/list/detail panels; each splitter can click to collapse or drag to resize.
- Refined the article list splitter so the second column can shrink independently into compact and micro layouts without leaving unused blank space.
- Restyled the article detail toolbar as a smaller right-aligned icon group within the reading width to reduce visual weight.
- Verification: frontend type check passed.

## 2026-06-15 (Reader large-library performance)

- Used AI Coding Agent to redesign the reader data flow for large feed collections.
- Changed `GET /api/articles` from a full article array to a paginated lightweight response with `items`, `total`, `limit`, `offset`, and `has_more`.
- Added `GET /api/articles/counts` for total, unread, starred, feed, and tag counts so the sidebar no longer recalculates counts by scanning loaded articles.
- Added persistent SQLite `tags` and `article_tags` tables so tag filtering and tag counts can be handled by the backend instead of local-only overrides.
- Updated the reader store to load the first page only, load additional pages on scroll, cache selected article details, and fetch full article bodies only when selected.
- Removed the reader list's full-body thumbnail scan; article cards now use lightweight list data.
- Fixed SQLite connection cleanup so test databases are not left locked on Windows.
- Verification: backend unittest discovery passed; frontend build passed with existing Rollup annotation and chunk-size warnings.

## 2026-06-15 (OPML import article count refresh)

- Used AI Coding Agent to fix a follow-on regression from the reader pagination/counts refactor.
- OPML stream item handling now refreshes backend article counts when imported article payloads are merged directly into the reader store.
- Feed management no longer calls `readerStore.loadAll()` with the default all-articles query after OPML import or sync-all; it refreshes counts and lets the embedded reader reload its current filtered list.
- ReaderView now refreshes counts even for lightweight feed-manager change events marked `reload: false`, so sidebar article totals stay correct after add, sync, and delete flows.
- Verification: frontend build passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-15 (OPML import counts and switching stability)

- Used AI Coding Agent to continue fixing OPML import regressions after the reader pagination/counts refactor.
- Normalized OPML import result matching by URL so backend-normalized feed URLs can replace local pending rows instead of leaving rows stuck at "uploading".
- Added immediate per-feed article count updates in the reader store, then kept backend aggregate counts as the final source of truth.
- Changed feed-management article refreshes to update counts without merging newly imported feed articles into whichever filtered article list is currently open.
- Added a reader list request guard so rapid feed/tag/filter switching ignores stale responses from earlier loads.
- Removed the reader grid-wide loading overlay and replaced it with an article-list-local loading indicator to avoid the white-screen effect during switching.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-15 (OPML import progressive feed visibility)

- Used AI Coding Agent to fix the remaining OPML import race where earlier imported feed counts could drop back to zero while later feeds were still syncing.
- Reader counts now keep protected per-feed values from streamed OPML item results until backend aggregate counts catch up, preventing stale `/api/articles/counts` responses from overwriting known article totals with zero.
- Each completed OPML feed now notifies the embedded reader to reload the current filtered article page, so selecting a feed during import can recover as soon as that feed finishes syncing.
- Feed management now merges the final backend feed list with feeds already inserted from streamed events, so the table below the OPML result does not stay empty or lose imported feeds until manual refresh.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-15 (OPML import stale counts and feed table source)

- Used AI Coding Agent to correct the unresolved OPML import race where older article-count requests could still overwrite newer imported feed counts.
- Added a count-request sequence guard in the reader store so only the latest `/api/articles/counts` response can update aggregate/sidebar counts.
- Changed the subscription management table to read from the shared reader feed store instead of a separate local `feeds` ref, removing the split-brain state where the sidebar had feeds but the management table showed `No Data`.
- Feed management now writes `GET /api/feeds` results through `readerStore.setFeeds()`, using merge mode during OPML import and initial mount so stream-inserted feeds are not lost to an empty or stale fetch.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-15 (OPML imported feed immediate reading)

- Used AI Coding Agent to fix the specific OPML import interaction where clicking an already imported feed during the remaining import stream could reset counts and leave the article list stuck loading.
- Reader store now caches articles carried by each successful OPML stream item by `feed_id`, including full article detail data for immediate reading.
- Clicking a feed with cached OPML articles now renders from the local cache first instead of waiting for `/api/articles?feed_id=...` while the backend is still busy syncing later feeds.
- Cached feed loading advances the reader load request sequence, so any older blocked network response cannot overwrite the cached readable list when it eventually returns.
- OPML item handling no longer calls `/api/articles/counts` after every successful feed; it updates protected per-feed counts from the streamed article payload and leaves aggregate reconciliation to later refreshes.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-15 (OPML import cached actions and note silence)

- Used AI Coding Agent to fix OPML import interactions around read/star actions and note auto-save noise.
- Cached OPML articles now support local read and star toggles while the backend import stream is still busy, avoiding repeated connection-failure messages.
- Reader aggregate unread/starred counts are adjusted locally for cached article actions so the unread and favorite filters no longer stay at zero during import.
- Cached article selection marks articles read locally instead of issuing a blocking backend read-state request.
- Note loading now fails quietly during transient backend unavailability, and unchanged notes are no longer saved during article switches or feed deletion.
- Deleting a feed now removes its detail cache entries, so a failed save for a removed article does not show the "save previous note failed" message.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-16 (Tag actions during OPML import)

- Used AI Coding Agent to fix tag creation, article tagging, and tag deletion while OPML import is still processing.
- Added a frontend tag-delete API wrapper and routed tag creation/deletion through the reader store.
- Cached OPML articles can now receive tag changes locally without waiting for backend article-tag writes, so imported articles remain usable during long uploads.
- Locally created tags receive temporary negative ids when the backend is busy, and tag counts update from the known cached/list/detail articles.
- The reader sidebar and article tag popover now include delete controls; deleting a tag removes it from visible article lists, cached OPML articles, detail cache, selected article state, and tag counts.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-16 (Reader tag popover layout and search)

- Used AI Coding Agent to improve the reader article tag popover after the tag action fixes.
- Changed the tag picker from one-tag-per-row cards to compact tag chips that wrap onto additional rows when space runs out.
- Added a tag search input in the article tag popover so users can quickly filter existing tags before assigning them.
- Pressing Enter in the tag search box now assigns an exact matching tag or creates and assigns a new tag using the current tag color.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-16 (AI tag candidate generation)

- Used AI Coding Agent to upgrade tag suggestions from a mock text response to real LLM-backed candidates.
- Added a backend tag agent that reuses the default Summary LLM Provider settings, sends article context plus existing tags, parses structured JSON, and saves an `ai_results` audit row.
- Changed `/api/ai/tag-suggest/{article_id}` to return `article_id`, structured candidates, and the saved AI result instead of a plain `AIResult` body.
- Added an AI generation panel to the article tag popover where users can generate candidates, deselect unwanted tags, and apply only confirmed labels.
- Manual tag creation, tag search, tag toggles, sidebar filtering, and tag deletion remain available.
- Remaining limitation: candidate quality depends on the configured LLM Provider and the available article content.

## 2026-06-16 (Tag sidebar scrolling and Chinese AI tag UI)

- Used AI Coding Agent to fix the reader sidebar tag section when large tag sets overflow the left column.
- Wrapped the sidebar tag list in its own scrollbar with a bounded height so tags can scroll without hiding the feed list below.
- Localized the AI tag candidate panel text, badges, success message, and error fallbacks from English to Chinese.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-16 (External browser link handling)

- Used AI Coding Agent to make reader links open through the system default browser in the desktop app.
- Added an Electron `openExternal` IPC bridge and main-window navigation/window-open guards so article links no longer create in-app popup windows.
- Routed article source links, article-body links, and AI summary result links through the same external-link handler, with a browser fallback for frontend development.
- Verification: `npm.cmd run build --prefix frontend` passed with the existing Rollup annotation and chunk-size warnings.

## 2026-06-22（Week16 摘要持久化与原文拉取）

- 使用 AI Coding Agent 协助完成徐治平负责的 Week16 摘要持久化与原文拉取功能。
- 切换文章后再返回，摘要不再被清除：新增 `summaryCache` 内存 Map，离开文章时保存当前摘要，切回时优先从内存恢复，内存无缓存则调用 `POST /ai/summary/{id}` 传 `refresh: false` 查询后端已有记录；`client.ts` 新增 `getCachedSummary()` 方法。
- 正文不足 280 字符时，点击"生成摘要"会先尝试调用 `POST /articles/{id}/refresh-content` 从原文链接拉取完整正文，拉取成功后更新 store 内容再生成摘要；拉取失败时在步骤流显示原因并继续生成。
- 实测确认 TechCrunch 等 Cloudflare 防护站点的原文拉取会返回 `Unable to load full article content from the source page`，此类站点暂时只能基于 RSS 已有内容生成摘要，后续需要浏览器级渲染方案才能绕过。
- 当前限制：摘要内存缓存在页面刷新后清空；原文拉取对启用机器人防护的站点无效。

- Used AI Coding Agent to rebase the RAG/AI configuration work onto the latest `upstream/develop`; conflicts came from newly merged AI Provider, streaming summary, and AI tag changes rather than a `main` branch base.
- Changed RAG Chat to reuse the enabled default LLM Provider from `/api/ai/providers`, so article summary, AI tag suggestion, and RAG Chat share one Provider configuration.
- Kept RAG Embedding settings independent, and removed the separate RAG Chat API Key/Base URL/model fields from the AI settings page.
- Added local API Key encryption for `llm_providers.api_key` and `rag_siliconflow_api_key`; frontend copy now states that keys are encrypted and leaves existing keys unchanged when edit fields are empty.
- Updated `update_docs/Week17_GentleCold.md` with the implementation notes, conflict reason, validation plan, and API Key handling details.
## 2026-06-14（Week17 AI Translation 开发准备）

- 使用 AI Coding Agent 根据张宥后续 Week17 开发需求，切换到 `develop` 分支并梳理当前项目进度。
- 确认 `develop` 是当前实际开发集成分支，已有完整 Vue 3 + Vite 前端、FastAPI 后端、SQLite 数据库、Electron 桌面端、AI Summary、RAG、导出、统计等模块。
- 重点阅读 Week16 Summary Agent、LLM Provider、AI 设置页、阅读页摘要抽屉、i18n 占位入口和 AI 用量统计实现，确认 Week17 Translation Agent 可以复用现有 provider 表、OpenAI-compatible 调用链路、`ai_results` 结果表和统计接口。
- 发现当前 `POST /api/ai/translate/{article_id}`、`ai_service.translate()`、`rssApi.translate()` 已存在，但后端仍是 mock translation，后续需要替换为真实 provider-backed Translation Agent。
- 将张宥 Week17 开发注意事项补充到 `AGENTS.md`，包括分支基线、翻译结果保存、统计接入、测试和文档更新要求。
- 当前限制：本次只做项目阅读、分支确认和协作记忆更新，尚未实现真实翻译接口或 i18n 页面改造。

## 2026-06-17（Week17 Translation Agent 本地实现）

- 使用 AI Coding Agent 按张宥 Week17 任务在本地实现 Translation Agent，不提交 GitHub。
- 新增 `backend/app/services/translation_agent.py`，复用 Week16 的 LLM Provider 体系和 OpenAI-compatible Chat Completions 调用链路，支持 OpenAI-compatible、vLLM、Ollama。
- 翻译输入优先使用 `cleaned_markdown`，回退到清洗 HTML 或 RSS summary；默认保留 Markdown 结构，长文按 token 预算分段翻译并累计用量。
- 将后端 `POST /api/ai/translate/{article_id}` 从 mock translation 替换为真实 provider-backed Translation Agent，支持 `provider_id`、`refresh`、`target_language`、`source_language`、`preserve_markdown` 请求参数。
- 翻译成功写入 `ai_results(task_type='translation')`，记录 provider、model、input/output tokens；翻译失败写入 `status='failed'` 记录后返回可读错误，因此统计页可自然聚合 translation 用量和失败次数。
- 前端阅读页顶部翻译按钮接入真实接口，复用底部 AI 抽屉展示译文、token 用量和复制译文按钮；目标语言复用摘要抽屉中的语言下拉框。
- 更新 `docs/API_DESIGN.md` 和 `update_docs/Week17_sdfhjisd.md`，记录翻译接口请求/响应、数据表、测试命令和当前限制。
- 当前限制：翻译暂未实现 SSE 事件流；完整 UI i18n 文本替换尚未展开，本次优先完成文章内容翻译 Agent。

## 2026-06-22（Week17 Translation Agent 增强）

- 使用 AI Coding Agent 完成 Week17 Translation Agent 的第二轮增强，实现逐句对齐翻译、SSE 事件流、译文对照视图和 UI i18n。
- 重构 `translation_agent.py`：新增 `parse_blocks`（识别 heading/list/blockquote/code_block 等，剥离前缀保留缩进符号）、`split_sentences`（句末标点切分，缩写/小数不切）、`_build_aligned_prompt`（`|行号|` 锚点逐句对齐）、`_parse_aligned_response`（行数校验）、`_reassemble_translation`（prefix 回填）和 `_translate_aligned`（主流程），替换原有的段落级翻译为 Block-Sentence-Aligned 翻译引擎。
- 新增 `POST /api/ai/translate/{article_id}/stream` SSE 端点，照搬 `summarize_stream` 的 queue+thread 架构，事件序列 align_check（对齐校验）和 parse（结构解析）为翻译专属。
- 后端 `ai_service.py` 透传 `on_event`，返回 `aligned_blocks` 结构化数据供前端对照视图。
- 前端阅读页正文区新增「原文/译文/对照」三态切换：译文视图将 AI 译文渲染到正文区，对照视图左右分栏展示逐块比对。
- 引入 `vue-i18n` 正式接入：新增 `locales/{zh,en}.ts` 覆盖阅读页 AI 文案，界面语言与 AI 输出语言解耦，通过 `localStorage` 持久化。
- 新增 `TranslationRequest.target_language` 正则校验（白名单 10 种语言），缓存按目标语言过滤。
- 共 32 个单元测试（27 个旧测试扩展 + 5 个 SSE 事件流测试），前端 `vue-tsc --noEmit && vite build` 通过。
- 当前限制：`aligned_blocks` 未持久化到数据库（刷新后需重新翻译）；SSE 翻译未实现 cancel；全站 i18n 未完成；`summaryEventTitle` 仍为硬编码中文（作为 fallback）。

## 2026-06-22（Week17 代码审查与缺陷修复）

- 对 deepseek 实现的 Translation Agent 代码做深度审查，发现并修复 7 类真实缺陷，新增 7 个回归测试，后端测试总数 39 个全部通过，前端 `vue-tsc + vite build` 通过。
- **Fix 1（崩溃 bug）**：`_translate_aligned` 在文章只含 code_block/HR/空白时，`aligned_chunks` 为空却直接访问 `aligned_chunks[0]`，抛 `IndexError` 被包装成「LLM Provider 调用失败」，用户无法理解。改为检测空 chunks 时原样返回原文并发 `single_done` 事件，usage 置 0。
- **Fix 2（空译文）**：`_parse_aligned_response` 原 70% 阈值会返回含空字符串的列表，导致重组译文出现空行。改为只接受所有行都非空的对齐结果，否则返回 None 触发回退。
- **Fix 3（作用域风险）**：多 chunk 分支里 `fallback_completion` 仅在 `is_aligned=False` 分支定义，但 `chunk_done` 事件无条件引用它；若 `_complete_chat` 抛异常会 NameError。重构为 `chunk_usage` 变量统一承载用量。
- **Fix 4（句子切分边界）**：原逻辑对句末 `.` 在文本末尾（无空格）时不触发边界，导致整句漏切；且小数点 `3.14` 末尾句号会被误判。新增 `_is_decimal_period` 数字两侧判定，重写 `_split_sentences_text` 边界规则。
- **Fix 5（缓存语言提取）**：`_extract_target_language` 提取的是显示名（如 "English"），与请求的代码 `en` 比较 `English == en` 永不相等，**语言过滤从未生效**。新增 `_LANGUAGE_DISPLAY_TO_CODE` 反向映射转回代码；同时排除 `status=failed` 的缓存记录（失败记录 `result` 存错误消息，否则会被当译文返回）。
- **Fix 6（死代码）**：移除未使用的 `import json`、`field`、`_SENTENCE_BOUNDARY` 正则、`min_sentences_for_aligned` 字段、`_build_aligned_blocks_data` 函数末尾空循环、`_emit` 内重复 `import time`。
- **Fix 7（前端）**：`renderComparisonHtml` 的 `i` 参数未使用已移除；`runSummary` 未重置 `readerViewMode`/`alignedBlocks`，导致翻译后切摘要时正文区仍显示翻译对照视图，已修复；对照视图 CSS 新增 `@media (max-width: 720px)` 窄屏上下堆叠，`overflow-wrap: break-word` 防溢出。
- 当前剩余限制与优化方案见 `update_docs/Week17_sdfhjisd.md` 审查记录小节。

## 2026-06-22（Week17 限制 1/2 优化实现）

- 针对审查报告中的两项高价值限制做实现优化，后端测试增至 46 个全部通过，前端构建通过。
- **限制 1（aligned_blocks 持久化）**：采用方案 A，在 `ai_results.prompt` 字段前缀嵌入 `aligned_blocks` JSON（`---aligned_blocks---\n{json}\n---aligned_blocks-end---\n<trace>`）。新增 `_encode_prompt_with_aligned`/`extract_aligned_blocks_from_prompt`/`_strip_aligned_blocks_marker`；`ai_service.translate()` 保存时编码、缓存命中时解析还原并附到响应，对照视图刷新后仍可用。不改表结构，兼容 stats 聚合。4 个回归用例覆盖 roundtrip/None/空/损坏 JSON。
- **限制 2（SSE cancel）**：新增 `CancelEvent`（`threading.Event` 封装）与 `TranslationCancelled` 异常；`translate_with_provider` 在每次 LLM 调用前 `_check_cancel`；路由 `translate_stream` 注入 `Request`，`event_stream` 每次 yield 前用 `request.is_disconnected()` 检测断开并 `cancel_event.set()`，worker 捕获 `TranslationCancelled` 发 `cancelled` 事件（非 error）。前端 `streamSse` 接受 `AbortSignal`，`runTranslate` 创建 `AbortController`，切文章/重译时 abort，`handleSummaryStreamEvent` 新增 `cancelled` 分支，catch 区分 `AbortError`（静默）与真实错误。3 个回归用例覆盖预设取消/chunk 间取消/无 cancel 正常工作。


## 2026-06-24（Week17 PR Review 修复）

- 使用 AI Coding Agent 协助处理 PR review：确认 Issue #44 内容为“清空 feed 后 token/日志统计清空，重加后 token 统计无法恢复”。
- 新增翻译专用 Provider 标记 `llm_providers.is_translation_default`，AI 设置页新增「翻译模型」选择栏和表格操作，后端翻译默认读取翻译专用模型而不是摘要/标签/RAG 的通用默认 Provider。
- 阅读页段落翻译移除通用摘要 Provider ID 透传，统一由后端选择翻译 Provider，降低 reviewer 环境配置不一致导致的翻译不可用风险。
- 新增 `ai_usage_logs` 独立用量流水并迁移回填历史 `ai_results`，统计接口改读流水表，避免文章随 feed 删除后 token 统计被级联清空。
- 剩余限制：历史上已经被删除文章对应的 `ai_results` 无法自动恢复；本次只能保证升级迁移之后的新用量统计不会随 feed 删除丢失。


## 2026-06-24（翻译不可用问题复审与修复）

- 使用 AI Coding Agent 复审同学反馈的“翻译功能不可用”问题，定位到翻译专用 Provider 缺失、旧库未设置翻译默认、前端全文翻译块与实际渲染块不一致、HTML-only 正文只翻译 summary 等高概率原因。
- 后端翻译 Provider 选择改为优先翻译默认、缺失时回退通用默认 Provider，便于将已有测试用 Qwen/Ollama 配置直接作为翻译兜底。
- 前端「翻译全文」改用实际渲染块，并为 HTML-only 正文增加纯文本提取，减少点翻译无效果或正文有内容但不可翻译的情况。
- 后端新增 Provider fallback 回归测试；后端 51 个相关测试与前端构建均通过。


## 2026-06-24（SOCKS 代理依赖修复）

- 根据实际测试报错 `Using SOCKS proxy, but the 'socksio' package is not installed`，确认问题来自系统 SOCKS 代理环境与 `httpx` extras 缺失。
- 选择安装并记录 `socksio==1.0.0`，而不是禁用代理，以兼容国外 OpenAI-compatible Provider 调用。
- 已重启本地 FastAPI 后端并验证 `/api/health` 正常。


## 2026-06-24（翻译 Provider 设置独立卡片）

- 根据协作反馈，将 AI 设置页中的翻译 Provider 选择从 AI Provider 主卡片拆分出来，放到 RAG 配置下方作为单独卡片。
- 新卡片展示当前实际翻译模型：优先翻译默认 Provider，未配置时展示回退的默认 AI Provider；Provider 表格仍保留快捷设为翻译默认入口。
- 前端构建通过，保留现有 Rollup chunk warning。


## 2026-06-24（翻译 Provider 独立存储实现）

- 根据 Hy-MT2/OpenAI-compatible 翻译模型配置讨论，将翻译 Provider 从通用 AI Provider 中拆出，新增 `translation_providers` 表与独立 CRUD API。
- 前端翻译模型卡片改为独立管理翻译 Provider，新增 Tencent Hy-MT2 快速模板，避免翻译直接复用摘要/标签/RAG 的通用 Provider。
- 迁移会从旧 `llm_providers.is_translation_default` 或通用默认 Provider 复制初始配置，减少已有本地环境升级成本。
- 后端和前端相关测试/构建已通过。


## 2026-06-24（译文标签恢复原文交互）

- 使用 AI Coding Agent 为阅读页段落翻译增加恢复原文交互：替换模式和对照模式中的「译文」标签均可点击，点击后清除该段翻译并展示原文。
- 前端构建通过，保留现有 Rollup chunk warning。

## 2026-06-24（Week17 PR 前代码检查）

- 使用 AI Coding Agent 进行 PR 前全量检查，发现并修复两个问题：RAG sqlite-vec 连接未显式关闭导致 Windows 临时数据库清理失败；翻译服务在显式传入 `provider_id` 时仍读取通用 `llm_providers` 而不是独立 `translation_providers`。
- 后端新增服务层回归测试，确保全文翻译与段落翻译都使用独立翻译 Provider 表。
- 验证结果：`pytest backend/tests` 90 项通过；`npm run build --prefix frontend` 通过，仍有现有 Rollup chunk size / pure annotation 警告，不阻塞 PR。
- PR 注意事项：不要提交本地日志、数据库、虚拟环境、构建产物；`frontend/dist/index.html` 是已跟踪构建产物改动，建议本次 PR 排除，除非团队明确要求提交 dist。

## 2026-06-29（Ripple 产品说明文档）

- 使用 AI Coding Agent 将产品说明整理为英文默认版 `README.md` 和中文版本 `README_CN.md`，并将原 README 内容迁移到 `TEAM_COLLABRATION.md`。
- 文档顶部采用居中 Logo、产品名、标语、徽章和语言切换入口，英文版可点击 `中文版` 跳转到中文 Markdown。
- 根据 `docs/pics` 中补充的应用截图，在英文版和中文版中加入阅读工作台、AI 摘要、AI 设置、RAG 问答、订阅源管理和搜索截图展示区。
- 文档覆盖产品概览、核心功能、技术架构、Windows/macOS 安装与打包部署、本地开发、AI Provider 配置、数据隐私、常见问题与 GitHub Issues 反馈入口。
- 按用户要求避免将文档表述为课程项目成果，保持面向用户和评审者的产品化语气。

## 2026-06-29（AI 摘要提示触发优化）

- 使用 AI Coding Agent 调整阅读页 AI 摘要抽屉的提示触发条件。
- 新增摘要交互状态，应用自动加载缓存摘要时不再显示“摘要内容展示不完全，请重新生成”警告。
- 用户主动打开摘要抽屉或点击生成摘要后，摘要失败和内容不完整提示仍按原逻辑展示。
- 前端 `npm.cmd run build` 验证通过，构建产物已恢复，未纳入本次源码改动。

## 2026-06-29（仓库文档与课程材料整理）

- 使用 AI Coding Agent 整理仓库顶层结构，将课程过程材料、需求截图、AI 编码案例 PDF、团队协作文档、PR 模板和参考 agent 配置统一归档到 `docs/coursework/`。
- 新增 `docs/coursework/README.md` 作为归档目录索引，并修正 `docs/REQUIREMENTS.md`、`docs/PROJECT_OVERVIEW.md`、`README.md`、`README_CN.md` 中相关文档入口和链接。
- 本次仅整理文档与资源位置，未改动前后端运行逻辑；现有已跟踪的 `__pycache__` 和 `frontend/dist` 等生成产物仍建议在单独清理 PR 中处理。

## 2026-06-29

- Used AI Coding Agent to diagnose why RAG indexing worked in `npm run dev:desktop` but failed in the installed Windows app.
- Found that the packaged backend is a PyInstaller build, while development mode runs the source backend from the local virtual environment.
- Updated the backend packaging configuration to collect `sqlite_vec`, including its dynamic SQLite extension files, so RAG vector indexing can load the required module in the installed app.
- Remaining limitation: the installer must be rebuilt and installed again for this packaging fix to take effect.
- Used AI Coding Agent to simplify the Reader AI tag candidate UI by hiding the generated tag status badge while keeping candidate selection, existing-tag reuse, and new-tag creation behavior unchanged.
- Used AI Coding Agent to harden AI tag generation against invalid JSON model responses by requesting JSON mode when supported, retrying without it when unsupported, and extracting valid JSON from common model chatter such as reasoning blocks, code fences, or surrounding prose.
- Added a final plain-text fallback for AI tag generation so non-JSON model replies can still produce reasonable tag candidates from comma-separated labels, Chinese tag lists, or numbered recommendation lines instead of failing with a JSON parse error.
- Strengthened the AI tag fallback again so unusable model text or model-call failures deterministically generate tag candidates from the article title, feed, body keywords, and matching existing tags rather than surfacing a "no usable tag candidates" error.
- Extended the tag suggestion endpoint to use the same local keyword fallback when no default LLM Provider is configured, returning stable candidates with a `Local fallback` AI result instead of blocking the workflow.
- Updated the AI settings translation configuration UI to remove the Tencent Hy-MT2 quick template and related front-end copy, leaving vLLM Qwen3-8B, Ollama, and OpenAI-compatible options visible.
- Tightened AI tag fallback filtering so malformed JSON field fragments such as `tag_id`, `name`, `reason`, `candidates`, and boolean/null values are rejected instead of appearing as selectable tags.
