<div align="center">
  <img src="docs/brand/ripple-logo-concept.png" alt="Ripple Logo" width="132" />

  <h1>Ripple</h1>

  <p><strong>A local-first RSS reader with AI summaries, translation, notes, search, export, and RAG Q&amp;A.</strong></p>

  <p>
    <a href="README_CN.md">中文版</a>
    ·
    <a href="https://github.com/TheadoraTang/RSSReader/issues">Report Issues</a>
  </p>

  <p>
    <img alt="Platform Windows" src="https://img.shields.io/badge/Windows-supported-2563eb?style=flat-square" />
    <img alt="Platform macOS" src="https://img.shields.io/badge/macOS-supported-111827?style=flat-square" />
    <img alt="Frontend Vue" src="https://img.shields.io/badge/Vue_3-frontend-42b883?style=flat-square" />
    <img alt="Backend FastAPI" src="https://img.shields.io/badge/FastAPI-backend-009688?style=flat-square" />
    <img alt="Database SQLite" src="https://img.shields.io/badge/SQLite-local--first-0f766e?style=flat-square" />
  </p>
</div>

---

## At a Glance

| Product | Ripple |
| --- | --- |
| Category | Desktop RSS/Atom Reader |
| Platforms | Windows, macOS |
| Data Model | Local SQLite database |
| AI Providers | OpenAI-compatible APIs, Ollama, vLLM, custom local services |
| Main Workflows | Subscribe, read, annotate, tag, search, export, summarize, translate, ask |
| Feedback | <https://github.com/TheadoraTang/RSSReader/issues> |

## Contents

- [Product Overview](#product-overview)
- [Product Screenshots](#product-screenshots)
- [Key Features](#key-features)
- [Technical Architecture](#technical-architecture)
- [Installation](#installation)
- [Local Development](#local-development)
- [Packaging and Deployment](#packaging-and-deployment)
- [AI Configuration](#ai-configuration)
- [Data and Privacy](#data-and-privacy)
- [Troubleshooting](#troubleshooting)
- [Feedback and Issues](#feedback-and-issues)

## Product Overview

**Ripple** is a desktop RSS/Atom reader designed for personal knowledge management and continuous information tracking. It combines feed management, article reading, notes, tags, search, export, AI summaries, AI translation, and RAG-based Q&A in one local-first reading workspace.

Ripple supports Windows and macOS desktop usage. Subscriptions, articles, notes, tags, and AI usage records are stored in a local SQLite database. AI providers can be configured through OpenAI-compatible APIs or local model services such as Ollama and vLLM.

<p align="center">
  <img src="docs/pics/read.png" alt="Ripple reader view" width="860" />
</p>

## Product Screenshots

| Reading Workspace | AI Summary |
| --- | --- |
| <img src="docs/pics/read.png" alt="Ripple reading workspace" /> | <img src="docs/pics/summary.png" alt="Ripple AI summary" /> |

| AI Settings | RAG Q&A |
| --- | --- |
| <img src="docs/pics/AI.png" alt="Ripple AI settings" /> | <img src="docs/pics/rag.png" alt="Ripple RAG Q&A" /> |

| Feed Management | Search |
| --- | --- |
| <img src="docs/pics/Feed.png" alt="Ripple feed management" /> | <img src="docs/pics/search.png" alt="Ripple search" /> |

## Key Features

| Feature | Description |
| --- | --- |
| Feed Management | Add, edit, delete, and batch-delete RSS/Atom feeds. |
| Article Sync | Sync one feed, sync all feeds, run startup sync, and configure scheduled sync. |
| OPML Import/Export | Import or export subscriptions for migration and backup. |
| Reader View | Browse feeds, article lists, and article details; manage read/unread and starred states. |
| Content Cleaning | Clean RSS HTML content and convert it into readable Markdown. |
| Notes | Write personal notes for individual articles. |
| Tags | Manage article tags while keeping AI tag suggestions under user confirmation. |
| Search | Search historical articles and quickly locate saved reading material. |
| Export | Export single articles or batch Markdown digests through desktop save dialogs. |
| AI Summary | Generate article summaries with a configured LLM provider and track usage. |
| AI Translation | Configure a dedicated translation provider; support streaming translation and comparison view. |
| RAG Q&A | Build a vector index over subscribed articles and ask questions in natural language. |
| Usage Statistics | Review LLM traffic, failed calls, and feed sync logs. |
| Reading Preferences | Customize theme, palette, font size, line height, and content width. |

## Technical Architecture

| Layer | Technology |
| --- | --- |
| Desktop | Electron |
| Frontend | Vue 3, Vite, Element Plus, Pinia, Vue Router |
| Backend | FastAPI, Python |
| Database | SQLite |
| Packaging | Electron Builder, PyInstaller |
| AI Integration | OpenAI-compatible API, Ollama, vLLM, local embedding services |

When the desktop app starts, Ripple launches a local backend service automatically and connects the frontend to the local API. User data is stored in the operating system's application data directory.

## Installation

### Windows

1. Download the latest `Ripple Setup x.x.x.exe` from `release/` or GitHub Releases.
2. Run the installer and follow the setup wizard.
3. Launch **Ripple** from the desktop shortcut or Start Menu.
4. Configure an LLM provider in AI Settings if AI features are needed.

### macOS

1. Download the latest `Ripple-x.x.x.dmg` from GitHub Releases.
2. Open the `.dmg` file.
3. Drag **Ripple** into the `Applications` folder.
4. Launch Ripple from Launchpad or `Applications`.
5. If macOS blocks the app, allow it in `System Settings -> Privacy & Security`.

## Local Development

### Requirements

| Tool | Recommended Version |
| --- | --- |
| Node.js | 18+ |
| npm | 9+ |
| Python | 3.10+ |
| Git | 2.40+ |

### Install Dependencies

```powershell
npm install
npm install --prefix frontend
python -m venv .venv1
.\.venv1\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### Start Desktop Development Mode

```powershell
npm run dev:desktop
```

This command starts:

| Service | Default Behavior |
| --- | --- |
| Vite frontend | `http://127.0.0.1:5173` |
| FastAPI backend | Automatically selects a local port |
| Electron desktop app | Loads the frontend and connects to the backend |

### Start Web Frontend and Backend Separately

```powershell
cd backend
uvicorn app.main:app --reload
```

```powershell
cd frontend
npm run dev
```

## Packaging and Deployment

### Windows Installer

```powershell
npm run dist:desktop
```

The installer will be generated at:

```text
release/Ripple Setup x.x.x.exe
```

The Windows package includes:

| Component | Description |
| --- | --- |
| Electron Shell | Desktop runtime |
| Vue frontend build | `frontend/dist` |
| PyInstaller backend | Bundled FastAPI backend |
| SQLite user data | Created automatically after installation |

### macOS DMG

Run the following on macOS:

```bash
npm install
npm install --prefix frontend
python3 -m venv .venv1
source .venv1/bin/activate
pip install -r backend/requirements.txt
npm run dist:desktop
```

The DMG file will be generated at:

```text
release/Ripple-x.x.x.dmg
```

macOS packaging notes:

| Item | Description |
| --- | --- |
| Build platform | Build the DMG on macOS whenever possible. |
| Python backend | Bundled with PyInstaller and shipped with the app. |
| Signing and notarization | Recommended for public distribution. |
| First launch warning | Unsigned builds may require manual approval in Privacy & Security settings. |

## AI Configuration

Open **AI Settings** in the app to configure:

| Configuration | Purpose |
| --- | --- |
| General AI Provider | Used for summaries, AI tag suggestions, and RAG Chat. |
| Translation Provider | Used for article translation and comparison reading. |
| Embedding Settings | Used for the RAG article index. |

Supported provider types:

| Type | Example |
| --- | --- |
| OpenAI-compatible | OpenAI, DeepSeek-compatible services, TokenHub-compatible services |
| vLLM Local | `http://127.0.0.1:8001/v1` |
| Ollama | `http://127.0.0.1:11434/v1` |
| Custom | Custom compatible endpoint |

API keys are encrypted locally. When editing a provider, leaving the API Key field empty keeps the existing key unchanged.

## Data and Privacy

| Data | Storage |
| --- | --- |
| Feeds, articles, notes, tags | Local SQLite database |
| AI provider settings | Local database with encrypted keys |
| AI usage logs | Local database |
| Exported files | User-selected local path |

Ripple is local-first by default. Reading data is only sent to external AI services when the user explicitly configures and uses a third-party AI provider.

## Troubleshooting

| Issue | Suggested Action |
| --- | --- |
| Feed sync fails | Check whether the Feed URL is reachable and review sync logs. |
| AI summary or translation fails | Verify Base URL, model name, API Key, and proxy settings. |
| RAG Q&A has no answer | Build the article index before asking questions. |
| Windows icon does not refresh | Reinstall the latest build and remove old desktop shortcuts if needed. |
| macOS blocks the app | Allow it in Privacy & Security settings, or use a signed build. |

## Feedback and Issues

Please report bugs, installation failures, AI provider issues, and feature requests through GitHub Issues:

<https://github.com/TheadoraTang/RSSReader/issues>

Recommended information:

| Information | Example |
| --- | --- |
| Operating system | Windows 11 / macOS 14 |
| Ripple version | `0.1.5` |
| Problem | Sync failure, UI error, AI call failure |
| Reproduction steps | 1. Open page; 2. Click button; 3. Error appears |
| Logs or screenshots | Sync logs, console errors, screenshots |
