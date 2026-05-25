# RSSReader Initial Requirements and Architecture

## Project Goal

RSSReader is a local-first RSS/Atom reader built as a course project for open
source collaboration practice. The project should provide a usable reading
experience for subscriptions, articles, notes, search, export, AI summary, and
AI translation workflows.

The application should support both web development and desktop delivery. The
desktop version must run on Windows, macOS, and Linux through Electron.

## Target Users

- Users who want to manage RSS/Atom subscriptions locally.
- Students and contributors who need a clear Vue + FastAPI + SQLite project for
  collaborative development.
- Reviewers who need a reproducible project structure, documented APIs, and a
  clear PR workflow.

## Required Technology Stack

- Frontend: Vue 3, Vite, TypeScript, Pinia, Vue Router, Element Plus.
- Backend: FastAPI, Pydantic, uvicorn.
- Database: SQLite.
- Desktop shell: Electron.
- Backend desktop packaging: PyInstaller.
- RSS parsing: feedparser.
- Content processing: BeautifulSoup, readability-lxml, markdownify.
- AI integration: OpenAI-compatible APIs and local providers such as Ollama or
  vLLM where possible.

## Core Functional Requirements

RSSReader should support the following product capabilities:

- Add, list, update, delete, and synchronize RSS/Atom feed subscriptions.
- Parse feed metadata and article entries from RSS/Atom sources.
- Store feeds, articles, notes, sync logs, and AI results in SQLite.
- Show a reading interface with feed filters, article lists, article details,
  read/unread state, and starred articles.
- Support article notes with Markdown content.
- Support OPML import and export for subscription migration.
- Support article export, especially Markdown export, with PDF export reserved
  as a later extension.
- Support cleaned HTML and Markdown conversion for better reading.
- Support search, preferably through SQLite full-text search in a later phase.
- Provide AI summary, AI translation, and tag suggestion workflows through
  reserved API endpoints and later provider integrations.
- Keep AI provider configuration outside source code and behind environment
  variables or local settings.

## Cross-Platform Desktop Requirements

The desktop application should:

- Run on Windows, macOS, and Linux.
- Use Electron as the desktop shell.
- Start the local FastAPI backend automatically.
- Bundle the backend as a PyInstaller executable so end users do not need to
  install Python.
- Bind the backend only to `127.0.0.1`.
- Use a dynamic local port to avoid conflicts with other services.
- Load the Vue production frontend inside Electron.
- Store desktop runtime data in the operating system user data directory:
  - Windows: `%APPDATA%/RSSReader/app.db`
  - macOS: `~/Library/Application Support/RSSReader/app.db`
  - Linux: `~/.config/RSSReader/app.db`
- Keep development databases, packaged outputs, dependency folders, logs, and
  caches out of Git.

## Architecture Overview

RSSReader uses a three-layer structure:

1. Frontend
   - Vue pages, router, Pinia store, and API client.
   - Calls backend endpoints under `/api`.
   - In desktop production, reads the backend base URL injected by Electron.

2. Backend
   - FastAPI application with routers, services, schemas, and repositories.
   - Owns RSS parsing, feed sync, article state, notes, export, logs, and AI
     placeholder workflows.
   - Initializes and migrates SQLite schema on startup.

3. Desktop shell
   - Electron main process starts the bundled backend.
   - Electron preload exposes only minimal desktop configuration to the
     renderer.
   - Electron loads the built frontend with a desktop-safe application protocol.

## Collaboration Requirements

- Use GitHub Issues for visible task discussion.
- Use feature branches and pull requests for changes.
- Keep changes small and reviewable.
- Use Conventional Commits.
- Document backend endpoints, database changes, frontend routes, and state
  assumptions when behavior changes.
- Update weekly notes under `update_docs/Week{xx}_{github_name}.md`.
- Append AI collaboration notes to `docs/AI_COLLABORATION.md` after AI-assisted
  work.

## Delivery Expectations

The final project should include:

- A working web development mode.
- A working desktop mode.
- Reproducible setup and build instructions.
- Documented API behavior and database assumptions.
- A clear PR workflow for future contributors.
- Cross-platform packaging notes and Mac testing records.
