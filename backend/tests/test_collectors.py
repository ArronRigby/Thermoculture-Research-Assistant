import pytest
from collectors.base import CollectedItem, BaseCollector
from collectors.locations import find_locations
from collectors.pipeline import IngestPipeline, _normalise_text, _content_hash
from datetime import datetime

class TestCollectedItem:
    def test_create_item(self):
        item = CollectedItem(
            title="Test Article",
            content="Test content about climate change",
            source_url="https://example.com/article",
            author="Test Author",
        )
        assert item.title == "Test Article"
        assert item.location_hints == []
        assert item.raw_metadata == {}

class TestLocationFinder:
    def test_find_london(self):
        locations = find_locations("The flooding in London was severe")
        assert len(locations) > 0
        assert any(loc["name"] == "London" for loc in locations)

    def test_find_multiple(self):
        locations = find_locations("Travel between Manchester and Birmingham was disrupted")
        names = [loc["name"] for loc in locations]
        assert "Manchester" in names
        assert "Birmingham" in names

    def test_find_scottish_cities(self):
        locations = find_locations("Edinburgh and Glasgow both reported high winds")
        names = [loc["name"] for loc in locations]
        assert "Edinburgh" in names
        assert "Glasgow" in names

    def test_no_false_positives(self):
        locations = find_locations("I was reading a book about the weather")
        # "Reading" as a verb should not match the city
        reading_matches = [loc for loc in locations if loc["name"] == "Reading"]
        assert len(reading_matches) == 0

    def test_empty_text(self):
        locations = find_locations("")
        assert locations == []

class TestIngestPipeline:
    def test_normalize_text(self):
        text = "  Hello   World  \n\n  "
        normalized = _normalise_text(text)
        assert normalized == "Hello World"

    def test_content_hash(self):
        hash1 = _content_hash("Hello World")
        hash2 = _content_hash("Hello World")
        hash3 = _content_hash("Different content")
        assert hash1 == hash2
        assert hash1 != hash3

    @pytest.mark.asyncio
    async def test_ingest_pipeline_triggers_analysis(self, db_session, test_source):
        from app.models.models import SentimentAnalysis, DiscourseClassification, sample_themes
        from sqlalchemy import select

        pipeline = IngestPipeline()

        item1 = CollectedItem(
            title="Severe Flooding in London",
            content="London experienced severe flooding yesterday as heavy rains overwhelmed drainage systems.",
            source_url="https://example.com/london",
            author="Reporter A",
            location_hints=["London"],
        )
        item2 = CollectedItem(
            title="Adapting to Heatwaves",
            content="We installed solar panels and a heat pump to keep our home cool and reduce emissions.",
            source_url="https://example.com/heatwave",
            author="Reporter B",
            location_hints=[],
        )

        # Ingest items
        stats = await pipeline.ingest_items([item1, item2], test_source.id, db_session)

        # Assert correct stats are returned
        assert stats["new"] == 2
        assert stats["analyzed"] == 2

        # Verify SentimentAnalysis rows are created
        sentiments = (await db_session.execute(select(SentimentAnalysis))).scalars().all()
        assert len(sentiments) == 2
        assert any(s.overall_sentiment < 0 for s in sentiments) # Flooding is negative
        assert any(s.overall_sentiment > 0 for s in sentiments) # Solar panels/heat pump is positive

        # Verify DiscourseClassification rows are created
        classifications = (await db_session.execute(select(DiscourseClassification))).scalars().all()
        assert len(classifications) == 2
        types = [c.classification_type for c in classifications]
        assert "PRACTICAL_ADAPTATION" in types

        # Verify sample_themes links are created
        themes_links = (await db_session.execute(select(sample_themes))).all()
        assert len(themes_links) >= 1
