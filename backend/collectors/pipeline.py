"""
Data ingestion pipeline.

Responsible for transforming :class:`CollectedItem` instances into
:class:`DiscourseSample` database records, de-duplicating on content hash,
normalising text, and attempting location resolution.
"""

from __future__ import annotations

import hashlib
import logging
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DiscourseSample, Location, Region
from collectors.base import CollectedItem
from collectors.locations import find_locations, UK_LOCATIONS

logger = logging.getLogger("pipeline.ingest")


class IngestPipeline:
    """
    Transforms raw :class:`CollectedItem` objects into persisted
    :class:`DiscourseSample` rows.

    Key responsibilities:

    * **Deduplication** -- an MD5 hash of the normalised content is stored in
      ``DiscourseSample.raw_metadata["content_hash"]``.  If a row with the same
      hash already exists, the item is silently skipped.
    * **Text normalisation** -- whitespace is collapsed, Unicode is NFC-
      normalised.
    * **Location resolution** -- ``location_hints`` (and the body text itself)
      are matched against a known set of UK locations; if a match is found the
      corresponding ``Location`` row is linked.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ingest_items(
        self,
        items: list[CollectedItem],
        source_id: UUID,
        db: AsyncSession,
    ) -> dict[str, int]:
        """
        Process a batch of collected items and persist new ones.

        Parameters
        ----------
        items:
            The items to ingest.
        source_id:
            The UUID of the :class:`Source` these items belong to.
        db:
            An active async database session.

        Returns
        -------
        dict:
            ``{"total": N, "new": N, "duplicates": N}``
        """
        stats: dict[str, int] = {"total": len(items), "new": 0, "duplicates": 0}

        if not items:
            return stats

        # Pre-load existing hashes so we can check duplicates in bulk.
        existing_hashes = await self._load_existing_hashes(db, source_id)

        # Pre-load location lookup from the database.
        location_cache = await self._load_location_cache(db)

        new_samples: list[DiscourseSample] = []

        for item in items:
            normalised_content = _normalise_text(item.content)
            content_hash = _content_hash(normalised_content)

            if content_hash in existing_hashes:
                stats["duplicates"] += 1
                continue

            # Mark this hash as "seen" to prevent intra-batch duplicates.
            existing_hashes.add(content_hash)

            # Resolve location.
            location_id = self._resolve_location(
                item=item,
                normalised_content=normalised_content,
                location_cache=location_cache,
            )

            # Build raw_metadata, including the content hash for future lookups.
            metadata = dict(item.raw_metadata) if item.raw_metadata else {}
            metadata["content_hash"] = content_hash
            if item.location_hints:
                metadata["location_hints"] = item.location_hints

            sample = DiscourseSample(
                title=_normalise_text(item.title)[:512],
                content=normalised_content,
                source_id=source_id,
                source_url=item.source_url[:2048] if item.source_url else "",
                author=item.author[:255] if item.author else None,
                published_at=item.published_at,
                collected_at=datetime.now(timezone.utc),
                location_id=location_id,
                raw_metadata=metadata,
            )
            new_samples.append(sample)

        # Batch insert.
        if new_samples:
            await self._batch_insert(db, new_samples)
            stats["new"] = len(new_samples)

        logger.info(
            "Ingest complete: total=%d, new=%d, duplicates=%d",
            stats["total"],
            stats["new"],
            stats["duplicates"],
        )
        return stats

    # ------------------------------------------------------------------
    # Location resolution
    # ------------------------------------------------------------------

    def _resolve_location(
        self,
        item: CollectedItem,
        normalised_content: str,
        location_cache: dict[str, UUID],
    ) -> Optional[UUID]:
        """
        Attempt to find a matching Location row for this item.

        We first look at ``item.location_hints`` (already extracted by the
        collector), then fall back to scanning the normalised body text.
        """
        # Try each hint from the collector.
        for hint in item.location_hints:
            loc_key = hint.lower()
            if loc_key in location_cache:
                return location_cache[loc_key]

        # Fallback: run find_locations on the content.
        matches = find_locations(normalised_content)
        for match in matches:
            loc_key = match["name"].lower()
            if loc_key in location_cache:
                return location_cache[loc_key]

        return None

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _load_existing_hashes(db: AsyncSession, source_id: UUID) -> set[str]:
        """
        Load all existing content_hash values for a given source.

        We store the hash inside ``raw_metadata->>'content_hash'``.
        For performance, this queries only the JSONB field.
        """
        stmt = (
            select(DiscourseSample.raw_metadata["content_hash"].as_string())
            .where(DiscourseSample.source_id == source_id)
            .where(DiscourseSample.raw_metadata["content_hash"].as_string().isnot(None))
        )
        result = await db.execute(stmt)
        return {row[0] for row in result.all() if row[0]}

    @staticmethod
    async def _load_location_cache(db: AsyncSession) -> dict[str, UUID]:
        """
        Build a mapping of lower-cased location names to their database UUIDs.
        """
        stmt = select(Location.id, Location.name)
        result = await db.execute(stmt)
        return {row.name.lower(): row.id for row in result.all()}

    @staticmethod
    async def _batch_insert(
        db: AsyncSession,
        samples: list[DiscourseSample],
        batch_size: int = 100,
    ) -> None:
        """
        Insert samples in batches, handling individual row conflicts
        gracefully.
        """
        for start in range(0, len(samples), batch_size):
            batch = samples[start : start + batch_size]
            for sample in batch:
                db.add(sample)

            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                # Fall back to one-by-one insertion so a single duplicate
                # doesn't block the whole batch.
                logger.warning(
                    "Batch insert hit IntegrityError -- falling back to "
                    "row-by-row insert for %d items",
                    len(batch),
                )
                for sample in batch:
                    try:
                        db.add(sample)
                        await db.flush()
                    except IntegrityError:
                        await db.rollback()
                        logger.debug(
                            "Skipped duplicate sample: %s", sample.title[:80]
                        )
                    except Exception:
                        await db.rollback()
                        logger.exception(
                            "Unexpected error inserting sample: %s",
                            sample.title[:80],
                        )
            except Exception:
                await db.rollback()
                logger.exception("Unexpected error during batch flush")

        # Final commit is handled by the caller / session context manager,
        # but we flush here to surface errors early.
        try:
            await db.flush()
        except Exception:
            await db.rollback()
            logger.exception("Final flush failed")


# ---------------------------------------------------------------------------
# Text normalisation utilities
# ---------------------------------------------------------------------------

def _normalise_text(text: str) -> str:
    """
    Normalise a text string:

    1. NFC Unicode normalisation.
    2. Strip leading/trailing whitespace.
    3. Collapse internal runs of whitespace to a single space.
    4. Remove null bytes.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\x00", "")
    text = " ".join(text.split())
    return text.strip()


def _content_hash(normalised_content: str) -> str:
    """
    Compute an MD5 hex digest of the normalised content string.

    MD5 is used here purely as a fast fingerprint for deduplication, not for
    any cryptographic purpose.
    """
    return hashlib.md5(normalised_content.encode("utf-8")).hexdigest()
