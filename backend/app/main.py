from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import (
    analysis_router,
    auth_router,
    citations_router,
    dashboard_router,
    export_router,
    jobs_router,
    locations_router,
    notes_router,
    samples_router,
    sources_router,
    themes_router,
)
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables for SQLite (no Alembic needed for dev)
    from app.core.database import engine, Base
    from app.models import models  # noqa: F401 - ensure models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Thermoculture Research Assistant API started")
    yield
    logger.info("Thermoculture Research Assistant API shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers under API v1 prefix
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(sources_router, prefix=settings.API_V1_PREFIX)
app.include_router(samples_router, prefix=settings.API_V1_PREFIX)
app.include_router(themes_router, prefix=settings.API_V1_PREFIX)
app.include_router(locations_router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis_router, prefix=settings.API_V1_PREFIX)
app.include_router(notes_router, prefix=settings.API_V1_PREFIX)
app.include_router(citations_router, prefix=settings.API_V1_PREFIX)
app.include_router(jobs_router, prefix=settings.API_V1_PREFIX)
app.include_router(export_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
