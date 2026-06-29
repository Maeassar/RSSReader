# PR Description — fix/week17-token-stats-persist-on-feed-delete

## Summary

Fix token usage statistics being wiped when feeds are deleted.

Closes #44

## Motivation

When all feeds were removed, the `ai_results` table was cascade-deleted alongside the `entries` table due to a `ON DELETE CASCADE` foreign key constraint. This caused all historical LLM token usage records to be permanently lost. After re-adding feeds, sync logs recovered normally but token stats remained at zero with no way to restore them.

## Changes

- `backend/schema.sql` — changed `ai_results.entry_id` foreign key from `ON DELETE CASCADE` to `ON DELETE SET NULL`; relaxed `entry_id` from `NOT NULL` to nullable
- `backend/app/database.py` — added migration in `_migrate_ai_tables()` that detects the old CASCADE constraint on existing databases and rebuilds the table via rename → recreate → copy → drop, preserving all existing records
- `update_docs/Week17_fwunai.md` — added weekly update doc
- `docs/AI_COLLABORATION.md` — added collaboration log entry

## Testing

- Ran `initialize_database()` on an existing database; confirmed new table schema contains `ON DELETE SET NULL` and all prior records are intact
- Manually deleted all feeds and verified token stats data is preserved with `entry_id` set to NULL
- Stats page aggregations (total calls, input/output tokens, time series) remain correct for records with NULL `entry_id`

## Notes

Records with `entry_id = NULL` retain all statistical dimensions (provider, model, task_type, timestamps) and are fully counted in all existing stat queries. The link back to the specific article is lost, but this does not affect any current feature.
