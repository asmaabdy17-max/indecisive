import csv
import json
import logging
import os
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from storage.models import Provider

logger = logging.getLogger(__name__)


class BaseExporter:
    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _build_filename(self, category: str = None, locality: str = None) -> str:
        timestamp = self._get_timestamp()
        parts = ["providers", timestamp]

        if category:
            parts.append(category.replace(" ", "_"))
        if locality:
            parts.append(locality.replace(" ", "_"))

        return "_".join(parts)


class CSVExporter(BaseExporter):
    """Export provider data to CSV format."""

    def export(
        self,
        db: Session,
        filename: Optional[str] = None,
        category: Optional[str] = None,
        locality: Optional[str] = None,
    ) -> str:
        """Export providers to CSV."""
        try:
            query = db.query(Provider).filter_by(active=True)

            if category:
                query = query.filter(Provider.category.ilike(f"%{category}%"))
            if locality:
                query = query.filter(Provider.locality == locality)

            providers = query.all()
            logger.info(f"Exporting {len(providers)} providers to CSV")

            if not filename:
                filename = self._build_filename(category, locality) + ".csv"

            filepath = os.path.join(self.output_dir, filename)

            data = []
            for provider in providers:
                data.append({
                    "ID": provider.id,
                    "Source": provider.source_platform,
                    "Name": provider.provider_name,
                    "Type": provider.teacher_or_business_type,
                    "Description": provider.description,
                    "Phone": provider.phone_number,
                    "WhatsApp": provider.whatsapp_number,
                    "Email": provider.email,
                    "Website": provider.website,
                    "Address": provider.full_address,
                    "Locality": provider.locality,
                    "Pincode": provider.pincode,
                    "Latitude": provider.latitude,
                    "Longitude": provider.longitude,
                    "Category": provider.category,
                    "Subcategory": provider.subcategory,
                    "Rating": provider.rating,
                    "Reviews": provider.review_count,
                    "Experience": provider.years_experience,
                    "Gender": provider.gender,
                    "Languages": provider.languages_spoken,
                    "Subjects": provider.subjects_taught,
                    "Pricing": provider.pricing,
                    "Home Service": provider.home_service_available,
                    "Online Classes": provider.online_classes_available,
                    "Scraped": provider.scraped_at,
                    "URL": provider.listing_url,
                    "Quality Score": provider.data_quality_score,
                })

            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding="utf-8")

            logger.info(f"CSV exported to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise

    def export_by_locality(self, db: Session) -> List[str]:
        """Export CSV file for each locality."""
        localities = db.query(Provider.locality).distinct().all()
        files = []

        for (locality,) in localities:
            if locality:
                filepath = self.export(db, locality=locality)
                files.append(filepath)

        return files


class JSONExporter(BaseExporter):
    """Export provider data to JSON format."""

    def export(
        self,
        db: Session,
        filename: Optional[str] = None,
        category: Optional[str] = None,
        locality: Optional[str] = None,
    ) -> str:
        """Export providers to JSON."""
        try:
            query = db.query(Provider).filter_by(active=True)

            if category:
                query = query.filter(Provider.category.ilike(f"%{category}%"))
            if locality:
                query = query.filter(Provider.locality == locality)

            providers = query.all()
            logger.info(f"Exporting {len(providers)} providers to JSON")

            if not filename:
                filename = self._build_filename(category, locality) + ".json"

            filepath = os.path.join(self.output_dir, filename)

            data = []
            for provider in providers:
                data.append({
                    "id": provider.id,
                    "source_platform": provider.source_platform,
                    "provider_name": provider.provider_name,
                    "teacher_or_business_type": provider.teacher_or_business_type,
                    "description": provider.description,
                    "phone_number": provider.phone_number,
                    "whatsapp_number": provider.whatsapp_number,
                    "email": provider.email,
                    "website": provider.website,
                    "full_address": provider.full_address,
                    "locality": provider.locality,
                    "pincode": provider.pincode,
                    "latitude": float(provider.latitude) if provider.latitude else None,
                    "longitude": float(provider.longitude) if provider.longitude else None,
                    "category": provider.category,
                    "subcategory": provider.subcategory,
                    "rating": float(provider.rating) if provider.rating else None,
                    "review_count": provider.review_count,
                    "years_experience": provider.years_experience,
                    "gender": provider.gender,
                    "languages_spoken": provider.languages_spoken,
                    "subjects_taught": provider.subjects_taught,
                    "pricing": provider.pricing,
                    "home_service_available": provider.home_service_available,
                    "online_classes_available": provider.online_classes_available,
                    "image_urls": provider.image_urls,
                    "scraped_at": provider.scraped_at.isoformat() if provider.scraped_at else None,
                    "listing_url": provider.listing_url,
                    "data_quality_score": float(provider.data_quality_score) if provider.data_quality_score else None,
                })

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"JSON exported to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            raise

    def export_summary(self, db: Session) -> str:
        """Export summary statistics."""
        try:
            stats = {
                "total_providers": db.query(Provider).count(),
                "by_platform": {},
                "by_category": {},
                "by_locality": {},
                "exported_at": datetime.now().isoformat(),
            }

            platforms = db.query(Provider.source_platform, db.func.count(Provider.id)).group_by(Provider.source_platform).all()
            for platform, count in platforms:
                stats["by_platform"][platform] = count

            categories = db.query(Provider.category, db.func.count(Provider.id)).group_by(Provider.category).all()
            for category, count in categories:
                if category:
                    stats["by_category"][category] = count

            localities = db.query(Provider.locality, db.func.count(Provider.id)).group_by(Provider.locality).all()
            for locality, count in localities:
                if locality:
                    stats["by_locality"][locality] = count

            filename = f"summary_{self._get_timestamp()}.json"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)

            logger.info(f"Summary exported to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error exporting summary: {str(e)}")
            raise
