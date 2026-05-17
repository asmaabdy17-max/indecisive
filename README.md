# Bangalore Marketplace Scraper

A production-grade web scraping pipeline for discovering educational and kids activity service providers across Bangalore, India.

## Features

- **Multi-Platform Support**: Scrape from Justdial, Sulekha, UrbanPro, and more
- **Comprehensive Categories**: 22+ service categories including music, dance, sports, coding, tutoring, and more
- **Smart Deduplication**: MD5-based duplicate detection across platforms
- **Data Quality Scoring**: Automatic quality assessment of extracted data
- **Structured Output**: PostgreSQL database + CSV/JSON exports
- **Rate Limiting**: Respectful crawling with configurable rate limits
- **Error Handling**: Comprehensive logging and retry mechanisms
- **Scalable Architecture**: Async I/O with worker pool support

## Project Structure

```
.
├── config/              # Configuration management
├── scrapers/            # Platform-specific scrapers
├── parsers/             # HTML/JSON parsers
├── storage/             # Database models and ORM
├── utils/               # Utility functions (normalization, validation, etc.)
├── queue/               # URL queue management
├── output/              # Export functionality (CSV, JSON)
├── migrations/          # Alembic database migrations
├── tests/               # Unit and integration tests
├── ARCHITECTURE.md      # System design documentation
├── DATABASE_SCHEMA.md   # PostgreSQL schema
├── requirements.txt     # Python dependencies
├── main.py              # CLI entry point
└── README.md            # This file
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Docker (optional)

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd bangalore-marketplace-scraper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install
```

4. Set up environment variables:
```bash
cp config/.env.example .env
# Edit .env with your database credentials
```

5. Initialize the database:
```bash
psql -U postgres -c "CREATE DATABASE bangalore_marketplace"
python -c "from storage.database import init_database; from config.settings import Settings; init_database(Settings())"
```

## Configuration

Edit `.env` file to configure:

```
DATABASE_URL=postgresql://user:password@localhost:5432/bangalore_marketplace
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT_PER_DOMAIN=1.0
PLAYWRIGHT_HEADLESS=true
LOG_LEVEL=INFO
```

## Usage

### Scrape a Single Category + Locality

```bash
python main.py scrape --platform justdial --category "music teacher" --locality "Whitefield" --limit 100
```

### Scrape Multiple Categories (Async)

```bash
python main.py scrape-all --platform justdial --categories "music teacher,dance classes" --limit 50
```

### Export Data

Export as CSV:
```bash
python main.py export --format csv --locality "HSR Layout"
```

Export as JSON:
```bash
python main.py export --format json --category "coding_classes"
```

### Check Database Status

```bash
python main.py status
```

## Supported Platforms

| Platform | Status | Support |
|----------|--------|---------|
| Justdial | ✅ Implemented | Search, listings, details |
| Sulekha | ✅ Implemented | Search, listings, details |
| UrbanPro | 🔄 In Progress | Contact format differs |
| TeacherOn | 🔄 Planned | API-first platform |
| Superprof | 🔄 Planned | React-based frontend |
| Google Maps | 🔄 Planned | API integration |

## Data Schema

### Core Fields

- **Identification**: source_platform, provider_id, listing_url, listing_hash
- **Basic Info**: provider_name, description, teacher_or_business_type
- **Contact**: phone_number, whatsapp_number, email, website
- **Location**: full_address, locality, city, pincode, latitude, longitude
- **Professional**: years_experience, gender, languages_spoken
- **Services**: category, subcategory, subjects_taught, age_group, pricing, timing
- **Service Modes**: home_service_available, online_classes_available
- **Quality**: rating, review_count, data_quality_score, confidence_score

See `DATABASE_SCHEMA.md` for complete schema.

## Localities Supported

- Whitefield
- HSR Layout
- Bellandur
- Sarjapur
- Marathahalli
- Koramangala
- Indiranagar
- Jayanagar
- Electronic City
- Yelahanka
- JP Nagar
- BTM Layout
- Hebbal
- Bannerghatta
- CV Raman Nagar
- Brookefield
- RR Nagar
- Rajajinagar
- Malleshwaram

(20+ more localities in settings)

## Service Categories

- Music teachers
- Dance classes
- Sports coaching (general)
- Swimming
- Martial arts
- Yoga
- Chess
- Coding classes
- Spoken English
- Language tutors
- Home tuition
- Art & craft
- Pottery
- Robotics
- Abacus
- Public speaking
- Daycare
- Babysitting
- Personality development
- Competitive exam coaching
- Kids activities
- Hobby classes

## Performance

- **Listing extraction**: ~500-1000 listings/hour per worker
- **Database insert**: <100ms per record
- **Deduplication check**: <10ms per record
- **Request timeout**: 30s with automatic retries

## Data Quality

The scraper calculates quality scores based on:
- Required fields present (70% weight): name, phone, city, locality, category, description
- Optional fields present (30% weight): rating, email, website, images, experience, languages, subjects

Quality scores range from 0 to 1.0.

## Error Handling

- **Max retries**: 3 attempts with exponential backoff (1s → 2s → 4s)
- **HTTP errors**: 403 (Forbidden) and 404 (Not Found) are skipped
- **CAPTCHA detection**: Logged and flagged for manual review
- **Database errors**: Logged and session rolled back

All errors are stored in `scraping_errors` table for analysis.

## Deduplication

Duplicates are detected using MD5 hash of:
```
{source_platform}:{provider_name}:{phone_number}:{email}
```

A duplicate is only inserted if the hash hasn't been seen before.

## Rate Limiting

- **Per-domain rate limiting**: 1 request/second per domain (configurable)
- **429 Too Many Requests**: Automatic backoff with exponential delay
- **User-Agent rotation**: Random user agents from configured list

## Logging

Logs are written to both console and file (`logs/scraper.log`):

```
2024-05-17 10:30:45 - bangalore_scraper - INFO - Starting scrape: justdial - music teacher - Whitefield
2024-05-17 10:30:46 - bangalore_scraper - INFO - Found 45 listings
2024-05-17 10:31:02 - bangalore_scraper - INFO - Saved provider: Raj's Music Academy
```

## Docker Support

```bash
docker build -t bangalore-scraper .
docker run -e DATABASE_URL=postgresql://user:pass@db:5432/scraped_data bangalore-scraper python main.py scrape --platform justdial --category "music teacher" --locality "Whitefield"
```

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

## Future Enhancements

- [ ] Real-time price monitoring
- [ ] AI-based category auto-tagging
- [ ] Lead quality scoring system
- [ ] Automatic inactivity detection
- [ ] Social media handle extraction
- [ ] Multi-city expansion (Mumbai, Delhi, Hyderabad)
- [ ] REST API for data access
- [ ] Web dashboard for monitoring

## Troubleshooting

### Database Connection Error

```
psycopg2.OperationalError: could not connect to server
```

Check PostgreSQL is running:
```bash
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS
```

### CAPTCHA Blocking

If seeing CAPTCHA errors:
1. Reduce `RATE_LIMIT_PER_DOMAIN` (e.g., 0.5 req/sec)
2. Enable proxy rotation in `.env`
3. Check `scraping_errors` table for captcha URLs

### Memory Issues

For large exports:
- Use `--locality` filter to reduce result set
- Process in batches instead of full export
- Increase available RAM or use streaming export

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes with tests
3. Submit PR with description

## License

MIT License - See LICENSE file

## Support

For issues, feature requests, or questions:
1. Check existing GitHub issues
2. Create detailed issue with reproduction steps
3. Include logs from `logs/scraper.log`

## Authors

- Built for Bangalore educational service discovery
- Production-ready scraping architecture
- Designed for scalability and maintainability
