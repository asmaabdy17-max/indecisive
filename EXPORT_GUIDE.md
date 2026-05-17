# Data Export Guide - PDF, Excel, CSV, JSON

## Quick Export Commands

### Export as Excel (Recommended)
```bash
python main.py export --format excel
```
Creates a nicely formatted Excel file with:
- Multiple sheets (Providers + Summary)
- Frozen header row
- Auto-sized columns
- Professional formatting

### Export as PDF
```bash
python main.py export --format pdf
```
Creates a printable PDF with:
- Summary statistics
- First 100 providers in table format
- Professional formatting
- Note about checking Excel for full data

### Export as CSV
```bash
python main.py export --format csv
```
Creates a comma-separated values file:
- All 30+ fields
- Compatible with all spreadsheet apps
- Easy to process programmatically

### Export as JSON
```bash
python main.py export --format json
```
Creates structured JSON files:
- Individual providers file
- Separate summary statistics file
- Easy to integrate with APIs

## Filtering by Locality

Export only providers from a specific area:

```bash
# Excel
python main.py export --format excel --locality "Whitefield"

# PDF
python main.py export --format pdf --locality "HSR Layout"

# CSV
python main.py export --format csv --locality "Koramangala"

# JSON
python main.py export --format json --locality "Indiranagar"
```

## Filtering by Category

Export only specific service types:

```bash
# All music teachers as Excel
python main.py export --format excel --category "music teacher"

# All dance classes as PDF
python main.py export --format pdf --category "dance classes"

# All coding classes as CSV
python main.py export --format csv --category "coding classes"
```

## Combined Filters

Export specific category + locality combination:

```bash
# Music teachers in Whitefield (Excel)
python main.py export --format excel --category "music teacher" --locality "Whitefield"

# Dance classes in HSR Layout (PDF)
python main.py export --format pdf --category "dance classes" --locality "HSR Layout"

# Coding classes in Electronic City (Excel)
python main.py export --format excel --category "coding classes" --locality "Electronic City"
```

## Export Locations

All exports are saved in: `data/output/`

Example file structure:
```
data/output/
├── providers_20240517_103045.csv
├── providers_20240517_103100.json
├── summary_20240517_103100.json
├── providers_20240517_103115.xlsx
├── providers_20240517_103130.pdf
├── providers_20240517_103145_music_teacher_whitefield.xlsx
└── providers_20240517_103200_dance_classes_hsr_layout.pdf
```

## Format Comparison

| Feature | Excel | PDF | CSV | JSON |
|---------|-------|-----|-----|------|
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Printable | ✅ | ✅✅ | ⚠️ | ❌ |
| Editable | ✅ | ❌ | ✅ | ❌ |
| File Size | Medium | Large | Small | Medium |
| Data Integrity | ✅ | Truncated* | ✅ | ✅ |
| Sheets | Multiple | Single | Single | Multiple |
| Formatting | Professional | Professional | None | None |
| Summary Stats | ✅ | ✅ | ❌ | ✅ |
| Best For | Desktop Use | Sharing/Print | Data Processing | Integration |

*PDF shows first 100 records (use Excel for full data)

## Excel Export Details

### File Structure
- **Sheet 1 - Providers**: All extracted provider data
  - 30+ columns with all information
  - Frozen header row for easy scrolling
  - Auto-sized columns
  - Professional styling

- **Sheet 2 - Summary**: Quick statistics
  - Total providers count
  - Unique localities
  - Unique categories
  - Export date/time

### Columns Included
```
ID, Source, Name, Type, Description, Phone, WhatsApp, Email, Website,
Address, Locality, Pincode, Latitude, Longitude, Category, Subcategory,
Rating, Reviews, Experience (Yrs), Gender, Languages, Subjects, Pricing,
Home Service, Online Classes, Scraped, URL, Quality Score
```

### Opening in Different Apps

**Microsoft Excel:**
```bash
# macOS
open data/output/providers_*.xlsx

# Windows
start data/output/providers_*.xlsx

# Linux
libreoffice data/output/providers_*.xlsx
```

**Google Sheets (Online):**
1. Go to https://sheets.google.com
2. File → Open
3. Select Excel file from `data/output/`

**LibreOffice Calc:**
```bash
libreoffice --calc data/output/providers_*.xlsx
```

## PDF Export Details

### What's Included
- Report title: "Bangalore Educational Service Providers"
- Summary section with key metrics
- Professional table with key provider info
- Column headers in blue
- Alternating row colors for readability

### Limitations
- Shows first 100 providers only
- Best for sharing/printing
- For full data, use Excel export

### Printing
```bash
# macOS
open -a "Preview" data/output/providers_*.pdf

# Windows
start data/output/providers_*.pdf

# Linux
evince data/output/providers_*.pdf
```

## CSV Export Details

### Features
- All 30+ data fields
- Standard comma-separated format
- UTF-8 encoding
- Compatible with all spreadsheet applications
- Easy to process with Python/SQL

### Opening CSV Files
```bash
# Excel
open data/output/providers_*.csv

# Google Sheets
# 1. Go to sheets.google.com
# 2. File → Open
# 3. Select the CSV file

# Python
import pandas as pd
df = pd.read_csv('data/output/providers_*.csv')
print(df.head())

# Command line
head -5 data/output/providers_*.csv
```

## JSON Export Details

### File Structure
```json
[
  {
    "id": 1,
    "source_platform": "justdial",
    "provider_name": "John's Music Academy",
    "phone_number": "+919876543210",
    "email": "john@musicacademy.com",
    "rating": 4.5,
    "category": "music_teacher",
    "locality": "Whitefield",
    ...
  }
]
```

### Two Files Generated
1. **providers_TIMESTAMP.json** - All provider records
2. **summary_TIMESTAMP.json** - Statistics and metadata

### Processing JSON Data
```python
import json

# Load data
with open('data/output/providers_20240517_103100.json') as f:
    providers = json.load(f)

# Access data
for provider in providers:
    print(provider['provider_name'], provider['phone_number'])

# Load summary
with open('data/output/summary_20240517_103100.json') as f:
    summary = json.load(f)
    print(f"Total: {summary['total_providers']}")
```

## Batch Export (All Formats)

Export data in multiple formats at once:

```bash
# Export all to Excel
python main.py export --format excel

# Then export to PDF
python main.py export --format pdf

# Then export to CSV
python main.py export --format csv

# Then export to JSON
python main.py export --format json
```

## Export with Date Filtering

Note: Current version exports active providers. To filter by date:

```bash
# Check database directly
psql -d bangalore_marketplace -c "
SELECT COUNT(*) FROM providers 
WHERE scraped_at > NOW() - INTERVAL '7 days';"
```

## Sharing Exported Data

### Via Email
- Excel file is smaller and easier to attach
- PDF is pre-formatted and print-ready
- CSV can be attached without compression

### Via Cloud Storage
```bash
# Google Drive
# Drag and drop from data/output/ to Google Drive

# OneDrive
cp data/output/providers_*.xlsx ~/OneDrive/

# DropBox
cp data/output/providers_*.xlsx ~/Dropbox/
```

### Via Web
1. Convert to PDF for read-only sharing
2. Share Excel for collaborative editing
3. Use JSON for API integration

## Troubleshooting

### Excel Export Issues

**"Module not found: openpyxl"**
```bash
pip install openpyxl xlsxwriter
```

**Large file issues**
- Export with locality filter to reduce size
- Use CSV for very large datasets
- Split by category instead

### PDF Export Issues

**"Module not found: reportlab"**
```bash
pip install reportlab pypdf
```

**PDF too large**
- PDF shows first 100 records only
- Use Excel for complete data
- Consider splitting by locality

### Opening Files

**File not found**
```bash
# Check output directory
ls -lah data/output/

# List all exports
find data/output/ -name "*.xlsx" -o -name "*.pdf"
```

**Permission denied**
```bash
# Fix permissions
chmod 644 data/output/*
```

## Advanced: Custom Export Script

Create your own export logic:

```python
from storage.database import get_db
from storage.models import Provider

db = get_db()

# Query
providers = db.query(Provider).filter_by(active=True).all()

# Process
for provider in providers:
    print(f"{provider.provider_name}: {provider.rating}")

# Custom export
import json
data = [{
    'name': p.provider_name,
    'phone': p.phone_number,
    'rating': float(p.rating) if p.rating else None,
} for p in providers]

with open('custom_export.json', 'w') as f:
    json.dump(data, f, indent=2)

db.close()
```

## Summary

**For most users:** Use Excel export → Open in Excel/Sheets → Filter/Sort/Analyze

**For sharing:** Use PDF export → Send via email → Print if needed

**For large datasets:** Use CSV export → Process with Python/SQL

**For APIs:** Use JSON export → Integrate with web services

---

**Need help?** Check status:
```bash
python main.py status
```

**See exported files:**
```bash
ls -lah data/output/
```
