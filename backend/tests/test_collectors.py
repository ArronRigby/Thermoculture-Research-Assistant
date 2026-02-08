import pytest
from collectors.base import CollectedItem, BaseCollector
from collectors.locations import find_locations
from collectors.pipeline import IngestPipeline
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
        pipeline = IngestPipeline()
        text = "  Hello   World  \n\n  "
        normalized = pipeline._normalize_text(text)
        assert normalized == "Hello World"

    def test_content_hash(self):
        pipeline = IngestPipeline()
        hash1 = pipeline._compute_hash("Hello World")
        hash2 = pipeline._compute_hash("Hello World")
        hash3 = pipeline._compute_hash("Different content")
        assert hash1 == hash2
        assert hash1 != hash3
