# RSSReader 项目初始化说明

本文档用于说明 RSSReader 的本地开发环境初始化、依赖安装、数据库初始化和前后端启动方式。

## 环境要求

建议使用以下环境：

- Python 3.10+
- Node.js 22+
- npm
- SQLite

## 后端初始化

进入后端目录：

```bash
cd backend
```

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

初始化 SQLite 数据库：

```bash
python init_db.py
```

执行后会创建或更新本地数据库文件：

```text
backend/app.db
```

`app.db` 是本地运行数据，不应该提交到 Git 仓库。

## 启动后端

在 `backend` 目录下运行：

```bash
uvicorn app.main:app --reload
```

后端服务地址：

```text
http://127.0.0.1:8000
```

API 文档地址：

```text
http://127.0.0.1:8000/docs
```

健康检查接口：

```text
GET /api/health
```

## 前端初始化

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

## 启动前端

在 `frontend` 目录下运行：

```bash
npm run dev
```

前端服务地址：

```text
http://127.0.0.1:5173
```

## 数据库说明

数据库初始化相关文件：

```text
backend/schema.sql
backend/init_db.py
backend/app/database.py
```

后端主要使用以下表：

- `feeds`：保存 RSS/Atom 订阅源信息。
- `entries`：保存从 RSS/Atom 中解析出的文章条目。
- `feed_fetch_logs`：保存 Feed 抓取和同步日志。
- `notes`：为文章笔记功能预留。
- `ai_results`：为 AI 摘要和翻译结果预留。

如果修改了表结构，可以删除本地数据库后重新初始化：

```bash
cd backend
python init_db.py
```

## 常用 API

后端启动后，可以在 Swagger 页面测试接口：

```text
http://127.0.0.1:8000/docs
```

常用接口：

- `GET /api/health`
- `GET /api/feeds`
- `POST /api/feeds`
- `GET /api/feeds/{feed_id}`
- `POST /api/feeds/{feed_id}/sync`
- `GET /api/feeds/{feed_id}/entries`
- `GET /api/articles`
- `GET /api/articles/{article_id}`

添加 RSS/Atom 订阅源的请求示例：

```json
{
  "title": "OpenAI News",
  "url": "https://openai.com/news/rss.xml"
}
```

注意：当前实现只保存 RSS/Atom Feed 中提供的内容，不会额外抓取文章原网页全文。

## 不应提交的文件

以下文件或目录不应提交到 Git：

- `.venv/`
- `node_modules/`
- `frontend/dist/`
- `__pycache__/`
- `*.pyc`
- `*.db`
- `*.sqlite`
- `*.sqlite3`
- 本地日志文件
- API key 或其它密钥

提交前建议检查：

```bash
git status
```

如果误暂存了本地数据库或缓存文件，可以取消暂存：

```bash
git restore --staged <file>
```

## 推荐启动顺序

第一次运行项目：

```bash
cd backend
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload
```

另开一个终端启动前端：

```bash
cd frontend
npm install
npm run dev
```

之后打开：

```text
http://127.0.0.1:5173
```

并通过以下地址查看后端接口：

```text
http://127.0.0.1:8000/docs
```
