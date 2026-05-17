from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/bangalore_marketplace"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 40

    # Scraping
    request_timeout: int = 30
    max_retries: int = 3
    retry_backoff_base: float = 1.0
    rate_limit_per_domain: float = 1.0  # requests per second
    user_agent_list: list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]

    # Playwright
    playwright_headless: bool = True
    playwright_timeout: int = 30000
    playwright_max_workers: int = 3

    # Proxy
    use_proxy: bool = False
    proxy_list: list = []

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/scraper.log"

    # File Paths
    data_dir: str = "data"
    output_dir: str = "data/output"
    export_format: str = "csv"  # csv, json, excel

    # Scraping Targets
    target_city: str = "Bangalore"
    target_localities: list = [
        "Whitefield",
        "HSR Layout",
        "Bellandur",
        "Sarjapur",
        "Marathahalli",
        "Koramangala",
        "Indiranagar",
        "Jayanagar",
        "Electronic City",
        "Yelahanka",
        "JP Nagar",
        "BTM Layout",
        "Hebbal",
        "Bannerghatta",
        "CV Raman Nagar",
        "Brookefield",
        "RR Nagar",
        "Rajajinagar",
        "Malleshwaram",
    ]

    target_categories: list = [
        "music_teacher",
        "dance_classes",
        "sports_coaching",
        "swimming",
        "martial_arts",
        "yoga",
        "chess",
        "coding_classes",
        "spoken_english",
        "language_tutors",
        "home_tuition",
        "art_craft",
        "pottery",
        "robotics",
        "abacus",
        "public_speaking",
        "daycare",
        "babysitting",
        "personality_development",
        "competitive_exam_coaching",
        "kids_activities",
        "hobby_classes",
    ]

    # Platform Configurations
    platforms: dict = {
        "justdial": {
            "enabled": True,
            "base_url": "https://www.justdial.com",
            "timeout": 30,
        },
        "sulekha": {
            "enabled": True,
            "base_url": "https://www.sulekha.com",
            "timeout": 30,
        },
        "urbanpro": {
            "enabled": True,
            "base_url": "https://www.urbanpro.com",
            "timeout": 30,
        },
        "teacherons": {
            "enabled": False,
            "base_url": "https://www.teacherons.com",
            "timeout": 30,
        },
        "superprof": {
            "enabled": False,
            "base_url": "https://www.superprof.com",
            "timeout": 30,
        },
        "google_maps": {
            "enabled": False,
            "timeout": 30,
        },
    }

    class Config:
        env_file = ".env"
        case_sensitive = False
