## Summary

- 重构翻译UI：逐段翻译按钮改用 pill 样式 + 图标，与左侧 sidebar 按钮风格一致
- 双语对照模式改为卡片式布局（原文/译文各自成卡），移除突兀的左边框
- 工具栏翻译按钮增加语言选择下拉和清除全部翻译功能
- 修复文章正文 h1-h4 标题字号过大的问题（使用浏览器默认 32px/24px，与正文 16px 不协调）

## Motivation

翻译部分 UI 之前比较简陋（按钮无图标、译文框左边框突兀、对照模式只有一条横线分隔），
与整个应用 sidebar 按钮、article-card 等组件的设计语言不一致。

Closes #（待关联 issue）

## Changes

- [x] Frontend
- [ ] Backend
- [ ] Database
- [ ] Documentation
- [ ] Tests / CI

## Test Plan

- [x] Frontend build or tests pass
- [x] Manual verification completed

Commands run:

```bash
npm run build
```

## Documentation

- [ ] README updated if setup, usage, or ownership changed
- [ ] `update_docs/` added or updated for weekly work
- [ ] API changes documented with request/response examples
- [x] Not applicable

## Checklist

- [ ] Branch is based on `main`（实际基于 `develop`）
- [x] PR title follows Conventional Commits
- [x] No secrets, API keys, local databases, or machine-specific paths committed
- [x] Scope is focused and reviewable
