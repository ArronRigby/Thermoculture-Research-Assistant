# VBW-Managed Project
This project uses VBW (Vibe Better with Claude Code) for structured development.
## VBW Rules
- **Always use VBW commands** for project work. Do not manually edit files in `.vbw-planning/`.
- **Commit format:** `{type}({scope}): {description}` — types: feat, fix, test, refactor, perf, docs, style, chore.
- **One commit per task.** Each task in a plan gets exactly one atomic commit.
- **Never commit secrets.** Do not stage .env, .pem, .key, credentials, or token files.
- **Plan before building.** Use /vbw:plan before /vbw:execute. Plans are the source of truth.
- **Do not fabricate content.** Only use what the user explicitly states in project-defining flows.
## State
- Planning directory: `.vbw-planning/`
- Active branch: `master`
- Merged: `fix/foundation` (PR #1), `feat/tags-and-trends` (PR #2)
- Next branch: `feat/collection-pipeline` (cut from master)
- Plans: `docs/plans/2026-02-18-*.md`

## Environment Notes

- **Git push:** Must be run from PowerShell/CMD — Windows Credential Manager auth does not work in the bash tool
- **`gh` CLI:** Installed and authenticated but not in bash PATH; use PowerShell/CMD for `gh` commands
- **VBW pre-push hook:** Was removed (`.git/hooks/pre-push`) — it was broken due to `set -euo pipefail` + missing VBW 1.30.0 scripts directory. Do not reinstall.

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
- TypeScript strict mode enabled (strict: true in tsconfig)
- ESLint max-warnings: 0 (all warnings are errors)
- React functional components with hooks only (no class components)
- Async/await for all I/O operations (no sync database calls)
- Pydantic schemas for all API request/response validation
- SQLAlchemy 2.0+ style with mapped_column and Mapped types
- All API routes under /api/v1 prefix
- TanStack React Query for server state management
- Environment-based configuration via Pydantic Settings

## Commands
Run /vbw:status for current progress.
Run /vbw:help for all available commands.
