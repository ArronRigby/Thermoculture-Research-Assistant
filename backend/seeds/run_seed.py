"""
Run database seeding.
Usage: python -m seeds.run_seed
Must be run from the backend directory.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.models import Base
from seeds.seed_data import seed_database


async def main():
    print(f"Connecting to database: {settings.DATABASE_URL}")

    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

    # Create all tables
    async with engine.begin() as conn:
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)

    # Create session and seed
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            await seed_database(session)
            print("\nDatabase seeded successfully!")
        except Exception as e:
            print(f"\nError seeding database: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
