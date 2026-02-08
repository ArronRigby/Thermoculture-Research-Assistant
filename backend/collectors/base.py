"""
Abstract base collector for the Thermoculture Research Assistant.

All data collectors inherit from BaseCollector and implement the collect()
method to gather discourse samples from their respective sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import asyncio
import logging


@dataclass
class CollectedItem:
    """
    A single item gathered by a collector before it is persisted.

    This is a transport object that sits between the raw external data and the
    database model.  Every collector converts its source-specific format into
    one or more CollectedItem instances.
    """

    title: str
    content: str
    source_url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    location_hints: list[str] = field(default_factory=list)
    raw_metadata: dict = field(default_factory=dict)


class BaseCollector(ABC):
    """
    Abstract base class for all data collectors.

    Subclasses must implement :meth:`collect` which returns a list of
    :class:`CollectedItem` instances.  The base class provides common
    facilities such as rate-limiting and structured logging.
    """

    #: Climate-related search terms used across all collectors.
    CLIMATE_KEYWORDS: list[str] = [
        "climate change",
        "global warming",
        "net zero",
        "carbon",
        "flooding",
        "heatwave",
        "energy bills",
        "insulation",
    ]

    #: Default HTTP headers for web requests.
    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": (
            "ThermocultureResearchBot/1.0 "
            "(+https://github.com/thermoculture-research; "
            "academic research project)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    }

    def __init__(self, source_name: str, rate_limit_seconds: float = 2.0):
        """
        Parameters
        ----------
        source_name:
            Human-readable name for the data source, also used as the logger
            suffix (e.g. ``"bbc_news"``).
        rate_limit_seconds:
            Minimum number of seconds to wait between consecutive HTTP
            requests to this source.
        """
        self.source_name = source_name
        self.rate_limit_seconds = rate_limit_seconds
        self.logger = logging.getLogger(f"collector.{source_name}")
        self.items_collected: int = 0

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def collect(self, **kwargs) -> list[CollectedItem]:
        """
        Run the collection process and return gathered items.

        Subclasses should handle all source-specific logic here, including
        HTTP requests, parsing, and error handling.
        """
        ...

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _rate_limit(self) -> None:
        """Sleep for the configured rate-limit interval."""
        await asyncio.sleep(self.rate_limit_seconds)

    def _build_search_query(self, keywords: list[str] | None = None) -> str:
        """
        Build a combined search query string from the given keywords or the
        default climate keywords.

        Some sources accept OR-separated terms; this helper returns a
        space-separated string suitable for most search APIs.
        """
        terms = keywords or self.CLIMATE_KEYWORDS
        return " OR ".join(f'"{term}"' for term in terms)
