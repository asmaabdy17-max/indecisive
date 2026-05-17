# Scraping Flow Documentation

## High-Level Flow

```
User Request (CLI)
    ↓
Initialize Database Connection
    ↓
Load Configuration
    ↓
Select Platform & Categories
    ↓
For Each Category + Locality Pair:
    - Discover Listing URLs
    - For Each URL:
        - Fetch Page Content
        - Parse & Extract Fields
        - Normalize Data
        - Check for Duplicates
        - Save to Database
    - Update Statistics
    ↓
Export Data (Optional)
    ↓
Generate Report
```

## Detailed Steps

### 1. Discovery Phase

**Category Discovery**
- Visit platform homepage or category listing page
- Parse category links/sections
- Extract category names and URLs
- Store in in-memory cache

**Listing Discovery**
- Visit category + locality page
- Parse search results
- Extract listing URLs (typically 20-100 per page)
- Handle pagination

**URL Queue Management**
- Add each discovered URL to database queue
- Check for duplicates using MD5 hash
- Set priority and metadata

### 2. Extraction Phase

For each listing URL:

```python
1. Fetch Page
   - Make HTTP request with rate limiting
   - Handle redirects and errors
   - Check for CAPTCHA

2. Parse Content
   - Use BeautifulSoup/lxml for static HTML
   - Use Playwright for JS-rendered content
   - Wait for dynamic content to load

3. Extract Fields
   - Provider name
   - Phone number(s)
   - Email
   - Address
   - Website
   - Rating/Reviews
   - Description
   - Images
   - Service details (subjects, age group, timing, pricing)

4. Normalize Data
   - Phone: Standardize to +91XXXXXXXXXX
   - Address: Remove extra spaces, special characters
   - Category: Map to standard slugs
   - Locality: Extract from address with fuzzy matching
   - URLs: Validate format

5. Quality Check
   - Verify required fields present
   - Validate phone format
   - Check email format
   - Validate coordinates
   - Calculate quality score (0-1)

6. Deduplication
   - Generate MD5 hash
   - Check if hash exists in database
   - Skip if duplicate found
   - Otherwise, insert record
```

### 3. Storage Phase

```python
1. Connect to Database
   - Use connection pooling
   - Retry on connection failure

2. Check Duplicate
   - Query by source_platform + provider_id
   - Query by listing_hash
   - Skip if exists

3. Insert Record
   - Create Provider object
   - Set all fields
   - Add metadata (scraped_at, quality_score, etc.)
   - Commit transaction

4. Update Statistics
   - Increment counters
   - Update category listing_count
   - Update locality listing_count

5. Error Logging
   - Log any errors to scraping_errors table
   - Record status code
   - Capture error message
```

### 4. Export Phase

```python
1. Query Database
   - Filter by category/locality if specified
   - Order by quality score
   - Select active records only

2. Transform Data
   - Convert DB objects to dictionaries
   - Handle NULL values
   - Format dates/numbers

3. Write Output
   - CSV: Use pandas to_csv()
   - JSON: Use json.dump() with indent
   - Excel: Use openpyxl

4. Metadata
   - Record export info in exports table
   - Log file path and size
   - Generate summary statistics
```

## Error Handling Strategy

### Network Errors
```
Try 1: Initial request (timeout 30s)
       ↓ timeout
Try 2: Wait 1s, retry
       ↓ timeout
Try 3: Wait 2s, retry
       ↓ timeout
Try 4: Wait 4s, retry
       ↓ timeout
Log Error: Max retries exceeded
Skip URL: Move to next
```

### CAPTCHA Detection
```
Parse response content
Check for CAPTCHA keywords
If CAPTCHA detected:
  - Log CAPTCHA error
  - Add to manual_review queue
  - Skip URL
  - Continue with next
```

### Parsing Errors
```
Try parsing with BeautifulSoup
If parse fails:
  - Log parse error
  - Try Playwright (if enabled)
  - If still fails, skip URL
  - Continue with next
```

## Rate Limiting

```python
class RateLimiter:
    min_interval = 1.0 / 1.0  # 1.0 req/sec

    def wait(domain):
        elapsed = now - last_request[domain]
        if elapsed < min_interval:
            sleep(min_interval - elapsed)
        last_request[domain] = now
```

For each domain:
- Track last request timestamp
- Before next request, ensure min_interval has passed
- Sleep if needed

## Async Concurrency

```python
async def scrape_multiple():
    tasks = [
        scrape_justdial("music", "whitefield"),
        scrape_sulekha("dance", "hsr"),
        scrape_urbanpro("coding", "indiranagar"),
    ]
    results = await asyncio.gather(*tasks)
```

- Tasks run concurrently
- Each task handles its own errors
- Database connections pooled
- Rate limiting per domain (not per task)

## Memory Management

```python
- Use generators for large result sets
- Process in batches (100 items)
- Close database sessions after use
- Clear URL queue periodically
- Use SQLAlchemy expunge_all() to free memory
```

## Monitoring & Logging

Each scraping session logs:
- Session ID (for grouping)
- Platform being scraped
- Category and locality
- Start time
- Total URLs found
- Total URLs processed
- Total listings extracted
- Total duplicates
- Total errors
- End time
- Status (completed/failed/paused)

Example log:
```
2024-05-17 10:30:45 - INFO - Session abc12345 started
2024-05-17 10:30:46 - INFO - Discovered 50 listing URLs
2024-05-17 10:31:30 - INFO - Processed 45 listings
2024-05-17 10:31:30 - INFO - 3 duplicates found
2024-05-17 10:31:30 - INFO - 2 errors encountered
2024-05-17 10:31:30 - INFO - Session completed: 40 new providers saved
```

## Resume Capability

If scraping is interrupted:

1. Check `scraping_sessions` for status = "running"
2. Query `url_queue` for status = "pending" or "processing"
3. Verify data integrity (no partial saves)
4. Resume from last incomplete batch
5. Skip completed URLs

```sql
SELECT * FROM url_queue
WHERE status IN ('pending', 'processing')
ORDER BY priority DESC, created_at ASC
LIMIT 100;
```
