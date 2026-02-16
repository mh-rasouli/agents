# Iranian Scrapers Implementation Guide

All 4 Iranian scrapers have been fully implemented with real scraping logic, error handling, and fallback mechanisms.

## ✅ Implemented Scrapers

### 1. **Rasmio Scraper** (`scrapers/rasmio_scraper.py`)
**Source:** https://www.rasmio.com (Company Registration)

**Extracts:**
- Legal company name
- Registration number (شناسه ملی)
- Registration date
- Registered capital
- Company address
- CEO name

**Status:**
- ⚠️ May be blocked without VPN
- ✅ Provides manual search URLs
- ✅ Error handling implemented
- ✅ Fallback to manual instructions

**Manual Search:**
```python
from scrapers.rasmio_scraper import RasmioScraper
scraper = RasmioScraper()
instructions = scraper.get_manual_instructions("دیجی‌کالا")
print(instructions["instructions_fa"])
```

---

### 2. **Codal Scraper** (`scrapers/codal_scraper.py`)
**Source:** https://www.codal.ir (Financial Statements)

**Extracts:**
- Company name & stock symbol
- Latest financial reports
- Revenue, Profit, Assets
- Liabilities, Equity
- Fiscal year information
- Report publish dates

**Status:**
- ✅ API search implemented
- ✅ Web interface fallback
- ✅ Works without VPN (usually)
- ✅ Extracts report links

**Features:**
- Tries API search first: `https://search.codal.ir/api/search/v2/q`
- Falls back to web interface
- Extracts up to 5 latest reports
- Provides direct report URLs

---

### 3. **TSETMC Scraper** (`scrapers/tsetmc_scraper.py`)
**Source:** http://www.tsetmc.com (Tehran Stock Exchange)

**Extracts:**
- Stock symbol & code
- Last price & price change
- Market capitalization
- Trading volume & value
- P/E ratio, EPS
- Number of trades

**Status:**
- ✅ New API support (`search.tsetmc.com`)
- ✅ Old API fallback (`tsetmc.com/tsev2`)
- ✅ Detailed stock page parsing
- ⚠️ May have proxy/network issues

**Features:**
- Tries new search API first
- Falls back to old TSETMC format
- Extracts detailed stock metrics
- Handles Persian numbers

---

### 4. **Linka Scraper** (`scrapers/linka_scraper.py`)
**Source:** https://www.linka.ir (Social Media Analytics)

**Extracts:**
- Instagram: handle, followers, engagement
- Telegram: handle, member count
- Twitter: handle, followers
- LinkedIn: company page, followers
- Aparat: channel, subscribers

**Status:**
- ✅ Multi-platform extraction
- ✅ Regex-based stat parsing
- ⚠️ May require authentication
- ✅ Fallback extraction methods

**Features:**
- Searches for brand profiles
- Extracts social media handles from links
- Parses follower/member counts
- Supports Persian text

---

## 🔧 How Scrapers Handle Failures

All scrapers implement a **3-tier fallback system:**

### Tier 1: Automated Scraping
```python
data["scraping_method"] = "automated"
# Try to scrape automatically
```

### Tier 2: Manual Recommendation
```python
data["scraping_method"] = "manual_recommended"
data["manual_search_url"] = "https://site.com/search?q=brand"
data["notes"].append("No results found. Try manual search.")
```

### Tier 3: Manual Instructions
```python
instructions = scraper.get_manual_instructions(brand_name)
# Returns detailed step-by-step guide in Persian & English
```

---

## 📋 Common Issues & Solutions

### Issue 1: VPN Required
**Scrapers Affected:** rasmio, possibly linka

**Solution:**
```python
# Scraper automatically provides manual URL
result = scraper.scrape(brand_name)
if result["scraping_method"] == "manual_required":
    print(f"Visit: {result['manual_search_url']}")
```

### Issue 2: CAPTCHA
**Scrapers Affected:** All may encounter

**Solution:**
- Scrapers detect when CAPTCHA blocks access
- Provide manual search URLs
- Return partial data with notes

### Issue 3: Network/Proxy
**Scrapers Affected:** tsetmc (proxy issues)

**Solution:**
- Check network connectivity
- Try different API endpoints
- Use manual instructions

---

## 🧪 Testing Scrapers

### Quick Test (Individual):
```python
from scrapers.codal_scraper import CodalScraper

scraper = CodalScraper()
result = scraper.scrape("دیجی‌کالا")

print(f"Method: {result['scraping_method']}")
print(f"Data available: {result['data_available']}")
print(f"Reports: {len(result.get('latest_reports', []))}")
```

### Full System Test:
```bash
python main.py --brand "دیجی‌کالا" --website "https://www.digikala.com"
```

Check output files in `output/` directory.

---

## 📊 Data Structure

All scrapers return consistent structure:
```python
{
    "source": "scraper_name",
    "brand_name": "...",
    "manual_search_url": "https://...",
    "scraping_method": "automated|manual_recommended|manual_required|failed",
    "data_available": true/false,
    # ... scraper-specific fields ...
    "notes": ["helpful messages"]
}
```

---

## 🎯 Next Steps

### If Scraping Works:
- Data is automatically collected
- Cached for 24 hours
- Passed to LLM for analysis (if API key available)
- Output in 4 formats (JSON, CSV, TXT, MD)

### If Scraping Fails:
1. Check `notes` field for error details
2. Use `manual_search_url` to search manually
3. Call `get_manual_instructions()` for step-by-step guide
4. Manually add data to system if needed

---

## 🔄 Manual Data Integration

If you need to manually add data:

```python
# Example: Add Codal financial data manually
manual_data = {
    "source": "codal",
    "brand_name": "دیجی‌کالا",
    "revenue": 50000000000,
    "profit": 5000000000,
    "fiscal_year": 1402
}

# Save to cache
from utils.helpers import save_json
from pathlib import Path

cache_path = Path("data/cache/manual_codal.json")
save_json(manual_data, cache_path)
```

---

## 📞 Support & Troubleshooting

### Logs Location:
- Console output shows scraping progress
- Check `data/cache/` for cached results
- Review `output/` for final reports

### Debug Mode:
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Fixes:
1. **Connection timeout:** Increase `SCRAPER_TIMEOUT` in `.env`
2. **Rate limit:** Increase `RATE_LIMIT_DELAY` in `.env`
3. **VPN needed:** Use manual search URLs

---

**All scrapers are production-ready with comprehensive error handling!** 🎉
