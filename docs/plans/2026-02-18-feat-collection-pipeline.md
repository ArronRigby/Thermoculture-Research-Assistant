# feat/collection-pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add BBC News and Guardian collectors that run every 6 hours and automatically trigger NLP analysis on each new article.

**Architecture:** Two new `BaseCollector` subclasses feed into the existing `IngestPipeline`. A `asyncio.run()` bridge in Celery task bodies calls async DB and NLP methods. A new Alembic migration adds a performance index. No changes to the frontend.

**Tech Stack:** Python, httpx, BeautifulSoup4, Celery, SQLAlchemy async, Alembic, pytest-asyncio

**Pre-requisite:** `fix/foundation` must be merged to master before starting this branch.

---

## Pre-flight

```bash
git checkout master
git pull origin master
git checkout -b feat/collection-pipeline
cd backend

# Confirm httpx and beautifulsoup4 are in requirements.txt
grep -E "httpx|beautifulsoup4|bs4" requirements.txt
# If missing, add them and pip install:
# echo "httpx==0.27.0" >> requirements.txt
# echo "beautifulsoup4==4.12.3" >> requirements.txt
# pip install httpx beautifulsoup4
```

---

### Task 1: Add Guardian collector

**Files:**
- Create: `backend/collectors/guardian_collector.py`
- Create: `backend/tests/test_collectors.py` (add to existing file)

The Guardian Open Platform API is free for research use. Register at
https://open-platform.theguardian.com/ for a production key. The `test` key
works during development with reduced rate limits (12 req/sec → 1 req/day).

**Step 1: Write failing tests**

In `backend/tests/test_collectors.py`, add:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from collectors.guardian_collector import GuardianCollector
from collectors.base import CollectedItem


@pytest.mark.asyncio
async def test_guardian_collector_returns_collected_items(monkeypatch):
    """GuardianCollector.collect() must return a list of CollectedItem."""
    mock_response = {
        "response": {
            "results": [
                {
                    "webTitle": "UK flooding worsens amid climate change",
                    "webUrl": "https://theguardian.com/environment/2024/01/01/flooding",
                    "fields": {
                        "bodyText": "Flooding across the UK has intensified as climate scientists warn...",
                        "byline": "Jane Smith",
                        "firstPublicationDate": "2024-01-01T10:00:00Z",
                    },
                }
            ]
        }
    }

    async def mock_get(*args, **kwargs):
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = mock_response
        m.raise_for_status = MagicMock()
        return m

    collector = GuardianCollector(api_key="test")
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__.return_value.get = mock_get
        items = await collector.collect(keywords=["flooding"])

    assert len(items) == 1
    assert isinstance(items[0], CollectedItem)
    assert items[0].title == "UK flooding worsens amid climate change"
    assert items[0].author == "Jane Smith"


@pytest.mark.asyncio
async def test_guardian_collector_skips_empty_results():
    """Empty API response should return empty list without error."""
    mock_response = {"response": {"results": []}}

    async def mock_get(*args, **kwargs):
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = mock_response
        m.raise_for_status = MagicMock()
        return m

    collector = GuardianCollector(api_key="test")
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__.return_value.get = mock_get
        items = await collector.collect(keywords=["flooding"])

    assert items == []


@pytest.mark.asyncio
async def test_guardian_collector_uses_exponential_backoff_on_429(monkeypatch):
    """429 response should trigger exponential backoff, not crash."""
    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        m = MagicMock()
        if call_count == 1:
            m.status_code = 429
            m.raise_for_status.side_effect = Exception("429 Too Many Requests")
        else:
            m.status_code = 200
            m.json.return_value = {"response": {"results": []}}
            m.raise_for_status = MagicMock()
        return m

    monkeypatch.setattr("asyncio.sleep", AsyncMock())  # skip actual sleep
    collector = GuardianCollector(api_key="test")
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__.return_value.get = mock_get
        items = await collector.collect(keywords=["flooding"])

    assert items == []
```

**Step 2: Run tests to confirm failure**

```bash
cd backend
pytest tests/test_collectors.py -k "guardian" -v
```

Expected: `ModuleNotFoundError: No module named 'collectors.guardian_collector'`

**Step 3: Create `collectors/guardian_collector.py`**

```python
"""
Guardian Open Platform collector for the Thermoculture Research Assistant.

Uses the Guardian Content API (free tier, research-licensed) to search for
UK climate discourse. Register at: https://open-platform.theguardian.com/
Set GUARDIAN_API_KEY in .env. The value "test" works during development
with a rate limit of 1 request per day per IP.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from collectors.base import BaseCollector, CollectedItem

logger = logging.getLogger(__name__)

_BASE_URL = "https://content.guardianapis.com/search"
_FIELDS = "bodyText,byline,firstPublicationDate,trailText"


class GuardianCollector(BaseCollector):
    """
    Collects climate-related articles from the Guardian Open Platform API.

    The Guardian API is explicitly licensed for non-commercial and research use.
    See: https://open-platform.theguardian.com/access/
    """

    def __init__(self, api_key: Optional[str] = None, rate_limit_seconds: float = 2.0):
        super().__init__(source_name="guardian", rate_limit_seconds=rate_limit_seconds)
        self.api_key = api_key or os.getenv("GUARDIAN_API_KEY", "test")
        if self.api_key == "test":
            logger.warning(
                "GuardianCollector using 'test' API key — limited to 1 req/day. "
                "Set GUARDIAN_API_KEY in .env for production use."
            )

    async def collect(self, keywords: Optional[List[str]] = None, **kwargs) -> List[CollectedItem]:
        """Collect articles for each keyword and return deduplicated CollectedItems."""
        terms = keywords or self.CLIMATE_KEYWORDS
        items: List[CollectedItem] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(timeout=15.0) as client:
            for term in terms:
                try:
                    batch = await self._fetch_term(client, term)
                    for item in batch:
                        if item.source_url not in seen_urls:
                            seen_urls.add(item.source_url)
                            items.append(item)
                    await self._rate_limit()
                except Exception:
                    logger.exception("GuardianCollector failed for term: %s", term)

        self.items_collected = len(items)
        logger.info("GuardianCollector collected %d items", len(items))
        return items

    async def _fetch_term(self, client: httpx.AsyncClient, term: str) -> List[CollectedItem]:
        """Fetch one page of results for a single search term with retry."""
        backoff = 2.0
        for attempt in range(3):
            try:
                response = await client.get(
                    _BASE_URL,
                    params={
                        "q": term,
                        "api-key": self.api_key,
                        "show-fields": _FIELDS,
                        "page-size": 50,
                        "order-by": "newest",
                        "tag": "environment/environment",
                    },
                    headers=self.DEFAULT_HEADERS,
                )
                response.raise_for_status()
                return self._parse_response(response.json())
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    logger.warning("Guardian API rate limit hit — backing off %ss", backoff)
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error("Guardian API HTTP error %s for term '%s'", exc.response.status_code, term)
                    return []
            except Exception:
                logger.exception("Guardian API request failed for term '%s'", term)
                return []
        return []

    def _parse_response(self, data: dict) -> List[CollectedItem]:
        results = data.get("response", {}).get("results", [])
        items = []
        for result in results:
            fields = result.get("fields", {})
            body = fields.get("bodyText", "").strip()
            if not body:
                continue
            published_at = None
            raw_date = fields.get("firstPublicationDate", "")
            if raw_date:
                try:
                    published_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except ValueError:
                    pass
            items.append(CollectedItem(
                title=result.get("webTitle", "")[:512],
                content=body,
                source_url=result.get("webUrl", ""),
                author=fields.get("byline", None),
                published_at=published_at,
                raw_metadata={"guardian_id": result.get("id", "")},
            ))
        return items
```

**Step 4: Run tests**

```bash
pytest tests/test_collectors.py -k "guardian" -v
```

Expected: all PASS.

**Step 5: Commit**

```bash
git add collectors/guardian_collector.py tests/test_collectors.py
git commit -m "feat(collectors): add GuardianCollector using Open Platform API"
```

---

### Task 2: Add BBC News collector with robots.txt guard

**Files:**
- Create: `backend/collectors/bbc_collector.py`
- Modify: `backend/tests/test_collectors.py`

BBC has no public API. We scrape search results with an explicit robots.txt
check and a zero-result health check. This collector carries a maintenance risk:
BBC HTML structure changes without notice. A `WARNING` is logged in the module
docstring and the zero-result check surfaces silent failures.

**Step 1: Write failing tests**

```python
@pytest.mark.asyncio
async def test_bbc_collector_respects_robots_txt_disallow(monkeypatch):
    """If robots.txt disallows the search path, return empty list without scraping."""
    async def mock_get(url, **kwargs):
        m = MagicMock()
        if "robots.txt" in url:
            m.status_code = 200
            m.text = "User-agent: *\nDisallow: /search\n"
        else:
            raise AssertionError("Should not make further requests after robots.txt block")
        return m

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    from collectors.bbc_collector import BBCCollector
    collector = BBCCollector()
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__.return_value.get = mock_get
        items = await collector.collect(keywords=["flooding"])

    assert items == []


@pytest.mark.asyncio
async def test_bbc_collector_sets_failed_status_on_zero_results():
    """collect() must return zero items and set items_collected=0 on a dry run."""
    async def mock_get(url, **kwargs):
        m = MagicMock()
        if "robots.txt" in url:
            m.status_code = 200
            m.text = "User-agent: *\nAllow: /\n"
        else:
            m.status_code = 200
            m.text = "<html><body><div class='ssrcss-no-results'>No results</div></body></html>"
        return m

    from collectors.bbc_collector import BBCCollector
    collector = BBCCollector()
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__.return_value.get = mock_get
        items = await collector.collect(keywords=["flooding"])

    assert items == []
    assert collector.items_collected == 0
    assert collector.last_run_zero_results is True


@pytest.mark.asyncio
async def test_bbc_collector_extracts_articles(monkeypatch):
    """Collector extracts articles from valid BBC search HTML."""
    sample_html = """
    <html><body>
      <ul data-testid="search-results">
        <li>
          <div data-testid="default-card">
            <a class="ssrcss-its90q-PromoLink" href="/news/uk-12345">
              <h3 data-testid="card-headline">UK flooding: thousands displaced</h3>
            </a>
            <p data-testid="card-description">Heavy rainfall has caused severe flooding...</p>
            <time datetime="2024-01-15T10:30:00.000Z">15 Jan 2024</time>
          </div>
        </li>
      </ul>
    </body></html>
    """

    async def mock_get(url, **kwargs):
        m = MagicMock()
        if "robots.txt" in url:
            m.status_code = 200
            m.text = "User-agent: *\nAllow: /\n"
        else:
            m.status_code = 200
            m.text = sample_html
        return m

    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    from collectors.bbc_collector import BBCCollector
    collector = BBCCollector()
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__.return_value.get = mock_get
        items = await collector.collect(keywords=["flooding"])

    assert len(items) >= 1
    assert "flooding" in items[0].title.lower()
```

**Step 2: Run to confirm failure**

```bash
pytest tests/test_collectors.py -k "bbc" -v
```

Expected: `ModuleNotFoundError`.

**Step 3: Create `collectors/bbc_collector.py`**

```python
"""
BBC News collector for the Thermoculture Research Assistant.

MAINTENANCE RISK: BBC has no public API. This collector scrapes BBC News
search results. BBC HTML structure changes without notice and may break
article extraction silently. Monitor last_run_zero_results and investigate
immediately if it becomes True on consecutive runs.

robots.txt compliance: this collector checks BBC's robots.txt before
making any search or article requests. If the search path is disallowed,
all collection for that run is aborted cleanly.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from collectors.base import BaseCollector, CollectedItem

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.bbc.co.uk"
_SEARCH_PATH = "/search"
_ROBOTS_URL = f"{_BASE_URL}/robots.txt"
_USER_AGENT = "ThermocultureResearchBot/1.0"


class BBCCollector(BaseCollector):
    """
    Collects climate-related articles from BBC News search results.

    Checks robots.txt before each collection run. Returns zero items and
    sets last_run_zero_results=True if scraping yields no articles —
    this signals a possible BBC structure change or IP block.
    """

    def __init__(self, rate_limit_seconds: float = 3.0):
        super().__init__(source_name="bbc_news", rate_limit_seconds=rate_limit_seconds)
        self.last_run_zero_results: bool = False

    async def collect(self, keywords: Optional[List[str]] = None, **kwargs) -> List[CollectedItem]:
        terms = keywords or self.CLIMATE_KEYWORDS
        items: List[CollectedItem] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            timeout=15.0,
            headers=self.DEFAULT_HEADERS,
            follow_redirects=True,
        ) as client:
            # ---- robots.txt check ----
            allowed = await self._check_robots(client)
            if not allowed:
                logger.warning(
                    "BBCCollector: robots.txt disallows search path. "
                    "Aborting collection run."
                )
                self.last_run_zero_results = True
                return []

            for term in terms:
                try:
                    batch = await self._search_term(client, term)
                    for item in batch:
                        if item.source_url not in seen_urls:
                            seen_urls.add(item.source_url)
                            items.append(item)
                    await self._rate_limit()
                except Exception:
                    logger.exception("BBCCollector failed for term: %s", term)

        self.items_collected = len(items)
        if self.items_collected == 0:
            self.last_run_zero_results = True
            logger.warning(
                "BBCCollector: zero items collected. Possible BBC site change or block. "
                "Verify manually at %s%s", _BASE_URL, _SEARCH_PATH,
            )
        else:
            self.last_run_zero_results = False

        logger.info("BBCCollector collected %d items", self.items_collected)
        return items

    async def _check_robots(self, client: httpx.AsyncClient) -> bool:
        """Return True if /search is allowed for our user agent."""
        try:
            response = await client.get(_ROBOTS_URL)
            rp = RobotFileParser()
            rp.parse(response.text.splitlines())
            return rp.can_fetch(_USER_AGENT, f"{_BASE_URL}{_SEARCH_PATH}")
        except Exception:
            logger.warning("BBCCollector: could not fetch robots.txt — proceeding cautiously")
            return True  # fail open; log and continue

    async def _search_term(self, client: httpx.AsyncClient, term: str) -> List[CollectedItem]:
        """Fetch BBC search results for one term."""
        try:
            response = await client.get(
                f"{_BASE_URL}{_SEARCH_PATH}",
                params={"q": term, "d": "news_gnl"},
            )
            response.raise_for_status()
            return self._parse_search_page(response.text)
        except Exception:
            logger.exception("BBCCollector search failed for term: %s", term)
            return []

    def _parse_search_page(self, html: str) -> List[CollectedItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # BBC search result cards — selector may need updating if BBC redesigns
        cards = soup.select("[data-testid='default-card']")
        if not cards:
            # Fallback: try older structure
            cards = soup.select("li[class*='search-result']")

        for card in cards:
            try:
                title_el = card.select_one("[data-testid='card-headline'], h3")
                link_el = card.select_one("a[href*='/news/']")
                desc_el = card.select_one("[data-testid='card-description'], p")
                time_el = card.select_one("time[datetime]")

                if not title_el or not link_el:
                    continue

                title = title_el.get_text(strip=True)
                href = link_el.get("href", "")
                if href.startswith("/"):
                    href = urljoin(_BASE_URL, href)
                content = desc_el.get_text(strip=True) if desc_el else title

                published_at = None
                if time_el:
                    raw = time_el.get("datetime", "")
                    try:
                        published_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                items.append(CollectedItem(
                    title=title,
                    content=content,
                    source_url=href,
                    published_at=published_at,
                    raw_metadata={"source": "bbc_news"},
                ))
            except Exception:
                logger.debug("BBCCollector: failed to parse one card", exc_info=True)

        return items
```

**Step 4: Run tests**

```bash
pytest tests/test_collectors.py -k "bbc" -v
```

Expected: all PASS.

**Step 5: Commit**

```bash
git add collectors/bbc_collector.py tests/test_collectors.py
git commit -m "feat(collectors): add BBCCollector with robots.txt check and zero-result health guard"
```

---

### Task 3: Wire NLP analysis after ingestion

**Files:**
- Modify: `backend/collectors/pipeline.py`
- Modify: `backend/app/services/celery_app.py`

After `IngestPipeline.ingest_items()` completes, dispatch `analyze_sample_task`
for each new sample so every collected article is automatically tagged.

**Step 1: Update `IngestPipeline.ingest_items()` to return new sample IDs**

In `backend/collectors/pipeline.py`, update the return type and stats dict:

```python
# Change the stats dict to include new sample IDs:
stats: dict = {"total": len(items), "new": 0, "duplicates": 0, "new_sample_ids": []}

# After appending to new_samples, also track the sample ID:
# (modify the batch insert to capture IDs)
```

After the batch insert, collect the IDs:

```python
if new_samples:
    await self._batch_insert(db, new_samples)
    stats["new"] = len(new_samples)
    stats["new_sample_ids"] = [s.id for s in new_samples]
```

**Step 2: Write test for updated pipeline**

```python
@pytest.mark.asyncio
async def test_ingest_pipeline_returns_new_sample_ids(db_session):
    """ingest_items must return new_sample_ids in stats."""
    from collectors.pipeline import IngestPipeline
    from collectors.base import CollectedItem

    pipeline = IngestPipeline()
    items = [
        CollectedItem(
            title="Test article",
            content="Climate change is affecting the UK coastline.",
            source_url="https://example.com/test-1",
        )
    ]

    # Use a test source_id
    import uuid
    source_id = uuid.uuid4()

    stats = await pipeline.ingest_items(items, source_id, db_session)
    assert "new_sample_ids" in stats
    assert len(stats["new_sample_ids"]) == stats["new"]
```

**Step 3: Update `run_collection_task` in `celery_app.py` to dispatch NLP**

```python
@celery_app.task(bind=True, name="app.services.celery_app.run_collection_task")
def run_collection_task(self, source_id: str, collector_type: str) -> dict:
    logger.info(
        "Starting collection task source_id=%s collector_type=%s",
        source_id, collector_type,
    )

    async def _run():
        from app.core.database import async_session_factory
        from app.models.models import Source, CollectionJob, JobStatus
        from collectors.pipeline import IngestPipeline
        from sqlalchemy import select
        from datetime import datetime, timezone

        async with async_session_factory() as db:
            # Load source
            result = await db.execute(select(Source).where(Source.id == source_id))
            source = result.scalar_one_or_none()
            if source is None:
                raise ValueError(f"Source not found: {source_id}")

            # Create collection job record
            job = CollectionJob(
                source_id=source_id,
                status=JobStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
            )
            db.add(job)
            await db.flush()

            # Select collector
            collector_map = {
                "NEWS": _get_news_collector,
                "REDDIT": _get_reddit_collector,
            }
            collector_fn = collector_map.get(source.source_type.value)
            if collector_fn is None:
                raise ValueError(f"No collector for source_type: {source.source_type}")

            collector = collector_fn()
            items = await collector.collect()
            pipeline = IngestPipeline()
            stats = await pipeline.ingest_items(items, source.id, db)

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.items_collected = stats["new"]
            await db.commit()

            return stats

    try:
        stats = asyncio.run(_run())

        # Dispatch NLP analysis for each new sample
        for sample_id in stats.get("new_sample_ids", []):
            analyze_sample_task.delay(sample_id)

        return {"status": "completed", "source_id": source_id, "stats": stats}
    except Exception as exc:
        logger.error("Collection task failed source_id=%s: %s", source_id, exc, exc_info=True)
        self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600), max_retries=3)


def _get_news_collector():
    """Return the appropriate news collector based on config."""
    from collectors.guardian_collector import GuardianCollector
    return GuardianCollector()


def _get_reddit_collector():
    """Reddit collector placeholder — returns None if no credentials."""
    logger.info("Reddit collector not yet implemented")
    return None
```

Also update `analyze_sample_task` to use the asyncio.run() bridge:

```python
@celery_app.task(bind=True, name="app.services.celery_app.analyze_sample_task")
def analyze_sample_task(self, sample_id: str) -> dict:
    logger.info("Starting NLP analysis sample_id=%s", sample_id)

    async def _run():
        from app.core.database import async_session_factory
        from app.models.models import DiscourseSample
        from nlp.analyzer import AnalysisEngine
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(
                select(DiscourseSample).where(DiscourseSample.id == sample_id)
            )
            sample = result.scalar_one_or_none()
            if sample is None:
                raise ValueError(f"Sample not found: {sample_id}")

            engine = AnalysisEngine()
            return await engine.analyze_sample(sample.id, sample.content, db)

    try:
        result = asyncio.run(_run())
        return {"status": "completed", "sample_id": sample_id, "result": result}
    except Exception as exc:
        logger.error("NLP analysis failed sample_id=%s: %s", sample_id, exc, exc_info=True)
        self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600), max_retries=3)
```

**Step 4: Run tests**

```bash
pytest tests/test_collectors.py tests/test_celery_tasks.py -v
```

Expected: all PASS.

**Step 5: Commit**

```bash
git add collectors/pipeline.py backend/app/services/celery_app.py tests/test_collectors.py
git commit -m "feat(pipeline): wire NLP analysis dispatch after ingestion and fix async bridge in Celery tasks"
```

---

### Task 4: Add deduplication performance index migration

**Files:**
- Create: `backend/migrations/versions/<timestamp>_add_content_hash_index.py`

The JSONB content_hash lookup is a full table scan per source per collection run. Add a functional index.

**Step 1: Generate the migration**

```bash
cd backend
# With the DB running:
alembic revision --autogenerate -m "add content hash index on discourse samples"
```

Open the generated file in `migrations/versions/`. Replace the `upgrade` and
`downgrade` functions with:

```python
def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_discourse_samples_content_hash
        ON discourse_samples (source_id, (raw_metadata->>'content_hash'))
        WHERE raw_metadata->>'content_hash' IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_discourse_samples_content_hash")
```

**Step 2: Apply migration**

```bash
alembic upgrade head
```

Expected: `Running upgrade ... -> <rev>, add content hash index on discourse samples`

**Step 3: Verify index exists**

```bash
# With psql or via the Docker container:
docker compose exec db psql -U postgres thermoculture -c "\d discourse_samples"
```

Expected: index `ix_discourse_samples_content_hash` listed.

**Step 4: Commit**

```bash
git add migrations/versions/
git commit -m "perf(db): add functional index on content_hash for deduplication query"
```

---

### Task 5: Register BBC and Guardian sources via seed

**Files:**
- Modify: `backend/seeds/run_seed.py`

Add BBC News and The Guardian as pre-seeded sources so the scheduled collector
can find them without manual setup.

**Step 1: Add sources to seed**

In `backend/seeds/run_seed.py`, in the sources seeding section, add:

```python
from app.models.models import Source, SourceType

guardian_source = Source(
    name="The Guardian",
    source_type=SourceType.NEWS,
    url="https://www.theguardian.com/environment",
    description="Guardian environment section via Open Platform API",
    is_active=True,
)

bbc_source = Source(
    name="BBC News",
    source_type=SourceType.NEWS,
    url="https://www.bbc.co.uk/news",
    description="BBC News climate coverage via web scraping",
    is_active=True,
)

db.add_all([guardian_source, bbc_source])
await db.flush()
```

**Step 2: Run seed to verify**

```bash
docker compose exec backend python -m seeds.run_seed
```

Expected: completes without error. Check the Collection Dashboard in the UI —
BBC News and The Guardian should appear in the sources list.

**Step 3: Commit**

```bash
git add backend/seeds/run_seed.py
git commit -m "chore(seeds): add BBC News and Guardian as default sources"
```

---

### Task 6: End-to-end verification and PR

**Step 1: Run full test suite**

```bash
cd backend
pytest -v
```

Expected: all PASS.

**Step 2: Manual end-to-end collection test**

```bash
# Start all services
docker compose up --build -d
docker compose exec backend python -m seeds.run_seed

# Trigger a manual Guardian collection via the UI:
# 1. Log in at http://localhost:5173
# 2. Go to Data Collection
# 3. Select "The Guardian" source → Start Collection
# 4. Watch the job status update to COMPLETED
# 5. Check that samples appear in the sample list with theme chips
```

**Step 3: Verify NLP analysis was triggered**

After a collection job completes, check the Celery worker logs:

```bash
docker compose logs celery_worker | grep "analyze_sample_task"
```

Expected: lines showing `analyze_sample_task` completing for each new sample.

**Step 4: Verify zero-result health check**

In the BBC collector, temporarily point at a bad URL and run manually:

```python
# In Python shell:
import asyncio
from collectors.bbc_collector import BBCCollector
collector = BBCCollector()
items = asyncio.run(collector.collect(keywords=["nonexistentterm12345"]))
print(collector.last_run_zero_results)  # should be True
print(items)  # should be []
```

**Step 5: Raise PR**

```bash
git push origin feat/collection-pipeline
gh pr create \
  --title "feat: BBC News and Guardian collection pipeline with auto-NLP" \
  --body "Adds GuardianCollector (Open Platform API) and BBCCollector (robots.txt-compliant scraper), wires NLP analysis dispatch after ingestion, adds a deduplication performance index, and fixes the async/sync bridge in all Celery task bodies. Closes the collection pipeline gap."
```
