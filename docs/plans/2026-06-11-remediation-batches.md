# Remediation Plan — Batched Fix Prompts

**Created:** 2026-06-11
**Source:** Full-codebase review (Claude, 2026-06-11). Findings verified against a passing baseline:
backend `pytest` = 64 passed, frontend `tsc --noEmit` = clean, `npm run lint` = broken (no ESLint config).

Each batch below is a self-contained prompt you can paste into a fresh Claude Code session.
Batches are ordered by priority and dependency — run them in order. One batch per branch/PR.

---

## Standard preamble (prepend to every batch prompt)

```
Read CLAUDE.md and STATE.md before doing anything. Follow the Karpathy guidelines in
CLAUDE.md strictly: state assumptions before coding, minimum code that solves the
problem, surgical changes only (do not refactor or "improve" code outside this batch's
scope), and verify every fix with a concrete check.

Workflow rules:
- Work on a new branch named for this batch (e.g. fix/batch-1-auth).
- One atomic commit per task, format: {type}({scope}): {description}.
- Run the backend suite (cd backend; venv\Scripts\python -m pytest) and the frontend
  type check (cd frontend; npx tsc --noEmit) before claiming any task done. Both must
  pass. Where a task says "write a failing test first", do that — red, then green.
- When the batch is complete, append a check-in entry to STATE.md (format is defined
  at the top of that file) listing each task completed, commits, and verification output.
- If you hit a genuine ambiguity, stop and ask rather than guessing.
```

---

## Between batches: merge protocol

Batches are sequential and assume the previous batch is already on master (later
batches touch the same files — routes.py, endpoints.ts, STATE.md). Do not run two
batches in parallel.

After a batch session finishes its STATE.md check-in:

1. Push the branch and open a PR (push/gh must run from PowerShell — see CLAUDE.md
   environment notes). Optionally run /code-review on the branch first.
2. Merge to master and delete the branch. (Local merge without a PR is fine for solo
   work — just say "merge this branch into master locally".)
3. Only then start the next batch, in a fresh session, branched from master.

The merge is what publishes STATE.md progress — until a batch branch is merged, the
tracker on master is stale and the next session will not see the completed work.

**Why first:** unauthenticated callers can currently delete research data and trigger scraping jobs.

```
TASK 1 — Enforce auth on all non-public endpoints.
In backend/app/api/routes.py, the only endpoints that should be reachable without a
token are POST /auth/register, POST /auth/login, and GET /health (in main.py).
Every other endpoint must take current_user: User = Depends(get_current_user).
Currently missing it (verify each, then fix):
  - GET /samples/{id}, DELETE /samples/{id}, GET /samples/{id}/analysis
  - POST /themes/, GET /themes/{id}/samples
  - POST /locations/, GET /locations/{id}/samples
  - POST /citations/, GET /citations/sample/{id}
  - ALL of jobs_router: GET /jobs/, POST /jobs/start, GET /jobs/stats,
    GET /jobs/{id}/status
Write the failing tests FIRST in backend/tests/test_api.py: for each endpoint above,
assert an unauthenticated request returns 401. Then add the dependency and make them
pass. Do not change any endpoint's behaviour beyond adding the auth dependency.

TASK 2 — Remove credential leakage from logs.
- backend/app/core/security.py: delete every print() statement (they log token
  prefixes and user emails on every request). Do NOT replace them with logger calls —
  the auth path needs no per-request logging.
- frontend/src/api/client.ts: remove the console.log lines in the request interceptor
  that print the token prefix.

TASK 3 — Fail fast on default SECRET_KEY.
In backend/app/core/config.py, add a model validator (Pydantic v2 style) that raises
at startup if SECRET_KEY is one of the known placeholder values
("change-me-in-production-use-a-long-random-string",
"change-this-to-a-random-secret-key") AND an env var THERMOCULTURE_ENV == "production".
Default behaviour in dev must be unchanged. Add one test.

ACCEPTANCE: full pytest passes including the new 401 tests; grep confirms no print(
in backend/app/core/security.py and no console.log in frontend/src/api/client.ts.
```

---

## Batch 2 — Make the NLP pipeline real (the core architectural fix)

**Why:** `AnalysisEngine` is only ever called from tests. Collected articles get no sentiment,
classification, or themes — all analytics reflect seed data only. The Celery layer that was
supposed to do this is dead code referencing modules that don't exist.

```
TASK 1 — Delete the dead Celery layer.
- Delete backend/app/services/celery_app.py and backend/tests/test_celery_tasks.py.
- Remove the celery_worker and celery_beat services from docker-compose.yml.
- Remove celery from backend/requirements.txt.
The module imports collectors.arxiv_collector, collectors.web_collector and
app.nlp.analyzer — none of which exist — and its scheduled_collection dispatches
collector_type values ("NEWS"/"REDDIT") its own task rejects. It cannot work and the
API already uses FastAPI BackgroundTasks instead. Confirm nothing else imports it
(grep for celery_app) before deleting.

TASK 2 — Trigger analysis at ingestion.
In backend/collectors/pipeline.py, after new samples are flushed in ingest_items(),
run nlp.analyzer.AnalysisEngine.analyze_sample(sample.id, sample.content, db) for each
new sample. Instantiate AnalysisEngine once per IngestPipeline instance (its
constructors are expensive — vectorisers, VADER), not per sample. Wrap each sample's
analysis in try/except so one bad sample logs and continues rather than failing the
whole ingest. Return the analysis count in the stats dict ({"analyzed": N}).
Write a test first: ingest two CollectedItems via IngestPipeline with an in-memory DB
and assert SentimentAnalysis and DiscourseClassification rows exist for both samples
afterwards, and at least one sample_themes link exists.

TASK 3 — Stop classifying empty/no-signal text as PRACTICAL_ADAPTATION.
In backend/nlp/classifier.py, when raw scores are all zero (or text is empty),
classify() must return classification_type=None with confidence 0.0, and callers
(AnalysisEngine._store_classification) must skip persisting a record in that case.
Also remove the duplicated ("rally", 1.1) entry. Update/add tests in test_nlp.py.

TASK 4 — Decide the fate of GeoExtractor output.
AnalysisEngine._store_locations is a no-op and location resolution already happens in
IngestPipeline. Per simplicity-first: remove the geo_extractor field, the
extract_locations call, and _store_locations from analyzer.py entirely. Keep
nlp/geographic.py only if anything else imports it — if nothing does after this
change, note it in STATE.md as dead (Batch 6 deletes it); do not delete it here.

ACCEPTANCE: pytest passes; the new ingestion test proves collected samples get
sentiment + classification + themes; grep finds no references to celery anywhere
outside docs.
```

---

## Batch 3 — Collection correctness

```
TASK 1 — Validate collector type before creating a job.
POST /jobs/start currently creates a PENDING job and lets it fail in the background
when the source has no usable collector (any NEWS source that isn't BBC/Guardian,
plus FORUM/SOCIAL_MEDIA/MANUAL). In backend/collectors/scheduler.py give
_resolve_collector_type a strict mode: return None when no concrete collector
matches. In routes.py start_collection_job, return 422 with a clear message
("No collector available for this source") before creating the job. Test first:
POST /jobs/start for a MANUAL source must 422 and create no CollectionJob row.

TASK 2 — Deduplicate across sources with a real constraint.
Move the content hash out of raw_metadata JSON into a dedicated indexed column:
DiscourseSample.content_hash (String(32), nullable=True, unique=True, index=True).
Update IngestPipeline to set it, keep writing it into raw_metadata for backward
compatibility with existing rows, and change _load_existing_hashes to query the
column WITHOUT the source_id filter (the same article ingested under two sources is
a duplicate). Because dev uses create_all (no Alembic), note in STATE.md that dev
databases need recreating or a manual ALTER. Update the dedup tests.

TASK 3 — Simplify _batch_insert.
The IntegrityError fallback in backend/collectors/pipeline.py is unreachable today
and its rollback() would discard the job's RUNNING update on the shared session.
After Task 2 the unique constraint makes IntegrityError real, so: flush per batch,
and on IntegrityError fall back to per-row flush with db.expunge(sample) on conflict
— but never call db.rollback() inside the pipeline (the caller owns the
transaction). Use a SAVEPOINT (db.begin_nested()) per row in the fallback path so a
conflict rolls back only that row. Keep it under ~30 lines.

TASK 4 — Remove the sleep hack and tighten the background runner.
In backend/app/api/routes.py _run_collection_in_background: delete
`await asyncio.sleep(1)  # Ensure DB visibility` (the route commits before the task
is scheduled; the sleep is cargo cult). Remove the "DEBUG:" prefixes from all logger
calls in this function and start_collection_job, keeping the genuinely useful
messages (job started / items collected / job failed) at info level.

TASK 5 — Fail fast on missing Reddit credentials.
RedditCollector currently warns at construction and fails mid-job. Raise a
ValueError in collect() (not __init__) when client id/secret are empty, so the job
fails immediately with a clear error_message.

ACCEPTANCE: pytest passes; new tests cover the 422 path and cross-source dedup;
manual check: starting a job for a MANUAL source returns 422.
```

---

## Batch 4 — API correctness and contract consistency

```
TASK 1 — Fix duplicate/skipped rows when sorting by sentiment.
In list_samples (backend/app/api/routes.py), sorting by sentiment outer-joins
SentimentAnalysis, producing one row per analysis record while pagination applies to
the joined rowset. Replace the join with ordering by a scalar correlated subquery
(latest analysis per sample: ORDER BY analyzed_at DESC LIMIT 1) so the result set
stays one row per sample. Test first: create one sample with two SentimentAnalysis
rows plus two other samples; request page_size=10 sorted by sentiment; assert 3
items, no duplicates.

TASK 2 — Whitelist sort_by.
Replace the getattr(DiscourseSample, params.sort_by...) logic with an explicit dict
{"collected_at": ..., "published_at": ..., "title": ...}. Unknown values fall back
to collected_at. Test: ?sort_by=themes returns 200 sorted by collected_at, not 500.

TASK 3 — Remove the duplicate theme-frequency endpoint.
/analysis/theme-frequency (outer join) and /analysis/theme-frequencies (inner join)
disagree on zero-count themes. Keep ONE: /analysis/theme-frequencies with the OUTER
join behaviour (zero-count themes included — the frontend bar chart should show
them). Delete the other route. Update the frontend if its path changes (it already
calls /analysis/theme-frequencies, so only the join behaviour moves).

TASK 4 — Single source of truth for citations.
Frontend SampleDetail.tsx generates its own citation text that differs from the
backend's. Change the frontend: when the citation panel opens or format changes,
preview by calling POST /citations is wrong (it persists) — instead, extract the
backend's _generate_citation_text into a pure function and expose
GET /citations/preview?sample_id=&format= returning {citation_text}. Frontend
deletes generateCitationText and fetches the preview. While there, update the MLA
template to MLA 9 (Author. "Title." Source, Day Month Year, URL.) and Chicago to
include the source name. Backend tests for all three formats.

TASK 5 — Order sample analysis results.
get_sample_analysis returns sentiments/classifications in arbitrary order and the
frontend takes [0] as "latest". Add order_by(analyzed_at.desc()) /
(classified_at.desc()) — use explicit queries rather than relying on selectinload
ordering, or set order_by on the relationships in models.py.

TASK 6 — Normalize API paths in the frontend client.
In frontend/src/api/endpoints.ts, several URLs have trailing slashes the backend
routes lack (/samples/${id}/, /samples/${id}/analysis/, /jobs/${id}/status/,
/citations/sample/${id}/) and /citations lacks the slash its route has. They only
work via 307 redirects. Make every path match the backend route exactly. Verify by
grepping routes.py for each path.

TASK 7 — Consistent count queries.
dashboard_stats executes bare func.count(...) without select() in two places. Wrap
them in select() like every other query in the file. Behaviour identical; add no
new code paths.

ACCEPTANCE: pytest passes with the new sort/citation tests; tsc passes; the
citation preview shown in the UI is byte-identical to what "Save Citation" stores.
```

---

## Batch 5 — Frontend: broken features and dishonest charts

```
TASK 1 — Quote Library: build the missing backend.
frontend calls /api/v1/quotes/ (fetchSavedQuotes/saveQuote/deleteQuote in
endpoints.ts) but no such router exists, so "Add to Quote Library" silently fails
and the library is always empty. Implement the minimal backend: a SavedQuote model
(id, user_id FK, sample_id FK, text, created_at), schemas, and a quotes_router with
GET /quotes/ (current user's quotes, joined with sample title + source name to fill
the SavedQuote TS interface: source_name, author, citation — generate citation_text
via the Batch 4 helper, APA), POST /quotes/, DELETE /quotes/{id} (owner-only). All
require auth. Tests for all three. Then fix the frontend: add onError toasts to
quoteMut (SampleDetail) and delMut (ResearchWorkspace). Do not add features beyond
what the existing UI uses.

TASK 2 — Fix the broken /workspace links.
SampleDetail.tsx links to /workspace twice; the route is /research. Fix both.
Grep the whole frontend for "/workspace" to be sure.

TASK 3 — Delete the fabricated charts.
In AnalysisInsights.tsx:
  a) "Theme Composition Over Time" multiplies real counts by Math.random() — delete
     the chart and the areaData computation entirely. Do not replace it with
     anything in this batch.
  b) "Classification Over Time" scales today's global percentages across history —
     delete it too.
  c) fetchTimeline('weekly') is rejected by the backend (it accepts 'week') — after
     (b) this call is gone; verify no caller passes 'weekly'.
  d) "Example Quotes by Type" shows 5 recent samples regardless of type — rename
     the heading to "Recent Samples" so it stops lying, or delete the panel.
This is a research tool; charts must only render data that exists.

TASK 4 — Fix "+ New" note creation.
ResearchWorkspace creates notes with content: '' but the backend requires
min_length=1. Relax the backend instead of faking content: change
ResearchNoteCreate.content to allow empty string (min_length=0 / plain str).
An empty new note is legitimate. Add onError toast to createMut and saveMut.

TASK 5 — Honest export buttons.
Settings.tsx offers "Export CSV" for notes but /export/notes only returns JSON
(the file downloads as JSON named .csv). Remove the notes CSV button. Remove
'bibtex' from the ExportFormat type (backend rejects it).

TASK 6 — Surface job errors and fix the provenance label.
- CollectionDashboard: failed jobs show a FAILED badge but error_message is never
  rendered. Add it (title attribute on the badge or an expandable row — smallest
  change wins). Also surface the backend's detail string in the start-collection
  onError toast (err.response?.data?.detail) instead of a generic message.
- TrendsPage ProvenanceBar says "articles collected this month" but CollectionStats
  counts jobs. Change the label to "collection runs this month".

TASK 7 — Add logout.
useAuth.logout() exists but nothing calls it. Replace the dead "U" placeholder
button in Layout.tsx with a minimal menu (user email + Logout) that calls logout()
and navigates to /login. No avatar libraries, no dropdown framework.

TASK 8 — Type/contract fixes.
- types/index.ts: make RegisterRequest.full_name required (backend requires it).
- client.ts 401 handler: it both dispatches the auth-unauthorized event AND does a
  hard window.location.href redirect, defeating the SPA state machinery. Keep the
  event dispatch + let AuthProvider clear state; perform navigation via the
  redirect only when not already on /login. Simplify to one mechanism (the hard
  redirect is acceptable — then delete the event/listener pair instead; pick ONE).

ACCEPTANCE: tsc passes; quotes round-trip works end to end (save on SampleDetail,
appears in ResearchWorkspace, delete works) via pytest API tests + manual check;
grep finds no Math.random() in AnalysisInsights.tsx; "+ New" creates a note.
```

---

## Batch 6 — Dead code and repo hygiene

```
TASK 1 — Delete dead frontend code (verify each is unimported first, then delete):
  - src/hooks/useFilters.ts (220 lines, never imported)
  - src/components/FilterBar.tsx (376 lines; DiscourseBrowser has its own inline one)
  - src/components/Pagination.tsx (DiscourseBrowser paginates inline)
  - src/components/SampleCard.tsx (Dashboard and DiscourseBrowser define their own)
  - then remove date-fns from package.json if SampleCard was its only consumer.

TASK 2 — Delete dead backend code:
  - backend/nlp/wordcloud_data.py and its tests (no endpoint uses it) — confirm via
    grep that only tests import it.
  - backend/nlp/geographic.py IF Batch 2 Task 4 left it orphaned (grep first).
  - _build_theme_vectors in theme_extractor.py; unused imports (quote_plus in
    news_collector, CountVectorizer in theme_extractor, os in reddit_collector).
  - The try/except ImportError blocks around model imports in nlp/analyzer.py —
    import normally at module top.
  - The _LogAdapter class in collectors/scheduler.py: loguru is a hard dependency;
    use it directly and move the model imports to the top of the file.

TASK 3 — Remove committed session debris:
  git rm: backend/check_bbc_keywords.py, check_recent_articles.py, check_status.py,
  check_stuck_jobs.py, check_users.py, cleanup_jobs.py, clear_stale_jobs.py,
  clear_stuck_jobs.py, kill_stuck_job.py, verify_bbc_pagination.py,
  verify_collection.py, verify_guardian_volume.py, test_bg_minimal.py,
  backend/test.db, and cleanup_leaked_data.py at the repo root.
  Delete untracked junk: nul (root and backend — use `del \\?\C:\...\nul` syntax on
  Windows), backend/bg_test.log, backend/test_background_logic.py, test.db (root),
  backend/thermoculture.db stays untracked (verify it is not tracked).
  Add to .gitignore: *.db, *.log, nul.

TASK 4 — Trim dependencies:
  backend/requirements.txt: remove praw (only asyncpraw is used), spacy, pandas,
  passlib — and ADD bcrypt explicitly (it currently arrives transitively via
  passlib[bcrypt]; removing passlib without adding bcrypt breaks auth).
  backend/Dockerfile: remove the spacy model download line.
  Verify: fresh-venv smoke test or at minimum grep that nothing imports the removed
  packages, then run pytest.

TASK 5 — One gazetteer, one stop-word list:
  collectors/locations.py and nlp/geographic.py (if still present) hold two
  conflicting UK gazetteers; theme_extractor.py and wordcloud_data.py (if still
  present) hold two CLIMATE_STOP_WORDS lists. After Batch 2/6 deletions there
  should be exactly one of each; if both gazetteers survived, merge coordinates
  into collectors/locations.py as the single source and delete the other.

TASK 6 — Strip remaining debug logging:
  Remove every console.log from frontend/src (useAuth.tsx logs on every render,
  ProtectedRoute.tsx, client.ts remnants). Remove remaining "DEBUG:" logger
  prefixes in backend (grep 'DEBUG:'). Keep real log lines.

ACCEPTANCE: pytest + tsc pass after every deletion commit; grep proves: no
console.log under frontend/src, no 'DEBUG:' in backend, none of the deleted
modules referenced anywhere.
```

---

## Batch 7 — Tooling, tests, and docs honesty

```
TASK 1 — Make lint real.
Frontend has a lint script and CLAUDE.md claims "ESLint max-warnings: 0", but there
is no ESLint config. Add a flat-config (eslint.config.js) for TS + React hooks
matching the installed eslint major version (check package.json first; upgrade to
ESLint 9 + typescript-eslint if needed — check current versions per the Version &
SDK Policy in CLAUDE.md). Rules: recommended TS + react-hooks, no-console: error.
Fix all violations until `npm run lint` exits 0. Add no-console exceptions only
where genuinely warranted (none expected after Batch 6).

TASK 2 — Negative-path test expansion (backend).
Add tests for: filter combinations on /samples (date range + theme + search
together), 409 on double job start, 404s with valid auth, pagination bounds
(page beyond total returns empty items, not error), export with filters,
notes user-isolation (user A cannot read/update/delete user B's note — write these
as failing tests first and fix if they fail).

TASK 3 — README accuracy pass.
README currently claims: PostgreSQL (default is SQLite; compose db service is
unreachable without a driver), spaCy (unused), nginx (absent), automated
scheduling (deleted with Celery), Python 3.11+ (venv is 3.10). Rewrite the Tech
Stack, Quick Start, and feature list to describe what exists. Quick Start should
lead with run_app.bat / manual uvicorn+vite, with Docker as secondary IF Task 4
keeps it. Remove the hardcoded seed credentials from the README; instead say the
seed script prints them.

TASK 4 — docker-compose: fix or trim (decision recorded in STATE.md).
Default decision: trim to what works — remove the db (Postgres) and redis services
(celery is already gone; SQLite is the database). Keep backend + frontend services,
fix the backend healthcheck (curl is not in python:3.11-slim — use python -c
urllib), and verify `docker compose up --build` actually serves both. If you keep
Postgres instead, you must add asyncpg to requirements and test against it — only
do this if the user asks.

TASK 5 — Alembic: commit or delete (decision recorded in STATE.md).
Default decision: delete backend/migrations/ and alembic.ini (create_all is the
working mechanism, alembic is not even in requirements.txt and has zero versions).
Note in README that schema changes require recreating the dev DB.

ACCEPTANCE: npm run lint exits 0; pytest passes with new tests; docker compose up
--build works for the trimmed stack; README contains no claim you cannot
demonstrate.
```

---

## Batch 8 — Hardening and polish (optional, lower priority)

```
TASK 1 — Timezone consistency. Decide and enforce one convention: store naive UTC
(strip tzinfo in _utcnow and all datetime.now(timezone.utc) call sites) since
SQLite stores naive strings and strftime grouping assumes it. Add a helper
utcnow() in one module and use it everywhere. Test the date_to end-of-day filter
boundary in list_samples.

TASK 2 — Indexes. Add index=True to DiscourseSample.source_id, location_id,
collected_at; SentimentAnalysis.sample_id; DiscourseClassification.sample_id;
CollectionJob.source_id, status. Dev DBs need recreating (create_all only).

TASK 3 — Login throttling. Add simple in-process rate limiting on /auth/login
(e.g. slowapi, 5/minute/IP) — only if the app will ever be exposed beyond
localhost; otherwise record "accepted risk: local research tool" in STATE.md.

TASK 4 — Settings "Custom Keywords" is decorative (saved to localStorage, read by
nothing). Default: remove the section. Alternative (only if asked): pass keywords
into POST /jobs/start and through to collector.collect(keywords=...).

TASK 5 — Dark mode decision. dark: classes exist on nearly every element but
tailwind.config.js sets no darkMode key and Layout's shell is light-only. Either
set darkMode: 'class' + a toggle, or strip the dark: classes. Default: set
darkMode: 'media' explicitly and fix Layout's shell backgrounds — smallest change
that makes the existing classes coherent.

TASK 6 — Methodology note. The sentiment lexicon conflates topic with sentiment
(a neutral news report about flooding scores negative). Document this limitation
in README's research notes section; optionally gate the climate adjustment to
first-person/opinion text later. Also note the classifier's keyword approach and
the theme threshold (0.01 cosine similarity attaches near-any theme — consider
raising to 0.05 and eyeballing seed-data tagging before/after).

TASK 7 — Minor UI nits: CollectionDashboard toggle has duplicate transform
(Tailwind classes + inline style — keep the inline style, drop the dead classes);
"Active Sources" heading shows all sources (rename to "Sources").
```

---

## Issue → batch coverage map

| Review finding | Batch |
|---|---|
| NLP never runs on collected data | 2 |
| Celery dead-on-arrival (+compose services) | 2 |
| Missing auth on mutating/job endpoints | 1 |
| Token/email logging (print/console.log) | 1 |
| Default SECRET_KEY accepted silently | 1 |
| Fabricated charts (Math.random, scaled percentages) | 5 |
| fetchTimeline('weekly') 422 | 5 |
| /quotes endpoints don't exist | 5 |
| /workspace broken links | 5 |
| "+ New" note 422 | 5 |
| Sentiment sort duplicates/pagination skew | 4 |
| sort_by getattr injection/500 | 4 |
| Duplicate theme-frequency endpoints (divergent joins) | 4 |
| Citation duplication + MLA 7 | 4 |
| sentiments[0] unordered | 4 |
| Trailing-slash 307s | 4 |
| Bare func.count execution | 4 |
| NEWS source collector resolution fails post-creation | 3 |
| Per-source dedup / no unique constraint | 3 |
| _batch_insert incoherent rollback | 3 |
| asyncio.sleep(1) hack + DEBUG logs | 3 |
| Reddit creds warn-then-fail | 3 |
| Empty text → PRACTICAL_ADAPTATION; duplicate "rally" | 2 |
| GeoExtractor output discarded (_store_locations no-op) | 2 (decide) / 6 (delete) |
| Dead frontend files (useFilters, FilterBar, Pagination, SampleCard) | 6 |
| Dead backend (wordcloud_data, _LogAdapter, ImportError guards, unused imports) | 6 |
| Debug scripts, test.db, nul, bg_test.log committed | 6 |
| Unused deps (praw, spacy, pandas, passlib) + missing explicit bcrypt | 6 |
| Two gazetteers, two stop-word lists | 6 |
| console.log render logging | 6 |
| No ESLint config despite stated convention | 7 |
| Happy-path-only tests; no user-isolation tests | 7 (+1) |
| README claims (Postgres/spaCy/nginx/scheduling/credentials) | 7 |
| docker-compose unreachable db / celery_beat network+volume | 7 (+2) |
| Alembic scaffolding without migrations or dependency | 7 |
| Naive/aware datetime mixing | 8 |
| Missing FK indexes | 8 |
| No login rate limiting | 8 |
| Decorative Settings keywords | 8 |
| Incoherent dark-mode classes | 8 |
| Sentiment topic-bias methodology | 8 |
| Notes CSV button downloads JSON / bibtex format | 5 |
| Job error_message never shown / generic toasts | 5 |
| "Jobs" mislabeled as "articles" | 5 |
| No logout button | 5 |
| RegisterRequest.full_name optional mismatch | 5 |
| 401 dual redirect mechanism | 5 |
