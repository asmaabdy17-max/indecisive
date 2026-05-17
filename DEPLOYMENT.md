# Deployment Guide

## Local Development

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- 2GB RAM minimum

### Quick Start

```bash
# Clone and setup
git clone <repo>
cd bangalore-marketplace-scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install

# Database
createdb bangalore_marketplace
python -c "from storage.database import init_database; init_database()"

# Test
python main.py status

# Scrape
python main.py scrape --platform justdial --category "music teacher" --locality "Whitefield"

# Export
python main.py export --format csv
```

## Docker Deployment

### Single Container

```bash
docker build -t bangalore-scraper:latest .

docker run \
  -e DATABASE_URL=postgresql://user:pass@db:5432/scraper_db \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  bangalore-scraper:latest \
  scrape --platform justdial --category "music teacher" --locality "Whitefield"
```

### Docker Compose (Recommended)

```bash
docker-compose up -d

# View logs
docker-compose logs -f scraper

# Run scraping job
docker-compose exec scraper python main.py scrape --platform justdial --category "music teacher" --locality "Whitefield"

# Stop
docker-compose down
```

## Production Deployment

### Requirements
- Dedicated PostgreSQL server (RDS or self-hosted)
- Multiple scraper instances (load balanced)
- Redis for distributed queue (optional)
- Monitoring (Prometheus, DataDog)
- Logging (ELK stack)

### Architecture

```
Load Balancer
    ↓
[Scraper-1] [Scraper-2] [Scraper-3]
    ↓          ↓          ↓
    └──────────┴──────────┘
              ↓
    PostgreSQL Database
              ↓
      [Redis Cache]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bangalore-scraper
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bangalore-scraper
  template:
    metadata:
      labels:
        app: bangalore-scraper
    spec:
      containers:
      - name: scraper
        image: bangalore-scraper:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: scraper-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: data
          mountPath: /app/data
      volumes:
      - name: logs
        emptyDir: {}
      - name: data
        persistentVolumeClaim:
          claimName: scraper-data
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@rds-instance.amazonaws.com:5432/bangalore_marketplace
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Scraping
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT_PER_DOMAIN=1.0

# Playwright
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_MAX_WORKERS=5

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/scraper.log

# Proxy (optional)
USE_PROXY=true
PROXY_LIST=http://proxy1:8080,http://proxy2:8080

# Performance
BATCH_SIZE=100
EXPORT_FORMAT=csv
```

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_providers_scraped_at_desc ON providers(scraped_at DESC);
CREATE INDEX idx_providers_quality_score ON providers(data_quality_score DESC);
CREATE INDEX idx_providers_active_locality ON providers(active, locality);

-- Archive old data
DELETE FROM scraping_errors WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM url_queue WHERE status = 'completed' AND processed_at < NOW() - INTERVAL '7 days';

-- Analyze tables
ANALYZE providers;
ANALYZE scraping_sessions;
```

### Backup Strategy

```bash
# Daily backup at 2 AM
0 2 * * * pg_dump -Fc $DATABASE_URL > /backups/db_$(date +\%Y\%m\%d).dump

# Weekly full backup to S3
0 3 * * 0 aws s3 cp /backups/db_latest.dump s3://backup-bucket/weekly/

# Test restore weekly
*/7 * * * 0 /scripts/test-restore.sh
```

## Monitoring

### Health Checks

```python
# Database
curl http://localhost:8000/health/db

# Queue status
curl http://localhost:8000/health/queue

# Scraper status
curl http://localhost:8000/health/scraper
```

### Alerts

```
- Database connection failures
- Error rate > 5%
- Queue backing up (>10K pending URLs)
- Scraping session timeout (>6 hours)
- Data quality score < 0.3
```

### Metrics

```
- URLs scraped per hour
- Duplicate rate (%)
- Average extraction time (ms)
- Database insert latency (ms)
- CAPTCHA encounter rate (%)
- Success rate (%)
```

## Scaling

### Horizontal Scaling

1. **Multiple Scraper Instances**
   - Each instance connects to same database
   - Rate limiting enforced per domain (shared)
   - URL queue managed centrally

2. **Load Balancing**
   - Use queue-based distribution
   - Each scraper picks next pending URL from database

3. **Redis Queue** (optional)
   ```python
   from rq import Queue
   q = Queue(connection=redis_conn)
   q.enqueue(scrape_single, 'justdial', 'music', 'whitefield')
   ```

### Vertical Scaling

- Increase `DB_POOL_SIZE` for more concurrent DB connections
- Increase `PLAYWRIGHT_MAX_WORKERS` for more browser instances (4GB RAM per worker)
- Use larger instance type with more CPU/RAM

## Troubleshooting

### High Error Rate
- Check logs for CAPTCHA keywords
- Reduce rate limit (1.0 → 0.5 req/sec)
- Enable proxy rotation
- Check network connectivity

### Memory Issues
- Reduce `BATCH_SIZE` from 100 to 50
- Increase swap space
- Use `--limit` flag to scrape smaller batches

### Database Connection Errors
```
Error: "too many connections"
Fix: Increase max_connections in postgresql.conf
     max_connections = 200
```

### Slow Extraction
- Profile with py-spy: `py-spy record -o profile.svg -- python main.py`
- Check network latency with `mtr`
- Increase `REQUEST_TIMEOUT` if platforms are slow

## Security

### Credentials

```bash
# Use environment variables (never commit credentials)
export DATABASE_URL=postgresql://...

# Or use .env file (add to .gitignore)
echo "DATABASE_URL=..." > .env

# Use AWS Secrets Manager in production
aws secretsmanager get-secret-value --secret-id scraper-db-url
```

### IP Whitelisting

```
If scraping IP-blocked:
- Use rotating proxy service
- Spread requests across time
- Add user-agent rotation (built-in)
```

### Data Privacy

- Scrape only publicly available info
- Respect robots.txt
- Rate limit to avoid server stress
- Don't store sensitive info unnecessarily

## Disaster Recovery

```bash
# Full backup
pg_dump -Fc $DATABASE_URL > backup.dump

# Restore from backup
pg_restore -d bangalore_marketplace backup.dump

# Point-in-time recovery
# Enable WAL archiving in postgresql.conf
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/archive/%f'

# Recover to specific timestamp
pg_ctl stop
# Edit recovery.conf
restore_command = 'cp /var/lib/postgresql/archive/%f %p'
recovery_target_timeline = 'latest'
recovery_target_time = '2024-05-17 10:30:00'
pg_ctl start
```

## Compliance

- GDPR: Don't store personal data unnecessarily
- CCPA: Implement data deletion procedures
- Terms of Service: Respect website ToS regarding scraping
- Robots.txt: Follow crawling guidelines
