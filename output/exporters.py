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
from io import BytesIO

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


class ExcelExporter(BaseExporter):
    """Export provider data to Excel format with formatting."""

    def export(
        self,
        db: Session,
        filename: Optional[str] = None,
        category: Optional[str] = None,
        locality: Optional[str] = None,
    ) -> str:
        """Export providers to Excel with formatting."""
        try:
            query = db.query(Provider).filter_by(active=True)

            if category:
                query = query.filter(Provider.category.ilike(f"%{category}%"))
            if locality:
                query = query.filter(Provider.locality == locality)

            providers = query.all()
            logger.info(f"Exporting {len(providers)} providers to Excel")

            if not filename:
                filename = self._build_filename(category, locality) + ".xlsx"

            filepath = os.path.join(self.output_dir, filename)

            # Build data
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
                    "Experience (Yrs)": provider.years_experience,
                    "Gender": provider.gender,
                    "Languages": json.dumps(provider.languages_spoken) if provider.languages_spoken else "",
                    "Subjects": json.dumps(provider.subjects_taught) if provider.subjects_taught else "",
                    "Pricing": provider.pricing,
                    "Home Service": "Yes" if provider.home_service_available else "No",
                    "Online Classes": "Yes" if provider.online_classes_available else "No",
                    "Scraped": provider.scraped_at.isoformat() if provider.scraped_at else "",
                    "URL": provider.listing_url,
                    "Quality Score": provider.data_quality_score,
                })

            df = pd.DataFrame(data)

            # Create Excel writer
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Providers', index=False)

                # Format the worksheet
                worksheet = writer.sheets['Providers']

                # Set column widths
                column_widths = {
                    'A': 6,   # ID
                    'B': 12,  # Source
                    'C': 20,  # Name
                    'D': 15,  # Type
                    'E': 25,  # Description
                    'F': 14,  # Phone
                    'G': 14,  # WhatsApp
                    'H': 18,  # Email
                    'I': 20,  # Website
                    'J': 25,  # Address
                    'K': 15,  # Locality
                    'L': 10,  # Pincode
                    'M': 12,  # Latitude
                    'N': 12,  # Longitude
                    'O': 15,  # Category
                    'P': 15,  # Subcategory
                    'Q': 8,   # Rating
                    'R': 8,   # Reviews
                    'S': 12,  # Experience
                    'T': 10,  # Gender
                    'U': 20,  # Languages
                    'V': 20,  # Subjects
                    'W': 12,  # Pricing
                    'X': 12,  # Home Service
                    'Y': 14,  # Online Classes
                    'Z': 18,  # Scraped
                }

                for col, width in column_widths.items():
                    worksheet.column_dimensions[col].width = width

                # Freeze header row
                worksheet.freeze_panes = 'A2'

                # Add summary sheet
                summary_data = {
                    'Metric': ['Total Providers', 'Unique Localities', 'Unique Categories', 'Export Date'],
                    'Value': [
                        len(providers),
                        db.query(Provider.locality).distinct().count() if not locality else 1,
                        db.query(Provider.category).distinct().count() if not category else 1,
                        datetime.now().isoformat(),
                    ]
                }

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

            logger.info(f"Excel exported to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            raise


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


class PDFExporter(BaseExporter):
    """Export provider data to PDF format."""

    def export(
        self,
        db: Session,
        filename: Optional[str] = None,
        category: Optional[str] = None,
        locality: Optional[str] = None,
    ) -> str:
        """Export providers to PDF."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT

            query = db.query(Provider).filter_by(active=True)

            if category:
                query = query.filter(Provider.category.ilike(f"%{category}%"))
            if locality:
                query = query.filter(Provider.locality == locality)

            providers = query.all()
            logger.info(f"Exporting {len(providers)} providers to PDF")

            if not filename:
                filename = self._build_filename(category, locality) + ".pdf"

            filepath = os.path.join(self.output_dir, filename)

            # Create PDF
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            elements.append(Paragraph("Bangalore Educational Service Providers", title_style))
            elements.append(Spacer(1, 0.3*inch))

            # Summary
            summary_style = styles['Normal']
            summary_text = f"Total Providers: {len(providers)} | Locality: {locality or 'All'} | Category: {category or 'All'} | Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            elements.append(Paragraph(summary_text, summary_style))
            elements.append(Spacer(1, 0.2*inch))

            # Table data
            table_data = [['Name', 'Phone', 'Email', 'Locality', 'Category', 'Rating']]

            for provider in providers[:100]:  # Limit to 100 for PDF (too large otherwise)
                table_data.append([
                    provider.provider_name[:30] if provider.provider_name else '',
                    provider.phone_number or '',
                    provider.email or '',
                    provider.locality or '',
                    provider.category or '',
                    str(provider.rating) if provider.rating else '',
                ])

            # Create table
            table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 1.5*inch, 1.2*inch, 1.2*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))

            elements.append(table)

            # Note if truncated
            if len(providers) > 100:
                elements.append(Spacer(1, 0.2*inch))
                note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, textColor=colors.red)
                elements.append(Paragraph(
                    f"Note: Showing first 100 of {len(providers)} providers. Export to Excel for complete data.",
                    note_style
                ))

            # Build PDF
            doc.build(elements)

            logger.info(f"PDF exported to {filepath}")
            return filepath

        except ImportError:
            logger.error("reportlab not installed. Install with: pip install reportlab")
            raise
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise
