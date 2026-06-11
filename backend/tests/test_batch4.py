import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy import select

from app.models.models import Source, SourceType, DiscourseSample, SentimentAnalysis, SentimentLabel, Theme, DiscourseClassification, ClassificationType

pytestmark = pytest.mark.asyncio

class TestBatch4:
    async def test_task1_sentiment_sorting_duplication(self, client: AsyncClient, auth_headers, db_session, test_source):
        # Create 3 samples
        sample_a = DiscourseSample(id=str(uuid4()), title="Sample A", content="Content A", source_id=test_source.id, collected_at=datetime.now(timezone.utc) - timedelta(minutes=3))
        sample_b = DiscourseSample(id=str(uuid4()), title="Sample B", content="Content B", source_id=test_source.id, collected_at=datetime.now(timezone.utc) - timedelta(minutes=2))
        sample_c = DiscourseSample(id=str(uuid4()), title="Sample C", content="Content C", source_id=test_source.id, collected_at=datetime.now(timezone.utc) - timedelta(minutes=1))
        db_session.add_all([sample_a, sample_b, sample_c])
        await db_session.commit()

        # For Sample A: two sentiment analysis rows
        s1 = SentimentAnalysis(id=str(uuid4()), sample_id=sample_a.id, overall_sentiment=0.5, sentiment_label=SentimentLabel.POSITIVE, confidence=0.9, analyzed_at=datetime.now(timezone.utc) - timedelta(minutes=5))
        s2 = SentimentAnalysis(id=str(uuid4()), sample_id=sample_a.id, overall_sentiment=0.8, sentiment_label=SentimentLabel.VERY_POSITIVE, confidence=0.95, analyzed_at=datetime.now(timezone.utc) - timedelta(minutes=1))
        
        # For Sample B: one sentiment analysis row
        s3 = SentimentAnalysis(id=str(uuid4()), sample_id=sample_b.id, overall_sentiment=0.2, sentiment_label=SentimentLabel.NEUTRAL, confidence=0.8, analyzed_at=datetime.now(timezone.utc) - timedelta(minutes=4))
        
        # Sample C: zero sentiment analysis rows

        db_session.add_all([s1, s2, s3])
        await db_session.commit()

        # Request page_size=10 sorted by sentiment desc
        response = await client.get("/api/v1/samples/?sort_by=sentiment&sort_order=desc&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        items = data["items"]
        assert len(items) == 3

        # Check for duplicates: sample ID should be unique in the list
        item_ids = [item["id"] for item in items]
        assert len(item_ids) == len(set(item_ids)), f"Duplicate samples returned: {item_ids}"

    async def test_task2_sort_by_whitelist_fallback(self, client: AsyncClient, auth_headers, test_sample):
        # Request with sorting by a non-whitelisted parameter "themes"
        response = await client.get("/api/v1/samples/?sort_by=themes", headers=auth_headers)
        assert response.status_code == 200
        # No 500 internal server error should occur, and it should return the samples list successfully

    async def test_task3_theme_frequencies_outer_join(self, client: AsyncClient, auth_headers, db_session, test_theme):
        # Ensure there is a theme with 0 sample links (test_theme has no samples linked to it)
        # Call theme-frequencies
        response = await client.get("/api/v1/analysis/theme-frequencies", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Verify test_theme is present with count 0
        theme_names = [t["theme_name"] for t in data]
        assert test_theme.name in theme_names
        
        theme_item = next(t for t in data if t["theme_name"] == test_theme.name)
        assert theme_item["count"] == 0

        # Verify theme-frequency endpoint returns 404 (or is deleted/does not exist)
        old_route_response = await client.get("/api/v1/analysis/theme-frequency", headers=auth_headers)
        assert old_route_response.status_code == 404

    async def test_task4_citation_preview(self, client: AsyncClient, auth_headers, db_session, test_sample, test_source):
        # We need sample's source relationship loaded and populated
        # Update test_sample's author/title to make it concrete
        test_sample.author = "Dr. Jane Doe"
        test_sample.title = "A Study on Thermoculture"
        test_sample.source_url = "https://example.com/study"
        test_sample.published_at = datetime(2026, 6, 11, tzinfo=timezone.utc)
        await db_session.commit()

        # Check preview GET /citations/preview
        # APA preview
        response_apa = await client.get(f"/api/v1/citations/preview?sample_id={test_sample.id}&format=APA", headers=auth_headers)
        assert response_apa.status_code == 200
        assert "Jane Doe" in response_apa.json()["citation_text"]
        assert "A Study on Thermoculture" in response_apa.json()["citation_text"]
        assert "Retrieved from https://example.com/study" in response_apa.json()["citation_text"]

        # MLA preview (MLA 9: Author. "Title." Source, Day Month Year, URL.)
        response_mla = await client.get(f"/api/v1/citations/preview?sample_id={test_sample.id}&format=MLA", headers=auth_headers)
        assert response_mla.status_code == 200
        # Author. "Title." Source, Day Month Year, URL.
        expected_mla = f'Dr. Jane Doe. "A Study on Thermoculture." {test_source.name}, 11 June 2026, https://example.com/study.'
        assert response_mla.json()["citation_text"] == expected_mla

        # Chicago preview (must include source name)
        response_chi = await client.get(f"/api/v1/citations/preview?sample_id={test_sample.id}&format=CHICAGO", headers=auth_headers)
        assert response_chi.status_code == 200
        assert test_source.name in response_chi.json()["citation_text"]

    async def test_task5_sample_analysis_ordering(self, client: AsyncClient, auth_headers, db_session, test_sample):
        # Create multiple sentiment analysis rows
        s1 = SentimentAnalysis(
            id=str(uuid4()), sample_id=test_sample.id, overall_sentiment=0.1, 
            sentiment_label=SentimentLabel.NEUTRAL, confidence=0.7, 
            analyzed_at=datetime.now(timezone.utc) - timedelta(minutes=10)
        )
        s2 = SentimentAnalysis(
            id=str(uuid4()), sample_id=test_sample.id, overall_sentiment=0.9, 
            sentiment_label=SentimentLabel.VERY_POSITIVE, confidence=0.99, 
            analyzed_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )

        # Create multiple classification rows
        c1 = DiscourseClassification(
            id=str(uuid4()), sample_id=test_sample.id, classification_type=ClassificationType.POLICY_DISCUSSION,
            confidence=0.6, classified_at=datetime.now(timezone.utc) - timedelta(minutes=10)
        )
        c2 = DiscourseClassification(
            id=str(uuid4()), sample_id=test_sample.id, classification_type=ClassificationType.PRACTICAL_ADAPTATION,
            confidence=0.95, classified_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )

        db_session.add_all([s1, s2, c1, c2])
        await db_session.commit()

        # Call get_sample_analysis
        response = await client.get(f"/api/v1/samples/{test_sample.id}/analysis", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify latest is first
        assert len(data["sentiments"]) >= 2
        assert data["sentiments"][0]["overall_sentiment"] == 0.9  # s2 is latest (5m ago)
        
        assert len(data["classifications"]) >= 2
        assert data["classifications"][0]["classification_type"] == "PRACTICAL_ADAPTATION"  # c2 is latest (5m ago)
