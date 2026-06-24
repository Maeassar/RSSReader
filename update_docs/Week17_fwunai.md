# Week17 fwunai - Token 统计持久化修复

## 本周负责范围

- 修复删除 feed 后 token 用量统计归零、重新添加 feed 后无法恢复的问题。

## 问题描述

清空 feed 后，统计页面的 token 统计数据清零。重新添加 feed、同步日志恢复正常后，token 统计仍然为零，无法恢复历史数据。

## 根本原因

`ai_results` 表通过外键与 `entries` 表关联，约束为 `ON DELETE CASCADE`：

```sql
FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
```

删除 feed 时，`entries` 表中关联的文章被级联删除，`ai_results` 表中的 token 记录也随之被自动删除，历史统计数据永久丢失。

## 修复方案

将 `ai_results` 的外键行为由 `ON DELETE CASCADE` 改为 `ON DELETE SET NULL`，同时将 `entry_id` 字段改为可空（`INTEGER` 不加 `NOT NULL`）。

删除文章后，token 记录保留，`entry_id` 被置为 `NULL`，历史统计数据不受影响。

## 主要实现

### 1. schema.sql 变更

```sql
-- 修改前
entry_id INTEGER NOT NULL,
...
FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE

-- 修改后
entry_id INTEGER,
...
FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE SET NULL
```

### 2. database.py 迁移逻辑

在 `_migrate_ai_tables()` 中新增迁移判断：读取 `ai_results` 表当前建表语句（`sqlite_master`），检测是否包含 `ON DELETE CASCADE`。若是，执行以下迁移步骤（全程在同一连接内完成，SQLite 不支持直接修改外键约束）：

1. 创建新表 `ai_results_new`，外键为 `ON DELETE SET NULL`，`entry_id` 可 NULL
2. `INSERT INTO ai_results_new SELECT * FROM ai_results` 复制全量数据
3. `DROP TABLE ai_results`
4. `ALTER TABLE ai_results_new RENAME TO ai_results`
5. 重建所有相关索引

迁移完整代码位于 `backend/app/database.py` `_migrate_ai_tables()` 函数末尾。

## 后端接口变更

无新增接口，现有统计接口行为不变。`entry_id` 为 NULL 的记录会被正常计入 token 统计聚合，不影响 `stats()` 和 `stats_timeseries()` 查询结果。

## 实际测试记录

```bash
cd backend
python -c "
import sqlite3, sys
sys.path.insert(0, '.')
from app.database import initialize_database
initialize_database()
import sqlite3
conn = sqlite3.connect('app.db')
sql = conn.execute(\"SELECT sql FROM sqlite_master WHERE name='ai_results'\").fetchone()[0]
print('Migration OK' if 'ON DELETE SET NULL' in sql else 'Migration FAILED')
print(sql)
conn.close()
"
```

结果：`Migration OK`，新表结构确认为 `ON DELETE SET NULL`。

## 当前限制

- `entry_id` 为 NULL 的历史记录无法再关联回具体文章，但 token 总量、provider、model、时序分布等统计维度均不受影响。
- 若数据库文件不存在（全新安装），`schema.sql` 直接建表为正确结构，无需迁移。
