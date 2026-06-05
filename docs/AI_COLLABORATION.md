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
