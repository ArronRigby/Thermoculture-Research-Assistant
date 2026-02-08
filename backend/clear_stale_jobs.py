"""Quick script to clear stale PENDING/RUNNING jobs from before the background task changes."""
import asyncio
from app.core.database import async_session_factory
from sqlalchemy import delete
from app.models.models import CollectionJob, JobStatus

async def clear_stale_jobs():
    async with async_session_factory() as db:
        result = await db.execute(
            delete(CollectionJob).where(
                CollectionJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
            )
        )
        await db.commit()
        print(f"Cleared {result.rowcount} stale jobs")

if __name__ == "__main__":
    asyncio.run(clear_stale_jobs())
