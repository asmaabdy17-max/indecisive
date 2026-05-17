# Bangalore Marketplace Scraper - System Architecture

## Overview
A scalable, modular web scraping pipeline for discovering educational and kids activity service providers across Bangalore.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Input: Seed URLs                          │
│                   (Categories & Localities)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               URL Discovery & Queue Management               │
│  - Category crawler discovers service types                  │
│  - Locality crawler discovers Bangalore areas               │
│  - Maintains deduplicated URL queue                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            HTTP Fetching & Request Management                │
│  - Rotating user agents                                      │
│  - Proxy rotation ready                                      │
│  - Rate limiting (1-2 req/sec per domain)                   │
│  - Retry logic with exponential backoff                     │
│  - CAPTCHA detection                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            HTML Parsing & Data Extraction                    │
│  - BeautifulSoup/lxml for static content                    │
│  - Playwright for dynamic JS-rendered pages                 │
│  - Structured field extraction                              │
│  - Data normalization                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Quality & Deduplication                    │
│  - Duplicate detection (MD5 hash of key fields)             │
│  - Phone number normalization                               │
│  - Address standardization                                   │
│  - Category tagging                                          │
│  - AI-based summary generation (optional)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           PostgreSQL Storage & Output Export                 │
│  - providers table with full denormalization                │
│  - CSV/JSON export pipelines                                │
│  - Incremental update support                               │
│  - Query indexing for fast lookups                          │
└─────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. **Config Module** (`config/`)
- Environment configuration
- Database credentials
- Scraping parameters (timeout, retries, rate limits)
- Proxy configuration
- Platform-specific settings (Justdial, Sulekha, UrbanPro, etc.)

### 2. **Scrapers Module** (`scrapers/`)
- Base scraper class with common logic
- Platform-specific scrapers:
  - `justdial_scraper.py` - Justdial.com listings
  - `sulekha_scraper.py` - Sulekha.com listings
  - `urbanpro_scraper.py` - UrbanPro.com listings
  - `google_maps_scraper.py` - Google Maps public listings
  - `teacherons_scraper.py` - TeacherOn listings
  - `superprof_scraper.py` - Superprof listings
- URL discovery and crawling

### 3. **Parsers Module** (`parsers/`)
- Platform-specific HTML/JSON parsers
- Listing extraction logic
- Field mapping and normalization

### 4. **Storage Module** (`storage/`)
- PostgreSQL connection pooling
- ORM models (SQLAlchemy)
- CRUD operations
- Deduplication logic
- Bulk insert/update

### 5. **Utils Module** (`utils/`)
- HTTP client with rotating user agents
- Phone number formatter
- Address normalizer
- Locality matcher
- Category tagger
- Email extractor
- Social media detector
- Rate limiter
- Logger

### 6. **Queue Management** (`queue/`)
- In-memory URL queue (expandable to Redis)
- URL deduplication
- Priority queue support
- Batch processing

### 7. **Output Module** (`output/`)
- CSV exporter
- JSON exporter
- Excel exporter
- Report generation

## Data Flow

```
Seed URLs (categories + localities)
        ↓
URL Discovery (extract listing URLs from category/locality pages)
        ↓
Listing Deduplication (check if URL already processed)
        ↓
Fetch Listing Details (HTML/JS rendering)
        ↓
Parse & Extract Fields (structured data extraction)
        ↓
Normalize & Validate (clean phone, address, etc.)
        ↓
Duplicate Check (MD5 hash of core fields)
        ↓
Store in PostgreSQL
        ↓
Export to CSV/JSON (on-demand)
```

## Concurrency Model

- **Async I/O** using Python `asyncio`
- Playwright for concurrent browser automation (3-5 workers)
- Connection pooling for database
- Rate limiting per domain (respect server load)

## Deduplication Strategy

- MD5 hash of: `(source_platform, provider_name, phone_number, city)`
- Store hash in `listing_hash` field
- Check before inserting to avoid duplicates

## Retry Strategy

- Max 3 retries per URL with exponential backoff
- 1s → 2s → 4s delays
- Skip on 403 (Forbidden), 404 (Not Found), 429 (Too Many Requests for that session)

## Scalability Considerations

1. **Horizontal Scaling**: Worker pool architecture allows running multiple scraper instances
2. **Database**: Proper indexing on frequently queried fields
3. **Caching**: In-memory cache for locality/category mappings
4. **Incremental**: Support for resuming scraping (timestamp tracking)
5. **Error Recovery**: Failed URLs logged separately for retry

## CAPTCHA Handling

- Manual bypass mode (logs CAPTCHA URLs)
- 2Captcha/DeathByCaptcha API integration ready
- Browser user-agent rotation to reduce CAPTCHA triggers

## Security & Ethics

- Respects `robots.txt` guidelines
- Rate limiting to avoid server overload
- Scrapes only publicly accessible information
- User-agent properly identifies bot
- Logs all scraping activity

## Performance Targets

- 500-1000 listings per hour per worker
- <2s average per listing detail page
- <100ms database insert per record
- Deduplication check in <10ms

## Future Expansion

- Multi-city support (Mumbai, Delhi, Hyderabad)
- Real-time price monitoring
- Lead quality scoring
- Automated outreach integration
- Mobile app integration
