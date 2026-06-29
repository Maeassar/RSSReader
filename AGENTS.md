# AGENTS.md

Guidelines for AI coding agents and human contributors working in this repository.

## Project

RSSReader is a course project for practicing open source collaboration. The
application is planned as a Vue 3 + Vite frontend, FastAPI backend, and SQLite
database for RSS/Atom reading, notes, search, export, AI summary, and AI
translation workflows.

- During development, use `develop` as the integration branch. Base feature
  branches and development PRs against `develop`.
- Before final delivery, keep `main` as a documentation branch for teaching
  assistants to review the README and project overview; do not merge daily
  development work into `main`.
- Keep frontend, backend, tests, and documentation in clearly named directories
  once the project scaffold is added.
- Update `update_docs/Week{xx}_{github_name}.md` after each weekly task so later
  contributors can understand new APIs, data models, and usage notes.
- After each AI Agent collaboration, append a dated note to
  `docs/AI_COLLABORATION.md` describing the collaboration content, outputs, and
  any remaining limitations.
- Use GitHub Issues for visible collaboration and PRs for all merged changes.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, commit format, and
  PR process.

## Collaboration Rules

1. Prefer small, reviewable changes tied to one issue or weekly task.
2. Do not commit secrets, API keys, local database files, virtual environments,
   generated build outputs, or machine-specific paths.
3. Document new backend endpoints with request/response examples.
4. Document new frontend routes, components, and state assumptions when they
   affect other contributors.
5. Keep database schema changes explicit and describe migration or reset steps.
6. For AI features, keep provider configuration behind environment variables and
   support OpenAI-compatible APIs where possible.
7. Add or update tests when changing behavior, especially for parser, sync,
   search, export, and AI service code.
8. If implementation details differ from the README plan, update the relevant
   documentation in the same PR.

## Expected Stack

- Frontend: Vue 3 + Vite
- Backend: FastAPI
- Database: SQLite
- AI: OpenAI-compatible API providers and local model providers such as
  Ollama/vLLM

## Commit Format

Use Conventional Commits:

```text
<type>(<scope>): <short description>
```

Recommended types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

Recommended scopes: `frontend`, `backend`, `rss`, `sync`, `notes`, `search`,
`export`, `ai-summary`, `ai-translation`, `docs`, `ci`.

