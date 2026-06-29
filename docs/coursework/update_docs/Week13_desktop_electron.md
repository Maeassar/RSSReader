# Week13 Desktop Packaging - Electron, FastAPI, SQLite

## Completed Scope

- Added an Electron desktop shell for RSSReader.
- Added `backend/desktop_server.py` so the FastAPI API can be started by Electron or packaged by PyInstaller.
- Updated backend database configuration so `RSSREADER_DB_PATH` can move SQLite data into the desktop app user data directory.
- Updated the frontend API client so Electron production builds can inject the local backend base URL.
- Added root-level scripts for desktop development and packaging.

## Desktop Architecture

Electron starts a local FastAPI backend on `127.0.0.1` with a free dynamic port, waits for `GET /api/health`, then loads the Vue UI.

In development, run:

```bash
npm install
npm run dev:desktop
```

For packaging, run:

```bash
npm run dist:desktop
```

The packaging flow builds:

- Vue frontend into `frontend/dist`
- FastAPI backend into `backend/dist/RSSReaderBackend/`
- Electron installers into `release`

## Runtime Data

The desktop backend reads the SQLite path from `RSSREADER_DB_PATH`. Electron sets this to the app user data folder:

- Windows: `%APPDATA%/RSSReader/app.db`
- macOS: `~/Library/Application Support/RSSReader/app.db`
- Linux: `~/.config/RSSReader/app.db`

The old development default remains `backend/app.db`.

## Notes

- The backend only binds to `127.0.0.1`.
- Electron uses `contextIsolation: true` and `nodeIntegration: false`.
- Code signing and notarization are not configured for the course version.
