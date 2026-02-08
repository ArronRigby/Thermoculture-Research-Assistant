"""
Reset themes and samples in the database and re-seed.
Usage: python -m seeds.reset_themes
Must be run from the backend directory.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete

from app.core.config import settings
from app.models.models import Base, Theme, DiscourseSample
from seeds.seed_data import seed_database


async def main():
    print(f"Connecting to database: {settings.DATABASE_URL}")

    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Wipe tables in reverse order of dependencies
            tables_to_wipe = [
                "ResearchNote",
                "SentimentAnalysis",
                "DiscourseClassification",
                "Citation",
                "CollectionJob",
                "DiscourseSample",
                "Theme",
                "Source",
                "Location",
                "User"
            ]
            
            from app.models.models import (
                ResearchNote, SentimentAnalysis, DiscourseClassification,
                Citation, CollectionJob, DiscourseSample, Theme, Source,
                Location, User, sample_themes, note_samples
            )
            
            print("Wiping all existing data...")
            # Association tables first
            await session.execute(delete(note_samples))
            await session.execute(delete(sample_themes))
            
            # Entities
            await session.execute(delete(ResearchNote))
            await session.execute(delete(SentimentAnalysis))
            await session.execute(delete(DiscourseClassification))
            await session.execute(delete(Citation))
            await session.execute(delete(CollectionJob))
            await session.execute(delete(DiscourseSample))
            await session.execute(delete(Theme))
            await session.execute(delete(Source))
            await session.execute(delete(Location))
            await session.execute(delete(User))
            
            print("Committing wipes...")
            await session.commit()
            
            print("Seeding new database data...")
            await seed_database(session)
            
            print("\nDatabase reset and seeded successfully with new theme taxonomy!")
        except Exception as e:
            print(f"\nError resetting database: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
