## 1. 新建分支

不要直接向 `main` 分支提交代码。请根据你的任务新建对应类型的分支，命名规则如下：

- 新功能：`feat/<topic>`      例：`feat/rss-import`
- 修bug：`fix/<topic>`         例：`fix/feed-parser`
- 文档更新：`docs/<topic>`     例：`docs/week13-notes`
- 测试相关：`test/<topic>`
- 重构：`refactor/<topic>`
- 配置/脚本等：`chore/<topic>`

**命名举例**：
```sh
git checkout -b feat/rss-import
```

---

## 2. Commit 信息格式

采用 Conventional Commits 格式：

```text
<type>(<scope>): <short description>
```
- type建议用：`feat` | `fix` | `docs` | `test` | `refactor` | `chore` | `revert`
- scope建议用：`frontend` | `backend` | `rss` | `sync` | `notes` | `search` | `export` | `ai-summary` | `ai-translation` | `docs` | `ci`

**示例：**
```sh
git commit -m "feat(rss): add OPML import and export"
git commit -m "fix(frontend): fix feed list rendering bug"
```

---

## 3. 提交 PR（Pull Request）

1. 保证你的功能或修复关联了一个 issue（建议在 PR 描述中引用 issue）。
2. 保持每个 PR 聚焦于一个任务或模块，不要一次提交太多内容。
3. 填写 PR 模板（包括 summary、motivation、测试和文档说明等）。
4. 若涉及新接口、新用法或模块变动，要同步更新 `README.md` 或 `update_docs/` 下对应的**每周文档说明**。
   - 命名约定：`update_docs/Week{week_number}_{github_name}.md`
5. 等待唐小卉 review 后再合并到 `develop`分支。
