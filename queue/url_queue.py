import hashlib
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from storage.models import URLQueue as URLQueueModel

logger = logging.getLogger(__name__)


class URLQueue:
    """In-memory + database URL queue with deduplication."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.seen_hashes = set()
        self._load_existing_hashes()

    def _load_existing_hashes(self):
        """Load existing URL hashes from database."""
        try:
            existing_urls = self.db.query(URLQueueModel.url).all()
            for (url,) in existing_urls:
                self.seen_hashes.add(self._hash_url(url))
        except Exception as e:
            logger.error(f"Error loading existing URL hashes: {str(e)}")

    @staticmethod
    def _hash_url(url: str) -> str:
        """Calculate URL hash."""
        return hashlib.md5(url.encode()).hexdigest()

    def add(
        self,
        url: str,
        url_type: str = "listing",
        source_platform: str = None,
        category: str = None,
        locality: str = None,
        priority: int = 0,
    ) -> bool:
        """Add URL to queue if not already present."""
        url_hash = self._hash_url(url)

        if url_hash in self.seen_hashes:
            logger.debug(f"URL already in queue: {url}")
            return False

        try:
            queue_item = URLQueueModel(
                url=url,
                url_type=url_type,
                source_platform=source_platform,
                category=category,
                locality=locality,
                priority=priority,
                status="pending",
            )
            self.db.add(queue_item)
            self.db.commit()
            self.seen_hashes.add(url_hash)
            return True
        except Exception as e:
            logger.error(f"Error adding URL to queue: {str(e)}")
            self.db.rollback()
            return False

    def get_pending(self, limit: int = 10) -> List[URLQueueModel]:
        """Get pending URLs sorted by priority."""
        try:
            return self.db.query(URLQueueModel).filter(
                URLQueueModel.status == "pending"
            ).order_by(
                URLQueueModel.priority.desc(),
                URLQueueModel.created_at.asc()
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching pending URLs: {str(e)}")
            return []

    def mark_processing(self, queue_id: int):
        """Mark URL as being processed."""
        try:
            item = self.db.query(URLQueueModel).filter_by(id=queue_id).first()
            if item:
                item.status = "processing"
                item.last_attempt_at = datetime.utcnow()
                item.attempts += 1
                self.db.commit()
        except Exception as e:
            logger.error(f"Error marking URL as processing: {str(e)}")
            self.db.rollback()

    def mark_completed(self, queue_id: int):
        """Mark URL as completed."""
        try:
            item = self.db.query(URLQueueModel).filter_by(id=queue_id).first()
            if item:
                item.status = "completed"
                item.processed_at = datetime.utcnow()
                self.db.commit()
        except Exception as e:
            logger.error(f"Error marking URL as completed: {str(e)}")
            self.db.rollback()

    def mark_failed(self, queue_id: int, retry: bool = True):
        """Mark URL as failed and set for retry."""
        try:
            item = self.db.query(URLQueueModel).filter_by(id=queue_id).first()
            if item:
                if retry and item.attempts < 3:
                    item.status = "pending"
                    item.priority -= 1
                else:
                    item.status = "failed"
                self.db.commit()
        except Exception as e:
            logger.error(f"Error marking URL as failed: {str(e)}")
            self.db.rollback()

    def get_stats(self) -> dict:
        """Get queue statistics."""
        try:
            total = self.db.query(URLQueueModel).count()
            pending = self.db.query(URLQueueModel).filter_by(status="pending").count()
            processing = self.db.query(URLQueueModel).filter_by(status="processing").count()
            completed = self.db.query(URLQueueModel).filter_by(status="completed").count()
            failed = self.db.query(URLQueueModel).filter_by(status="failed").count()

            return {
                "total": total,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
            }
        except Exception as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            return {}

    def clear_completed(self):
        """Clear completed URLs from queue."""
        try:
            self.db.query(URLQueueModel).filter_by(status="completed").delete()
            self.db.commit()
        except Exception as e:
            logger.error(f"Error clearing completed URLs: {str(e)}")
            self.db.rollback()
