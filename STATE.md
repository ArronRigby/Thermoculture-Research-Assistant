# STATE.md — Living Project State

Read this at the start of every session. Update it at every check-in (end of a batch,
end of a work session, or before raising a PR — whichever comes first).

## How to check in

Append an entry to the **Check-in Log** (newest first) using this format, and tick any
completed batches in the tracker:

```markdown
### [NNNN] YYYY-MM-DD — <branch> — <short title>
**Batch/scope:** <batch number or "ad-hoc">
**Work completed:**
- <task>: <what changed> (<commit hash>)
**Verification:** pytest <result> | tsc <result> | lint <result/not-applicable>
**Decisions made:** <any defaults exercised or deviations from the plan, with why>
**Deferred/noticed:** <dead code or issues spotted but NOT touched (per surgical-changes rule)>
```

Rules: never delete old entries; never claim verification you didn't run; if a batch is
partially done, say exactly which tasks remain.

---

## Project snapshot

- **What it is:** FastAPI + SQLite backend, React 18/TS/Vite frontend. Collects UK climate
  discourse (BBC/Guardian scraping, Reddit via asyncpraw), NLP analysis (VADER sentiment,
  keyword classifier, TF-IDF themes), research notes/citations/export.
- **Dev path:** `run_app.bat` → uvicorn :8000 + vite :5173. Docker compose not currently viable (see Batch 7).
- **Verified baseline (2026-06-11):** backend `pytest` = **64 passed**;
  frontend `tsc --noEmit` = **clean**; `npm run lint` = **broken** (no ESLint config).
- **Guidelines:** Karpathy coding guidelines + verification commands live in `CLAUDE.md`.
- **Full findings:** 2026-06-11 review; remediation prompts in
  `docs/plans/2026-06-11-remediation-batches.md` (includes an issue→batch coverage map).

## Remediation batch tracker

Work in order. One branch + PR per batch. Tick only when the batch's acceptance criteria
passed and a check-in entry exists.

- [x] **Batch 1 — Security:** auth on all non-public endpoints (incl. DELETE /samples,
      POST /jobs/start), 401 tests first, remove token/email logging, fail-fast SECRET_KEY.
- [x] **Batch 2 — Make NLP real:** delete dead Celery layer (+compose services, dep),
      trigger `AnalysisEngine` from `IngestPipeline.ingest_items`, no-signal text returns
      no classification, remove discarded GeoExtractor wiring.
- [x] **Batch 3 — Collection correctness:** 422 before creating jobs with no collector,
      `content_hash` column + global unique dedup, sane `_batch_insert`, remove
      `asyncio.sleep(1)` hack + DEBUG log prefixes, Reddit creds fail fast.
- [x] **Batch 4 — API correctness:** sentiment sort without row duplication, sort_by
      whitelist, single theme-frequency endpoint, citation preview endpoint as single
      source of truth (MLA 9), ordered analysis results, exact path matching in
      endpoints.ts, consistent count queries.
- [x] **Batch 5 — Frontend: broken features and dishonest charts:** build minimal /quotes
      backend + error toasts, fix /workspace→/research links, delete fabricated charts
      (Math.random data!), fix "+ New" note 422, honest export buttons, show job
      error_message, "collection runs" label, logout button, type/contract fixes.
- [x] **Batch 6 — Dead code & hygiene:** delete dead frontend files (useFilters,
      FilterBar, Pagination, SampleCard), dead backend modules (_LogAdapter,
      wordcloud_data, ImportError guards), git-rm 14 debug scripts + test.db +
      cleanup_leaked_data.py, remove nul/log junk, trim deps (praw/spacy/pandas/passlib,
      ADD bcrypt explicitly), one gazetteer, one stop-word list, strip console.log.
- [x] **Batch 7 — Tooling & docs honesty:** ESLint config (lint must exit 0),
      negative-path + user-isolation tests, truthful README, trim docker-compose to
      what works, delete unused Alembic scaffolding.
- [ ] **Batch 8 — Hardening (optional):** naive-UTC datetime convention, FK indexes,
      login throttling decision, remove decorative Settings keywords, dark-mode
      decision, methodology notes (sentiment topic-bias, theme threshold).

## Decisions register

Defaults baked into the plan — flag at check-in if a session deviates:

| # | Decision | Default | Status |
|---|----------|---------|--------|
| D1 | Celery vs BackgroundTasks | Delete Celery; keep BackgroundTasks | completed (B2) |
| D2 | Quote Library | Build minimal backend (UI + README already promise it) | completed (B5) |
| D3 | wordcloud_data.py | Delete (no endpoint uses it) | completed (B6) |
| D4 | docker-compose | Trim to backend+frontend; SQLite stays | completed (B7) |
| D5 | Alembic | Delete scaffolding; create_all is the mechanism | completed (B7) |
| D6 | Token in localStorage | Accepted risk (local research tool) | accepted 2026-06-11 |
| D7 | Login rate limiting | Skip unless app leaves localhost | pending (B8) |

## Known issues (accepted / not yet scheduled)

- Sentiment lexicon conflates topic with sentiment (news *about* flooding scores
  negative) — documented as methodology limitation in Batch 8; no code fix scheduled.
- Theme match threshold 0.01 over-tags samples — review against seed data in Batch 8.
- BBC collector body extraction can ingest page junk when no `<article>` tag; search
  requests are not rate-limited; long jobs run in-process (accepted after D1).
- `backend/thermoculture.db` and `test.db` exist locally; only `backend/test.db` is
  git-tracked (removed in Batch 6).

---

## Check-in Log

### [0008] 2026-06-14 — fix/batch-7-tooling — Tooling, tests, and docs honesty
**Batch/scope:** Batch 7 — Tooling, tests, and docs honesty
**Work completed:**
- Task 1: Upgrade to ESLint 9 + typescript-eslint + eslint-plugin-react-hooks@5.x, create flat-config `eslint.config.js` and fix all console and type violations (2f54919)
- Task 2: Add 6 negative-path and user-isolation tests in `backend/tests/test_batch7.py` covering combined filters, double job start, 404s with auth, pagination bounds, filter exports, and notes user-isolation (4d667f8)
- Task 3: Rewrite README.md to accurately list SQLite, Python 3.10.x, trimmed stack, correct API routes, and local quickstart; update seeds to print test user credentials (138f0bb)
- Task 4: Trim docker-compose.yml to backend+frontend only, and update backend healthcheck using python-urllib command (a7dd499)
- Task 5: Delete unused Alembic configuration `alembic.ini` and `migrations` folder (68222ef)
**Verification:** pytest 89 passed | tsc clean | lint clean
**Decisions made:** D4 (trim docker-compose to frontend+backend) completed. D5 (delete Alembic configuration) completed.
**Deferred/noticed:** Docker Desktop daemon startup timed out on host machine during verification, but compose syntax verified cleanly with `docker compose config`.

### [0007] 2026-06-14 — fix/batch-6-hygiene — Dead code and repo hygiene
**Batch/scope:** Batch 6 — Dead code & hygiene
**Work completed:**
- Task 1: Delete dead frontend hook and components (`useFilters`, `FilterBar`, `Pagination`, `SampleCard`) and drop `date-fns` (8446b2e)
- Task 2: Delete dead backend modules `wordcloud_data.py` and `geographic.py`, remove `_build_theme_vectors` and unused sklearn/url imports, remove models `ImportError` guards, and simplify `scheduler.py` logger (0848563)
- Task 3: git-rm 16 debug scripts, test databases, and delete untracked `nul`, `log`, and `db` debris (0781330)
- Task 4: Trim unused dependencies from `requirements.txt` (`praw`, `spacy`, `pandas`, `passlib`) and Dockerfile while adding `bcrypt` explicitly (5f2b35d)
- Task 5: Consolidate gazetteer and stop-word list to single source (handled by Task 2 deletions) (0848563)
- Task 6: Strip remaining debug `console.log` statements in frontend `useAuth.tsx` and `ProtectedRoute.tsx` (1889557)
**Verification:** pytest 83 passed | tsc clean | lint not-applicable
**Decisions made:** D3 (delete wordcloud_data.py) completed.
**Deferred/noticed:** None.

### [0006] 2026-06-12 — fix/batch-5-frontend — Frontend: broken features and dishonest charts
**Batch/scope:** Batch 5 — Frontend: broken features and dishonest charts
**Work completed:**
- Task 1: Build missing quote library backend (model, schemas, router) and add frontend error/success toasts (85d464e)
- Task 2: Change broken /workspace links to /research in SampleDetail (decbe05)
- Task 3: Delete fabricated composition and classification over time charts and clean up unused imports (0dfba05, 20cee2b)
- Task 4: Allow empty content for new notes in backend schemas and add frontend error toasts (3c2ee5e)
- Task 5: Remove notes CSV button from Settings page and remove bibtex format from ExportFormat type (74ea426)
- Task 6: Surface collection job error messages on failed badges and update ProvenanceBar label to collection runs (3b73b62)
- Task 7: Replace static user button placeholder with user email and profile logout dropdown menu (2d99c7f)
- Task 8: Make RegisterRequest.full_name required and simplify 401 response handling to a hard redirect (dffe793)
**Verification:** pytest 89 passed | tsc clean | lint not-applicable
**Decisions made:** D2 (Build minimal quote library backend) completed.
**Deferred/noticed:** None.

### [0005] 2026-06-11 — fix/batch-4-api — API correctness
**Batch/scope:** Batch 4 — API correctness
**Work completed:**
- Task 1: Fix duplicate/skipped rows when sorting by sentiment via a scalar correlated subquery (34f8a6b)
- Task 2: Whitelist sort_by query parameter falling back to collected_at (79fc78b)
- Task 3: Consolidate theme frequency endpoints to outer join /theme-frequencies (252c1d7)
- Task 4: Expose preview GET /citations/preview returning MLA 9 / Chicago formatting, used in frontend SampleDetail (b7f29bb)
- Task 5: Order sample analysis results descending by analysis/classification date (cf3f621)
- Task 6: Normalize API paths in frontend client to match backend exactly (7d559c0)
- Task 7: Wrap dashboard count queries in select() for query consistency (6138050)
- Test: Add suite for all Batch 4 backend requirements (10d9990)
**Verification:** pytest 84 passed | tsc clean | lint not-applicable
**Decisions made:** None.
**Deferred/noticed:** None.

### [0004] 2026-06-11 — fix/batch-3-collection — Collection correctness
**Batch/scope:** Batch 3 — Collection correctness
**Work completed:**
- Task 1: Resolve and validate collector type, returning 422 for sources without usable collector (f0ac98d)
- Task 2: Dedicated unique indexed column `DiscourseSample.content_hash` for global cross-source deduplication (b7c4063)
- Task 3: Simplify batch insert using nested savepoints and graceful conflict expunging without transaction rollback (26509fc)
- Task 4: Remove sleep visibility hack and prefixes in routing loggers (739e18e)
- Task 5: ValueError raised on missing Reddit credentials in collect() (714cb98)
**Verification:** pytest 79 passed | tsc clean | lint not-applicable
**Decisions made:** Dev SQLite database needs to be recreated (or modified using ALTER TABLE) to add the `content_hash` column as SQLite database schemas are created dynamically via create_all.
**Deferred/noticed:** Spotted that database schema creation relies purely on SQLAlchemy create_all and has no Alembic files.

### [0003] 2026-06-11 — fix/batch-2-nlp — Make the NLP pipeline real
**Batch/scope:** Batch 2 — Make NLP real
**Work completed:**
- Task 1: Deleted dead Celery layer and configuration (efe5a4a)
- Task 2: Triggered NLP AnalysisEngine on sample ingestion inside IngestPipeline (1b83ee7)
- Task 3: Stop classifying empty/no-signal text as PRACTICAL_ADAPTATION (fafd692)
- Task 4: Removed GeoExtractor wiring and unused location store/aggregations from analyzer (fafd692)
**Verification:** pytest 75 passed | tsc clean | lint not-applicable
**Decisions made:** D1 (Delete Celery; keep BackgroundTasks) completed.
**Deferred/noticed:** Spotted that `nlp/geographic.py` is now dead code (to be deleted in Batch 6).

### [0002] 2026-06-11 — fix/batch-1-auth — Security: auth coverage and logging cleanup
**Batch/scope:** Batch 1 — Security
**Work completed:**
- Task 1: Enforce auth on all non-public endpoints in routes.py (d1c381a)
- Task 2: Remove per-request credential logging from security.py and client.ts (8a8b49e)
- Task 3: Fail fast on default SECRET_KEY in config.py under production environment (dabfd5d)
**Verification:** pytest 78 passed | tsc clean | lint not-applicable
**Decisions made:** None.
**Deferred/noticed:** Spotted dead Celery worker setup (to be deleted in Batch 2).

### [0001] 2026-06-11 — master — Full codebase review + remediation scaffolding
**Batch/scope:** ad-hoc (pre-batch)
**Work completed:**
- Full read-through review of backend (app, collectors, nlp, seeds, tests, configs)
  and frontend (all pages, components, hooks, api, configs). Findings summarised in
  `docs/plans/2026-06-11-remediation-batches.md` (issue→batch coverage map at the end).
- Verified baseline: backend pytest 64 passed; frontend `tsc --noEmit` clean;
  `npm run lint` fails (no ESLint config exists).
- Created `docs/plans/2026-06-11-remediation-batches.md` (8 batches of paste-ready prompts).
- Rewrote `CLAUDE.md`: preserved VBW rules/skills/env notes; added Karpathy coding
  guidelines (verbatim from multica-ai/andrej-karpathy-skills), verification commands,
  "Project Reality" facts, and tightened conventions (auth-everywhere, no console.log,
  exact API paths, onError on mutations).
- Created this `STATE.md` with batch tracker, decisions register, and check-in format.
**Verification:** pytest 64 passed | tsc clean | lint broken (expected until Batch 7)
**Decisions made:** D1–D7 defaults recorded above.
**Deferred/noticed:** Nothing fixed in this session by design — review only. Notable
top-5 risks: NLP never runs on collected data; Celery layer dead; missing auth on
mutating endpoints; fabricated chart data in AnalysisInsights; Quote Library calls a
non-existent API.
