# Week17 Theadora Tang

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

## Follow-up: Reader Layout Polish

### Summary

- Added persistent controls for collapsing and restoring the subscription sidebar and article list panel.
- Replaced the floating controls with draggable splitters on the two column boundaries, supporting click-to-collapse and drag-to-resize behavior.
- Lowered the article-list minimum width and added compact/micro list layouts so the second column can be resized independently.
- Restyled the article detail toolbar into a smaller right-aligned icon group matching the reading content width.
- Moved read/unread, pin, and favorite actions into article cards so the article detail toolbar stays focused on detail-only actions.
- Updated article list read state styling so unread articles are indicated by stronger/darker title text.
- Constrained the article detail content to a centered fixed reading width for a calmer reading surface.

### Verification

```bash
cd frontend
.\node_modules\.bin\vue-tsc.cmd --noEmit
```

## Follow-up: Reader Large-Library Performance

### Summary

- Reworked the reader page so large feed collections no longer load and render every article when entering the page.
- `GET /api/articles` now returns a paginated lightweight payload: `items`, `total`, `limit`, `offset`, and `has_more`.
- Article list items no longer include `raw_html`, `cleaned_html`, or `cleaned_markdown`; full article content remains available from `GET /api/articles/{id}`.
- Added `GET /api/articles/counts` for sidebar totals: all, unread, starred, per-feed, and per-tag.
- Added persistent SQLite `tags` and `article_tags` tables plus tag-aware article filtering and counts.
- The frontend reader store now keeps `articleItems`, `selectedArticle`, `articleCounts`, pagination state, and a small detail cache.
- The reader page loads the first 50 articles, loads more while scrolling, and reloads only the current filtered page when filters or sort order change.
- Sidebar counts now read backend aggregates instead of repeatedly filtering the article array.
- Full article HTML is loaded only when a user selects an article.
- SQLite connections now close after each context-managed use, which also prevents Windows test database cleanup failures.

### API Notes

- `GET /api/articles`
  - Query: `feed_id`, `tag_id`, `unread`, `starred`, `limit`, `offset`, `sort_order`.
  - `limit` defaults to 50 and is capped at 100.
  - `sort_order` supports `newest` and `oldest`.
- `GET /api/articles/counts`
  - Returns `total`, `unread`, `starred`, `by_feed`, and `by_tag`.
- `GET /api/feeds/{feed_id}/entries` keeps the old full-array behavior for compatibility.

### Verification

```bash
cd backend
$env:PYTHONDONTWRITEBYTECODE='1'; ..\.venv1\Scripts\python.exe -m unittest discover -s tests
```

Result: 33 tests passed.

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk size warnings.

### Follow-up Fix

- OPML import and sync-all flows now refresh `articleCounts` instead of directly calling `readerStore.loadAll()` with the default query.
- When streamed OPML item events include article payloads, the reader store merges those articles and immediately reloads backend counts so newly imported feeds show correct sidebar totals.
- Embedded ReaderView handles lightweight feed-manager change events by refreshing counts, keeping feed article badges correct after add, sync, delete, and OPML import operations.

### Follow-up Fix: OPML Counts and Reader Switching Stability

- OPML import result rows now match pending rows with normalized URLs, so backend-normalized URLs replace the correct local row and no longer leave imported feeds stuck in the uploading state.
- The reader store can patch a single feed's article count immediately after OPML sync or feed refresh, then reconcile with `/api/articles/counts`.
- Feed-management refreshes update feed counts without merging imported articles into the currently open filtered article list; the current list reloads its own first page after the OPML stream completes.
- Reader article-list loads now use a request sequence guard so quick switching between feeds/tags ignores stale responses from earlier requests.
- The reader page no longer applies a grid-wide loading overlay. Loading is shown inside the article list only, avoiding the white screen seen when switching during OPML import.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Fix: External Browser Link Handling

- Desktop reader links now open through the system default browser instead of creating popup windows inside the Electron app.
- Electron exposes a small `openExternal` preload bridge backed by `shell.openExternal`, and the main window denies external `window.open` popups after handing them to the OS.
- The article source URL, rendered article-body links, and AI summary result links all share the same external-link handler.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Feature: AI Tag Candidate Generation

- Replaced the mock `/api/ai/tag-suggest/{article_id}` response with real LLM-backed tag candidate generation using the same default provider configuration as Summary.
- Added structured tag suggestion responses with `article_id`, `candidates`, and the saved `ai_result` audit record.
- The tag agent prompt sends article context and existing tag names so the model can reuse current tags or suggest new reusable labels.
- The reader tag popover now includes an AI generation panel where users can generate candidates, deselect unwanted labels, and apply only the selected tags.
- Applying AI candidates reuses the existing manual tag flow: existing tags are assigned directly, new names are created first, then the article tag list is saved.
- Manual tag search, Enter-to-create, chip toggles, sidebar tag filters, and tag deletion remain unchanged.

### Verification

```bash
python -m unittest discover backend/tests
npm.cmd run build --prefix frontend
```

Result: both checks passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Fix: Tag Sidebar Scrolling and Chinese AI Tag UI

- The left sidebar tag group is now wrapped in a bounded `el-scrollbar`, so large tag sets can scroll inside the tag section instead of being clipped.
- The AI tag candidate panel now uses Chinese labels for the title, generate button, existing/new badges, clear/apply actions, and user-facing messages.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Fix: Reader Tag Popover Layout and Search

- The article tag popover now renders tags as compact chips instead of full-width rows.
- Tag chips wrap automatically when the row is full, making large tag sets easier to scan and assign.
- Added a search input to filter existing tags in the article tag popover.
- Pressing Enter in the search box assigns an exact matching tag, or creates and assigns a new tag with the current tag color if no exact match exists.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Fix: Tag Actions During OPML Import

- Added a frontend `deleteTag` API wrapper for the existing backend `DELETE /api/tags/{tag_id}` endpoint.
- Reader tag operations now support cached OPML articles: article tag assignments update the visible list item, selected detail, detail cache, per-feed article cache, and tag counts locally when the backend is still busy.
- Tag creation falls back to temporary local tags with negative ids if the backend cannot respond during a long OPML stream, allowing users to organize already imported articles immediately.
- Tag deletion is available from both the sidebar tag list and the article tag popover, and removes the deleted tag from all known local article states.
- Local tag filters can render from cached/list/detail articles, so temporary tags remain usable before backend reconciliation.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Fix: OPML Progressive Feed Visibility

- Protected per-feed article counts learned from OPML stream item events until backend `/api/articles/counts` reports the same or higher value, preventing older aggregate responses from resetting already imported feeds to `0`.
- Each completed OPML feed now emits a reader refresh after its local feed/count state has been applied, so a feed selected during import can load articles as soon as its own sync finishes.
- The subscription management table now merges final `GET /api/feeds` results with feeds already inserted from stream events, avoiding the `No Data` table state after a successful OPML import.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Fix: Stale Counts and Shared Feed Table State

- Added a request sequence guard for `/api/articles/counts`; stale count responses from earlier refreshes are ignored and can no longer reset newer OPML feed counts to `0`.
- Subscription management now uses `readerStore.feeds` as its table data source instead of a separate component-local feed array.
- `loadFeeds()` writes through `readerStore.setFeeds()`, with merge mode on OPML import and initial mount so streamed feed rows remain visible even if a fetch returns an older snapshot.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Fix: Immediate Reading During OPML Import

- Successful OPML stream item payloads now populate a per-feed article cache in the reader store.
- The cache stores both lightweight article list items and full article details, allowing an already imported feed to be opened and read while the remaining OPML feeds are still syncing.
- `loadAll({ feed_id })` now uses the cached feed page immediately when available, avoiding a blocked `/api/articles?feed_id=...` request during the long-running OPML import stream.
- Loading a cached feed increments the reader load request sequence so older in-flight network loads cannot overwrite the cached readable page.
- OPML item handling updates protected feed counts from the streamed articles without issuing a per-item aggregate counts request.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.

### Follow-up Fix: Cached Actions and Note Auto-Save During Import

- Cached OPML articles now support local read and favorite toggles while the backend is still processing the remaining feeds.
- Local cached actions update the selected article, article list item, per-feed cache, and unread/starred aggregate counters without waiting on backend PATCH requests.
- Cached article selection marks the article read locally, preventing backend connection errors when users read imported articles during OPML upload.
- Note auto-save skips unchanged content even when article switches pass an explicit old article id.
- Note loading failures during transient backend unavailability are handled quietly, and deleted feed articles are removed from the reader detail cache so deleting a feed does not show "save previous note failed" for removed articles.

### Verification

```bash
npm.cmd run build --prefix frontend
```

Result: build passed. Vite/Rollup still reports existing third-party annotation and chunk-size warnings.
