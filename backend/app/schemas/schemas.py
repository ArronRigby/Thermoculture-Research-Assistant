from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import (
    CitationFormat,
    ClassificationType,
    JobStatus,
    Region,
    SentimentLabel,
    SourceType,
)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Filter Params
# ---------------------------------------------------------------------------

class FilterParams(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    location_ids: Optional[List[str]] = None
    theme_ids: Optional[List[str]] = None
    sentiment_range: Optional[List[float]] = Field(
        None, description="Two-element list: [min_sentiment, max_sentiment], each -1 to 1"
    )
    source_types: Optional[List[SourceType]] = None
    discourse_types: Optional[List[ClassificationType]] = None
    search_query: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Source schemas
# ---------------------------------------------------------------------------

class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    source_type: Optional[SourceType] = None
    url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SourceResponse(BaseModel):
    id: str
    name: str
    source_type: SourceType
    url: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Location schemas
# ---------------------------------------------------------------------------

class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    region: Region
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    region: Optional[Region] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationResponse(BaseModel):
    id: str
    name: str
    region: Region
    latitude: Optional[float]
    longitude: Optional[float]

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Theme schemas
# ---------------------------------------------------------------------------

class ThemeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None


class ThemeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None


class ThemeResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# DiscourseSample schemas
# ---------------------------------------------------------------------------

class DiscourseSampleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)
    source_id: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    location_id: Optional[str] = None
    raw_metadata: Optional[dict] = None
    theme_ids: Optional[List[str]] = None


class DiscourseSampleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    content: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    location_id: Optional[str] = None
    raw_metadata: Optional[dict] = None


class DiscourseSampleResponse(BaseModel):
    id: str
    title: str
    content: str
    source_id: str
    source_url: Optional[str]
    author: Optional[str]
    published_at: Optional[datetime]
    collected_at: datetime
    location_id: Optional[str]
    raw_metadata: Optional[dict]

    model_config = ConfigDict(from_attributes=True)


class DiscourseSampleDetailResponse(DiscourseSampleResponse):
    source: Optional[SourceResponse] = None
    location: Optional[LocationResponse] = None
    themes: List[ThemeResponse] = []


# ---------------------------------------------------------------------------
# SentimentAnalysis schemas
# ---------------------------------------------------------------------------

class SentimentAnalysisCreate(BaseModel):
    sample_id: str
    overall_sentiment: float = Field(ge=-1.0, le=1.0)
    sentiment_label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)


class SentimentAnalysisUpdate(BaseModel):
    overall_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_label: Optional[SentimentLabel] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class SentimentAnalysisResponse(BaseModel):
    id: str
    sample_id: str
    overall_sentiment: float
    sentiment_label: SentimentLabel
    confidence: float
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# DiscourseClassification schemas
# ---------------------------------------------------------------------------

class DiscourseClassificationCreate(BaseModel):
    sample_id: str
    classification_type: ClassificationType
    confidence: float = Field(ge=0.0, le=1.0)


class DiscourseClassificationUpdate(BaseModel):
    classification_type: Optional[ClassificationType] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class DiscourseClassificationResponse(BaseModel):
    id: str
    sample_id: str
    classification_type: ClassificationType
    confidence: float
    classified_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# ResearchNote schemas
# ---------------------------------------------------------------------------

class ResearchNoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)


class ResearchNoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    content: Optional[str] = None


class ResearchNoteResponse(BaseModel):
    id: str
    title: str
    content: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchNoteDetailResponse(ResearchNoteResponse):
    discourse_samples: List[DiscourseSampleResponse] = []


# ---------------------------------------------------------------------------
# Citation schemas
# ---------------------------------------------------------------------------

class CitationCreate(BaseModel):
    sample_id: str
    note_id: Optional[str] = None
    format: CitationFormat = CitationFormat.APA


class CitationUpdate(BaseModel):
    citation_text: Optional[str] = None
    format: Optional[CitationFormat] = None


class CitationResponse(BaseModel):
    id: str
    sample_id: str
    note_id: Optional[str]
    citation_text: str
    format: CitationFormat
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# CollectionJob schemas
# ---------------------------------------------------------------------------

class CollectionJobCreate(BaseModel):
    source_id: str


class CollectionJobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    items_collected: Optional[int] = None
    error_message: Optional[str] = None


class CollectionJobResponse(BaseModel):
    id: str
    source_id: str
    status: JobStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    items_collected: int
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Analysis response schemas
# ---------------------------------------------------------------------------

class SentimentOverTimePoint(BaseModel):
    date: str
    average_sentiment: float
    sample_count: int


class SentimentOverTimeResponse(BaseModel):
    data: List[SentimentOverTimePoint]
    granularity: str


class ThemeFrequencyItem(BaseModel):
    theme_id: str
    theme_name: str
    count: int


class ThemeFrequencyResponse(BaseModel):
    data: List[ThemeFrequencyItem]


class GeographicDistributionItem(BaseModel):
    region: str
    count: int
    average_sentiment: Optional[float]


class GeographicDistributionResponse(BaseModel):
    data: List[GeographicDistributionItem]


class DiscourseTypeItem(BaseModel):
    classification_type: str
    count: int
    percentage: float


class DiscourseTypeResponse(BaseModel):
    data: List[DiscourseTypeItem]


class TrendingThemeItem(BaseModel):
    theme_id: str
    theme_name: str
    count: int
    trend_direction: str  # "up", "down", "stable"


class TrendingThemesResponse(BaseModel):
    data: List[TrendingThemeItem]


class TimelinePoint(BaseModel):
    date: str
    count: int


class TimelineResponse(BaseModel):
    data: List[TimelinePoint]
    granularity: str


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

class DashboardStatsResponse(BaseModel):
    total_samples: int
    active_sources: int
    themes_identified: int
    running_jobs: int


# ---------------------------------------------------------------------------
# Sentiment distribution
# ---------------------------------------------------------------------------

class SentimentDistributionItem(BaseModel):
    label: str
    count: int


class SentimentDistributionResponse(BaseModel):
    data: List[SentimentDistributionItem]


# ---------------------------------------------------------------------------
# Map locations
# ---------------------------------------------------------------------------

class MapLocationItem(BaseModel):
    name: str
    lat: float
    lng: float
    count: int
    avgSentiment: float


# ---------------------------------------------------------------------------
# Theme co-occurrence
# ---------------------------------------------------------------------------

class ThemeCoOccurrenceItem(BaseModel):
    theme_a: str
    theme_b: str
    count: int


class ThemeCoOccurrenceResponse(BaseModel):
    data: List[ThemeCoOccurrenceItem]


# ---------------------------------------------------------------------------
# Collection stats
# ---------------------------------------------------------------------------

class CollectionStatsResponse(BaseModel):
    today: int
    this_week: int
    this_month: int


# ---------------------------------------------------------------------------
# Sample analysis combined response
# ---------------------------------------------------------------------------

class SampleAnalysisResponse(BaseModel):
    sentiments: List[SentimentAnalysisResponse]
    classifications: List[DiscourseClassificationResponse]
    themes: List[ThemeResponse]
