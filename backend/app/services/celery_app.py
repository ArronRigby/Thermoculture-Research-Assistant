"""
Celery application configuration for Thermoculture Research Assistant.

Handles asynchronous task processing for data collection and NLP analysis.
"""

import os
import logging

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Celery app initialization
# ---------------------------------------------------------------------------

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "thermoculture",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task behaviour
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Result expiry (24 hours)
    result_expires=86400,
)

# ---------------------------------------------------------------------------
# Beat schedule
# ---------------------------------------------------------------------------

celery_app.conf.beat_schedule = {
    "scheduled-collection-every-6-hours": {
        "task": "app.services.celery_app.scheduled_collection",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, name="app.services.celery_app.run_collection_task")
def run_collection_task(self, source_id: str, collector_type: str) -> dict:
    """
    Run a data collection job for a given source.

    Parameters
    ----------
    source_id : str
        Unique identifier of the data source to collect from.
    collector_type : str
        Type of collector to use (e.g. "reddit", "arxiv", "web").

    Returns
    -------
    dict
        Summary of the collection run including counts and status.
    """
    logger.info(
        "Starting collection task for source_id=%s with collector_type=%s",
        source_id,
        collector_type,
    )

    try:
        # Import collectors dynamically based on collector_type
        if collector_type == "reddit":
            from app.collectors.reddit_collector import RedditCollector

            collector = RedditCollector()
        elif collector_type == "arxiv":
            from app.collectors.arxiv_collector import ArxivCollector

            collector = ArxivCollector()
        elif collector_type == "web":
            from app.collectors.web_collector import WebCollector

            collector = WebCollector()
        else:
            raise ValueError(f"Unknown collector type: {collector_type}")

        result = collector.collect(source_id)

        logger.info(
            "Collection task completed for source_id=%s: %s",
            source_id,
            result,
        )
        return {
            "status": "completed",
            "source_id": source_id,
            "collector_type": collector_type,
            "result": result,
        }

    except Exception as exc:
        logger.error(
            "Collection task failed for source_id=%s: %s",
            source_id,
            str(exc),
            exc_info=True,
        )
        self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True, name="app.services.celery_app.analyze_sample_task")
def analyze_sample_task(self, sample_id: str) -> dict:
    """
    Run NLP analysis on a collected sample.

    Parameters
    ----------
    sample_id : str
        Unique identifier of the sample to analyze.

    Returns
    -------
    dict
        Analysis results including extracted entities, sentiment, and topics.
    """
    logger.info("Starting NLP analysis for sample_id=%s", sample_id)

    try:
        from app.nlp.analyzer import Analyzer

        analyzer = Analyzer()
        result = analyzer.analyze(sample_id)

        logger.info(
            "NLP analysis completed for sample_id=%s: %s",
            sample_id,
            result,
        )
        return {
            "status": "completed",
            "sample_id": sample_id,
            "result": result,
        }

    except Exception as exc:
        logger.error(
            "NLP analysis failed for sample_id=%s: %s",
            sample_id,
            str(exc),
            exc_info=True,
        )
        self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(name="app.services.celery_app.scheduled_collection")
def scheduled_collection() -> dict:
    """
    Run collection for all active data sources.

    This task is triggered by the Celery beat schedule every 6 hours.
    It retrieves all active sources from the database and dispatches
    individual collection tasks for each one.

    Returns
    -------
    dict
        Summary of dispatched collection tasks.
    """
    logger.info("Starting scheduled collection for all active sources")

    try:
        from app.models.source import Source
        from app.db.session import get_sync_session

        dispatched = []

        with get_sync_session() as session:
            active_sources = (
                session.query(Source).filter(Source.is_active.is_(True)).all()
            )

            for source in active_sources:
                run_collection_task.delay(
                    source_id=str(source.id),
                    collector_type=source.collector_type,
                )
                dispatched.append(
                    {
                        "source_id": str(source.id),
                        "collector_type": source.collector_type,
                    }
                )

        logger.info(
            "Scheduled collection dispatched %d tasks", len(dispatched)
        )
        return {
            "status": "completed",
            "dispatched_count": len(dispatched),
            "dispatched": dispatched,
        }

    except Exception as exc:
        logger.error(
            "Scheduled collection failed: %s", str(exc), exc_info=True
        )
        raise
