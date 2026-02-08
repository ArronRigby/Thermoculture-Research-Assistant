"""
Collection job scheduler.

Orchestrates running data collectors for registered sources and records the
outcome in :class:`CollectionJob` rows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from loguru import logger  # type: ignore[import-untyped]

    _USE_LOGURU = True
except ImportError:
    import logging as _logging

    _USE_LOGURU = False
    _stdlib_logger = _logging.getLogger("scheduler")


class _LogAdapter:
    """
    Thin adapter so that the rest of this module can use loguru-style
    ``logger.info("msg {key}", key=val)`` calls regardless of whether
    loguru is installed.  When loguru is present the calls go straight
    through; otherwise they are converted to stdlib %-style formatting.
    """

    def _format(self, msg: str, kwargs: dict) -> str:  # noqa: ANN001
        try:
            return msg.format(**kwargs)
        except (KeyError, IndexError):
            return msg

    def info(self, msg: str, **kw: object) -> None:
        if _USE_LOGURU:
            logger.info(msg, **kw)  # type: ignore[union-attr]
        else:
            _stdlib_logger.info(self._format(msg, kw))

    def warning(self, msg: str, **kw: object) -> None:
        if _USE_LOGURU:
            logger.warning(msg, **kw)  # type: ignore[union-attr]
        else:
            _stdlib_logger.warning(self._format(msg, kw))

    def error(self, msg: str, **kw: object) -> None:
        if _USE_LOGURU:
            logger.error(msg, **kw)  # type: ignore[union-attr]
        else:
            _stdlib_logger.error(self._format(msg, kw))

    def debug(self, msg: str, **kw: object) -> None:
        if _USE_LOGURU:
            logger.debug(msg, **kw)  # type: ignore[union-attr]
        else:
            _stdlib_logger.debug(self._format(msg, kw))


log = _LogAdapter()

from app.models.models import CollectionJob, JobStatus, Source, SourceType
from collectors.base import BaseCollector
from collectors.news_collector import BBCNewsCollector, GuardianCollector
from collectors.reddit_collector import RedditCollector
from collectors.pipeline import IngestPipeline


# ---------------------------------------------------------------------------
# Mapping from source_type / collector_type strings to collector factories.
# ---------------------------------------------------------------------------

_COLLECTOR_REGISTRY: dict[str, type[BaseCollector]] = {
    "news_bbc": BBCNewsCollector,
    "news_guardian": GuardianCollector,
    "reddit": RedditCollector,
    # Aliases that match the SourceType enum values (upper-case).
    "NEWS": BBCNewsCollector,       # Default news collector; override per source.
    "REDDIT": RedditCollector,
}


def _get_collector(collector_type: str, source: Optional[Source] = None) -> BaseCollector:
    """
    Instantiate the correct collector for *collector_type*.

    If a ``Source`` row is provided its ``rate_limit_seconds`` value (if
    stored) is forwarded to the collector.  For news sources we inspect the
    source name to decide between BBC and Guardian.
    """
    # Try an exact match first.
    cls = _COLLECTOR_REGISTRY.get(collector_type)

    # For the generic "NEWS" type, refine based on source name/url.
    if cls is BBCNewsCollector and source is not None:
        name_lower = (source.name or "").lower()
        url_lower = (source.url or "").lower()
        if "guardian" in name_lower or "theguardian" in url_lower:
            cls = GuardianCollector

    if cls is None:
        raise ValueError(f"Unknown collector type: {collector_type!r}")

    return cls()


class CollectionScheduler:
    """
    High-level scheduler that runs collection jobs and records results.
    """

    def __init__(self) -> None:
        self.pipeline = IngestPipeline()

    # ------------------------------------------------------------------
    # Run a single collection job
    # ------------------------------------------------------------------

    async def run_collection_job(
        self,
        source_id: UUID,
        collector_type: str,
        db: AsyncSession,
    ) -> CollectionJob:
        """
        Execute a full collection cycle for one source.

        1. Create a :class:`CollectionJob` in ``PENDING`` state.
        2. Update to ``RUNNING``.
        3. Instantiate the correct collector and call ``collect()``.
        4. Pipe results through :class:`IngestPipeline`.
        5. Update the job to ``COMPLETED`` or ``FAILED``.

        Returns the finalised :class:`CollectionJob` instance.
        """
        # Fetch the source row (needed for smart collector selection).
        source = await db.get(Source, source_id)
        if source is None:
            raise ValueError(f"Source {source_id} not found")

        # -- Step 1: create the job record in PENDING state -------------
        job = CollectionJob(
            source_id=source_id,
            status=JobStatus.PENDING,
            items_collected=0,
        )
        db.add(job)
        await db.flush()

        log.info(
            "Created collection job {job_id} for source {source_name} ({collector_type})",
            job_id=str(job.id),
            source_name=source.name,
            collector_type=collector_type,
        )

        # -- Step 2: transition to RUNNING ------------------------------
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        await db.flush()

        try:
            # -- Step 3: run the collector ------------------------------
            collector = _get_collector(collector_type, source=source)
            log.info(
                "Running collector {cls} for job {job_id}",
                cls=type(collector).__name__,
                job_id=str(job.id),
            )
            items = await collector.collect()

            # -- Step 4: ingest collected items -------------------------
            stats = await self.pipeline.ingest_items(
                items=items,
                source_id=source_id,
                db=db,
            )

            # -- Step 5a: mark as COMPLETED -----------------------------
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.items_collected = stats.get("new", 0)

            log.info(
                "Job {job_id} completed: {stats}",
                job_id=str(job.id),
                stats=stats,
            )

        except Exception as exc:
            # -- Step 5b: mark as FAILED --------------------------------
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = f"{type(exc).__name__}: {exc}"

            log.error(
                "Job {job_id} failed: {error}",
                job_id=str(job.id),
                error=str(exc),
            )

        # Persist the final job state.
        await db.flush()
        return job

    # ------------------------------------------------------------------
    # Schedule all active sources
    # ------------------------------------------------------------------

    async def schedule_all_active_sources(self, db: AsyncSession) -> list[CollectionJob]:
        """
        Iterate over every active :class:`Source` and run a collection job
        for each.

        Returns the list of completed (or failed) :class:`CollectionJob`
        records.
        """
        stmt = select(Source).where(Source.is_active.is_(True))
        result = await db.execute(stmt)
        sources = result.scalars().all()

        if not sources:
            log.warning("No active sources found -- nothing to schedule")
            return []

        log.info(
            "Scheduling collection for {n} active source(s)", n=len(sources)
        )

        jobs: list[CollectionJob] = []

        for source in sources:
            collector_type = self._resolve_collector_type(source)
            try:
                job = await self.run_collection_job(
                    source_id=source.id,
                    collector_type=collector_type,
                    db=db,
                )
                jobs.append(job)
            except Exception as exc:
                log.error(
                    "Failed to run job for source {source_name}: {error}",
                    source_name=source.name,
                    error=str(exc),
                )

        log.info(
            "Scheduling round complete: {completed}/{total} jobs succeeded",
            completed=sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
            total=len(jobs),
        )
        return jobs

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_collector_type(source: Source) -> str:
        """
        Determine the collector type string to use for a source.

        Uses the ``source_type`` enum value as the primary key, but also
        checks the source name/URL for more specific matching (e.g.
        distinguishing BBC from Guardian).
        """
        source_type_val = source.source_type
        # Handle both enum members and plain strings.
        type_str = source_type_val.value if hasattr(source_type_val, "value") else str(source_type_val)

        # For NEWS sources, refine to BBC or Guardian.
        if type_str == SourceType.NEWS.value or type_str == "NEWS":
            name_lower = (source.name or "").lower()
            url_lower = (source.url or "").lower()
            if "guardian" in name_lower or "theguardian" in url_lower:
                return "news_guardian"
            if "bbc" in name_lower or "bbc.co.uk" in url_lower:
                return "news_bbc"
            # Default to BBC for unrecognised news sources.
            return "news_bbc"

        if type_str == SourceType.REDDIT.value or type_str == "REDDIT":
            return "reddit"

        # Fallback: use the raw type string.
        return type_str
