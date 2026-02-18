import asyncio
import csv
import io
import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_, delete, distinct, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory, get_db
from collectors.scheduler import CollectionScheduler

from loguru import logger
from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.models.models import (
    Citation,
    CitationFormat,
    ClassificationType,
    CollectionJob,
    DiscourseClassification,
    DiscourseSample,
    JobStatus,
    Location,
    Region,
    ResearchNote,
    SentimentAnalysis,
    SentimentLabel,
    Source,
    SourceType,
    Theme,
    User,
    note_samples,
    sample_themes,
)
from app.schemas.schemas import (
    CitationCreate,
    CitationResponse,
    CollectionJobCreate,
    CollectionJobResponse,
    CollectionStatsResponse,
    DashboardStatsResponse,
    DiscourseClassificationResponse,
    DiscourseSampleCreate,
    DiscourseSampleDetailResponse,
    DiscourseSampleResponse,
    DiscourseTypeItem,
    DiscourseTypeResponse,
    FilterParams,
    GeographicDistributionItem,
    GeographicDistributionResponse,
    LocationCreate,
    LocationResponse,
    MapLocationItem,
    PaginatedResponse,
    ResearchNoteCreate,
    ResearchNoteDetailResponse,
    ResearchNoteResponse,
    ResearchNoteUpdate,
    SampleAnalysisResponse,
    SentimentAnalysisResponse,
    SentimentDistributionItem,
    SentimentDistributionResponse,
    SentimentOverTimePoint,
    SentimentOverTimeResponse,
    SourceCreate,
    SourceResponse,
    SourceUpdate,
    ThemeCoOccurrenceItem,
    ThemeCoOccurrenceResponse,
    ThemeCreate,
    ThemeFrequencyItem,
    ThemeFrequencyResponse,
    ThemeResponse,
    TimelinePoint,
    TimelineResponse,
    Token,
    TrendingThemeItem,
    TrendingThemesResponse,
    UserCreate,
    UserResponse,
)

# ---------------------------------------------------------------------------
# Router definitions
# ---------------------------------------------------------------------------

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
sources_router = APIRouter(prefix="/sources", tags=["Sources"])
samples_router = APIRouter(prefix="/samples", tags=["Discourse Samples"])
themes_router = APIRouter(prefix="/themes", tags=["Themes"])
locations_router = APIRouter(prefix="/locations", tags=["Locations"])
analysis_router = APIRouter(prefix="/analysis", tags=["Analysis"])
notes_router = APIRouter(prefix="/notes", tags=["Research Notes"])
citations_router = APIRouter(prefix="/citations", tags=["Citations"])
jobs_router = APIRouter(prefix="/jobs", tags=["Collection Jobs"])
export_router = APIRouter(prefix="/export", tags=["Export"])


# ===========================================================================
# AUTH
# ===========================================================================


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@auth_router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


# ===========================================================================
# DASHBOARD
# ===========================================================================


@dashboard_router.get("/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_samples = (await db.execute(func.count(DiscourseSample.id))).scalar() or 0
    active_sources = (
        await db.execute(
            select(func.count(Source.id)).where(Source.is_active.is_(True))
        )
    ).scalar() or 0
    themes_identified = (await db.execute(func.count(Theme.id))).scalar() or 0
    running_jobs = (
        await db.execute(
            select(func.count(CollectionJob.id)).where(
                CollectionJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
            )
        )
    ).scalar() or 0
    return DashboardStatsResponse(
        total_samples=total_samples,
        active_sources=active_sources,
        themes_identified=themes_identified,
        running_jobs=running_jobs,
    )


# ===========================================================================
# SOURCES
# ===========================================================================


@sources_router.get("/", response_model=List[SourceResponse])
async def list_sources(
    source_type: Optional[SourceType] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Source)
    if source_type is not None:
        stmt = stmt.where(Source.source_type == source_type)
    if is_active is not None:
        stmt = stmt.where(Source.is_active == is_active)
    stmt = stmt.order_by(Source.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@sources_router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = Source(**payload.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


@sources_router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@sources_router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    payload: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)
    await db.flush()
    await db.refresh(source)
    return source


@sources_router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    await db.delete(source)
    await db.flush()
    return None


# ===========================================================================
# DISCOURSE SAMPLES
# ===========================================================================


def _build_sample_filters(stmt, params: FilterParams):
    """Append dynamic WHERE clauses based on FilterParams."""
    if params.date_from is not None:
        stmt = stmt.where(DiscourseSample.collected_at >= params.date_from)
    if params.date_to is not None:
        # Make the "to" date inclusive of the entire day if it's just a date
        date_to = params.date_to
        if date_to.hour == 0 and date_to.minute == 0 and date_to.second == 0:
            date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
        stmt = stmt.where(DiscourseSample.collected_at <= date_to)
    if params.location_ids:
        stmt = stmt.where(DiscourseSample.location_id.in_(params.location_ids))
    if params.source_types:
        stmt = stmt.join(Source, Source.id == DiscourseSample.source_id, isouter=True).where(
            Source.source_type.in_(params.source_types)
        )
    if params.theme_ids:
        stmt = stmt.where(
            DiscourseSample.id.in_(
                select(sample_themes.c.sample_id).where(
                    sample_themes.c.theme_id.in_(params.theme_ids)
                )
            )
        )
    if params.sentiment_range and len(params.sentiment_range) == 2:
        min_s, max_s = params.sentiment_range
        stmt = stmt.where(
            DiscourseSample.id.in_(
                select(SentimentAnalysis.sample_id).where(
                    and_(
                        SentimentAnalysis.overall_sentiment >= min_s,
                        SentimentAnalysis.overall_sentiment <= max_s,
                    )
                )
            )
        )
    if params.discourse_types:
        stmt = stmt.where(
            DiscourseSample.id.in_(
                select(DiscourseClassification.sample_id).where(
                    DiscourseClassification.classification_type.in_(params.discourse_types)
                )
            )
        )
    if params.search_query:
        search = f"%{params.search_query}%"
        stmt = stmt.where(
            or_(
                DiscourseSample.title.ilike(search),
                DiscourseSample.content.ilike(search),
            )
        )
    return stmt


@samples_router.get("/", response_model=PaginatedResponse[DiscourseSampleResponse])
async def list_samples(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    location_ids: Optional[str] = Query(None, description="Comma-separated UUIDs"),
    theme_ids: Optional[str] = Query(None, description="Comma-separated UUIDs"),
    sentiment_min: Optional[float] = Query(None, ge=-1, le=1),
    sentiment_max: Optional[float] = Query(None, ge=-1, le=1),
    source_types: Optional[str] = Query(None, description="Comma-separated SourceType values"),
    discourse_types: Optional[str] = Query(None, description="Comma-separated ClassificationType values"),
    search_query: Optional[str] = None,
    sort_by: Optional[str] = "collected_at",
    sort_order: Optional[str] = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Parse comma-separated query params into FilterParams
    parsed_location_ids = (
        [lid.strip() for lid in location_ids.split(",") if lid.strip()]
        if location_ids
        else None
    )
    parsed_theme_ids = (
        [tid.strip() for tid in theme_ids.split(",") if tid.strip()]
        if theme_ids
        else None
    )
    parsed_source_types = (
        [SourceType(st.strip()) for st in source_types.split(",") if st.strip()]
        if source_types
        else None
    )
    parsed_discourse_types = (
        [ClassificationType(dt.strip()) for dt in discourse_types.split(",") if dt.strip()]
        if discourse_types
        else None
    )
    sentiment_range = None
    if sentiment_min is not None and sentiment_max is not None:
        sentiment_range = [sentiment_min, sentiment_max]

    params = FilterParams(
        date_from=date_from,
        date_to=date_to,
        location_ids=parsed_location_ids,
        theme_ids=parsed_theme_ids,
        sentiment_range=sentiment_range,
        source_types=parsed_source_types,
        discourse_types=parsed_discourse_types,
        search_query=search_query,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    # Count query
    count_stmt = select(func.count(distinct(DiscourseSample.id))).select_from(DiscourseSample)
    count_stmt = _build_sample_filters(count_stmt, params)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Data query
    stmt = select(DiscourseSample)
    stmt = _build_sample_filters(stmt, params)
    # Sorting
    if params.sort_by == "sentiment":
        # Sort by sentiment analysis score
        stmt = stmt.outerjoin(SentimentAnalysis)
        if params.sort_order == "asc":
            stmt = stmt.order_by(SentimentAnalysis.overall_sentiment.asc().nulls_last())
        else:
            stmt = stmt.order_by(SentimentAnalysis.overall_sentiment.desc().nulls_last())
    elif params.sort_by == "title":
        if params.sort_order == "asc":
            stmt = stmt.order_by(DiscourseSample.title.asc())
        else:
            stmt = stmt.order_by(DiscourseSample.title.desc())
    elif params.sort_by == "relevance":
        # For now, default to collected_at if no full-text relevance weighting
        # If search_query is present, we could add text-rank later
        if params.sort_order == "asc":
            stmt = stmt.order_by(DiscourseSample.collected_at.asc())
        else:
            stmt = stmt.order_by(DiscourseSample.collected_at.desc())
    else:
        # Default to collected_at
        col = getattr(DiscourseSample, params.sort_by or "collected_at", DiscourseSample.collected_at)
        # Verify it's actually a column to avoid getattr issues
        if not hasattr(DiscourseSample, str(params.sort_by)):
            col = DiscourseSample.collected_at
            
        if params.sort_order == "asc":
            stmt = stmt.order_by(col.asc())
        else:
            stmt = stmt.order_by(col.desc())

    stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)
    result = await db.execute(stmt)
    items = result.scalars().unique().all()

    total_pages = max(1, math.ceil(total / params.page_size))
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
    )


@samples_router.post("/", response_model=DiscourseSampleResponse, status_code=status.HTTP_201_CREATED)
async def create_sample(
    payload: DiscourseSampleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate source exists
    source_result = await db.execute(select(Source).where(Source.id == payload.source_id))
    if source_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    # Validate location if provided
    if payload.location_id is not None:
        loc_result = await db.execute(select(Location).where(Location.id == payload.location_id))
        if loc_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    data = payload.model_dump(exclude={"theme_ids"})
    sample = DiscourseSample(**data)
    db.add(sample)
    await db.flush()

    # Attach themes
    if payload.theme_ids:
        theme_result = await db.execute(select(Theme).where(Theme.id.in_(payload.theme_ids)))
        themes = theme_result.scalars().all()
        sample.themes = list(themes)
        await db.flush()

    await db.refresh(sample)
    return sample


@samples_router.get("/{sample_id}", response_model=DiscourseSampleDetailResponse)
async def get_sample(sample_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(DiscourseSample)
        .options(
            selectinload(DiscourseSample.source),
            selectinload(DiscourseSample.location),
            selectinload(DiscourseSample.themes),
        )
        .where(DiscourseSample.id == sample_id)
    )
    result = await db.execute(stmt)
    sample = result.scalar_one_or_none()
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    return sample


@samples_router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sample(sample_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiscourseSample).where(DiscourseSample.id == sample_id))
    sample = result.scalar_one_or_none()
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    await db.delete(sample)
    await db.flush()
    return None


@samples_router.get("/{sample_id}/analysis", response_model=SampleAnalysisResponse)
async def get_sample_analysis(sample_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(DiscourseSample)
        .options(
            selectinload(DiscourseSample.sentiments),
            selectinload(DiscourseSample.classifications),
            selectinload(DiscourseSample.themes),
        )
        .where(DiscourseSample.id == sample_id)
    )
    result = await db.execute(stmt)
    sample = result.scalar_one_or_none()
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    return SampleAnalysisResponse(
        sentiments=sample.sentiments,
        classifications=sample.classifications,
        themes=sample.themes,
    )


# ===========================================================================
# THEMES
# ===========================================================================


@themes_router.get("/", response_model=List[ThemeResponse])
async def list_themes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Theme).order_by(Theme.name))
    return result.scalars().all()


@themes_router.post("/", response_model=ThemeResponse, status_code=status.HTTP_201_CREATED)
async def create_theme(payload: ThemeCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Theme).where(Theme.name == payload.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A theme with this name already exists",
        )
    theme = Theme(**payload.model_dump())
    db.add(theme)
    await db.flush()
    await db.refresh(theme)
    return theme


@themes_router.get("/{theme_id}/samples", response_model=PaginatedResponse[DiscourseSampleResponse])
async def get_theme_samples(
    theme_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Verify theme exists
    theme_result = await db.execute(select(Theme).where(Theme.id == theme_id))
    if theme_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")

    sample_ids_subq = select(sample_themes.c.sample_id).where(
        sample_themes.c.theme_id == theme_id
    )

    count_stmt = select(func.count()).select_from(
        select(DiscourseSample.id).where(DiscourseSample.id.in_(sample_ids_subq)).subquery()
    )
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(DiscourseSample)
        .where(DiscourseSample.id.in_(sample_ids_subq))
        .order_by(DiscourseSample.collected_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = max(1, math.ceil(total / page_size))
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ===========================================================================
# LOCATIONS
# ===========================================================================


@locations_router.get("/", response_model=List[LocationResponse])
async def list_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Location).order_by(Location.name))
    return result.scalars().all()


@locations_router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(payload: LocationCreate, db: AsyncSession = Depends(get_db)):
    location = Location(**payload.model_dump())
    db.add(location)
    await db.flush()
    await db.refresh(location)
    return location


@locations_router.get("/{location_id}/samples", response_model=PaginatedResponse[DiscourseSampleResponse])
async def get_location_samples(
    location_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    loc_result = await db.execute(select(Location).where(Location.id == location_id))
    if loc_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    count_stmt = select(func.count(DiscourseSample.id)).where(
        DiscourseSample.location_id == location_id
    )
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(DiscourseSample)
        .where(DiscourseSample.location_id == location_id)
        .order_by(DiscourseSample.collected_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = max(1, math.ceil(total / page_size))
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ===========================================================================
# ANALYSIS
# ===========================================================================


@analysis_router.get("/sentiment-over-time", response_model=SentimentOverTimeResponse)
async def sentiment_over_time(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    granularity: str = Query("day", regex="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strftime_map = {
        "day": "%Y-%m-%d",
        "week": "%Y-%W",
        "month": "%Y-%m",
    }
    fmt = strftime_map[granularity]
    period_expr = func.strftime(fmt, SentimentAnalysis.analyzed_at)

    stmt = (
        select(
            period_expr.label("period"),
            func.avg(SentimentAnalysis.overall_sentiment).label("avg_sentiment"),
            func.count(SentimentAnalysis.id).label("sample_count"),
        )
        .group_by(period_expr)
        .order_by(period_expr)
    )

    if date_from is not None:
        stmt = stmt.where(SentimentAnalysis.analyzed_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(SentimentAnalysis.analyzed_at <= date_to)

    result = await db.execute(stmt)
    rows = result.all()

    data = [
        SentimentOverTimePoint(
            date=row.period or "",
            average_sentiment=round(float(row.avg_sentiment), 4),
            sample_count=row.sample_count,
        )
        for row in rows
    ]

    return SentimentOverTimeResponse(data=data, granularity=granularity)


@analysis_router.get("/theme-frequency", response_model=ThemeFrequencyResponse)
async def theme_frequency(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(
            Theme.id,
            Theme.name,
            func.count(sample_themes.c.sample_id).label("cnt"),
        )
        .join(sample_themes, sample_themes.c.theme_id == Theme.id, isouter=True)
        .group_by(Theme.id, Theme.name)
        .order_by(text("cnt DESC"))
    )
    result = await db.execute(stmt)
    rows = result.all()

    data = [
        ThemeFrequencyItem(theme_id=row.id, theme_name=row.name, count=row.cnt)
        for row in rows
    ]
    return ThemeFrequencyResponse(data=data)


@analysis_router.get("/geographic-distribution", response_model=GeographicDistributionResponse)
async def geographic_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(
            Location.region,
            func.count(DiscourseSample.id).label("cnt"),
            func.avg(SentimentAnalysis.overall_sentiment).label("avg_sentiment"),
        )
        .join(DiscourseSample, DiscourseSample.location_id == Location.id)
        .join(
            SentimentAnalysis,
            SentimentAnalysis.sample_id == DiscourseSample.id,
            isouter=True,
        )
        .group_by(Location.region)
        .order_by(text("cnt DESC"))
    )
    result = await db.execute(stmt)
    rows = result.all()

    data = [
        GeographicDistributionItem(
            region=row.region.value if row.region else "UNKNOWN",
            count=row.cnt,
            average_sentiment=round(float(row.avg_sentiment), 4) if row.avg_sentiment is not None else None,
        )
        for row in rows
    ]
    return GeographicDistributionResponse(data=data)


@analysis_router.get("/discourse-types", response_model=DiscourseTypeResponse)
async def discourse_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(
            DiscourseClassification.classification_type,
            func.count(DiscourseClassification.id).label("cnt"),
        )
        .group_by(DiscourseClassification.classification_type)
        .order_by(text("cnt DESC"))
    )
    result = await db.execute(stmt)
    rows = result.all()

    grand_total = sum(row.cnt for row in rows) or 1

    data = [
        DiscourseTypeItem(
            classification_type=row.classification_type.value,
            count=row.cnt,
            percentage=round((row.cnt / grand_total) * 100, 2),
        )
        for row in rows
    ]
    return DiscourseTypeResponse(data=data)


@analysis_router.get("/trending-themes", response_model=TrendingThemesResponse)
async def trending_themes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    last_30_days = now - timedelta(days=30)
    previous_30_days_start = last_30_days - timedelta(days=30)

    # Current period counts
    current_stmt = (
        select(
            Theme.id,
            Theme.name,
            func.count(sample_themes.c.sample_id).label("cnt"),
        )
        .join(sample_themes, sample_themes.c.theme_id == Theme.id)
        .join(DiscourseSample, DiscourseSample.id == sample_themes.c.sample_id)
        .where(DiscourseSample.collected_at >= last_30_days)
        .group_by(Theme.id, Theme.name)
        .order_by(text("cnt DESC"))
    )
    current_result = await db.execute(current_stmt)
    current_rows = current_result.all()

    # Previous period counts for trend direction
    previous_stmt = (
        select(
            Theme.id,
            func.count(sample_themes.c.sample_id).label("cnt"),
        )
        .join(sample_themes, sample_themes.c.theme_id == Theme.id)
        .join(DiscourseSample, DiscourseSample.id == sample_themes.c.sample_id)
        .where(
            and_(
                DiscourseSample.collected_at >= previous_30_days_start,
                DiscourseSample.collected_at < last_30_days,
            )
        )
        .group_by(Theme.id)
    )
    prev_result = await db.execute(previous_stmt)
    prev_map = {row.id: row.cnt for row in prev_result.all()}

    data = []
    for row in current_rows:
        prev_count = prev_map.get(row.id, 0)
        if row.cnt > prev_count:
            direction = "up"
        elif row.cnt < prev_count:
            direction = "down"
        else:
            direction = "stable"
        data.append(
            TrendingThemeItem(
                theme_id=row.id,
                theme_name=row.name,
                count=row.cnt,
                trend_direction=direction,
            )
        )

    return TrendingThemesResponse(data=data)


@analysis_router.get("/timeline", response_model=TimelineResponse)
async def volume_timeline(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    granularity: str = Query("day", regex="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strftime_map = {
        "day": "%Y-%m-%d",
        "week": "%Y-%W",
        "month": "%Y-%m",
    }
    fmt = strftime_map[granularity]
    period_expr = func.strftime(fmt, DiscourseSample.collected_at)

    stmt = (
        select(
            period_expr.label("period"),
            func.count(DiscourseSample.id).label("cnt"),
        )
        .group_by(period_expr)
        .order_by(period_expr)
    )
    if date_from is not None:
        stmt = stmt.where(DiscourseSample.collected_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(DiscourseSample.collected_at <= date_to)

    result = await db.execute(stmt)
    rows = result.all()

    data = [
        TimelinePoint(
            date=row.period or "",
            count=row.cnt,
        )
        for row in rows
    ]
    return TimelineResponse(data=data, granularity=granularity)


@analysis_router.get("/sentiment-distribution", response_model=SentimentDistributionResponse)
async def sentiment_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(
            SentimentAnalysis.sentiment_label,
            func.count(SentimentAnalysis.id).label("cnt"),
        )
        .group_by(SentimentAnalysis.sentiment_label)
    )
    result = await db.execute(stmt)
    rows = result.all()
    data = [
        SentimentDistributionItem(label=row.sentiment_label.value, count=row.cnt)
        for row in rows
    ]
    return SentimentDistributionResponse(data=data)


@analysis_router.get("/map-locations", response_model=List[MapLocationItem])
async def map_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(
            Location.name,
            Location.latitude,
            Location.longitude,
            func.count(DiscourseSample.id).label("cnt"),
            func.avg(SentimentAnalysis.overall_sentiment).label("avg_sent"),
        )
        .join(DiscourseSample, DiscourseSample.location_id == Location.id)
        .outerjoin(SentimentAnalysis, SentimentAnalysis.sample_id == DiscourseSample.id)
        .where(Location.latitude.isnot(None), Location.longitude.isnot(None))
        .group_by(Location.id, Location.name, Location.latitude, Location.longitude)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        MapLocationItem(
            name=row.name,
            lat=row.latitude,
            lng=row.longitude,
            count=row.cnt,
            avgSentiment=round(row.avg_sent or 0.0, 3),
        )
        for row in rows
    ]


@analysis_router.get("/theme-frequencies", response_model=ThemeFrequencyResponse)
async def theme_frequencies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(
            Theme.id,
            Theme.name,
            func.count(sample_themes.c.sample_id).label("cnt"),
        )
        .join(sample_themes, sample_themes.c.theme_id == Theme.id)
        .group_by(Theme.id, Theme.name)
        .order_by(text("cnt DESC"))
    )
    result = await db.execute(stmt)
    rows = result.all()
    data = [
        ThemeFrequencyItem(theme_id=row.id, theme_name=row.name, count=row.cnt)
        for row in rows
    ]
    return ThemeFrequencyResponse(data=data)


@analysis_router.get("/theme-co-occurrence", response_model=ThemeCoOccurrenceResponse)
async def theme_co_occurrence(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    st1 = sample_themes.alias("st1")
    st2 = sample_themes.alias("st2")
    t1 = Theme.__table__.alias("t1")
    t2 = Theme.__table__.alias("t2")
    stmt = (
        select(
            t1.c.name.label("theme_a"),
            t2.c.name.label("theme_b"),
            func.count().label("cnt"),
        )
        .select_from(st1)
        .join(st2, and_(st1.c.sample_id == st2.c.sample_id, st1.c.theme_id < st2.c.theme_id))
        .join(t1, t1.c.id == st1.c.theme_id)
        .join(t2, t2.c.id == st2.c.theme_id)
        .group_by(t1.c.name, t2.c.name)
        .order_by(text("cnt DESC"))
        .limit(20)
    )
    result = await db.execute(stmt)
    rows = result.all()
    data = [
        ThemeCoOccurrenceItem(theme_a=row.theme_a, theme_b=row.theme_b, count=row.cnt)
        for row in rows
    ]
    return ThemeCoOccurrenceResponse(data=data)


# ===========================================================================
# RESEARCH NOTES
# ===========================================================================


@notes_router.get("/", response_model=List[ResearchNoteResponse])
async def list_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ResearchNote)
        .where(ResearchNote.user_id == current_user.id)
        .order_by(ResearchNote.updated_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@notes_router.post("/", response_model=ResearchNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: ResearchNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = ResearchNote(
        title=payload.title,
        content=payload.content,
        user_id=current_user.id,
    )
    db.add(note)
    await db.flush()
    await db.refresh(note)
    return note


@notes_router.get("/{note_id}", response_model=ResearchNoteDetailResponse)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ResearchNote)
        .options(selectinload(ResearchNote.discourse_samples))
        .where(ResearchNote.id == note_id, ResearchNote.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@notes_router.put("/{note_id}", response_model=ResearchNoteResponse)
async def update_note(
    note_id: str,
    payload: ResearchNoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchNote).where(
            ResearchNote.id == note_id, ResearchNote.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    await db.flush()
    await db.refresh(note)
    return note


@notes_router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchNote).where(
            ResearchNote.id == note_id, ResearchNote.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    await db.delete(note)
    await db.flush()
    return None


@notes_router.post("/{note_id}/link-sample/{sample_id}", status_code=status.HTTP_200_OK)
async def link_sample_to_note(
    note_id: str,
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ResearchNote)
        .options(selectinload(ResearchNote.discourse_samples))
        .where(ResearchNote.id == note_id, ResearchNote.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    sample_result = await db.execute(
        select(DiscourseSample).where(DiscourseSample.id == sample_id)
    )
    sample = sample_result.scalar_one_or_none()
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    if sample not in note.discourse_samples:
        note.discourse_samples.append(sample)
        await db.flush()

    return {"detail": "Sample linked to note"}


@notes_router.post("/{note_id}/unlink-sample/{sample_id}", status_code=status.HTTP_200_OK)
async def unlink_sample_from_note(
    note_id: str,
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ResearchNote)
        .options(selectinload(ResearchNote.discourse_samples))
        .where(ResearchNote.id == note_id, ResearchNote.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    sample_result = await db.execute(
        select(DiscourseSample).where(DiscourseSample.id == sample_id)
    )
    sample = sample_result.scalar_one_or_none()
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    if sample in note.discourse_samples:
        note.discourse_samples.remove(sample)
        await db.flush()

    return {"detail": "Sample unlinked from note"}


# ===========================================================================
# CITATIONS
# ===========================================================================


def _generate_citation_text(
    sample: DiscourseSample,
    fmt: CitationFormat,
) -> str:
    author = sample.author or "Unknown Author"
    title = sample.title or "Untitled"
    year = sample.published_at.strftime("%Y") if sample.published_at else "n.d."
    date_full = sample.published_at.strftime("%B %d, %Y") if sample.published_at else "n.d."
    url = sample.source_url or ""

    if fmt == CitationFormat.APA:
        citation = f"{author} ({year}). {title}."
        if url:
            citation += f" Retrieved from {url}"
        return citation

    if fmt == CitationFormat.MLA:
        citation = f'{author}. "{title}."'
        if url:
            citation += f" Web. {date_full}. <{url}>."
        else:
            citation += f" {date_full}."
        return citation

    if fmt == CitationFormat.CHICAGO:
        citation = f'{author}. "{title}."'
        if url:
            citation += f" Accessed {date_full}. {url}."
        else:
            citation += f" {date_full}."
        return citation

    return f"{author}. {title}. {year}."


@citations_router.post("/", response_model=CitationResponse, status_code=status.HTTP_201_CREATED)
async def generate_citation(
    payload: CitationCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiscourseSample).where(DiscourseSample.id == payload.sample_id)
    )
    sample = result.scalar_one_or_none()
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    if payload.note_id is not None:
        note_result = await db.execute(
            select(ResearchNote).where(ResearchNote.id == payload.note_id)
        )
        if note_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    citation_text = _generate_citation_text(sample, payload.format)

    citation = Citation(
        sample_id=payload.sample_id,
        note_id=payload.note_id,
        citation_text=citation_text,
        format=payload.format,
    )
    db.add(citation)
    await db.flush()
    await db.refresh(citation)
    return citation


@citations_router.get("/sample/{sample_id}", response_model=List[CitationResponse])
async def get_sample_citations(sample_id: str, db: AsyncSession = Depends(get_db)):
    # Verify sample exists
    sample_result = await db.execute(
        select(DiscourseSample).where(DiscourseSample.id == sample_id)
    )
    if sample_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    stmt = (
        select(Citation)
        .where(Citation.sample_id == sample_id)
        .order_by(Citation.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


# ===========================================================================
# COLLECTION JOBS
# ===========================================================================


async def _run_collection_in_background(
    job_id: str,
    source_id: str,
    collector_type: str,
) -> None:
    """
    Background task that runs the actual collection.
    
    Creates its own database session since the request session is closed
    after the response is sent.
    """
    logger.info(f"DEBUG: Starting background collection for job {job_id}")
    await asyncio.sleep(1)  # Ensure DB visibility
    async with async_session_factory() as db:
        try:
            # Get the job and update to RUNNING
            result = await db.execute(
                select(CollectionJob).where(CollectionJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            if job is None:
                logger.error(f"DEBUG: Job {job_id} not found")
                return
            
            logger.info(f"DEBUG: Updating job {job_id} to RUNNING")
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            await db.commit()
            
            # Run the collection using the scheduler
            scheduler = CollectionScheduler()
            
            # Get the source for the collector
            source = await db.get(Source, source_id)
            if source is None:
                logger.error(f"DEBUG: Source {source_id} not found")
                job.status = JobStatus.FAILED
                job.error_message = "Source not found"
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
                return
            
            logger.info(f"DEBUG: Resolved source: {source.name} ({collector_type})")
            
            # Run the collector
            from collectors.scheduler import _get_collector
            collector = _get_collector(collector_type, source=source)
            logger.info(f"DEBUG: Collector instance: {type(collector).__name__}")
            
            logger.info(f"DEBUG: Starting collection...")
            items = await collector.collect()
            logger.info(f"DEBUG: Collected {len(items)} items")
            
            # Ingest the collected items
            logger.info(f"DEBUG: Ingesting items...")
            stats = await scheduler.pipeline.ingest_items(
                items=items,
                source_id=source_id,
                db=db,
            )
            logger.info(f"DEBUG: Ingestion stats: {stats}")
            
            # Update job as completed
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.items_collected = stats.get("new", 0)
            await db.commit()
            logger.info(f"DEBUG: Job {job_id} COMPLETED")
            
        except Exception as exc:
            logger.exception(f"DEBUG: EXCEPTION in background task for job {job_id}")
            
            # Update job as failed
            try:
                result = await db.execute(
                    select(CollectionJob).where(CollectionJob.id == job_id)
                )
                job = result.scalar_one_or_none()
                if job:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(timezone.utc)
                    job.error_message = f"{type(exc).__name__}: {exc}"
                    await db.commit()
            except Exception as inner_exc:
                logger.error(f"DEBUG: Failed to update job status on error: {inner_exc}")


@jobs_router.get("/", response_model=List[CollectionJobResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    stmt = select(CollectionJob).order_by(CollectionJob.started_at.desc().nulls_last())
    result = await db.execute(stmt)
    return result.scalars().all()


@jobs_router.post("/start", response_model=CollectionJobResponse, status_code=status.HTTP_201_CREATED)
async def start_collection_job(
    payload: CollectionJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"DEBUG: start_collection_job called for source {payload.source_id}")
    # Verify source
    source_result = await db.execute(select(Source).where(Source.id == payload.source_id))
    source = source_result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Source is inactive"
        )

    # Check for already running job on same source
    running_check = await db.execute(
        select(CollectionJob).where(
            CollectionJob.source_id == payload.source_id,
            CollectionJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
        )
    )
    if running_check.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A collection job is already running for this source",
        )

    # Determine the collector type based on source
    collector_type = CollectionScheduler._resolve_collector_type(source)

    job = CollectionJob(
        source_id=payload.source_id,
        status=JobStatus.PENDING,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    
    # Commit now so the background task can see the record
    await db.commit()
    
    logger.info(f"DEBUG: Adding background task for job {job.id}...")
    # Schedule the collection to run in the background
    background_tasks.add_task(
        _run_collection_in_background,
        job_id=str(job.id),
        source_id=str(payload.source_id),
        collector_type=collector_type,
    )
    logger.info(f"DEBUG: Background task added.")
    
    return job


@jobs_router.get("/stats", response_model=CollectionStatsResponse)
async def collection_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    today_count = (
        await db.execute(
            select(func.count(CollectionJob.id)).where(
                CollectionJob.started_at >= today_start
            )
        )
    ).scalar() or 0
    week_count = (
        await db.execute(
            select(func.count(CollectionJob.id)).where(
                CollectionJob.started_at >= week_start
            )
        )
    ).scalar() or 0
    month_count = (
        await db.execute(
            select(func.count(CollectionJob.id)).where(
                CollectionJob.started_at >= month_start
            )
        )
    ).scalar() or 0
    return CollectionStatsResponse(today=today_count, this_week=week_count, this_month=month_count)


@jobs_router.get("/{job_id}/status", response_model=CollectionJobResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollectionJob).where(CollectionJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


# ===========================================================================
# EXPORT
# ===========================================================================


@export_router.get("/samples")
async def export_samples(
    format: str = Query("json", regex="^(json|csv)$"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    location_ids: Optional[str] = Query(None),
    theme_ids: Optional[str] = Query(None),
    source_types: Optional[str] = Query(None),
    search_query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parsed_location_ids = (
        [lid.strip() for lid in location_ids.split(",") if lid.strip()]
        if location_ids
        else None
    )
    parsed_theme_ids = (
        [tid.strip() for tid in theme_ids.split(",") if tid.strip()]
        if theme_ids
        else None
    )
    parsed_source_types = (
        [SourceType(st.strip()) for st in source_types.split(",") if st.strip()]
        if source_types
        else None
    )

    params = FilterParams(
        date_from=date_from,
        date_to=date_to,
        location_ids=parsed_location_ids,
        theme_ids=parsed_theme_ids,
        source_types=parsed_source_types,
        search_query=search_query,
        page=1,
        page_size=100,  # Will not be used for limit in export
    )

    stmt = select(DiscourseSample)
    stmt = _build_sample_filters(stmt, params)
    stmt = stmt.order_by(DiscourseSample.collected_at.desc())
    # No pagination limit for export -- fetch all matching rows
    result = await db.execute(stmt)
    samples = result.scalars().unique().all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "title", "content", "source_id", "source_url",
            "author", "published_at", "collected_at", "location_id",
        ])
        for s in samples:
            writer.writerow([
                str(s.id),
                s.title,
                s.content,
                str(s.source_id),
                s.source_url or "",
                s.author or "",
                s.published_at.isoformat() if s.published_at else "",
                s.collected_at.isoformat() if s.collected_at else "",
                str(s.location_id) if s.location_id else "",
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=samples_export.csv"},
        )

    # JSON
    import json as json_lib

    data = [
        {
            "id": str(s.id),
            "title": s.title,
            "content": s.content,
            "source_id": str(s.source_id),
            "source_url": s.source_url,
            "author": s.author,
            "published_at": s.published_at.isoformat() if s.published_at else None,
            "collected_at": s.collected_at.isoformat() if s.collected_at else None,
            "location_id": str(s.location_id) if s.location_id else None,
        }
        for s in samples
    ]
    json_bytes = json_lib.dumps(data, indent=2)
    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=samples_export.json"},
    )


@export_router.get("/notes")
async def export_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import json as json_lib

    stmt = (
        select(ResearchNote)
        .options(selectinload(ResearchNote.discourse_samples))
        .where(ResearchNote.user_id == current_user.id)
        .order_by(ResearchNote.updated_at.desc())
    )
    result = await db.execute(stmt)
    notes = result.scalars().unique().all()

    data = [
        {
            "id": str(n.id),
            "title": n.title,
            "content": n.content,
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
            "linked_sample_ids": [str(s.id) for s in n.discourse_samples],
        }
        for n in notes
    ]
    json_bytes = json_lib.dumps(data, indent=2)
    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=notes_export.json"},
    )
