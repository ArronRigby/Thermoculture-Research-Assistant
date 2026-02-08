import asyncio
import sys
import os

# Add backend to path so we can import app modules
sys.path.append(os.getcwd())

from app.api.routes import _run_collection_in_background

async def test_logic():
    job_id = "06249af4-f33c-4708-bfbb-faf4324890c1"
    source_id = "c304d9f0-9d30-4c03-84cd-31b796184d3a"
    collector_type = "news_bbc"
    
    print(f"Testing background logic for job {job_id}...")
    await _run_collection_in_background(job_id, source_id, collector_type)
    print("Test finished.")

if __name__ == "__main__":
    asyncio.run(test_logic())
