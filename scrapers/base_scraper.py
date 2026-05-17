import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid

from config.settings import Settings
from utils.http_client import HTTPClient
from utils.normalizers import (
    calculate_hash, normalize_phone, normalize_address,
    extract_email, extract_phone_numbers, calculate_data_quality_score
)
from storage.database import Database
from storage.models import Provider, ScrapingSession, ScrapingError
from queue.url_queue import URLQueue
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all platform scrapers."""

    def __init__(self, settings: Settings, database: Database):
        self.settings = settings
        self.database = database
        self.http_client = HTTPClient(settings)
        self.session_id = str(uuid.uuid4())[:8]
        self.platform = self.__class__.__name__.lower()
        self._init_session()

    def _init_session(self):
        """Initialize scraping session."""
        try:
            db = self.database.get_session()
            session = ScrapingSession(
                session_id=self.session_id,
                status="running",
                platform=self.platform,
            )
            db.add(session)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Error initializing session: {str(e)}")

    def _save_error(self, url: str, error_type: str, error_message: str, status_code: int = None):
        """Log scraping error to database."""
        try:
            db = self.database.get_session()
            error = ScrapingError(
                session_id=self.session_id,
                url=url,
                error_type=error_type,
                error_message=error_message,
                status_code=status_code,
            )
            db.add(error)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Error saving error log: {str(e)}")

    def _check_duplicate(self, db: Session, provider_data: Dict[str, Any]) -> bool:
        """Check if provider already exists."""
        if not provider_data.get("phone_number"):
            return False

        existing = db.query(Provider).filter(
            Provider.source_platform == provider_data["source_platform"],
            Provider.provider_id == provider_data.get("provider_id"),
        ).first()

        return existing is not None

    def _save_provider(self, db: Session, provider_data: Dict[str, Any]) -> Optional[int]:
        """Save provider to database."""
        try:
            provider_hash = calculate_hash(
                provider_data["source_platform"],
                provider_data["provider_name"],
                provider_data.get("phone_number"),
                provider_data.get("email"),
            )

            existing = db.query(Provider).filter_by(listing_hash=provider_hash).first()
            if existing:
                logger.debug(f"Duplicate found: {provider_hash}")
                return None

            data_quality_score = calculate_data_quality_score(provider_data)

            provider = Provider(
                **{k: v for k, v in provider_data.items() if k != "listing_hash"},
                listing_hash=provider_hash,
                data_quality_score=data_quality_score,
            )

            db.add(provider)
            db.commit()
            logger.info(f"Saved provider: {provider_data.get('provider_name')}")
            return provider.id

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving provider: {str(e)}")
            return None

    @abstractmethod
    async def discover_categories(self) -> List[str]:
        """Discover available categories on the platform."""
        pass

    @abstractmethod
    async def discover_listings(self, category: str, locality: str) -> List[str]:
        """Discover listing URLs for category and locality."""
        pass

    @abstractmethod
    async def extract_listing_details(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract structured data from listing page."""
        pass

    async def scrape_category_locality(
        self,
        category: str,
        locality: str,
        limit: int = None,
    ) -> int:
        """Scrape all listings for category + locality combination."""
        logger.info(f"Scraping {self.platform} - {category} in {locality}")

        db = self.database.get_session()
        url_queue = URLQueue(db)

        listings_extracted = 0

        try:
            listing_urls = await self.discover_listings(category, locality)
            logger.info(f"Found {len(listing_urls)} listings")

            if limit:
                listing_urls = listing_urls[:limit]

            for idx, url in enumerate(listing_urls, 1):
                try:
                    provider_data = await self.extract_listing_details(url)

                    if provider_data:
                        provider_data["source_platform"] = self.platform
                        saved_id = self._save_provider(db, provider_data)

                        if saved_id:
                            listings_extracted += 1

                    if idx % 10 == 0:
                        logger.info(f"Progress: {idx}/{len(listing_urls)} listings")

                except Exception as e:
                    logger.error(f"Error extracting {url}: {str(e)}")
                    self._save_error(url, "parse_error", str(e))
                    continue

            logger.info(f"Extraction complete: {listings_extracted} listings saved")

        finally:
            db.close()

        return listings_extracted

    def finalize_session(self, status: str = "completed", error_message: str = None):
        """Finalize scraping session."""
        try:
            db = self.database.get_session()
            session = db.query(ScrapingSession).filter_by(session_id=self.session_id).first()
            if session:
                session.status = status
                session.end_time = datetime.utcnow()
                if error_message:
                    session.error_message = error_message
                db.commit()
        except Exception as e:
            logger.error(f"Error finalizing session: {str(e)}")
        finally:
            db.close()
