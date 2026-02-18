import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.main import app
from app.core.database import get_db
from app.models.models import Base, User, Source, Location, Theme, DiscourseSample, SourceType, Region
from app.core.security import get_password_hash

# Use SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session):
    user = User(
        id=str(uuid4()),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def auth_headers(client, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def test_source(db_session):
    source = Source(
        id=str(uuid4()),
        name="Test BBC News",
        source_type=SourceType.NEWS,
        url="https://www.bbc.co.uk/news",
        description="Test news source",
        is_active=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source

@pytest.fixture
async def test_location(db_session):
    location = Location(
        id=str(uuid4()),
        name="London",
        region=Region.LONDON,
        latitude=51.5074,
        longitude=-0.1278,
    )
    db_session.add(location)
    await db_session.commit()
    await db_session.refresh(location)
    return location

@pytest.fixture
async def test_theme(db_session):
    theme = Theme(
        id=str(uuid4()),
        name="Extreme Weather",
        description="Flooding, storms, heatwaves",
        category="Environmental",
    )
    db_session.add(theme)
    await db_session.commit()
    await db_session.refresh(theme)
    return theme

@pytest.fixture
async def test_sample(db_session, test_source, test_location):
    from datetime import datetime, timezone
    sample = DiscourseSample(
        id=str(uuid4()),
        title="Test Climate Article",
        content="London experienced severe flooding yesterday as heavy rains overwhelmed drainage systems.",
        source_id=test_source.id,
        location_id=test_location.id,
        author="Test Author",
        published_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc),
    )
    db_session.add(sample)
    await db_session.commit()
    await db_session.refresh(sample)
    return sample
