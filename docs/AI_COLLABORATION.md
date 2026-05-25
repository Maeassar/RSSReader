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
