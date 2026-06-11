import pytest
from httpx import AsyncClient
from sqlalchemy import select
from uuid import uuid4

from app.models.models import Source, SourceType, CollectionJob, DiscourseSample
from collectors.base import CollectedItem
from collectors.pipeline import IngestPipeline
from collectors.reddit_collector import RedditCollector

pytestmark = pytest.mark.asyncio

class TestBatch3:
    async def test_task1_start_job_manual_source_422(self, client: AsyncClient, auth_headers, db_session):
        # Create a manual source
        source = Source(
            id=str(uuid4()),
            name="Manual Source for Test",
            source_type=SourceType.MANUAL,
            is_active=True,
        )
        db_session.add(source)
        await db_session.commit()

        # Try to start a job
        response = await client.post(
            "/api/v1/jobs/start",
            headers=auth_headers,
            json={"source_id": str(source.id)},
        )
        assert response.status_code == 422
        assert "No collector available for this source" in response.json()["detail"]

        # Verify no job row was created
        result = await db_session.execute(
            select(CollectionJob).where(CollectionJob.source_id == source.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_task2_cross_source_deduplication(self, db_session):
        # Create source A and source B
        source_a = Source(id=str(uuid4()), name="Source A", source_type=SourceType.NEWS, is_active=True)
        source_b = Source(id=str(uuid4()), name="Source B", source_type=SourceType.NEWS, is_active=True)
        db_session.add(source_a)
        db_session.add(source_b)
        await db_session.commit()

        pipeline = IngestPipeline()
        item = CollectedItem(
            title="Shared Article",
            content="This is identical content in two different sources.",
            source_url="https://example.com/shared",
            author="Author",
        )

        # Ingest under Source A
        stats_a = await pipeline.ingest_items([item], source_a.id, db_session)
        assert stats_a["new"] == 1
        assert stats_a["duplicates"] == 0

        # Ingest under Source B (same content hash)
        stats_b = await pipeline.ingest_items([item], source_b.id, db_session)
        assert stats_b["new"] == 0
        assert stats_b["duplicates"] == 1

    async def test_task3_batch_insert_integrity_error_fallback(self, db_session, test_source):
        # Create a sample to duplicate
        sample_ok = DiscourseSample(
            id=str(uuid4()),
            title="OK Sample",
            content="OK Content",
            source_id=test_source.id,
        )
        sample_ok.raw_metadata = {"content_hash": "unique_hash_123"}
        # Wait, since content_hash column is not yet present, we'll assign it to raw_metadata first for now,
        # but once we add content_hash column, we will set it there. Let's write the test assuming the column exists
        # since we are doing Red-Green and the model change happens in the Green phase.
        # But wait! If we pass content_hash to constructor before adding the column, Python will raise TypeError.
        # Let's set it as attribute dynamically or in constructor. 
        # Actually, let's write it using constructor argument `content_hash`. It will fail with TypeError in the Red phase,
        # and then pass in the Green phase when the column is added. This is a perfect Red test!
        
        sample_ok = DiscourseSample(
            id=str(uuid4()),
            title="OK Sample",
            content="OK Content",
            source_id=test_source.id,
            content_hash="unique_hash_123",
        )
        db_session.add(sample_ok)
        await db_session.commit()

        pipeline = IngestPipeline()

        # Now we try to batch insert two samples: one with a new hash, one with the duplicate hash
        sample_new = DiscourseSample(
            id=str(uuid4()),
            title="New Sample",
            content="New Content",
            source_id=test_source.id,
            content_hash="unique_hash_456",
        )
        sample_dup_again = DiscourseSample(
            id=str(uuid4()),
            title="Dup Again",
            content="Dup Content",
            source_id=test_source.id,
            content_hash="unique_hash_123", # duplicates unique_hash_123
        )

        await pipeline._batch_insert(db_session, [sample_new, sample_dup_again])

        # Verify that sample_new is persisted, but sample_dup_again was expunged
        result_new = await db_session.execute(
            select(DiscourseSample).where(DiscourseSample.content_hash == "unique_hash_456")
        )
        assert result_new.scalar_one_or_none() is not None

        result_dup = await db_session.execute(
            select(DiscourseSample).where(DiscourseSample.id == sample_dup_again.id)
        )
        assert result_dup.scalar_one_or_none() is None

    async def test_task5_reddit_collector_missing_credentials(self, monkeypatch):
        from app.core.config import settings
        monkeypatch.setattr(settings, "REDDIT_CLIENT_ID", "")
        monkeypatch.setattr(settings, "REDDIT_CLIENT_SECRET", "")

        collector = RedditCollector()
        with pytest.raises(ValueError) as exc_info:
            await collector.collect()
        assert "credentials" in str(exc_info.value)
