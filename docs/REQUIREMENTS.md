# 需求对照

本项目根据 [`coursework/demand.png`](coursework/demand.png) 中的 Mercury Features 和 Technical Constraints 设计。

## 功能要求

| 要求 | 实现方式 |
| --- | --- |
| 基础功能：Feed / OPML 解析 + Sync + 内容呈现 | FastAPI 提供 Feed、Article、OPML、Sync API；Vue 提供阅读首页和订阅管理页 |
| 内容清洗：Cleaned HTML + Cleaned Markdown + 定制样式 | 后端预留 `content_cleaner.py`；文章 Schema 包含 `raw_html`、`cleaned_html`、`cleaned_markdown` |
| AI 功能之一：Summary Agent + LLM Providers | 后端提供摘要接口；前端提供 AI Provider 配置页面 |
| AI 功能之二：Translation Agent | 后端提供翻译接口；阅读页提供翻译按钮 |
| 辅助功能：多语言支持、日志上报和调试工具 | 前端预留 i18n；后端提供同步日志接口 |
| 辅助功能：大语言模型用量统计 | 后端提供 `/api/stats/llm`；前端提供统计日志页 |
| 笔记和文摘导出 | 后端提供笔记 API 和 Markdown 导出 API |
| 标签系统 | 后端提供标签 API；前端提供标签管理和按标签筛选 |

## 技术约束

- 产品体验：使用 Element Plus 构建完整 Web 应用界面。
- 本地优先：当前无登录、无云端同步；后续数据保存到本地 SQLite。
- 平台中立：浏览器访问，支持 Windows / Linux / macOS。
- 大模型中立：AI Provider 采用 OpenAI-compatible API 设计。
- Coding Agent 留痕：保留开发日志和 AI 协作记录。
- 团队协同留痕：建议使用规范 Git 提交记录开发历史。

