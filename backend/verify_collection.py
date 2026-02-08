import asyncio
import sys
import os
import logging

# Add backend to path
sys.path.append(os.getcwd())

from app.core.database import async_session_factory
from app.api.routes import _run_collection_in_background
from app.models.models import Source, CollectionJob, JobStatus, SourceType
from sqlalchemy import select
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_collection():
    print("Starting verification...")
    async with async_session_factory() as db:
        # 1. Create/Get a test source
        # We'll use a dummy BBC source
        source_url = "https://www.bbc.co.uk/news/test-verification"
        result = await db.execute(select(Source).where(Source.url == source_url))
        source = result.scalar_one_or_none()
        
        if not source:
            print("Creating test source...")
            source = Source(
                name="Test Verification Source",
                url=source_url,
                source_type=SourceType.NEWS,
                is_active=True
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)
        else:
            print(f"Found existing test source: {source.id}")

        # 2. Create a Job in PENDING state (simulating the API endpoint)
        print("Creating test job...")
        job = CollectionJob(
            source_id=source.id,
            status=JobStatus.PENDING,
            items_collected=0
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        job_id = str(job.id)
        source_id = str(source.id)
        collector_type = "news_bbc" # Force this type

        print(f"Job created: {job_id}")

    # 3. Run background task (outside of the previous session to simulate real background task)
    print("Triggering background task...")
    try:
        await _run_collection_in_background(job_id, source_id, collector_type)
        print("Background task execution finished (function returned).")
    except Exception as e:
        print(f"Background task raised exception: {e}")

    # 4. Verify Job Status
    print("Verifying final job status...")
    async with async_session_factory() as db:
        result = await db.execute(select(CollectionJob).where(CollectionJob.id == job_id))
        updated_job = result.scalar_one_or_none()
        
        if updated_job:
            print(f"Final Job Status: {updated_job.status}")
            print(f"Items Collected: {updated_job.items_collected}")
            print(f"Error Message: {updated_job.error_message}")
            
            if updated_job.status == JobStatus.COMPLETED or updated_job.status == JobStatus.FAILED:
                print("SUCCESS: Job transitioned to a final state.")
            else:
                print("FAILURE: Job did not transition to COMPLETED or FAILED.")
        else:
            print("FAILURE: Job not found.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_collection())
