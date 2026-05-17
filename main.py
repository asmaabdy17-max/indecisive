#!/usr/bin/env python3
import asyncio
import argparse
import logging
import sys
from pathlib import Path

from config.settings import Settings
from storage.database import init_database
from utils.logger import setup_logger
from scrapers.justdial_scraper import JustdialScraper
from scrapers.sulekha_scraper import SulkhaScraper
from output.exporters import CSVExporter, JSONExporter


def setup_logging(settings: Settings):
    """Setup application logging."""
    logger = setup_logger("bangalore_scraper", settings.log_file, settings.log_level)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    return logger


async def scrape_single(
    platform: str,
    category: str,
    locality: str,
    limit: int = None,
    settings: Settings = None,
    database = None,
    logger = None,
):
    """Scrape a single category + locality combination."""
    if not settings:
        settings = Settings()
    if not database:
        database = init_database(settings)
    if not logger:
        logger = setup_logging(settings)

    logger.info(f"Starting scrape: {platform} - {category} - {locality}")

    try:
        if platform.lower() == "justdial":
            scraper = JustdialScraper(settings, database)
        elif platform.lower() == "sulekha":
            scraper = SulkhaScraper(settings, database)
        else:
            logger.error(f"Unknown platform: {platform}")
            return False

        count = await scraper.scrape_category_locality(
            category=category,
            locality=locality,
            limit=limit,
        )

        scraper.finalize_session()
        logger.info(f"Completed: {count} listings extracted")
        return True

    except Exception as e:
        logger.error(f"Scraping error: {str(e)}", exc_info=True)
        return False


async def scrape_all(
    settings: Settings = None,
    database = None,
    logger = None,
):
    """Scrape all configured categories and localities."""
    if not settings:
        settings = Settings()
    if not database:
        database = init_database(settings)
    if not logger:
        logger = setup_logging(settings)

    logger.info("Starting full scrape of all categories and localities")

    total_listings = 0
    tasks = []

    for platform, config in settings.platforms.items():
        if not config.get("enabled"):
            continue

        for category in settings.target_categories[:5]:
            for locality in settings.target_localities[:5]:
                task = scrape_single(
                    platform=platform,
                    category=category,
                    locality=locality,
                    limit=50,
                    settings=settings,
                    database=database,
                    logger=logger,
                )
                tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"Scraping complete. Total tasks: {len(tasks)}")


async def export_data(
    format_type: str = "csv",
    category: str = None,
    locality: str = None,
    settings: Settings = None,
    database = None,
    logger = None,
):
    """Export scraped data."""
    if not settings:
        settings = Settings()
    if not database:
        database = init_database(settings)
    if not logger:
        logger = setup_logging(settings)

    db_session = database.get_session()

    try:
        if format_type.lower() == "csv":
            exporter = CSVExporter(settings.output_dir)
            filepath = exporter.export(db_session, category=category, locality=locality)
        elif format_type.lower() == "json":
            exporter = JSONExporter(settings.output_dir)
            filepath = exporter.export(db_session, category=category, locality=locality)
            summary = exporter.export_summary(db_session)
            logger.info(f"Summary exported to {summary}")
        else:
            logger.error(f"Unknown export format: {format_type}")
            return False

        logger.info(f"Data exported to {filepath}")
        return True

    except Exception as e:
        logger.error(f"Export error: {str(e)}", exc_info=True)
        return False

    finally:
        db_session.close()


async def check_database(
    settings: Settings = None,
    database = None,
    logger = None,
):
    """Check database connectivity and show statistics."""
    if not settings:
        settings = Settings()
    if not database:
        database = init_database(settings)
    if not logger:
        logger = setup_logging(settings)

    if database.health_check():
        logger.info("Database connection OK")

        db_session = database.get_session()
        try:
            from storage.models import Provider

            total = db_session.query(Provider).count()
            logger.info(f"Total providers in database: {total}")

            platforms = db_session.query(
                Provider.source_platform, db_session.func.count(Provider.id)
            ).group_by(Provider.source_platform).all()

            for platform, count in platforms:
                logger.info(f"  {platform}: {count}")

        finally:
            db_session.close()

        return True
    else:
        logger.error("Database connection failed")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Bangalore Marketplace Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py scrape --platform justdial --category "music teacher" --locality "Whitefield"
  python main.py export --format csv --locality "HSR Layout"
  python main.py status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    scrape_parser = subparsers.add_parser("scrape", help="Scrape listings")
    scrape_parser.add_argument("--platform", required=True, help="Platform: justdial, sulekha, urbanpro")
    scrape_parser.add_argument("--category", required=True, help="Category to scrape")
    scrape_parser.add_argument("--locality", required=True, help="Locality to scrape")
    scrape_parser.add_argument("--limit", type=int, help="Limit number of listings")

    export_parser = subparsers.add_parser("export", help="Export data")
    export_parser.add_argument("--format", default="csv", choices=["csv", "json"], help="Export format")
    export_parser.add_argument("--category", help="Filter by category")
    export_parser.add_argument("--locality", help="Filter by locality")

    subparsers.add_parser("status", help="Show database status")

    args = parser.parse_args()

    settings = Settings()
    database = init_database(settings)
    logger = setup_logging(settings)

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "scrape":
            asyncio.run(
                scrape_single(
                    platform=args.platform,
                    category=args.category,
                    locality=args.locality,
                    limit=args.limit,
                    settings=settings,
                    database=database,
                    logger=logger,
                )
            )

        elif args.command == "export":
            asyncio.run(
                export_data(
                    format_type=args.format,
                    category=args.category,
                    locality=args.locality,
                    settings=settings,
                    database=database,
                    logger=logger,
                )
            )

        elif args.command == "status":
            asyncio.run(
                check_database(
                    settings=settings,
                    database=database,
                    logger=logger,
                )
            )

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        database.close()


if __name__ == "__main__":
    main()
