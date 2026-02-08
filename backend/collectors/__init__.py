"""
Thermoculture Research Assistant -- Data Collectors Package.

This package provides data collection infrastructure for gathering climate
discourse from UK-focused web sources.  It includes:

- **base** -- Abstract :class:`BaseCollector` and :class:`CollectedItem` dataclass.
- **news_collector** -- :class:`BBCNewsCollector` and :class:`GuardianCollector`.
- **reddit_collector** -- :class:`RedditCollector` (via asyncpraw).
- **locations** -- UK location reference data and :func:`find_locations` matcher.
- **pipeline** -- :class:`IngestPipeline` for deduplication, normalisation, and persistence.
- **scheduler** -- :class:`CollectionScheduler` for orchestrating collection jobs.
"""

from collectors.base import BaseCollector, CollectedItem
from collectors.news_collector import BBCNewsCollector, GuardianCollector
from collectors.reddit_collector import RedditCollector
from collectors.locations import find_locations, UK_LOCATIONS
from collectors.pipeline import IngestPipeline
from collectors.scheduler import CollectionScheduler

__all__ = [
    # Base
    "BaseCollector",
    "CollectedItem",
    # News collectors
    "BBCNewsCollector",
    "GuardianCollector",
    # Reddit collector
    "RedditCollector",
    # Location utilities
    "find_locations",
    "UK_LOCATIONS",
    # Pipeline
    "IngestPipeline",
    # Scheduler
    "CollectionScheduler",
]
