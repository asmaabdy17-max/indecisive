# Quick Start Guide

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- 2GB RAM minimum

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install
```

### 2. Setup Database
```bash
# Create database
createdb bangalore_marketplace

# Initialize tables
python -c "from storage.database import init_database; init_database()"
```

### 3. Configure Environment
```bash
# Copy example
cp config/.env.example .env

# Edit with your database URL if needed
# (localhost defaults should work)
```

### 4. Verify Setup
```bash
python main.py status
```

Expected output:
```
Database connection OK
Total providers in database: 0
```

## Basic Usage

### Scrape Justdial

```bash
python main.py scrape \
  --platform justdial \
  --category "music teacher" \
  --locality "Whitefield" \
  --limit 50
```

### Scrape Sulekha

```bash
python main.py scrape \
  --platform sulekha \
  --category "dance classes" \
  --locality "HSR Layout" \
  --limit 100
```

### Export Data

```bash
# Export all as CSV
python main.py export --format csv

# Export specific locality
python main.py export --format csv --locality "Whitefield"

# Export as JSON with summary
python main.py export --format json
```

## Expected Results

After successful scraping, you'll have:

✅ **Database entries** in `providers` table
✅ **CSV file** in `data/output/` with columns:
- ID, Source, Name, Phone, Email, Address, Locality, Category, Rating, etc.

✅ **JSON file** with structured data and summary statistics

## With Docker

### One Command Setup

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Ready for scraping commands

### Run Scraping in Docker

```bash
docker-compose exec scraper python main.py scrape \
  --platform justdial \
  --category "music teacher" \
  --locality "Whitefield"
```

### View Results

```bash
# Check database status
docker-compose exec scraper python main.py status

# View logs
docker-compose logs scraper

# Export data
docker-compose exec scraper python main.py export --format csv
```

## Next Steps

1. **Read** [README.md](README.md) for full documentation
2. **Explore** [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. **Check** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for data model
4. **Review** [DEPLOYMENT.md](DEPLOYMENT.md) for production setup

## Troubleshooting

### PostgreSQL Connection Error
```
Error: could not connect to server
```
Make sure PostgreSQL is running:
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql

# Docker
docker-compose up -d
```

### No Data Extracted
- Check website layout hasn't changed
- Try `--limit 5` to test small batch
- Check `logs/scraper.log` for errors
- Verify network connectivity

### Rate Limited (HTTP 429)
- Reduce rate limit in `.env`: `RATE_LIMIT_PER_DOMAIN=0.5`
- Add delay between requests
- Use proxy (edit config)

## Available Scraping Commands

```bash
# Single category
python main.py scrape \
  --platform justdial \
  --category "coding classes" \
  --locality "Electronic City"

# With limit
python main.py scrape \
  --platform sulekha \
  --category "sports coaching" \
  --locality "Marathahalli" \
  --limit 200

# Check status
python main.py status

# Export options
python main.py export --format csv
python main.py export --format json
python main.py export --format csv --category "music teacher"
python main.py export --format csv --locality "Indiranagar"
```

## File Locations

| Item | Location |
|------|----------|
| Database | PostgreSQL (default: localhost:5432) |
| Logs | `logs/scraper.log` |
| CSV Exports | `data/output/*.csv` |
| JSON Exports | `data/output/*.json` |
| Config | `.env` |

## Performance Tips

1. **Faster Extraction**: Use multiple workers
   - Edit `config/settings.py` → `playwright_max_workers=5`

2. **Faster Insertion**: Batch processing
   - Increase batch size in `.env`

3. **Better Dedup**: Use dedicated database
   - PostgreSQL on separate server
   - Proper indexing (built-in)

4. **Resume Interrupted Scrapes**
   - Database stores progress
   - Re-run same command to resume

## Common Workflows

### Get all music teachers in Whitefield
```bash
python main.py scrape --platform justdial --category "music teacher" --locality "Whitefield"
python main.py export --format csv --category "music_teacher" --locality "Whitefield"
```

### Collect dance classes across major localities
```bash
for locality in Whitefield "HSR Layout" Koramangala Indiranagar; do
  python main.py scrape --platform sulekha --category "dance classes" --locality "$locality" --limit 100
done
python main.py export --format csv --category "dance_classes"
```

### Get all providers and export as JSON
```bash
python main.py scrape --platform justdial --category "music teacher" --locality "Bangalore" --limit 500
python main.py export --format json
```

## Support

- Check [README.md](README.md) for detailed documentation
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Check logs: `tail -f logs/scraper.log`
- Query database directly:
  ```bash
  psql -d bangalore_marketplace -c "SELECT count(*) FROM providers;"
  ```

## What's Next?

- ✅ Basic scraping working
- 📚 Read documentation for advanced features
- 🚀 Deploy to production
- 🔄 Set up scheduled jobs
- 📊 Create dashboard
- 🤖 Add AI-based categorization

Happy scraping! 🎉
