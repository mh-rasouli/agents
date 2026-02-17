# Brand Intelligence Agent - Quick Start Guide

**Last Updated:** 2026-02-17
**Status:** Production Ready ✅

---

## 🚀 Quick Start

### Run Single Brand Analysis

```bash
# Basic
python main.py --brand "Dafi_Iran"

# With website
python main.py --brand "Dafi_Iran" --website "https://dafiiran.com/"

# With parent company
python main.py --brand "Dafi_Iran" \
  --website "https://dafiiran.com/" \
  --parent "Silaneh Sabz Manufacturing and Trading Co."
```

### Run Batch Mode (Google Sheets)

```bash
# Process all brands from sheet
python main.py --google-sheets

# Force reprocess all (ignore cache)
python main.py --google-sheets --force
```

---

## 📊 What You Get

### For Each Brand (Automatically):

✅ **12-15 products** with detailed descriptions
✅ **3-5 campaign opportunities** with reach estimates
✅ **Sister brands** and relationships
✅ **Strategic insights** (channels, timing, budget)
✅ **Persian executive summary**
✅ **CSV exports** for products, opportunities, brands
✅ **Vector database chunks** (300-500 words each)

### Processing Time:

- Single brand: **40-50 seconds**
- 10 brands: **7-8 minutes**

---

## 📁 Output Structure

```
output/
└── brand_name/
    ├── human_reports/
    │   ├── 6_executive_summary.md           ← Persian summary
    │   ├── complete_analysis_report.md      ← Full report
    │   ├── quick_reference.json             ← API-ready
    │   └── data_exports/
    │       ├── product_catalog.csv          ← 12+ products
    │       ├── campaign_opportunities.csv   ← 3-5 campaigns
    │       └── 3_brands_database.csv        ← Sister brands
    └── vector_database/
        ├── chunks/                          ← 12 semantic chunks
        ├── metadata.json
        ├── entities.jsonl
        └── relationships.json
```

---

## ⚙️ Configuration

### Required Environment Variables (.env)

```bash
# LLM API (Required)
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE

# Tavily Search (Optional but recommended)
TAVILY_API_KEY=tvly-dev-YOUR_KEY_HERE
TAVILY_ENABLED=true
```

### Get API Keys

- **OpenRouter:** https://openrouter.ai/keys
- **Tavily:** https://tavily.com

---

## 🎯 Expected Results

### Product Catalog Example (Dafi_Iran):

| Product | Category | Description Length |
|---------|----------|-------------------|
| Dafi Micellar Water 7-in-1 | Skin Care | 45 words |
| Dafi Keratin Repair Shampoo | Hair Care | 38 words |
| Dafi Baby Sensitive Wet Wipes | Baby Care | 32 words |
| **Total:** 12 products | 5 categories | 20-60 words each |

### Campaign Opportunities Example:

| Partner | Reach | Campaign | Timing |
|---------|-------|----------|--------|
| Comeon (Sister Brand) | 5M+ Instagram users | "Double Care" bundle | Pre-Nowruz |
| Snapp Market | 3M+ shoppers | Flash Sales | Monthly payday |
| Misswake | 2.5M+ families | "Family Travel Pack" | Summer travel |

### Vector Chunks Quality:

- **Word count:** 300-500 words per chunk
- **Example:** Strategic opportunities chunk = 351 words
- **Content:** Rich context, market analysis, detailed breakdowns

---

## ✅ System Status Check

### Test API Connection

```bash
python test_api.py
```

**Expected output:**
```
Testing OpenRouter API...
Testing model: google/gemini-3-flash-preview
  SUCCESS: OK
```

### Test Single Brand

```bash
python main.py --brand "Dafi_Iran" --website "https://dafiiran.com/"
```

**Expected results:**
- ✅ Processing time: 40-50 seconds
- ✅ Products extracted: 10-15+
- ✅ Campaign opportunities: 3-5
- ✅ Vector chunks: 300-500 words

---

## 🐛 Troubleshooting

### Problem: Empty Outputs

**Symptom:** Product catalog, campaign opportunities empty

**Solution:**
```bash
# Test API key
python test_api.py

# If fails, update .env with new key
OPENROUTER_API_KEY=sk-or-v1-NEW_KEY
```

### Problem: Only 2-5 Products

**Symptom:** Low product count

**Solution:**
```bash
# Enable Tavily in .env
TAVILY_ENABLED=true
TAVILY_API_KEY=tvly-dev-YOUR_KEY
```

### Problem: Short Vector Chunks

**Symptom:** Chunks only 50-100 words

**Solution:**
```bash
# Verify latest code
git pull origin master
git log --oneline -3

# Should show: cc88229 Phase 2: Deep data enrichment
```

---

## 📚 Key Files

- **DEVELOPMENT_LOG.md** - Complete conversation history & all changes
- **QUICK_START.md** - This file
- **.env** - Configuration (API keys)
- **main.py** - Entry point
- **test_api.py** - API connection test

---

## 🎓 Important Notes

### No Manual Intervention Needed

The system processes **every brand automatically** with the same quality:
- ✅ All improvements are permanent (in code)
- ✅ LLM extraction for all brands
- ✅ Tavily integration for all brands
- ✅ Consistent output quality

### Caching

- **Cache duration:** 24 hours
- **Location:** `cache/` directory
- **Benefit:** Reduces API costs, faster reruns
- **Override:** Use `--force` flag

### Batch Processing

```bash
# Process all brands in Google Sheet
python main.py --google-sheets

# The system:
# - Skips already-processed brands (unless --force)
# - Updates status in Google Sheet
# - Writes output paths to sheet
# - Tracks progress in logs/
```

---

## 💰 Cost Estimates

### Per Brand:

- **OpenRouter (Gemini Flash):** ~$0.01-0.02
- **Tavily Search:** ~$0.02-0.03
- **Total:** ~$0.03-0.05 per brand

### For 100 Brands:

- **Total cost:** ~$3-5
- **Processing time:** ~1.5 hours

---

## 🚨 Error Messages

### "401 - User not found"

**Meaning:** OpenRouter API key is invalid

**Fix:** Get new key at https://openrouter.ai/keys

### "Tavily API error"

**Meaning:** Tavily key invalid or quota exceeded

**Fix:** Check key at https://tavily.com or disable Tavily:
```bash
TAVILY_ENABLED=false
```

### "No data collected"

**Meaning:** All scrapers failed (network issue)

**Fix:** Check internet connection, try again

---

## 📞 Support

**Issues:** https://github.com/mh-rasouli/agents/issues
**Documentation:** See DEVELOPMENT_LOG.md for full details

---

**Ready to analyze brands? Run:**

```bash
python main.py --brand "YOUR_BRAND_NAME"
```

🚀 **The system will do the rest automatically!**
