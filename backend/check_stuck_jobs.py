import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# Add backend to path so we can import models
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from app.models.models import CollectionJob, JobStatus, Source, Base

# Database config
DATABASE_URL = "sqlite+aiosqlite:///./thermoculture.db"

async def check_running_jobs():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        stmt = (
            select(CollectionJob, Source)
            .join(Source, CollectionJob.source_id == Source.id)
            .where(CollectionJob.status == JobStatus.RUNNING)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        print(f"Found {len(rows)} running jobs:")
        for job, source in rows:
            if job.started_at:
                started_at = job.started_at
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                duration = datetime.now(timezone.utc) - started_at
                print(f"- Job {job.id}")
                print(f"  Source: {source.name} ({source.source_type})")
                print(f"  Duration: {duration}")
            else:
                print(f"- Job {job.id}: UNKNOWN START")

if __name__ == "__main__":
    asyncio.run(check_running_jobs())
