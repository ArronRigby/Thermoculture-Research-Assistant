import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SourceType(str, enum.Enum):
    NEWS = "NEWS"
    REDDIT = "REDDIT"
    FORUM = "FORUM"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    MANUAL = "MANUAL"


class Region(str, enum.Enum):
    LONDON = "LONDON"
    SOUTH_EAST = "SOUTH_EAST"
    SOUTH_WEST = "SOUTH_WEST"
    EAST = "EAST"
    WEST_MIDLANDS = "WEST_MIDLANDS"
    EAST_MIDLANDS = "EAST_MIDLANDS"
    NORTH_WEST = "NORTH_WEST"
    NORTH_EAST = "NORTH_EAST"
    YORKSHIRE = "YORKSHIRE"
    SCOTLAND = "SCOTLAND"
    WALES = "WALES"
    NORTHERN_IRELAND = "NORTHERN_IRELAND"


class SentimentLabel(str, enum.Enum):
    VERY_NEGATIVE = "VERY_NEGATIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    VERY_POSITIVE = "VERY_POSITIVE"


class ClassificationType(str, enum.Enum):
    PRACTICAL_ADAPTATION = "PRACTICAL_ADAPTATION"
    EMOTIONAL_RESPONSE = "EMOTIONAL_RESPONSE"
    POLICY_DISCUSSION = "POLICY_DISCUSSION"
    COMMUNITY_ACTION = "COMMUNITY_ACTION"
    DENIAL_DISMISSAL = "DENIAL_DISMISSAL"


class CitationFormat(str, enum.Enum):
    APA = "APA"
    MLA = "MLA"
    CHICAGO = "CHICAGO"


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Association tables
# ---------------------------------------------------------------------------

sample_themes = Table(
    "sample_themes",
    Base.metadata,
    Column("sample_id", String(36), ForeignKey("discourse_samples.id", ondelete="CASCADE"), primary_key=True),
    Column("theme_id", String(36), ForeignKey("themes.id", ondelete="CASCADE"), primary_key=True),
)

note_samples = Table(
    "note_samples",
    Base.metadata,
    Column("note_id", String(36), ForeignKey("research_notes.id", ondelete="CASCADE"), primary_key=True),
    Column("sample_id", String(36), ForeignKey("discourse_samples.id", ondelete="CASCADE"), primary_key=True),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _genuuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow, nullable=False)

    research_notes: Mapped[List["ResearchNote"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum", create_constraint=True),
        nullable=False,
    )
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)

    discourse_samples: Mapped[List["DiscourseSample"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    collection_jobs: Mapped[List["CollectionJob"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[Region] = mapped_column(
        Enum(Region, name="region_enum", create_constraint=True),
        nullable=False,
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    discourse_samples: Mapped[List["DiscourseSample"]] = relationship(
        back_populates="location"
    )


class DiscourseSample(Base):
    __tablename__ = "discourse_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    collected_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)
    location_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    source: Mapped["Source"] = relationship(back_populates="discourse_samples")
    location: Mapped[Optional["Location"]] = relationship(back_populates="discourse_samples")
    themes: Mapped[List["Theme"]] = relationship(
        secondary=sample_themes, back_populates="discourse_samples"
    )
    sentiments: Mapped[List["SentimentAnalysis"]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )
    classifications: Mapped[List["DiscourseClassification"]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )
    research_notes: Mapped[List["ResearchNote"]] = relationship(
        secondary=note_samples, back_populates="discourse_samples"
    )
    citations: Mapped[List["Citation"]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)

    discourse_samples: Mapped[List["DiscourseSample"]] = relationship(
        secondary=sample_themes, back_populates="themes"
    )


class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    sample_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discourse_samples.id", ondelete="CASCADE"), nullable=False
    )
    overall_sentiment: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_label: Mapped[SentimentLabel] = mapped_column(
        Enum(SentimentLabel, name="sentiment_label_enum", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)

    sample: Mapped["DiscourseSample"] = relationship(back_populates="sentiments")


class DiscourseClassification(Base):
    __tablename__ = "discourse_classifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    sample_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discourse_samples.id", ondelete="CASCADE"), nullable=False
    )
    classification_type: Mapped[ClassificationType] = mapped_column(
        Enum(ClassificationType, name="classification_type_enum", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    classified_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)

    sample: Mapped["DiscourseSample"] = relationship(back_populates="classifications")


class ResearchNote(Base):
    __tablename__ = "research_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="research_notes")
    discourse_samples: Mapped[List["DiscourseSample"]] = relationship(
        secondary=note_samples, back_populates="research_notes"
    )


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    sample_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discourse_samples.id", ondelete="CASCADE"), nullable=False
    )
    note_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("research_notes.id", ondelete="SET NULL"), nullable=True
    )
    citation_text: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[CitationFormat] = mapped_column(
        Enum(CitationFormat, name="citation_format_enum", create_constraint=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)

    sample: Mapped["DiscourseSample"] = relationship(back_populates="citations")
    note: Mapped[Optional["ResearchNote"]] = relationship()


class CollectionJob(Base):
    __tablename__ = "collection_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_genuuid)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum", create_constraint=True),
        default=JobStatus.PENDING,
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    items_collected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped["Source"] = relationship(back_populates="collection_jobs")
