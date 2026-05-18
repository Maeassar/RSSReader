# AI 协作记录

本项目开发过程中使用 Coding Agent 辅助完成需求拆解、架构规划和代码骨架生成。

## 协作内容

- 根据 `demand.png` 提取 Mercury Features 和 Technical Constraints。
- 将桌面端 Mercury 功能转换为 Vue + FastAPI Web 应用方案。
- 设计 Mock-first 后端架构，保留 SQLite Repository 替换点。
- 生成 FastAPI 路由、Pydantic Schema、Service 和 Repository。
- 生成 Vue 页面、API Client、Pinia Store 和基础样式。
- 编写项目 README 和设计文档。

## 当前限制

- 当前版本使用 Mock 数据，不进行真实数据库持久化。
- AI 摘要、翻译、标签推荐为 Mock 结果。
- RSS 和 OPML 服务接口已预留，后续需要接入真实解析和入库逻辑。

