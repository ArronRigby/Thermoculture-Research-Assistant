# fix/foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all confirmed pre-existing bugs so both feature branches start from a known-working baseline.

**Architecture:** Four isolated fixes across `celery_app.py`, `nlp/analyzer.py`, `api/routes.py`, and `docker-compose.yml`. No new features. Each task is independently verifiable.

**Tech Stack:** FastAPI, SQLAlchemy async, Celery, Docker Compose, pytest

---

## Pre-flight

```bash
# Create and switch to the fix branch
git checkout -b fix/foundation

# Confirm you are in the backend venv before running any Python commands
cd backend
# Windows: venv\Scripts\activate
# Unix:    source venv/bin/activate
```

---

### Task 1: Fix Celery import paths and field reference

**Files:**
- Modify: `backend/app/services/celery_app.py`

Three bugs in `scheduled_collection`:
1. `from app.models.source import Source` — module doesn't exist
2. `from app.db.session import get_sync_session` — module doesn't exist; replace with `asyncio.run()` wrapping the async session factory
3. `source.collector_type` — field doesn't exist; use `source.source_type`

Also fix `run_collection_task`: collector imports reference `app.collectors.*` but modules live at `collectors.*`.

**Step 1: Write the failing test**

Create `backend/tests/test_celery_tasks.py`:

```python
"""Tests for Celery task import integrity and basic execution."""
import pytest


def test_celery_app_imports_without_error():
    """Importing celery_app must not raise ImportError."""
    from app.services import celery_app  # noqa: F401


def test_scheduled_collection_task_is_registered():
    """scheduled_collection must be registered in the Celery app."""
    from app.services.celery_app import celery_app as app
    registered = list(app.tasks.keys())
    assert "app.services.celery_app.scheduled_collection" in registered


def test_run_collection_task_is_registered():
    from app.services.celery_app import celery_app as app
    assert "app.services.celery_app.run_collection_task" in app.tasks


def test_analyze_sample_task_is_registered():
    from app.services.celery_app import celery_app as app
    assert "app.services.celery_app.analyze_sample_task" in app.tasks
```

**Step 2: Run to confirm failure**

```bash
cd backend
pytest tests/test_celery_tasks.py -v
```

Expected: `ImportError` or task not found.

**Step 3: Fix `celery_app.py`**

Replace the entire `scheduled_collection` task and fix `run_collection_task` imports:

```python
# At top of file, add:
import asyncio

# Replace run_collection_task collector imports (lines ~87-98):
# Change: from app.collectors.reddit_collector import RedditCollector
# To:     from collectors.reddit_collector import RedditCollector
# Change: from app.collectors.arxiv_collector import ArxivCollector
# To:     from collectors.arxiv_collector import ArxivCollector  (or remove)
# Change: from app.collectors.web_collector import WebCollector
# To:     from collectors.web_collector import WebCollector  (or remove)

# Replace scheduled_collection entirely:
@celery_app.task(name="app.services.celery_app.scheduled_collection")
def scheduled_collection() -> dict:
    """
    Run collection for all active data sources.
    Triggered by Celery beat every 6 hours.
    """
    logger.info("Starting scheduled collection for all active sources")

    async def _fetch_active_sources():
        from app.core.database import async_session_factory
        from app.models.models import Source
        from sqlalchemy import select
        async with async_session_factory() as session:
            result = await session.execute(
                select(Source).where(Source.is_active.is_(True))
            )
            # Return plain dicts so data is safe outside the session
            sources = result.scalars().all()
            return [
                {"id": str(s.id), "source_type": s.source_type.value}
                for s in sources
            ]

    try:
        active_sources = asyncio.run(_fetch_active_sources())
        dispatched = []
        for source in active_sources:
            run_collection_task.delay(
                source_id=source["id"],
                collector_type=source["source_type"],
            )
            dispatched.append(source)

        logger.info("Scheduled collection dispatched %d tasks", len(dispatched))
        return {
            "status": "completed",
            "dispatched_count": len(dispatched),
            "dispatched": dispatched,
        }

    except Exception as exc:
        logger.error("Scheduled collection failed: %s", str(exc), exc_info=True)
        raise
```

**Step 4: Run tests**

```bash
pytest tests/test_celery_tasks.py -v
```

Expected: all 4 tests PASS.

**Step 5: Commit**

```bash
git add backend/app/services/celery_app.py backend/tests/test_celery_tasks.py
git commit -m "fix(celery): correct import paths and use asyncio.run for DB access in scheduled_collection"
```

---

### Task 2: Fix `AnalysisEngine.get_aggregated_insights()` model aliases

**Files:**
- Modify: `backend/nlp/analyzer.py`

`get_aggregated_insights` imports three non-existent model aliases inside a
try/except that silently returns empty data:
- `SampleTheme` → use the `sample_themes` Table object directly
- `SampleLocation` → does not exist; `Location` is FK on `DiscourseSample`
- `DataSample` → use `DiscourseSample`

Also fix `_store_themes` which tries to insert a `SampleTheme` ORM row — the
actual `sample_themes` is a plain association `Table`, not a mapped class. Use
`insert()` instead.

Fix `_store_locations` which tries to insert a `SampleLocation` row — location
is stored as `DiscourseSample.location_id` (FK). The `IngestPipeline` already
resolves location; `_store_locations` should update `DiscourseSample.location_id`
if not already set.

**Step 1: Write failing tests**

Add to `backend/tests/test_nlp.py` (or create it):

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_get_aggregated_insights_returns_all_keys(db_session):
    """get_aggregated_insights must return all expected keys, never empty dicts."""
    from nlp.analyzer import AnalysisEngine
    engine = AnalysisEngine()
    result = await engine.get_aggregated_insights(db_session)
    assert "sentiment_distribution" in result
    assert "theme_frequency" in result
    assert "geographic_distribution" in result
    assert "discourse_distribution" in result
    assert "trending_themes" in result
    # Must not silently return empty — if DB has seed data, expect content
    # At minimum the keys must be present and be the right type
    assert isinstance(result["theme_frequency"], list)
    assert isinstance(result["trending_themes"], list)
    assert isinstance(result["sentiment_distribution"], dict)
```

**Step 2: Run to confirm failure**

```bash
pytest tests/test_nlp.py::test_get_aggregated_insights_returns_all_keys -v
```

Expected: FAIL — ImportError caught silently, returns empty.

**Step 3: Fix `analyzer.py`**

Replace `get_aggregated_insights` and its private helpers with corrected queries:

```python
async def get_aggregated_insights(
    self,
    db: AsyncSession,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Dict[str, Any]:
    from app.models.models import (
        SentimentAnalysis,
        DiscourseClassification,
        DiscourseSample,
        Theme,
        Location,
        sample_themes,
    )

    def _date_filter(col):
        conditions = []
        if date_from is not None:
            conditions.append(col >= date_from)
        if date_to is not None:
            conditions.append(col <= date_to)
        return conditions

    sentiment_distribution = await self._aggregate_sentiment(
        db, SentimentAnalysis, _date_filter
    )
    theme_frequency = await self._aggregate_themes(
        db, sample_themes, Theme, _date_filter
    )
    geographic_distribution = await self._aggregate_geography(
        db, DiscourseSample, Location, _date_filter
    )
    discourse_distribution = await self._aggregate_discourse(
        db, DiscourseClassification, _date_filter
    )
    trending_themes = await self._compute_trending_themes(
        db, sample_themes, Theme, DiscourseSample, _date_filter
    )

    return {
        "sentiment_distribution": sentiment_distribution,
        "theme_frequency": theme_frequency,
        "geographic_distribution": geographic_distribution,
        "discourse_distribution": discourse_distribution,
        "trending_themes": trending_themes,
    }
```

Replace `_aggregate_themes` to use `sample_themes` Table:

```python
async def _aggregate_themes(self, db, sample_themes, Theme, _date_filter):
    try:
        stmt = (
            select(
                Theme.name,
                func.count(sample_themes.c.sample_id).label("count"),
            )
            .join(Theme, sample_themes.c.theme_id == Theme.id)
            .group_by(Theme.name)
            .order_by(func.count(sample_themes.c.sample_id).desc())
        )
        result = await db.execute(stmt)
        return [
            {"theme": name, "count": count}
            for name, count in result.all()
        ]
    except Exception:
        logger.exception("Error aggregating theme data")
        return []
```

Replace `_aggregate_geography` to use `Location` via `DiscourseSample`:

```python
async def _aggregate_geography(self, db, DiscourseSample, Location, _date_filter):
    try:
        stmt = (
            select(
                Location.region,
                func.count(DiscourseSample.id).label("count"),
            )
            .join(DiscourseSample, DiscourseSample.location_id == Location.id)
            .group_by(Location.region)
            .order_by(func.count(DiscourseSample.id).desc())
        )
        date_conditions = _date_filter(DiscourseSample.collected_at)
        if date_conditions:
            stmt = stmt.where(and_(*date_conditions))
        result = await db.execute(stmt)
        return {region: count for region, count in result.all()}
    except Exception:
        logger.exception("Error aggregating geographic data")
        return {}
```

Fix `_store_themes` to use `insert()` into the association Table:

```python
async def _store_themes(self, db, sample_id, themes):
    from app.models.models import Theme, sample_themes
    from sqlalchemy import insert

    for theme_data in themes:
        theme_name = theme_data["theme"]

        stmt = select(Theme).where(Theme.name == theme_name)
        result = await db.execute(stmt)
        theme_record = result.scalar_one_or_none()

        if theme_record is None:
            theme_record = Theme(name=theme_name)
            db.add(theme_record)
            await db.flush()

        # Insert into association table directly (it has no mapped class)
        await db.execute(
            insert(sample_themes).values(
                sample_id=str(sample_id),
                theme_id=theme_record.id,
            ).prefix_with("OR IGNORE")  # skip if already linked
        )
```

Fix `_compute_trending_themes` to use `DiscourseSample` and `sample_themes` Table:

```python
async def _compute_trending_themes(self, db, sample_themes, Theme, DiscourseSample, _date_filter):
    try:
        from datetime import timedelta

        total_result = await db.execute(select(func.count()).select_from(sample_themes))
        total_all = total_result.scalar() or 1

        all_time_stmt = (
            select(Theme.name, func.count(sample_themes.c.sample_id).label("count"))
            .join(Theme, sample_themes.c.theme_id == Theme.id)
            .group_by(Theme.name)
        )
        all_time_rows = {name: count for name, count in (await db.execute(all_time_stmt)).all()}

        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent_stmt = (
            select(Theme.name, func.count(sample_themes.c.sample_id).label("count"))
            .join(Theme, sample_themes.c.theme_id == Theme.id)
            .join(DiscourseSample, sample_themes.c.sample_id == DiscourseSample.id)
            .where(DiscourseSample.collected_at >= recent_cutoff)
            .group_by(Theme.name)
        )
        recent_total_result = await db.execute(
            select(func.count())
            .select_from(sample_themes)
            .join(DiscourseSample, sample_themes.c.sample_id == DiscourseSample.id)
            .where(DiscourseSample.collected_at >= recent_cutoff)
        )
        total_recent = recent_total_result.scalar() or 1
        recent_rows = {name: count for name, count in (await db.execute(recent_stmt)).all()}

        trending = []
        for theme_name, recent_count in recent_rows.items():
            recent_share = recent_count / total_recent
            historical_count = all_time_rows.get(theme_name, 0)
            historical_share = historical_count / total_all
            trending.append({
                "theme": theme_name,
                "recent_count": recent_count,
                "historical_count": historical_count,
                "trend_score": round(recent_share - historical_share, 4),
            })

        trending.sort(key=lambda t: t["trend_score"], reverse=True)
        return trending[:20]
    except Exception:
        logger.exception("Error computing trending themes")
        return []
```

**Step 4: Run tests**

```bash
pytest tests/test_nlp.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/nlp/analyzer.py backend/tests/test_nlp.py
git commit -m "fix(nlp): replace non-existent model aliases in AnalysisEngine aggregation queries"
```

---

### Task 3: Add auth guards to unprotected endpoints

**Files:**
- Modify: `backend/app/api/routes.py`

The following endpoints are missing `current_user: User = Depends(get_current_user)`:
- `POST /sources/` (line 214)
- `DELETE /sources/{source_id}` (line 251)
- `GET /sources/{source_id}` (line 223)
- `PUT /sources/{source_id}` (line 232)
- All `analysis_router` endpoints
- `GET /export/samples`
- `POST /samples/`

The pattern already used on authenticated routes is:
```python
current_user: User = Depends(get_current_user),
```

**Step 1: Write failing tests**

Add to `backend/tests/test_api.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_source_requires_auth(client: AsyncClient):
    response = await client.post("/api/v1/sources/", json={
        "name": "Test", "source_type": "NEWS", "is_active": True
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_source_requires_auth(client: AsyncClient):
    response = await client.delete("/api/v1/sources/nonexistent-id")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analysis_theme_frequency_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/analysis/theme-frequency")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_samples_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/export/samples")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_sample_requires_auth(client: AsyncClient):
    response = await client.post("/api/v1/samples/", json={
        "title": "Test", "content": "Test", "source_id": "fake-id"
    })
    assert response.status_code == 401
```

**Step 2: Run to confirm failure**

```bash
pytest tests/test_api.py::test_create_source_requires_auth -v
```

Expected: FAIL — returns 2xx or 4xx other than 401.

**Step 3: Add missing auth guards**

For each unprotected route, add `current_user: User = Depends(get_current_user)` as a parameter. Example for `create_source`:

```python
# Before:
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):

# After:
async def create_source(
    payload: SourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
```

Apply the same change to:
- `delete_source`
- `get_source`
- `update_source`
- Every function decorated with `@analysis_router.*`
- `export_samples`
- `create_sample`

The `current_user` parameter does not need to be used in the function body —
FastAPI will enforce the dependency and return 401 automatically if no valid token is present.

**Step 4: Run tests**

```bash
pytest tests/test_api.py -v
```

Expected: all auth tests PASS.

**Step 5: Commit**

```bash
git add backend/app/api/routes.py backend/tests/test_api.py
git commit -m "fix(auth): add missing get_current_user dependency to sources, analysis, export, and sample routes"
```

---

### Task 4: Add `celery_beat` service to docker-compose.yml

**Files:**
- Modify: `docker-compose.yml`

Without a `celery_beat` container, the 6-hour schedule exists only in code and never runs.

**Step 1: Read current docker-compose.yml**

```bash
cat docker-compose.yml
```

Note the existing `celery_worker` service — copy its structure.

**Step 2: Add `celery_beat` service**

In `docker-compose.yml`, add after the `celery_worker` service:

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
    restart: unless-stopped
```

At the bottom of the file, add the named volume:

```yaml
volumes:
  celery_beat_data:
  # ... any existing volumes
```

**Step 3: Verify docker-compose config is valid**

```bash
docker compose config --quiet
```

Expected: no errors printed.

**Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "fix(infra): add celery_beat service to docker-compose so the 6-hour schedule actually runs"
```

---

### Task 5: Verify `.env` is not tracked by git

**Files:**
- Modify: `.gitignore` (if needed)

**Step 1: Check git tracking status**

```bash
git ls-files .env
```

If this prints `.env`, the file is tracked. If blank, it is not tracked.

**Step 2: If tracked — remove from git history**

```bash
# Remove from tracking without deleting the file
git rm --cached .env
echo ".env" >> .gitignore
git add .gitignore
git commit -m "chore: stop tracking .env and add to gitignore"
```

**Step 3: If not tracked — confirm .gitignore covers it**

```bash
git check-ignore -v .env
```

Expected: output shows `.gitignore:.env` or similar rule. If no output, add it:

```bash
echo ".env" >> .gitignore
git add .gitignore
git commit -m "chore: ensure .env is in .gitignore"
```

**Step 4: Add Guardian API key placeholder to `.env.example`**

```bash
# Open .env.example and add:
echo "GUARDIAN_API_KEY=" >> .env.example
git add .env.example
git commit -m "chore: add GUARDIAN_API_KEY placeholder to .env.example"
```

---

### Task 6: Verification gate

Run the full verification checklist before merging to master.

**Step 1: Run all backend tests**

```bash
cd backend
pytest -v
```

Expected: all tests PASS, none ERROR.

**Step 2: Verify Celery task registration**

```bash
# With Redis running:
docker compose up redis -d
celery -A app.services.celery_app inspect registered 2>/dev/null || \
  python -c "
from app.services.celery_app import celery_app
tasks = list(celery_app.tasks.keys())
required = [
  'app.services.celery_app.scheduled_collection',
  'app.services.celery_app.run_collection_task',
  'app.services.celery_app.analyze_sample_task',
]
for t in required:
    status = 'OK' if t in tasks else 'MISSING'
    print(f'{status}: {t}')
"
```

Expected: all three tasks show OK.

**Step 3: Verify analysis endpoints return data**

```bash
# Start the app with seed data
docker compose up --build -d
docker compose exec backend python -m seeds.run_seed

# Get a token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=researcher@thermoculture.ac.uk&password=research2024" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Check theme-frequency returns data
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/analysis/theme-frequency | python -m json.tool

# Check 401 without token
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:8000/api/v1/analysis/theme-frequency
# Expected: 401
```

**Step 4: Verify celery_beat starts**

```bash
docker compose up celery_beat -d
docker compose logs celery_beat
```

Expected: logs show `beat: Starting...` and the schedule entries.

**Step 5: Merge to master**

```bash
git checkout master
git merge fix/foundation --no-ff -m "fix: foundation fixes for Celery, NLP aggregation, auth guards, and celery_beat"
git push origin master
```

Now branch both feature branches off this clean master.
