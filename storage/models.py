from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique Identifiers
    source_platform = Column(String(50), nullable=False, index=True)
    provider_id = Column(String(100))
    listing_url = Column(Text, unique=True)
    listing_hash = Column(String(64), unique=True, index=True)

    # Basic Information
    provider_name = Column(String(255), nullable=False)
    teacher_or_business_type = Column(String(100))
    description = Column(Text)

    # Location
    city = Column(String(100), default="Bangalore", index=True)
    locality = Column(String(150), index=True)
    full_address = Column(Text)
    pincode = Column(String(10))

    # Geographic Data
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))

    # Contact Information
    phone_number = Column(String(20), index=True)
    whatsapp_number = Column(String(20))
    email = Column(String(255))
    website = Column(Text)

    # Social Media
    instagram_handle = Column(String(255))
    facebook_url = Column(Text)
    youtube_channel = Column(Text)

    # Ratings & Reviews
    rating = Column(Numeric(3, 2))
    review_count = Column(Integer, default=0)

    # Professional Details
    years_experience = Column(Integer)
    gender = Column(String(20))
    languages_spoken = Column(JSON)

    # Service Details
    subjects_taught = Column(JSON)
    age_group = Column(Text)
    pricing = Column(Text)
    timing = Column(Text)

    # Service Modes
    home_service_available = Column(Boolean, default=False)
    online_classes_available = Column(Boolean, default=False)

    # Categories
    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    tags = Column(JSON)

    # Media
    image_urls = Column(JSON)

    # Activity Tracking
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified = Column(DateTime)
    active = Column(Boolean, default=True, index=True)

    # Metadata
    data_quality_score = Column(Numeric(3, 2))
    confidence_score = Column(Numeric(3, 2))
    notes = Column(Text)

    # Relationships
    history = relationship("ProviderHistory", back_populates="provider", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_providers_city_locality", "city", "locality"),
        Index("idx_providers_source_unique", "source_platform", "provider_id", unique=True),
        UniqueConstraint("source_platform", "provider_id", name="uq_provider_source_id"),
    )


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    description = Column(Text)
    parent_category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    level = Column(Integer)
    source_platform = Column(String(50))
    discovered_at = Column(DateTime, default=datetime.utcnow)
    listing_count = Column(Integer, default=0, index=True)

    # Self-referential relationship
    parent = relationship("Category", remote_side=[id], backref="children")


class Locality(Base):
    __tablename__ = "localities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False, index=True)
    slug = Column(String(150), unique=True, nullable=False)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    pincode = Column(String(10))
    listing_count = Column(Integer, default=0, index=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)


class ScrapingSession(Base):
    __tablename__ = "scraping_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50), index=True)
    platform = Column(String(50), index=True)
    category = Column(String(100))
    locality = Column(String(150))
    total_urls_found = Column(Integer, default=0)
    total_urls_processed = Column(Integer, default=0)
    total_listings_extracted = Column(Integer, default=0)
    total_duplicates = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    error_message = Column(Text)
    config_hash = Column(String(64))

    # Relationships
    errors = relationship("ScrapingError", back_populates="session")


class ScrapingError(Base):
    __tablename__ = "scraping_errors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("scraping_sessions.session_id"), index=True)
    url = Column(Text)
    error_type = Column(String(100))
    error_message = Column(Text)
    status_code = Column(Integer)
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship("ScrapingSession", back_populates="errors")


class URLQueue(Base):
    __tablename__ = "url_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text, unique=True, nullable=False, index=True)
    url_type = Column(String(50))
    source_platform = Column(String(50), index=True)
    category = Column(String(100))
    locality = Column(String(150))
    priority = Column(Integer, default=0, index=True)
    status = Column(String(50), default="pending", index=True)
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


class ProviderHistory(Base):
    __tablename__ = "provider_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("providers.id", ondelete="CASCADE"), index=True)
    field_name = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    provider = relationship("Provider", back_populates="history")


class Export(Base):
    __tablename__ = "exports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    export_type = Column(String(50))
    file_path = Column(Text)
    filter_category = Column(String(100))
    filter_locality = Column(String(150))
    total_records = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(100))
