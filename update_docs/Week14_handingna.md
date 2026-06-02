# Week14 handingna - OPML 与 Feed 同步系统

## 完成范围

本次补齐 RSS 订阅同步系统，重点从“已有同步 API”扩展为完整用户路径：

- OPML 导入从占位接口改为真实解析上传文件。
- OPML 导入后立即调用现有 Feed 创建逻辑，同步文章并写入 SQLite。
- OPML 导出从固定示例 XML 改为读取当前 SQLite 订阅源。
- `同步全部` 改为逐个 Feed 同步，单个失败不会中断整体流程。
- 前端订阅管理页支持 OPML 上传、OPML 下载和同步结果提示。
- 设置页新增启动自动同步和定时同步配置。

## 后端接口

### `POST /api/opml/import`

请求格式：`multipart/form-data`

字段：

- `file`: OPML 文件，建议后缀为 `.opml` 或 `.xml`

行为：

- 递归解析 OPML 中的 `outline` 节点。
- 使用 `xmlUrl` 作为 RSS/Atom Feed URL。
- 使用 `title` 或 `text` 作为可选订阅标题。
- 导入后立即解析 Feed 并保存文章。
- 已存在的订阅会跳过。
- 无效 URL 或不可解析 Feed 会记录失败结果。

响应字段：

- `total`: 本次识别出的订阅总数
- `imported`: 新增并同步成功数量
- `skipped`: 已存在或跳过数量
- `failed`: 失败数量
- `results`: 每条订阅的处理结果

### `GET /api/opml/export`

从当前 SQLite `feeds` 表导出 OPML 2.0 XML。

每条订阅包含：

- `text`
- `title`
- `type="rss"`
- `xmlUrl`
- `htmlUrl`，仅当订阅源存在站点地址时输出

### `POST /api/feeds/sync-all`

响应从原来的 `Feed[]` 改为同步汇总对象。

返回字段：

- `total`: 尝试同步的 Feed 数量
- `success`: 成功数量
- `failed`: 失败数量
- `skipped`: 跳过数量，当前固定为 0
- `results`: 每个 Feed 的同步状态、消息和成功后的 Feed 数据

单个 Feed 同步失败不会阻断其它 Feed。

## 前端交互

### 订阅管理页

文件：`frontend/src/views/FeedManageView.vue`

- `OPML 导入` 按钮会打开文件选择并上传到 `POST /api/opml/import`。
- 导入完成后刷新订阅列表。
- 根据导入结果显示成功、部分失败或失败提示。
- `OPML 导出` 通过 Axios 获取后端 XML Blob，再触发浏览器或 Electron 下载。
- `同步全部` 会根据汇总结果显示全部成功、部分失败或失败提示。

### 设置页

文件：`frontend/src/views/SettingsView.vue`

新增同步设置：

- 启动时同步：默认开启。
- 定时同步：默认关闭。
- 同步间隔：默认 60 分钟，最小 5 分钟。

同步偏好保存在前端 `localStorage`，不新增数据库表。

### 应用启动与定时同步

文件：`frontend/src/App.vue`

- 应用启动后，如果启动同步开启，会异步触发一次 `sync-all`。
- 启动同步有 10 分钟冷却，避免短时间反复打开应用造成重复抓取。
- 定时同步只在应用运行期间生效，不做系统级后台任务。
- 背景同步完成后会通知阅读页刷新文章列表。

## 测试

新增测试文件：

```text
backend/tests/test_opml_sync.py
```

覆盖场景：

- OPML 嵌套 outline 解析。
- 重复 `xmlUrl` 去重。
- OPML 导入中的新增、跳过和失败结果。
- OPML 导出读取当前订阅源。
- `sync-all` 在某个 Feed 失败后继续同步其它 Feed。

建议执行：

```bash
cd backend
python -m unittest discover -s tests
npm run build --prefix ../frontend
```

## 当前限制

- 定时同步只在前端页面运行期间触发，关闭 Web 页面或 Electron 应用后不会继续后台同步。
- OPML 导入会立即同步，遇到慢速或不可访问 Feed 时导入完成时间会受影响。
- 当前不新增每个 Feed 的独立同步周期配置。
