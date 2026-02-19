# Design: Collection Pipeline, Tags & Trend Dashboard

**Date**: 2026-02-18
**Status**: Approved
**Branches**: `fix/foundation` → `feat/tags-and-trends` + `feat/collection-pipeline`

---

## Overview

Three sequential branches to add automated article collection (BBC News + Guardian),
surface existing theme tags throughout the UI, and add a live trend dashboard for
researchers. A foundation branch fixes confirmed pre-existing bugs before either
feature branch begins.

## Sequencing

```
master
  └── fix/foundation      (merge + verify first)
        ├── feat/tags-and-trends      (branch off fixed master)
        └── feat/collection-pipeline  (branch off fixed master, parallel)
```

Both feature branches are independent and can be developed in parallel once
`fix/foundation` is merged and verified.

---

## Branch 0: `fix/foundation`

Fixes all confirmed pre-existing bugs. No new features. Must pass verification
gate before either feature branch begins.

### Celery task layer (`backend/app/services/celery_app.py`)

Three runtime-fatal import errors confirmed in `scheduled_collection`:

| Bug | Current (broken) | Fix |
|-----|-----------------|-----|
| Source model import | `from app.models.source import Source` | `from app.models.models import Source` |
| Session import | `from app.db.session import get_sync_session` | Replace with `asyncio.run()` wrapper pattern |
| Field access | `source.collector_type` | `source.source_type` |

All Celery task bodies that call async methods must use a consistent
`asyncio.run()` wrapper — establish this as the project pattern here so
new collectors follow it automatically.

### NLP aggregation layer (`backend/nlp/analyzer.py`)

`AnalysisEngine.get_aggregated_insights()` imports three non-existent model
aliases. The `ImportError` is silently caught and returns empty dicts, meaning
every analysis endpoint returns empty data without surfacing an error.

| Non-existent alias | Actual object |
|-------------------|---------------|
| `SampleTheme` | `sample_themes` (SQLAlchemy `Table` object in `app.models.models`) |
| `SampleLocation` | Does not exist — remove or rewrite query |
| `DataSample` | Does not exist — use `DiscourseSample` |

Rewrite the aggregation queries to use the actual ORM objects.

### API authentication (`backend/app/api/routes.py`)

The following endpoints are missing `Depends(get_current_user)` and are
publicly accessible without a token:

- All `/api/v1/analysis/*` endpoints (theme-frequency, geographic-distribution,
  discourse-types, trending-themes, timeline, sentiment-distribution,
  map-locations, theme-frequencies, theme-co-occurrence)
- `GET /api/v1/export/samples` (bulk export)
- `POST /api/v1/sources/` (source creation)
- `DELETE /api/v1/sources/{source_id}` (source deletion)
- `POST /api/v1/samples/` (sample creation)

Add `current_user: User = Depends(get_current_user)` to each route.

### Infrastructure (`docker-compose.yml`)

A `celery_beat` service is absent. The 6-hour beat schedule exists in code
but nothing executes it in the containerised deployment.

Add a `celery_beat` service:
```yaml
celery_beat:
  build: ./backend
  command: celery -A app.services.celery_app beat --loglevel=info --schedule=/app/celerybeat-schedule
  volumes:
    - celery_beat_data:/app
  depends_on:
    - redis
    - db
  env_file: .env
```

### Secret hygiene

Verify `.env` is listed in `.gitignore` and is not tracked by git before any
API keys are added. If `.env` has ever been committed, remove it from git
history. Add `GUARDIAN_API_KEY=` as a placeholder to `.env.example`.

### Verification gate

Before merging `fix/foundation`, confirm all of the following:

- [ ] `celery -A app.services.celery_app inspect registered` lists all three tasks without ImportError
- [ ] `scheduled_collection` task completes without exception when no active sources exist
- [ ] `GET /api/v1/analysis/theme-frequency` returns populated data (not empty dict/list) with seed data loaded
- [ ] `GET /api/v1/analysis/trending-themes` returns populated data
- [ ] All protected endpoints return `401 Unauthorized` when called without a token
- [ ] `celery_beat` container starts and logs the beat schedule without error
- [ ] `.env` is confirmed absent from `git ls-files`

---

## Branch 1: `feat/tags-and-trends`

Branches off merged `fix/foundation`. Primarily frontend work. Low risk.

### Tag surfacing on samples

**Tag pills above sample list:**
- Display the top 15 themes by article count as clickable pills above the sample list
- A "show all" toggle expands to the full theme list
- Clicking a pill sets `theme_ids` in the filter params (existing filter param, already supported by the backend)
- Active (selected) pills are visually highlighted

**NLP vs manual tag distinction:**
- NLP auto-assigned tags rendered with a small bot icon (e.g. `⚙` or a small SVG)
- Any future manually assigned tags rendered plain
- This distinction must be present from day one so researchers can identify label provenance

**Tag chips on cards and detail:**
- `SampleCard` shows up to 3 theme chips inline, truncated with a count if more
- `SampleDetail` shows all theme chips with full names

### Trends page (`/trends`)

New page added to the frontend router. Layout follows a strict reading order:

1. **Headline insight card** (top, full width) — fastest-rising theme this month,
   pulled from `/api/v1/analysis/trending-themes`. Single large number + label.
2. **Trending themes bar chart** — top 10 themes by trend score
3. **Sentiment over time line chart** — from `/api/v1/analysis/sentiment-over-time`
4. **Discourse type breakdown** — from `/api/v1/analysis/discourse-types`
5. **Recent articles feed** (bottom, paginated) — last 20 collected samples with
   their theme chips and sentiment label

**Provenance bar** present on every chart section:
> "Based on N articles from M sources · Last collected [timestamp]"

Timestamp drawn from the most recent completed `CollectionJob.completed_at`.

**Refresh:** Manual refresh button only. Data fetches on page load.
React Query default `staleTime` handles subsequent navigations.
No polling interval — collection runs every 6 hours, not every 30 seconds.

---

## Branch 2: `feat/collection-pipeline`

Branches off merged `fix/foundation`. Backend-heavy, higher operational risk.

### `GuardianCollector` (`backend/collectors/guardian_collector.py`)

Uses the [Guardian Open Platform API](https://open-platform.theguardian.com/)
which is explicitly licensed for non-commercial and research use.

- Searches by each keyword in `BaseCollector.CLIMATE_KEYWORDS`
- Returns structured article data (title, body, author, published date, URL)
- API key: `GUARDIAN_API_KEY` env var (add to `.env.example` as placeholder)
- Development: Guardian's `test` key works with reduced rate limits
- Exponential backoff on retries: 2s → 4s → 8s (not flat 60s)
- Inherits from `BaseCollector`, emits `CollectedItem` objects

### `BBCNewsCollector` (`backend/collectors/bbc_collector.py`)

BBC has no public news API. Scraping approach with explicit safeguards:

- **robots.txt check first**: fetch and parse `https://www.bbc.co.uk/robots.txt`
  before any search requests. If the target path is disallowed, log a `WARNING`
  and return an empty list — no silent violations.
- **Zero-result health check**: if a collection run returns 0 items (whether from
  a block, HTML structure change, or empty results), set `CollectionJob.status`
  to `FAILED` with message `"Zero items collected — possible site structure change
  or block"`. Do not mark as `COMPLETED`.
- Scrapes BBC News search results for each climate keyword
- Extracts title, content snippet, URL, publish date via BeautifulSoup
- Respects `rate_limit_seconds` (default 3s for BBC, more conservative than default)
- **Maintenance risk noted in module docstring**: BBC HTML structure changes
  without notice. This collector requires manual verification after any BBC
  site redesign.

### NLP pipeline wiring

After `IngestPipeline.ingest_items()` returns, dispatch `analyze_sample_task`
for each new sample ID:

```python
stats = await pipeline.ingest_items(items, source_id, db)
# Dispatch analysis for each new sample
for sample_id in stats["new_sample_ids"]:
    analyze_sample_task.delay(str(sample_id))
```

`IngestPipeline.ingest_items()` must be updated to return new sample IDs in
addition to the existing counts dict.

### Database migration

Add a functional index for content-hash deduplication performance:

```sql
CREATE INDEX ix_discourse_samples_content_hash
ON discourse_samples (source_id, (raw_metadata->>'content_hash'));
```

As corpus grows, the current full-table scan per collection run will degrade.

### Out of scope for this branch

- Reddit collector — no API key, no user demand. Add as a named future milestone.
- Email/push notifications
- AI-generated digest summaries (Phase D, future)

### Operational notes

- `celery_beat` service (added in `fix/foundation`) handles the 6-hour schedule
- Manual UI-triggered collection jobs use `BackgroundTasks` and create a
  `CollectionJob` row; the beat schedule checks for a RUNNING job for the same
  source before dispatching to avoid duplicates
- Celery retry policy: exponential backoff, max 3 retries, no flat countdown

---

## What This Does Not Include

- AI-generated trend summaries (identified as Phase D, post-launch)
- Reddit integration (deferred until API credentials are available)
- Email/push alerts for theme spikes
- Manual tag assignment by researchers (auto-tags only for now)

---

## Board Review Summary

Reviewed 2026-02-18 by a 5-director board. Overall: **APPROVE WITH CONDITIONS (6.6/10)**.
All conditions have been incorporated into this design.

| Director | Verdict | Score |
|----------|---------|-------|
| Chief Architect | CONCERNS | 6/10 |
| Chief Product Officer | APPROVE | 7/10 |
| Chief Security Officer | CONCERNS | 6/10 |
| Chief Operations Officer | APPROVE | 7/10 |
| Chief Experience Officer | APPROVE | 7/10 |
