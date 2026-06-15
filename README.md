# 开源软件开发与治理

## 成员
| 姓名  | GitHub账号 | 学号          |
|-----| ---------- |-------------|
| 唐小卉 |https://github.com/TheadoraTang | 51285903071 |
| 方蕴仪 |https://github.com/gloriaaa0312 | 51275903070 |
| 洪贝贝 |https://github.com/handingna|51285903034|
| 唐益  |https://github.com/maeassar| 51285903075 |
| 徐治平 |https://github.com/fwunai| 51285903022 |
| 仲韦萱 |https://github.com/bouboo1| 51285903052 |
| 朱文韬 | https://github.com/GentleCold| 51285903136 |
| 赖鑫  |https://github.com/specia1weak| 51285903020 |
| 张宥  |https://github.com/sdfhjisd|             |

## 成员分工概览
| 成员  | 负责时间                               | 负责模块                       | 实际工作内容                                                             | 最终实现效果                                      |
|-----|------------------------------------|----------------------------| ------------------------------------------------------------------ | ------------------------------------------- |
| 唐小卉 | Week12、Week13、Week15、Week17、Week18 | 项目初始化和分工，RSS Reader 后端核心系统 | 项目初始化（Vue/FastAPI/SQLite）、SQLite 数据模型设计、RSS/Atom Feed解析、Feed API开发 | 完成 RSS Reader 后端基础架构，支持 RSS 解析、数据存储与 API 提供 |
| 方蕴仪 | Week13                             | RSS Reader 前端阅读系统+笔记功能开发   | 基础阅读页面开发、Feed列表与文章展示UI、笔记功能开发                                      | 用户可以浏览 Feed、阅读文章并记录笔记                       |
| 赖鑫 | Week14、Week18                      | 导出与项目工程化系统                 | 笔记与文章单篇/多篇导出、Markdown/PDF 导出、Bug修复与联调、Docker部署、项目文档整理              | 支持文章导出与项目部署，实现项目最终交付                        |
| 洪贝贝 | Week14                             | RSS 订阅同步系统                 | OPML 导入导出功能、Feed Sync 同步机制、更新内容存储进 SQLite、Feed 更新调度机制              | 支持 RSS 自动同步、订阅迁移以及数据自动更新                    |
| 仲韦萱 | Week15、Week17                      | 内容处理与阅读优化系统，Mac端功能测试       | HTML 内容清洗模块、Markdown 转换模块、阅读主题与样式系统、文章详情渲染优化                       | 提供干净的阅读内容与更好的阅读体验                           |
| 唐益 | Week13、Week14、Week15、Week16        | 搜索系统搭建，Mac端功能测试            | 参与 Week13 和 Week14 的 macOS 桌面端功能测试，验证 Electron 打包、后端自动启动、用户数据目录、应用退出后的后端进程清理；Week18 继续负责导出、工程化和最终交付验证 | 支持文章导出与项目工程化交付，并补充 macOS 端桌面运行兼容性验证 |
| 朱文韬 | Week16                             | AI Summary 后端系统            | Summary Agent 核心开发、LLM Provider 抽象层、OpenAI-Compatible API 接入       | 支持 AI 文章摘要与多模型切换                            |
| 徐治平 | Week16                             | 本地模型与 AI 摘要前端              | Ollama/vLLM 本地模型支持、AI摘要结果展示页面                                      | 支持本地大模型与 AI 摘要结果展示                          |
| 张宥  | Week17                             | AI Translation 系统          | Translation Agent 开发、多语言支持（i18n）、AI翻译接口实现                          | 支持 AI 翻译功能与多语言阅读界面                          |

## 开发过程中的注意事项
1. 每个人每周开发完自己的任务之后，要把自己实现的功能，包括方便后面进行开发的新产出的接口等等更新在**update_docs**中，以便后续开发的同学能够快速了解当前功能实现的细节和接口使用方式，命名方式为**Week{xx}_{github_name}.md**。
2. 有任何问题同时在微信群和issues中提出，因为要体现**开源协作**
3. 貌似是每周都要汇报的，每周负责报告的人就是这周负责开发功能的人（1-2个）
4. 提交PR的时候要稍微详细一点，不要只写"update XXX文件"之类的,可以参考template中的要求
5. 如果你想提交修改的代码，根据 [CONTRIBUTING.md](CONTRIBUTING.md) 的要求，标准流程如下:[提交流程](template_CN.md)



## 与AI协作的过程（参考PDF，开发过程中可以参考）
| Stage             | 本质    | 主要目标       | 核心产物                              |
| ----------------- | ----- | ---------- | --------------------------------- |
| Stage1 Plan       | 架构设计  | 定义项目       | INIT.md / AGENTS.md / PLAN.md     |
| Stage2 Build      | 迭代开发  | 构建功能       | phase plans / README / tests      |
| Stage3 Change     | 架构迁移  | 技术栈升级      | migration docs / new architecture |
| Stage4 Reflection | 经验复盘  | 理解 AI 边界   | lessons learned / issue docs      |
| Stage5 Guide      | 方法论沉淀 | 建立 AI 工程体系 | engineering guide / skills        |

## 几个核心概念
| 功能                 | 在项目里的作用     |
| ------------------ | ----------- |
| RSS Parser         | 解析 RSS XML  |
| Feed API           | 管理订阅源       |
| OPML Import/Export | 导入导出订阅      |
| Feed Sync          | 自动更新文章      |
| SQLite             | 保存 Feed 和文章 |


# RSS Reader Web Application 开发计划（Week12–Week18）

## 技术栈：

* Frontend：Vue3 + Vite
* Backend：FastAPI
* Database：SQLite
* AI：OpenAI-Compatible API + 本地模型（API可以使用学校大模型的，本地模型找一个小一点的开源大模型）

## 周历
| 周历     | 时间                      |
|--------|-------------------------|
| Week12 | 2026/05/18 ~ 2026/05/24 |
| Week13 | 2026/05/25 ~ 2026/05/31 | 
| Week14 | 2026/06/01 ~ 2026/06/07 |       
| Week15 | 2026/06/08 ~ 2026/06/14 |   
| Week16 | 2026/06/15 ~ 2026/06/21 |       
| Week17 | 2026/06/22 ~ 2026/06/28 |
| Week18 | 2026/06/29 ~ 2026/07/03 |

---

# Week12 — 项目初始化构建
## 本周目标

完成：

* 计划分工
* 确定技术栈和开发计划
* 准备汇报内容
* 编写INIT.md / AGENTS.md / PLAN.md

## 负责人

| 时间     | 分工内容       | 负责人 |
|--------|------------|-----|
| Week12 | 初始化文档编写和讨论 | 唐小卉 |
---

# Week13 — 项目规划与 RSS 基础呈现

## 本周目标

完成：

* 项目初始化
* SQLite 数据模型建立
* RSS/Atom Feed解析
* Feed内容存储
* Feed内容呈现
* 基础阅读页面

## 负责人

| 时间     | 分工内容                      | 负责人 |
|--------| ------------------------- |-----|
| Week13 | 项目初始化（Vue/FastAPI/SQLite） | 唐小卉 |
| Week13 | SQLite 数据模型实现             | 唐小卉 |
| Week13 | RSS/Atom Feed解析模块         | 唐小卉 |
| Week13 | Feed API开发                | 唐小卉 |
| Week13 | 基础阅读页面开发                  | 方蕴仪 |
| Week13 | Feed列表与文章展示UI             | 方蕴仪 |
| Week13 | 设置里的内容（字号/深色浅色模式/不需要的内容删除） | 方蕴仪 |
| Week13 | 笔记功能开发          | 方蕴仪 |
| Week13 | macOS 桌面端基础功能测试：启动 Electron、加载 Vue 前端、自动启动 FastAPI 后端、读取 SQLite 用户数据目录 | 唐益 |


## 本周交付成果

* RSS Reader 基础可运行版本
* SQLite 数据持久化
* 支持订阅 Feed
* 支持文章列表展示
* 支持文章阅读
* 笔记系统
---

# Week14 — OPML 与 Sync 功能开发

## 本周目标

完成：

* OPML导入导出
* Feed同步机制
* Feed更新调度机制
* 数据同步优化

## 负责人

| 时间     | 分工内容            | 负责人 |
|--------|-----------------|-----|
| Week14 | OPML 导入导出功能     | 洪贝贝 |
| Week14 | Feed Sync 同步机制  | 洪贝贝 |
| Week14 | 更新内容存储进SQLite中  | 洪贝贝 |
| Week14 | Feed 更新调度机制     | 洪贝贝 |
| Week14 | 笔记以及文章单篇/多篇导出功能 | 赖鑫  |
| Week14 | Markdown/PDF 导出 | 赖鑫  |
| Week14 | Mac端功能测试          | 唐益  |


---
## 本周交付成果

* 支持 OPML 导入导出
* 自动同步 Feed
* 数据持久化（入库）
* 导出功能

---

# Week15 — 内容清洗与阅读优化

## 本周目标

完成：

* Cleaned HTML
* Cleaned Markdown
* 阅读样式优化
* Else可能的清洗格式

## 负责人

| 时间     | 分工内容              | 负责人 |
|--------|-------------------|-----|
| Week15 | HTML 内容清洗模块       | 仲韦萱 |
| Week15 | Markdown 转换模块     | 仲韦萱 |
| Week15 | 阅读主题与样式系统         | 仲韦萱 |
| Week15 | 文章详情渲染优化          | 仲韦萱 |
| Week15 | Mac端功能测试          | 仲韦萱 |
| Week15 | SQLite 全文搜索（API端） | 唐益  |
| Week15 | 搜索页面 UI           | 唐益  |
| Week15 | Windows端功能测试          | 唐小卉  |

## 本周交付成果

* 干净的 HTML 阅读内容
* Markdown 转换能力
* 更好的阅读体验

---

# Week16 — AI Summary Agent 开发

## 本周目标

完成：

* Summary Agent
* LLM Provider 接入
* OpenAI-Compatible API支持

## 负责人

| 时间     | 分工内容                     | 负责人                     |
|--------|--------------------------|-------------------------|
| Week16 | Summary Agent 核心开发       | 朱文韬                     |
| Week16 | LLM Provider 抽象层         | 朱文韬                     |
| Week16 | OpenAI-Compatible API 接入 | 朱文韬                     |
| Week16 | 本地模型支持（Ollama/vLLM）      | 徐治平                     |
| Week16 | AI摘要结果展示页面               | 徐治平                     |
| Week16 | Summary LLM用量统计          | 朱文韬&徐治平（有困难就不做，记得把前端删掉） |
| Week16 | Mac端功能测试                 | 唐益                      |
| Week16 | 已有bug修改和UI完善             | 唐小卉                     |

## 本周交付成果

* AI文章摘要
* 支持切换不同LLM
* 支持本地大模型
* 支持用量统计

---

# Week17 — Translation Agent 与扩展功能

## 本周目标

完成：

* Translation Agent
* 多语言支持
* AI统计功能

## 负责人

| 时间     | 分工内容                 | 负责人 |
|--------| -------------------- | --- |
| Week17 | Translation Agent 开发（需支持本地+API调用，可参考上周的实现方式） | 张宥 |
| Week17 | 多语言支持（i18n）          | 张宥 |
| Week17 | AI翻译接口实现             | 张宥 |
| Week17 | Summary LLM用量统计        | 张宥（有困难就不做，记得把前端删掉） |
| Week17 | Mac端功能测试          | 仲韦萱 |

## 本周交付成果

* AI翻译功能
* 多语言界面
* 多语言阅读支持

---

# Week18 — 项目汇总与最终交付

## 本周目标

完成：

* 项目测试
* Docker部署
* 文档整理
* 最终演示

## 负责人

| 时间     | 分工内容                     | 负责人         |
| ------ |--------------------------|-------------|
| Week18 | Bug修复与联调                 | 赖鑫          |
| Week18 | 项目文档（文档要规范，比如AGENTS.md,INIT.md）整理                   | 赖鑫          |
| Week18 | Mac端功能测试                 | 赖鑫         |
| Week18 | Windows端功能测试          | 唐小卉  |
| Week18 | PPT和汇报                   | 所有成员负责自己的板块 |
