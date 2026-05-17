# PostgreSQL Database Schema

## Core Tables

### 1. providers
Master table for all scraped service providers.

```sql
CREATE TABLE providers (
    id BIGSERIAL PRIMARY KEY,
    
    -- Unique Identifiers
    source_platform VARCHAR(50) NOT NULL,  -- 'justdial', 'sulekha', 'urbanpro', etc.
    provider_id VARCHAR(100),  -- Platform-specific ID
    listing_url TEXT UNIQUE,   -- Source URL
    listing_hash VARCHAR(64) UNIQUE,  -- MD5 hash for deduplication
    
    -- Basic Information
    provider_name VARCHAR(255) NOT NULL,
    teacher_or_business_type VARCHAR(100),  -- 'individual', 'academy', 'coaching_center'
    description TEXT,
    
    -- Location
    city VARCHAR(100) DEFAULT 'Bangalore',
    locality VARCHAR(150),  -- 'HSR Layout', 'Whitefield', etc.
    full_address TEXT,
    pincode VARCHAR(10),
    
    -- Geographic Data
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Contact Information
    phone_number VARCHAR(20),
    whatsapp_number VARCHAR(20),
    email VARCHAR(255),
    website TEXT,
    
    -- Social Media
    instagram_handle VARCHAR(255),
    facebook_url TEXT,
    youtube_channel TEXT,
    
    -- Ratings & Reviews
    rating DECIMAL(3, 2),  -- 0-5 scale
    review_count INTEGER DEFAULT 0,
    
    -- Professional Details
    years_experience INTEGER,
    gender VARCHAR(20),  -- 'male', 'female', 'unknown'
    languages_spoken TEXT,  -- JSON array: ["English", "Hindi", "Kannada"]
    
    -- Service Details
    subjects_taught TEXT,  -- JSON array
    age_group TEXT,  -- e.g., "5-8 years", "10-18 years"
    pricing TEXT,  -- e.g., "₹500/hour"
    timing TEXT,  -- e.g., "Mon-Fri 4-6 PM"
    
    -- Service Modes
    home_service_available BOOLEAN DEFAULT FALSE,
    online_classes_available BOOLEAN DEFAULT FALSE,
    
    -- Categories
    category VARCHAR(100),  -- 'music_teacher', 'dance_class', etc.
    subcategory VARCHAR(100),
    tags TEXT,  -- JSON array for flexible categorization
    
    -- Media
    image_urls TEXT,  -- JSON array
    
    -- Activity Tracking
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    data_quality_score DECIMAL(3, 2),  -- 0-1 score
    confidence_score DECIMAL(3, 2),  -- Extraction confidence
    notes TEXT
);

-- Indexes for performance
CREATE INDEX idx_providers_city_locality ON providers(city, locality);
CREATE INDEX idx_providers_category ON providers(category);
CREATE INDEX idx_providers_phone ON providers(phone_number);
CREATE INDEX idx_providers_source_platform ON providers(source_platform);
CREATE INDEX idx_providers_listing_hash ON providers(listing_hash);
CREATE INDEX idx_providers_active ON providers(active);
CREATE INDEX idx_providers_scraped_at ON providers(scraped_at DESC);
CREATE UNIQUE INDEX idx_providers_unique ON providers(source_platform, provider_id);
```

### 2. categories
Dynamic category taxonomy discovered during scraping.

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    slug VARCHAR(150) UNIQUE NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(id),
    level INTEGER,  -- 0=top, 1=sub, etc.
    source_platform VARCHAR(50),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    listing_count INTEGER DEFAULT 0,
    
    CONSTRAINT category_slug_format CHECK (slug ~ '^[a-z0-9_]+$')
);

CREATE INDEX idx_categories_parent ON categories(parent_category_id);
CREATE INDEX idx_categories_listing_count ON categories(listing_count DESC);
```

### 3. localities
Bangalore localities for search and filtering.

```sql
CREATE TABLE localities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    slug VARCHAR(150) UNIQUE NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    pincode VARCHAR(10),
    listing_count INTEGER DEFAULT 0,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_localities_name ON localities(name);
CREATE INDEX idx_localities_listing_count ON localities(listing_count DESC);
```

### 4. scraping_sessions
Track scraping runs for monitoring and resumption.

```sql
CREATE TABLE scraping_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50),  -- 'running', 'completed', 'failed', 'paused'
    platform VARCHAR(50),
    category VARCHAR(100),
    locality VARCHAR(150),
    total_urls_found INTEGER DEFAULT 0,
    total_urls_processed INTEGER DEFAULT 0,
    total_listings_extracted INTEGER DEFAULT 0,
    total_duplicates INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    error_message TEXT,
    config_hash VARCHAR(64)  -- Hash of scraping config for reproducibility
);

CREATE INDEX idx_scraping_sessions_status ON scraping_sessions(status);
CREATE INDEX idx_scraping_sessions_platform ON scraping_sessions(platform);
```

### 5. scraping_errors
Detailed error logging for debugging and retry.

```sql
CREATE TABLE scraping_errors (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(50),
    url TEXT,
    error_type VARCHAR(100),  -- 'timeout', 'captcha', 'parse_error', '404', etc.
    error_message TEXT,
    status_code INTEGER,
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES scraping_sessions(session_id)
);

CREATE INDEX idx_scraping_errors_session ON scraping_errors(session_id);
CREATE INDEX idx_scraping_errors_retry_at ON scraping_errors(next_retry_at);
```

### 6. url_queue
Tracks URLs to be processed (for resumable scraping).

```sql
CREATE TABLE url_queue (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    url_type VARCHAR(50),  -- 'category', 'listing', 'detail'
    source_platform VARCHAR(50),
    category VARCHAR(100),
    locality VARCHAR(150),
    priority INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_url_queue_status ON url_queue(status);
CREATE INDEX idx_url_queue_priority ON url_queue(priority DESC);
CREATE INDEX idx_url_queue_platform ON url_queue(source_platform);
```

### 7. provider_history
Audit trail for provider updates.

```sql
CREATE TABLE provider_history (
    id BIGSERIAL PRIMARY KEY,
    provider_id BIGINT NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
);

CREATE INDEX idx_provider_history_provider ON provider_history(provider_id);
CREATE INDEX idx_provider_history_timestamp ON provider_history(changed_at DESC);
```

### 8. exports
Track data exports for reporting.

```sql
CREATE TABLE exports (
    id BIGSERIAL PRIMARY KEY,
    export_type VARCHAR(50),  -- 'csv', 'json', 'excel'
    file_path TEXT,
    filter_category VARCHAR(100),
    filter_locality VARCHAR(150),
    total_records INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

CREATE INDEX idx_exports_created_at ON exports(created_at DESC);
```

## Normalization Views

```sql
-- View for provider statistics by category
CREATE VIEW provider_stats_by_category AS
SELECT 
    category,
    COUNT(*) as provider_count,
    AVG(rating) as avg_rating,
    COUNT(DISTINCT city) as cities,
    COUNT(DISTINCT locality) as localities
FROM providers
WHERE active = TRUE
GROUP BY category;

-- View for provider statistics by locality
CREATE VIEW provider_stats_by_locality AS
SELECT 
    locality,
    COUNT(*) as provider_count,
    AVG(rating) as avg_rating,
    COUNT(DISTINCT category) as categories,
    COUNT(DISTINCT source_platform) as platforms
FROM providers
WHERE active = TRUE
GROUP BY locality;

-- View for data quality metrics
CREATE VIEW data_quality_metrics AS
SELECT 
    COUNT(*) as total_providers,
    COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as with_ratings,
    COUNT(CASE WHEN phone_number IS NOT NULL THEN 1 END) as with_phone,
    COUNT(CASE WHEN website IS NOT NULL THEN 1 END) as with_website,
    AVG(CASE WHEN data_quality_score IS NOT NULL THEN data_quality_score ELSE 0 END) as avg_quality_score
FROM providers
WHERE active = TRUE;
```

## Data Types & Constraints

- **VARCHAR(255)**: Names, emails, single-line text
- **TEXT**: Long descriptions, addresses, JSON arrays
- **DECIMAL(10,8)**: Latitude coordinates
- **DECIMAL(11,8)**: Longitude coordinates
- **DECIMAL(3,2)**: Ratings (0-5.00)
- **BIGINT**: Large sequential IDs
- **TIMESTAMP**: All timestamps use server timezone

## JSON Fields

Fields like `subjects_taught`, `languages_spoken`, `image_urls` stored as TEXT containing JSON:

```json
{
  "subjects_taught": ["Math", "Physics", "Chemistry"],
  "languages_spoken": ["English", "Hindi", "Kannada"],
  "image_urls": ["https://...img1.jpg", "https://...img2.jpg"],
  "tags": ["verified", "active", "experienced"]
}
```

## Backup & Recovery

- Daily automated backups (WAL archiving)
- Point-in-time recovery enabled
- Test backup restoration weekly
