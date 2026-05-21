# Contributing to RSSReader

RSSReader is a course project for practicing open source collaboration. Please
use issues, branches, commits, and pull requests so the development process is
easy to review.

## Branch Naming

Create a branch for every change. Do not commit directly to `main`.

```text
feat/<topic>       # new feature          e.g. feat/ai-summary-api
fix/<topic>        # bug fix              e.g. fix/feed-parser-date
docs/<topic>       # documentation        e.g. docs/week16-summary-plan
test/<topic>       # tests only           e.g. test/rss-parser
refactor/<topic>   # refactor             e.g. refactor/feed-service
chore/<topic>      # tooling/config       e.g. chore/pr-templates
```

## Commit Format

Use Conventional Commits:

```text
<type>(<scope>): <short description>
```

Types: `feat` | `fix` | `docs` | `test` | `refactor` | `chore` | `revert`

Suggested scopes: `frontend` | `backend` | `rss` | `sync` | `notes` |
`search` | `export` | `ai-summary` | `ai-translation` | `docs` | `ci`

Examples:

```text
feat(ai-summary): add summary provider interface
fix(rss): handle Atom feeds without published date
docs(docs): add Week16 AI summary backend notes
test(backend): cover feed subscription API
chore(ci): add pull request template
```

## Pull Request Process

1. Open or reference an issue before implementing a non-trivial feature.
2. Keep the PR focused on one task or module.
3. Fill in the PR template with summary, motivation, tests, and documentation
   updates.
4. Update `README.md` or `update_docs/` when behavior, setup, APIs, or module
   ownership changes.
5. Wait for review before merging to `main`.

## Reporting Issues

Use the templates in `.github/ISSUE_TEMPLATE/`.

- For bugs, include reproduction steps, expected behavior, actual behavior, and
  environment information.
- For feature requests, describe the motivation, expected interface, alternatives,
  and out-of-scope items.

## Documentation Notes

Weekly documentation should be placed under `update_docs/` and named:

```text
Week{week_number}_{github_name}.md
```

For backend work, include endpoint paths, request/response examples, database
tables touched, environment variables, and test commands. For frontend work,
include route/component names, interaction flow, and API assumptions.

