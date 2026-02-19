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
- Active branch: `master` (fix/foundation merged)
- Next branches: `feat/tags-and-trends` and `feat/collection-pipeline` (run in parallel from master)
- Plans: `docs/plans/2026-02-18-*.md`

## Installed Skills
- find-skills (global)
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
