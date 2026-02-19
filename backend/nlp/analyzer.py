"""
Main analysis orchestrator for the Thermoculture Research Assistant.

Combines all NLP sub-modules (sentiment, themes, discourse classification,
geographic extraction) and persists results to the database via SQLAlchemy
async sessions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select, and_, insert
from sqlalchemy.ext.asyncio import AsyncSession

from nlp.sentiment import SentimentAnalyzer
from nlp.theme_extractor import ThemeExtractor
from nlp.classifier import DiscourseClassifier
from nlp.geographic import GeoExtractor

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """
    High-level orchestrator that runs every NLP analysis pipeline on a
    piece of content and stores the results in the database.
    """

    def __init__(self) -> None:
        self.sentiment_analyzer = SentimentAnalyzer()
        self.theme_extractor = ThemeExtractor()
        self.discourse_classifier = DiscourseClassifier()
        self.geo_extractor = GeoExtractor()

    # ------------------------------------------------------------------
    # Single-sample analysis
    # ------------------------------------------------------------------

    async def analyze_sample(
        self,
        sample_id: UUID,
        content: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Run the full analysis pipeline on a single text sample and
        persist the results.

        Parameters
        ----------
        sample_id : UUID
            The primary key of the sample record to annotate.
        content : str
            The raw text content to analyse.
        db : AsyncSession
            An active SQLAlchemy async session.

        Returns
        -------
        dict
            Combined analysis results.
        """
        # Run each analyser -------------------------------------------------
        sentiment_result = self.sentiment_analyzer.analyze(content)
        theme_results = self.theme_extractor.extract_themes(content)
        keywords = self.theme_extractor.get_keywords(content, top_n=10)
        classification_result = self.discourse_classifier.classify(content)
        location_results = self.geo_extractor.extract_locations(content)

        # Persist to database ------------------------------------------------
        await self._store_sentiment(db, sample_id, sentiment_result)
        await self._store_classification(db, sample_id, classification_result)
        await self._store_themes(db, sample_id, theme_results)
        await self._store_locations(db, sample_id, location_results)

        # Flush to get IDs assigned without committing the transaction
        await db.flush()

        return {
            "sample_id": str(sample_id),
            "sentiment": sentiment_result,
            "themes": theme_results,
            "keywords": keywords,
            "classification": classification_result,
            "locations": location_results,
        }

    # ------------------------------------------------------------------
    # Batch analysis
    # ------------------------------------------------------------------

    async def analyze_batch(
        self,
        sample_ids: List[UUID],
        contents: List[str],
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Run analysis on multiple samples.

        Parameters
        ----------
        sample_ids : list[UUID]
            Primary keys for each sample.
        contents : list[str]
            Corresponding text content for each sample.
        db : AsyncSession
            An active SQLAlchemy async session.

        Returns
        -------
        list[dict]
            One combined-result dict per sample.
        """
        if len(sample_ids) != len(contents):
            raise ValueError(
                "sample_ids and contents must have the same length."
            )

        results: List[Dict[str, Any]] = []
        for sid, content in zip(sample_ids, contents):
            try:
                result = await self.analyze_sample(sid, content, db)
                results.append(result)
            except Exception:
                logger.exception("Failed to analyse sample %s", sid)
                results.append({
                    "sample_id": str(sid),
                    "error": "Analysis failed",
                })

        return results

    # ------------------------------------------------------------------
    # Aggregated insights
    # ------------------------------------------------------------------

    async def get_aggregated_insights(
        self,
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Build an aggregated view of all analysis results, optionally
        filtered by date range.

        Returns
        -------
        dict
            Keys: sentiment_distribution, theme_frequency, geographic_distribution,
                  discourse_distribution, trending_themes.
        """
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

        # 1. Sentiment distribution -----------------------------------------
        sentiment_distribution = await self._aggregate_sentiment(
            db, SentimentAnalysis, _date_filter
        )

        # 2. Theme frequency counts -----------------------------------------
        theme_frequency = await self._aggregate_themes(
            db, sample_themes, Theme, _date_filter
        )

        # 3. Geographic distribution ----------------------------------------
        geographic_distribution = await self._aggregate_geography(
            db, DiscourseSample, Location, _date_filter
        )

        # 4. Discourse type distribution ------------------------------------
        discourse_distribution = await self._aggregate_discourse(
            db, DiscourseClassification, _date_filter
        )

        # 5. Trending themes ------------------------------------------------
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

    # ------------------------------------------------------------------
    # Private persistence helpers
    # ------------------------------------------------------------------

    async def _store_sentiment(
        self,
        db: AsyncSession,
        sample_id: UUID,
        result: Dict[str, Any],
    ) -> None:
        """Persist a SentimentAnalysis record."""
        try:
            from app.models.models import SentimentAnalysis
        except ImportError:
            logger.debug("SentimentAnalysis model not available; skipping persist.")
            return

        record = SentimentAnalysis(
            id=str(uuid4()),
            sample_id=str(sample_id),
            overall_sentiment=result["overall_sentiment"],
            sentiment_label=result["sentiment_label"],
            confidence=result["confidence"],
            analyzed_at=datetime.now(timezone.utc),
        )
        db.add(record)

    async def _store_classification(
        self,
        db: AsyncSession,
        sample_id: UUID,
        result: Dict[str, Any],
    ) -> None:
        """Persist a DiscourseClassification record."""
        try:
            from app.models.models import DiscourseClassification
        except ImportError:
            logger.debug("DiscourseClassification model not available; skipping persist.")
            return

        record = DiscourseClassification(
            id=str(uuid4()),
            sample_id=str(sample_id),
            classification_type=result["classification_type"],
            confidence=result["confidence"],
            classified_at=datetime.now(timezone.utc),
        )
        db.add(record)

    async def _store_themes(
        self,
        db: AsyncSession,
        sample_id: UUID,
        themes: List[Dict[str, Any]],
    ) -> None:
        """
        Persist theme links.  For each extracted theme, look up (or create)
        the Theme record and insert a row into the sample_themes association table.
        """
        from app.models.models import Theme, sample_themes

        for theme_data in themes:
            theme_name = theme_data["theme"]

            # Upsert theme
            stmt = select(Theme).where(Theme.name == theme_name)
            result = await db.execute(stmt)
            theme_record = result.scalar_one_or_none()

            if theme_record is None:
                theme_record = Theme(
                    id=str(uuid4()),
                    name=theme_name,
                )
                db.add(theme_record)
                await db.flush()

            # Check if already linked before inserting to avoid rolling back
            # the shared session on a duplicate-key error.
            existing = await db.execute(
                select(sample_themes).where(
                    (sample_themes.c.sample_id == str(sample_id))
                    & (sample_themes.c.theme_id == theme_record.id)
                )
            )
            if existing.first() is None:
                await db.execute(
                    insert(sample_themes).values(
                        sample_id=str(sample_id),
                        theme_id=theme_record.id,
                    )
                )
                await db.flush()

    async def _store_locations(
        self,
        db: AsyncSession,
        sample_id: UUID,
        locations: List[Dict[str, Any]],
    ) -> None:
        """
        Location is resolved by IngestPipeline and stored as DiscourseSample.location_id.
        This method is a no-op placeholder — location storage happens at ingestion time.
        """
        if locations:
            logger.debug(
                "_store_locations: %d locations noted (resolved at ingestion)",
                len(locations),
            )

    # ------------------------------------------------------------------
    # Private aggregation helpers
    # ------------------------------------------------------------------

    async def _aggregate_sentiment(
        self, db, SentimentAnalysis, _date_filter
    ) -> Dict[str, Any]:
        """Aggregate sentiment scores into a distribution."""
        try:
            base_query = select(
                SentimentAnalysis.sentiment_label,
                func.count(SentimentAnalysis.id).label("count"),
                func.avg(SentimentAnalysis.overall_sentiment).label("avg_score"),
            )

            date_conditions = _date_filter(SentimentAnalysis.analyzed_at)
            if date_conditions:
                base_query = base_query.where(and_(*date_conditions))

            base_query = base_query.group_by(SentimentAnalysis.sentiment_label)
            result = await db.execute(base_query)
            rows = result.all()

            distribution: Dict[str, Any] = {}
            for label, count, avg_score in rows:
                distribution[label] = {
                    "count": count,
                    "average_score": round(float(avg_score), 4) if avg_score else 0.0,
                }
            return distribution
        except Exception:
            logger.exception("Error aggregating sentiment data")
            return {}

    async def _aggregate_themes(
        self, db, sample_themes, Theme, _date_filter
    ) -> List[Dict[str, Any]]:
        """Count how often each theme appears."""
        try:
            stmt = (
                select(
                    Theme.name,
                    func.count(sample_themes.c.sample_id).label("count"),
                )
                .select_from(sample_themes)
                .join(Theme, sample_themes.c.theme_id == Theme.id)
                .group_by(Theme.name)
                .order_by(func.count(sample_themes.c.sample_id).desc())
            )
            result = await db.execute(stmt)
            return [{"theme": name, "count": count} for name, count in result.all()]
        except Exception:
            logger.exception("Error aggregating theme data")
            return []

    async def _aggregate_geography(
        self, db, DiscourseSample, Location, _date_filter
    ) -> Dict[str, Any]:
        """Count samples per region via DiscourseSample.location_id -> Location."""
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
            return {str(region): count for region, count in result.all()}
        except Exception:
            logger.exception("Error aggregating geographic data")
            return {}

    async def _aggregate_discourse(
        self, db, DiscourseClassification, _date_filter
    ) -> Dict[str, Any]:
        """Count discourse classification types."""
        try:
            base_query = select(
                DiscourseClassification.classification_type,
                func.count(DiscourseClassification.id).label("count"),
                func.avg(DiscourseClassification.confidence).label("avg_confidence"),
            )

            date_conditions = _date_filter(DiscourseClassification.classified_at)
            if date_conditions:
                base_query = base_query.where(and_(*date_conditions))

            base_query = base_query.group_by(
                DiscourseClassification.classification_type
            )

            result = await db.execute(base_query)
            rows = result.all()

            distribution: Dict[str, Any] = {}
            for cls_type, count, avg_conf in rows:
                distribution[cls_type] = {
                    "count": count,
                    "average_confidence": round(float(avg_conf), 4) if avg_conf else 0.0,
                }
            return distribution
        except Exception:
            logger.exception("Error aggregating discourse data")
            return {}

    async def _compute_trending_themes(
        self, db, sample_themes, Theme, DiscourseSample, _date_filter
    ) -> List[Dict[str, Any]]:
        """
        Compute trending themes by comparing recent frequency against
        historical frequency.  A theme is 'trending' when its recent share
        is higher than its historical share.
        """
        try:
            from datetime import timedelta

            # Total theme count (all time)
            total_result = await db.execute(
                select(func.count()).select_from(sample_themes)
            )
            total_all = total_result.scalar() or 1

            # Per-theme count (all time)
            all_time_stmt = (
                select(
                    Theme.name,
                    func.count(sample_themes.c.sample_id).label("count"),
                )
                .select_from(sample_themes)
                .join(Theme, sample_themes.c.theme_id == Theme.id)
                .group_by(Theme.name)
            )
            all_time_rows = {
                name: count
                for name, count in (await db.execute(all_time_stmt)).all()
            }

            # Recent theme count (last 30 days)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)

            recent_stmt = (
                select(
                    Theme.name,
                    func.count(sample_themes.c.sample_id).label("count"),
                )
                .select_from(sample_themes)
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

            recent_rows = {
                name: count
                for name, count in (await db.execute(recent_stmt)).all()
            }

            # Compute trend score: (recent_share - historical_share)
            trending: List[Dict[str, Any]] = []
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
