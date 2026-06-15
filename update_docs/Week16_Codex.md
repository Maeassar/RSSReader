# Week16 Codex - Subscription Batch Delete

## Summary

- Added batch delete support for feed subscriptions in the subscription management page.
- Reused the existing feed table selection flow, so users can select multiple feeds, confirm once, and delete them together.
- Added a backend batch delete API that reports per-feed results instead of failing the whole request on the first error.

## Backend

### API

`POST /api/feeds/batch-delete`

Request:

```json
{
  "feed_ids": [1, 2, 3]
}
```

Response:

```json
{
  "total": 3,
  "success": 3,
  "failed": 0,
  "skipped": 0,
  "results": [
    {
      "feed_id": 1,
      "status": "success",
      "message": "Feed deleted."
    }
  ]
}
```

### Behavior

- Each feed ID is deleted independently.
- Duplicate IDs in the same request are skipped.
- Missing or invalid feed IDs are reported as failed, but other feed deletions continue.
- The endpoint reuses the existing repository `delete_feed()` behavior, including entry cleanup and vector index cleanup.

## Frontend

- Added a toolbar action named "删除选中" in `frontend/src/views/FeedManageView.vue`.
- The button is enabled only when at least one feed is selected and the page is not busy.
- The action uses `el-popconfirm` before deleting selected feeds.
- After deletion, the page reloads feeds, clears table selection, emits the existing `changed` event, and shows a summary message.

## Files Changed

- `backend/app/schemas/rss.py`
- `backend/app/services/feed_service.py`
- `backend/app/routers/feeds.py`
- `backend/tests/test_opml_sync.py`
- `frontend/src/api/client.ts`
- `frontend/src/views/FeedManageView.vue`
- `docs/AI_COLLABORATION.md`

## Verification

- Backend syntax check:

```bash
python -m py_compile backend\app\schemas\rss.py backend\app\services\feed_service.py backend\app\routers\feeds.py
```

- Backend unit test:

```bash
cd backend
..\.venv\Scripts\python.exe -m unittest tests.test_opml_sync
```

- Frontend type/build check:

```bash
npm.cmd run build --prefix frontend
```

## Limitations

- No end-to-end UI automation was added in this task.
- Batch delete is intentionally conservative and still relies on the existing single-feed repository deletion path.

## Follow-up: Immediate Article Availability After Import

### Summary

- Fixed the issue where newly imported OPML feeds appeared in the reader sidebar with article count 0 until the app restarted.
- The reader store now supports merging articles for an individual feed without resetting the whole reading state.
- When an OPML item is imported successfully, the subscription list is updated immediately and the imported feed's articles are fetched into the reader store right away.
- OPML import no longer triggers a full reader reload for each completed row, preventing early imported articles from being overwritten by older in-flight reloads.
- Initial OPML rows now display "上传中" with the reason "正在上传".
- After the OPML stream finishes, the reader store performs one full load from the final backend state so early completed feeds no longer stay at article count 0 until restart.
- Each successful OPML stream item now includes the imported feed's articles, and the frontend merges those articles immediately when the item event arrives. This makes per-feed reader counts update strictly when that feed sync completes.

### Frontend

- Added `mergeArticles()` and `refreshFeedArticles(feedId)` to `frontend/src/stores/reader.ts`.
- `FeedManageView.vue` now refreshes the imported feed's articles as each successful stream item arrives.
- Manual feed add and single-feed sync also refresh the affected feed's articles immediately.
- `reader.ts` tracks article mutations during `loadAll()` so a late full reload merges with newer per-feed article refreshes instead of replacing them.

### Verification

```bash
cd frontend
.\node_modules\.bin\vue-tsc.cmd --noEmit
```

```bash
cd backend
..\.venv\Scripts\python.exe -m unittest tests.test_opml_sync
```

## Follow-up: Sync Log Range Filtering

### Summary

- Added the same time range filtering used by LLM traffic stats to the sync log list.
- Supported ranges are `today`, `week`, `month`, and `all`.
- The stats page now refreshes sync logs when the selected range changes.

### Backend

- `GET /api/logs/sync` accepts a `range` query parameter.
- `SQLiteRepository.list_logs(range)` filters `feed_fetch_logs.fetched_at` with the existing range cutoff helper.
- Added a repository test covering `today` and `all` sync log filtering.

### Frontend

- `rssApi.syncLogs(range)` passes the selected range to the backend.
- `StatsView.vue` now shows range tabs in the sync log panel and reloads logs alongside the LLM stats/timeseries.
- Traffic stats and sync logs now keep separate range states, so changing one panel no longer changes the other.
- The sync log list uses an internal scroll container instead of growing the whole stats page indefinitely.

### Verification

```bash
cd backend
..\.venv\Scripts\python.exe -m unittest tests.test_llm_provider_repository tests.test_opml_sync
```

```bash
cd frontend
.\node_modules\.bin\vue-tsc.cmd --noEmit
```

## Follow-up: OPML Article Refresh Race and Upload Wording

### Summary

- Fixed a race where earlier OPML imports could refresh their articles, then lose them again when the parent reader view performed a full `loadAll()`.
- Feed management now emits a lightweight `changed` event for operations that already updated the reader store directly.
- OPML import collects per-feed article refresh promises and waits for them before finishing the stream workflow.
- Initial OPML rows now show status "上传中" and reason "正在上传" for pending upload/import work.

### Verification

```bash
cd frontend
.\node_modules\.bin\vue-tsc.cmd --noEmit
```

```bash
cd backend
..\.venv\Scripts\python.exe -m unittest tests.test_opml_sync
```

## Follow-up: OPML Import Queue Feedback

### Summary

- Updated OPML streaming import so the frontend can show all parsed feeds immediately as pending rows.
- Each feed row is then updated as soon as its import/sync finishes.
- Successful or partially successful feed imports continue to trigger the existing `changed` event, so the reader sidebar can refresh while the import is still running.

### Backend

- `POST /api/opml/import/stream` now emits a `parsed` SSE event before processing feeds.
- The `parsed` event contains all discovered OPML feed items with `pending` status.
- The parser now recognizes common URL attribute variants: `xmlUrl`, `feedUrl`, `rssUrl`, `atomUrl`, `url`, and `href`.
- If an OPML file contains no recognizable feed URLs, the import result includes a failed row instead of silently returning zero results.

### Frontend

- `OPMLImportItem.status` now includes `pending`.
- `OPMLImportStreamEvent.type` now includes `parsed`.
- `FeedManageView.vue` uses the `parsed` event to fill the OPML result table immediately, then replaces individual rows as `item` events arrive.
- `FeedManageView.vue` also performs a local OPML preview parse as soon as files are selected, so all feeds appear as pending even before the backend stream sends its first event.
- Added `frontend/src/stores/opmlImport.ts` to preserve OPML import progress when users switch away from and back to the subscription management page.
- Added reader store feed upsert/remove helpers so imported feeds appear in the reader sidebar immediately without waiting for the full OPML import to finish.

### Verification

```bash
cd backend
..\.venv\Scripts\python.exe -m unittest tests.test_opml_sync
```

Result: 15 tests passed.

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports third-party annotation and chunk size warnings.

## Follow-up: Ripple Branding and Installer Icon

### Summary

- Renamed the desktop package identity from RSSReader to Ripple for packaging metadata.
- Reused `docs/brand/ripple-logo-concept.png` as the source for desktop and web brand assets.
- Added `build/icon.ico`, `build/icon.png`, and `frontend/public/ripple-logo.png`.
- Updated the Electron window title/name/icon and the frontend title, favicon, header logo, and i18n app name.
- Configured Electron Builder so the Windows app and NSIS installer/uninstaller point at `build/icon.ico`.

### Verification

```bash
cd frontend
.\node_modules\.bin\vue-tsc.cmd --noEmit
```

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports third-party annotation and chunk size warnings.

```bash
npx.cmd electron-builder --config.asar=false --dir --config.win.target=dir --config.npmRebuild=false
```

Result: generated a `Ripple.exe` directory package for configuration verification; the generated `release/win-unpacked` output was cleaned afterward.
