# VBW-Managed Project
This project uses VBW (Vibe Better with Claude Code) for structured development.

## VBW Rules
- **Always use VBW commands** for project work. Do not manually edit files in `.vbw-planning/`.
- **Commit format:** `{type}({scope}): {description}` — types: feat, fix, test, refactor, perf, docs, style, chore.
- **One commit per task.** Each task in a plan gets exactly one atomic commit.
- **Never commit secrets.** Do not stage .env, .pem, .key, credentials, or token files.
- **Plan before building.** Use /vbw:plan before /vbw:execute. Plans are the source of truth.
- **Do not fabricate content.** Only use what the user explicitly states in project-defining flows. This applies to DATA as well as text: never render invented or randomised numbers in charts — this is a research tool.

## State
- Planning directory: `.vbw-planning/`
- Active branch: `master`
- Merged: `fix/foundation` (PR #1), `feat/tags-and-trends` (PR #2)
- **Living state file: `STATE.md`** (repo root) — read it at the start of every session. It tracks remediation batch progress and a check-in log of completed work. Update it at every check-in.
- Remediation plan: `docs/plans/2026-06-11-remediation-batches.md` — batched fix prompts from the 2026-06-11 full-codebase review. Work these in order unless told otherwise.
- Plans: `docs/plans/*.md`

## Coding Guidelines (Karpathy)

Behavioral guidelines to reduce common LLM coding mistakes, from
https://github.com/multica-ai/andrej-karpathy-skills (MIT). These bias toward
caution over speed; for trivial tasks, use judgment.

### 1. Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First
**Minimum code that solves the problem. Nothing speculative.**
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes
**Touch only what you must. Clean up only your own mess.**
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it (log it in STATE.md) — don't delete it.
- Remove imports/variables/functions that YOUR changes made unused; don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution
**Define success criteria. Loop until verified.**
- "Add validation" → "Write tests for invalid inputs, then make them pass."
- "Fix the bug" → "Write a test that reproduces it, then make it pass."
- "Refactor X" → "Ensure tests pass before and after."

For multi-step tasks, state a brief plan: `[Step] → verify: [check]` per step.
Never claim something works without running the verification commands below.

## Verification Commands

Run these before claiming any task complete (PowerShell, from repo root):

```powershell
# Backend tests (baseline 2026-06-11: 64 passed)
cd backend; venv\Scripts\python -m pytest

# Frontend type check (baseline 2026-06-11: clean)
cd frontend; npx tsc --noEmit

# Frontend lint (BROKEN until Batch 7 adds an ESLint config — do not claim lint passes before then)
cd frontend; npm run lint
```

## Environment Notes

- **Git push:** Must be run from PowerShell/CMD — Windows Credential Manager auth does not work in the bash tool
- **`gh` CLI:** Installed and authenticated but not in bash PATH; use PowerShell/CMD for `gh` commands
- **VBW pre-push hook:** Was removed (`.git/hooks/pre-push`) — it was broken due to `set -euo pipefail` + missing VBW 1.30.0 scripts directory. Do not reinstall.
- **Dev runtime:** `run_app.bat` (uvicorn :8000 + vite :5173) is the working dev path. Docker compose is partially aspirational until Batch 7 (db service has no driver; celery services are dead code until Batch 2 removes them).
- **Database:** SQLite via aiosqlite (default `DATABASE_URL`). Schema comes from `Base.metadata.create_all` at app startup — there are no Alembic migrations. Schema changes require recreating the dev DB.
- **Python:** the backend venv is Python 3.10.x (README's 3.11+ claim is wrong until corrected in Batch 7).

## Project Reality (verified 2026-06-11 — see STATE.md for current status)

Facts that contradict older docs/comments; trust these over the README until Batch 7 lands:
- NLP analysis (`nlp/analyzer.py` `AnalysisEngine`) is NOT triggered by collection — only by tests. (Fixed by Batch 2.)
- The Celery layer (`app/services/celery_app.py`) references modules that don't exist and is never dispatched. (Removed by Batch 2.)
- Several endpoints lack authentication, including DELETE /samples and POST /jobs/start. (Fixed by Batch 1.)
- The frontend Quote Library calls `/api/v1/quotes/`, which has no backend. (Fixed by Batch 5.)
- `frontend/src/hooks/useFilters.ts`, `components/FilterBar.tsx`, `components/Pagination.tsx`, `components/SampleCard.tsx` are dead code. (Removed by Batch 6.)

## Installed Skills
- find-skills (global)

## Required Skills for Plan Execution
When a plan file says `REQUIRED SUB-SKILL`, always use the skill from:
`C:\Users\Arron\.claude\plugins\marketplaces\conductor-orchestrator-superpowers\skills\`

Key skills for this project:
- **`executing-plans`** — Use when a plan file says "Use superpowers:executing-plans". This is the correct skill for implementing plan tasks step-by-step.
- **`writing-plans`** — Use when creating a new implementation plan from a spec.
- **`verification-before-completion`** — Use before claiming any task is done or raising a PR.
- **`finishing-a-development-branch`** — Use when all tasks are complete and the branch is ready to merge.
- **`systematic-debugging`** — Use when encountering any bug or unexpected behaviour before proposing a fix.
- **`requesting-code-review`** — Use before merging to verify work meets requirements.

Do NOT use `vbw:execute` as a substitute for `executing-plans`. They are different skills.

## Project Conventions

These conventions are enforced during planning and verified during QA.
- Python functions and variables use snake_case
- TypeScript strict mode enabled (strict: true in tsconfig) — verified passing
- ESLint max-warnings: 0 (all warnings are errors) — NOTE: no ESLint config exists yet; Batch 7 creates it
- React functional components with hooks only (no class components)
- Async/await for all I/O operations (no sync database calls)
- Pydantic schemas for all API request/response validation
- SQLAlchemy 2.0+ style with mapped_column and Mapped types
- All API routes under /api/v1 prefix
- Every non-public endpoint takes `Depends(get_current_user)` (public: register, login, /health)
- API paths in `frontend/src/api/endpoints.ts` must match backend routes exactly (no trailing-slash drift)
- One logging system per layer: loguru in backend app code; no `print()` in backend, no `console.log` under frontend/src
- TanStack React Query for server state management; mutations must have an `onError` handler that surfaces `err.response?.data?.detail`
- Environment-based configuration via Pydantic Settings

## Commands
Run /vbw:status for current progress.
Run /vbw:help for all available commands.

## Version & SDK Policy
When writing code that uses any external SDK, API, or AI model:
- STOP before writing any import or install command
- Search for the latest package version, correct model identifiers, and current initialization pattern
- Use what you find, NOT your training data
