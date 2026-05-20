# Week12 唐小卉 - 项目规划、协作规范与汇报整理

## 本周工作概述

Week12 主要完成 RSSReader 项目的前期组织工作，包括建立项目仓库、确定开源协作流程、制定 AI 协作与项目初始化文档、拆分开发计划、安排组员分工，并整理阶段性汇报内容。

## 1. 建立仓库与协作流程

本周完成了 RSSReader 项目仓库的建立，并指导组员通过 GitHub Fork + Pull Request 的方式参与开发。

确定的协作标准如下：

- 项目主仓库作为统一代码源。
- 组员先 Fork 主仓库到个人账号。
- 每位组员在自己的 Fork 仓库中创建功能分支。
- 开发完成后向团队仓库发起 Pull Request。
- 所有合并通过 PR 完成，避免直接修改主分支。
- PR 内容需要聚焦一个任务或一个功能模块，方便 review。
- 提交信息使用 Conventional Commits 格式，例如：

```text
feat(backend): add feed api
docs(readme): update setup guide
fix(frontend): correct article list rendering
```

该流程用于模拟开源项目协作方式，让组员熟悉 Fork、分支开发、PR、代码审查和合并流程。

## 2. 制定项目文档

本周制定和整理了项目开发所需的基础文档，方便后续成员快速了解项目结构、协作方式和初始化流程。

主要文档包括：

- `AGENTS.md`：说明 AI Coding Agent 和人类贡献者在本仓库中的协作规则。
- `Plan.md`：记录项目整体开发计划、技术路线和阶段目标。
- `INIT.md`：说明本地项目初始化、依赖安装、数据库初始化和前后端启动方式。
- `docs/AI_COLLABORATION.md`：记录项目中 AI 辅助写作、需求拆解、代码生成和文档整理的使用情况。
- `CONTRIBUTING.md`：整理分支命名、提交格式、PR 流程和协作规范。
- `README.md`：整理项目介绍、功能规划、技术栈和基础使用说明。

这些文档用于保证后续开发有统一的入口说明和协作标准，减少组员之间因为环境、分支或任务理解不同产生的问题。

## 3. 制定开发计划与组员分工

根据项目需求，将 RSSReader 拆分为多个功能模块，并制定阶段性开发计划。

主要模块包括：

- 项目初始化：Vue 3 + Vite 前端、FastAPI 后端、SQLite 数据库。
- Feed 管理：RSS/Atom 地址添加、解析、同步、删除和查询。
- 文章阅读：文章列表、文章详情、已读状态、收藏状态。
- 笔记功能：为文章添加和更新 Markdown 笔记。
- 搜索功能：根据标题、摘要或正文搜索文章。
- 导出功能：将文章或笔记导出为 Markdown。
- AI 摘要：为文章生成摘要。
- AI 翻译：为文章生成翻译结果。
- OPML：订阅源导入和导出。
- 文档与测试：维护周任务文档、接口说明和基础测试。

同时为组员分配不同周任务和功能方向，确保每个人负责的内容清晰、可拆分、可提交。

分工原则：

- 每个成员负责一个相对独立的功能模块。
- 每个 PR 尽量对应一个明确任务。
- 涉及 API、数据库结构或前端状态变化时，需要同步更新文档。
- 对后续成员有影响的改动，需要在 `update_docs/` 中记录。

## 4. 整理汇报内容

本周还整理了项目阶段性汇报内容，用于说明项目目标、技术方案、团队协作方式和后续开发计划。

汇报内容主要包括：

- 项目背景：RSSReader 是一个用于课程项目和开源协作练习的 RSS/Atom 阅读器。
- 功能目标：支持订阅源管理、文章阅读、笔记、搜索、导出、AI 摘要和 AI 翻译。
- 技术栈：Vue 3 + Vite、FastAPI、SQLite。
- 协作方式：GitHub Fork + Pull Request。
- AI 使用方式：AI 辅助需求拆解、文档撰写、代码骨架生成和问题排查。
- 当前进度：完成项目规划、仓库搭建、协作规范制定和任务分工。
- 后续计划：逐步完成后端 API、数据库模型、RSS 解析、前端页面和 AI 功能。

## 本周产出

- 建立 RSSReader 项目仓库。
- 确定 Fork + PR 的开源协作标准。
- 制定 `AGENTS.md`、`Plan.md`、`INIT.md`、`docs/AI_COLLABORATION.md` 等项目文档。
- 制定整体开发计划和功能模块拆分。
- 为组员安排开发任务和协作规范。
- 整理项目汇报内容。

## 后续待办

- 根据 Week13 分工推进 Vue/FastAPI/SQLite 项目初始化。
- 完成 SQLite 数据表设计和初始化脚本。
- 完成 RSS/Atom Feed 解析模块。
- 完成 Feed API 的开发和文档记录。
- 持续更新 `update_docs/` 中的周任务记录。

---

# Week12 TheadoraTang - Project Planning, Collaboration Rules, and Presentation Preparation

## Weekly Summary

In Week12, I mainly worked on the early organization of the RSSReader project. The work included creating the project repository, defining the open source collaboration workflow, preparing project and AI collaboration documents, drafting the development plan, assigning responsibilities to team members, and organizing the presentation content.

## 1. Repository Setup and Collaboration Workflow

I created the RSSReader project repository and guided team members to participate through the GitHub Fork + Pull Request workflow.

The collaboration rules are:

- The team repository is used as the shared source of truth.
- Each member forks the main repository to their own GitHub account.
- Each member creates feature branches in their forked repository.
- Completed work is submitted through Pull Requests.
- All merges should happen through PRs instead of direct changes to shared branches.
- Each PR should focus on one task or one feature module.
- Commit messages should follow the Conventional Commits format, for example:

```text
feat(backend): add feed api
docs(readme): update setup guide
fix(frontend): correct article list rendering
```

This workflow helps the team practice open source collaboration, including Fork, branch-based development, Pull Requests, code review, and merge processes.

## 2. Project Documentation

I prepared and organized the basic documents needed for project development so that team members can quickly understand the project structure, collaboration rules, and initialization process.

Main documents include:

- `AGENTS.md`: Defines collaboration rules for AI Coding Agents and human contributors.
- `Plan.md`: Records the project development plan, technical direction, and milestone goals.
- `INIT.md`: Explains local initialization, dependency installation, database initialization, and frontend/backend startup steps.
- `docs/AI_COLLABORATION.md`: Records how AI was used for writing assistance, requirement decomposition, code generation, and documentation organization.
- `CONTRIBUTING.md`: Documents branch naming, commit format, PR workflow, and collaboration rules.
- `README.md`: Provides the project introduction, feature plan, technology stack, and basic usage notes.

These documents provide a shared entry point and consistent collaboration standard for later development.

## 3. Development Plan and Team Assignment

Based on the project requirements, I divided RSSReader into several feature modules and prepared a phased development plan.

Main modules include:

- Project initialization: Vue 3 + Vite frontend, FastAPI backend, and SQLite database.
- Feed management: add, parse, sync, delete, and query RSS/Atom feeds.
- Article reading: article list, article detail, read status, and starred status.
- Notes: create and update Markdown notes for articles.
- Search: search articles by title, summary, or content.
- Export: export articles or notes as Markdown.
- AI summary: generate article summaries.
- AI translation: generate translated article content.
- OPML: import and export feed subscriptions.
- Documentation and testing: maintain weekly documents, API notes, and basic tests.

I also assigned different weekly tasks and feature areas to team members so that each person's responsibility is clear, reviewable, and easy to submit through PRs.

Assignment principles:

- Each member should own a relatively independent module.
- Each PR should map to a clear task.
- API, database, or frontend state changes should be documented.
- Changes that affect later contributors should be recorded in `update_docs/`.

## 4. Presentation Preparation

I also organized the project presentation content for explaining the project goal, technical solution, collaboration workflow, and future development plan.

The presentation content includes:

- Project background: RSSReader is an RSS/Atom reader for course project practice and open source collaboration.
- Feature goals: feed management, article reading, notes, search, export, AI summary, and AI translation.
- Technology stack: Vue 3 + Vite, FastAPI, and SQLite.
- Collaboration workflow: GitHub Fork + Pull Request.
- AI usage: AI-assisted requirement decomposition, documentation writing, code skeleton generation, and debugging.
- Current progress: project planning, repository setup, collaboration rules, and task assignment.
- Next steps: backend APIs, database models, RSS parsing, frontend pages, and AI features.

## Weekly Deliverables

- Created the RSSReader project repository.
- Defined the Fork + PR open source collaboration workflow.
- Prepared project documents such as `AGENTS.md`, `Plan.md`, `INIT.md`, and `docs/AI_COLLABORATION.md`.
- Created the overall development plan and feature module breakdown.
- Assigned development tasks and collaboration rules to team members.
- Organized the project presentation content.

## Next Steps

- Continue Week13 work on Vue/FastAPI/SQLite initialization.
- Complete SQLite table design and initialization scripts.
- Complete the RSS/Atom Feed parsing module.
- Complete Feed API development and documentation.
- Continue updating weekly task records in `update_docs/`.
