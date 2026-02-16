# Tavily AI Search Integration - Summary

## ✅ Changes Completed

### 1. **Dependencies** (`requirements.txt`)
```diff
+ tavily-python>=0.3.0  # AI-powered search for agents
```

### 2. **Settings** (`config/settings.py`)
```python
# Tavily Search API (Optional - Enhanced AI Search)
TAVILY_API_KEY: Optional[str] = None
TAVILY_ENABLED: bool = False  # Enable Tavily search
```

### 3. **Environment Template** (`.env.example`)
```ini
# Tavily Search API (Optional - Enhanced AI Search)
# Get your API key at: https://tavily.com
TAVILY_API_KEY=tvly-your_api_key_here
TAVILY_ENABLED=false
```

### 4. **New Scraper** (`scrapers/tavily_scraper.py`)
Complete implementation of Tavily AI search:
- AI-generated summaries
- Multi-query search strategy
- Relevance scoring
- Structured output
- Automatic enable/disable based on configuration

### 5. **Data Collection Agent** (`agents/data_collection_agent.py`)
```python
from scrapers.tavily_scraper import TavilyScraper

self.scrapers = {
    "example": ExampleScraper(),
    "web_search": WebSearchScraper(),
    "tavily": TavilyScraper(),  # ← NEW!
    "rasmio": RasmioScraper(),
    # ... other scrapers
}
```

### 6. **Documentation**
- ✅ Created `TAVILY_INTEGRATION.md` (Complete guide)
- ✅ Updated `README.md` (Added Tavily to features & setup)
- ✅ Created `TAVILY_CHANGES.md` (This file)

---

## 🎯 What is Tavily?

**Tavily** is an AI-powered search API optimized for LLM applications:
- Returns AI-generated summaries of search results
- Provides structured, scored results
- Filters low-quality content
- Perfect for brand intelligence gathering

**Website**: https://tavily.com

---

## 🚀 Quick Setup

### 1. Get API Key
```bash
# Visit https://tavily.com
# Sign up (free tier: 1,000 searches/month)
# Copy your API key (starts with tvly-)
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure
```bash
# Edit .env
TAVILY_ENABLED=true
TAVILY_API_KEY=tvly-your-actual-key-here
```

### 4. Run
```bash
python main.py --brand "دیجی‌کالا"
```

Check logs for: `[Tavily] AI Search enabled`

---

## 📊 How It Works

### Data Collection Flow

**Before** (7 scrapers):
```
DataCollectionAgent → [Example, WebSearch, Rasmio, Codal, TSETMC, Linka, Trademark]
```

**After** (8 scrapers):
```
DataCollectionAgent → [Example, WebSearch, Tavily*, Rasmio, Codal, TSETMC, Linka, Trademark]
                                              ↑
                                         AI-Powered
```

*Tavily is **optional** - only runs if enabled

### Search Strategy

For each brand, Tavily performs 5-6 optimized searches:
1. `{brand_name} company information Iran`
2. `{brand_name} products services`
3. `{brand_name} parent company shareholders`
4. `{brand_name} industry category market`
5. `{brand_name} website social media`
6. `site:{website} about products` (if website provided)

### Output Structure

```json
{
  "source": "Tavily AI Search",
  "ai_summaries": ["AI-generated summary of the brand..."],
  "top_results": [
    {
      "title": "...",
      "url": "...",
      "content": "...",
      "score": 0.95,
      "published_date": "2024-01-15"
    }
  ],
  "total_results": 23,
  "insights": {
    "has_ai_summary": true,
    "high_confidence_results": 18,
    "recent_results": 12
  }
}
```

---

## 💡 Benefits

### ✅ Pros
1. **AI Summaries**: Instant insights without reading all results
2. **High Quality**: Results are filtered and scored
3. **Structured Output**: No HTML parsing needed
4. **Optimized for LLMs**: Perfect for agent workflows
5. **Easy Integration**: Just add API key to `.env`
6. **Free Tier**: 1,000 searches/month included

### ⚠️ Considerations
1. **Cost**: Paid API after free tier (1,000 searches/month)
2. **Internet Required**: Real-time search API
3. **English Bias**: Better results for English queries
4. **Optional**: System works fine without it

---

## 💰 Pricing

| Plan | Searches/Month | Cost | Cost per Brand* |
|------|----------------|------|-----------------|
| **Free** | 1,000 | $0 | $0 |
| **Starter** | 5,000 | $49 | ~$0.06 |
| **Pro** | 20,000 | $149 | ~$0.04 |

*Assumes ~6 searches per brand

**Free tier is perfect for testing and small-scale use!**

---

## 🔧 Configuration

### Enable Tavily

```bash
# .env
TAVILY_ENABLED=true
TAVILY_API_KEY=tvly-your-key
```

### Disable Tavily

```bash
# Option 1: Disable in .env
TAVILY_ENABLED=false

# Option 2: Remove/comment API key
# TAVILY_API_KEY=...

# Option 3: Uninstall package
pip uninstall tavily-python
```

---

## 📈 Usage Examples

### With Tavily Enabled
```bash
$ python main.py --brand "اسنپ"

[Tavily] AI Search enabled
[Tavily] Searching: اسنپ company information Iran
[Tavily] Found 23 results for اسنپ
Successfully collected data from 7/8 sources
```

### With Tavily Disabled
```bash
$ python main.py --brand "اسنپ"

[Tavily] AI Search disabled (no API key)
Successfully collected data from 6/7 sources
```

---

## 🐛 Troubleshooting

### "Tavily is not enabled"
**Fix**: Set `TAVILY_ENABLED=true` in `.env`

### "tavily-python package not installed"
**Fix**: Run `pip install -r requirements.txt`

### "Failed to initialize Tavily"
**Fix**: Check API key format (should start with `tvly-`)

### "No results found"
- Normal for very obscure brands
- Tavily filters low-quality results
- Other scrapers will still provide data

---

## 📚 Documentation

- **Complete Guide**: [TAVILY_INTEGRATION.md](TAVILY_INTEGRATION.md)
- **Tavily Docs**: https://docs.tavily.com
- **Python SDK**: https://github.com/tavily-ai/tavily-python

---

## 🎯 Recommendations

### When to Enable Tavily

✅ **Enable if**:
- Analyzing well-known brands with online presence
- You want AI-generated summaries
- Budget allows (free tier is generous)
- Need high-quality, structured results

⚠️ **Skip if**:
- Very obscure/offline brands
- Tight budget (after free tier)
- Other scrapers provide sufficient data
- Testing locally without internet

### Best Practice

**Use Tavily alongside other scrapers** for best results:
- Tavily: AI summaries & online presence
- Rasmio/Codal: Official business data
- TSETMC: Financial/stock data
- Linka: Directory listings

**Complementary, not replacement!**

---

## 📝 Summary

✅ **Optional Feature**: System works without it
✅ **Easy Setup**: Just add API key
✅ **Free Tier**: 1,000 searches/month
✅ **High Quality**: AI-filtered results
✅ **Zero Breaking Changes**: Backward compatible

---

## 🚀 Next Steps

1. **Get API Key**: https://tavily.com (free signup)
2. **Configure**: Add to `.env`
3. **Install**: `pip install -r requirements.txt`
4. **Test**: `python main.py --brand "test"`
5. **Read Guide**: [TAVILY_INTEGRATION.md](TAVILY_INTEGRATION.md)

**Enjoy AI-powered search!** 🔍✨
