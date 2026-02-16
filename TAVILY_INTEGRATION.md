# Tavily AI Search Integration

## Overview

Tavily is an AI-powered search API optimized for LLM applications and AI agents. It provides high-quality, structured search results perfect for brand intelligence gathering.

## What is Tavily?

**Tavily** (https://tavily.com) is a search API designed specifically for AI agents:
- ✅ Returns AI-optimized, structured results
- ✅ Provides AI-generated summaries
- ✅ Filters out low-quality content
- ✅ Real-time web data access
- ✅ Better than generic web scraping for many use cases

## Features

### 1. **AI-Generated Summaries**
Tavily returns AI summaries of search results, giving you instant insights.

### 2. **High-Quality Results**
Results are scored by relevance and filtered for quality.

### 3. **Structured Output**
Perfect for LLM processing - no HTML parsing needed.

### 4. **Advanced Search**
Uses "advanced" search depth for comprehensive results.

### 5. **Optional Integration**
Tavily is **optional** - the system works fine without it.

---

## Setup

### 1. Get API Key

1. Go to https://tavily.com
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes **1,000 searches/month**

### 2. Configure Environment

Edit your `.env` file:

```bash
# Enable Tavily
TAVILY_ENABLED=true
TAVILY_API_KEY=tvly-your-actual-api-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
# This will install tavily-python>=0.3.0
```

### 4. Test Integration

```bash
# Test with single brand
python main.py --brand "دیجی‌کالا"

# Check logs for "[Tavily] AI Search enabled"
```

---

## How It Works

### Integration Flow

```
DataCollectionAgent
  ↓
  Parallel Scrapers (8 total):
  ├─ Example (Wikipedia)
  ├─ Web Search (Generic)
  ├─ Tavily (AI Search) ← NEW!
  ├─ Rasmio
  ├─ Codal
  ├─ TSETMC
  ├─ Linka
  └─ Trademark
```

### Search Queries

Tavily performs multiple optimized searches:
1. `{brand_name} company information Iran`
2. `{brand_name} products services`
3. `{brand_name} parent company shareholders`
4. `{brand_name} industry category market`
5. `{brand_name} website social media`
6. `site:{website} about products` (if website provided)

### Output Structure

```json
{
  "brand_name": "دیجی‌کالا",
  "source": "Tavily AI Search",
  "ai_summaries": [
    "Digikala is Iran's largest online marketplace..."
  ],
  "top_results": [
    {
      "title": "About Digikala",
      "url": "https://...",
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

## Usage

### Enabled Mode (Recommended)

```bash
# .env
TAVILY_ENABLED=true
TAVILY_API_KEY=tvly-your-key

# Run normally
python main.py --brand "اسنپ"
```

Tavily will run automatically alongside other scrapers.

### Disabled Mode (Default)

```bash
# .env
TAVILY_ENABLED=false
# or omit TAVILY_API_KEY

# Run normally
python main.py --brand "اسنپ"
```

System will skip Tavily and use other 7 scrapers.

---

## Benefits vs Regular Web Search

| Feature | Regular Web Search | Tavily AI Search |
|---------|-------------------|------------------|
| **Result Quality** | Variable | Filtered & scored |
| **AI Summaries** | ❌ | ✅ |
| **Structured Output** | ❌ HTML parsing | ✅ Clean JSON |
| **Relevance Scoring** | ❌ | ✅ 0-1 score |
| **Content Filtering** | ❌ | ✅ Quality filter |
| **Optimized for LLMs** | ❌ | ✅ Yes |

---

## Cost & Limits

### Free Tier
- **1,000 searches/month** free
- Perfect for testing and small-scale use

### Paid Tiers
- **Starter**: $49/month - 5,000 searches
- **Pro**: $149/month - 20,000 searches
- **Enterprise**: Custom pricing

### Cost Per Brand (Estimate)
- ~6 search queries per brand
- **Free tier**: ~166 brands/month
- **Paid starter**: ~833 brands/month

See pricing: https://tavily.com/pricing

---

## Configuration Options

In `config/settings.py`:

```python
# Tavily Search API (Optional - Enhanced AI Search)
TAVILY_API_KEY: Optional[str] = None
TAVILY_ENABLED: bool = False  # Enable Tavily search
```

In `.env`:

```ini
# Enable/disable
TAVILY_ENABLED=true

# API key (get from https://tavily.com)
TAVILY_API_KEY=tvly-your-key-here
```

---

## Troubleshooting

### "Tavily is not enabled"
**Solution**: Set `TAVILY_ENABLED=true` in `.env`

### "tavily-python package not installed"
**Solution**:
```bash
pip install tavily-python
# or
pip install -r requirements.txt
```

### "Failed to initialize Tavily"
**Solution**: Check that `TAVILY_API_KEY` is correct and starts with `tvly-`

### "No results found"
- Normal for very obscure brands
- Tavily filters low-quality results
- Check search queries in logs

### Rate limit errors
- Free tier: 1,000 searches/month
- Upgrade plan or reduce usage
- Add retry logic (TODO)

---

## Advanced Configuration

### Custom Search Queries

Edit `scrapers/tavily_scraper.py`:

```python
def _build_search_queries(self, brand_name: str, brand_website: Optional[str] = None):
    queries = [
        f"{brand_name} company information Iran",
        f"{brand_name} YOUR CUSTOM QUERY HERE",
        # Add more...
    ]
    return queries
```

### Adjust Max Results

```python
response = self.client.search(
    query=query,
    max_results=10,  # Change from 5 to 10
    search_depth="advanced",
)
```

### Include Domains

```python
response = self.client.search(
    query=query,
    include_domains=["digikala.com", "snapp.ir"],  # Only these domains
)
```

---

## When to Use Tavily

### ✅ Use Tavily When:
- You need high-quality, AI-summarized results
- Analyzing well-known brands with online presence
- You want instant insights without HTML parsing
- Budget allows (free tier is generous)

### ⚠️ Skip Tavily When:
- Brand is very obscure or offline
- You're on a tight budget
- Other scrapers provide sufficient data
- Testing locally without API keys

---

## Comparison with Other Scrapers

| Scraper | Data Source | Quality | Speed | Cost |
|---------|-------------|---------|-------|------|
| **Tavily** | AI Search | ⭐⭐⭐⭐⭐ | Fast | Paid API |
| Web Search | Google | ⭐⭐⭐ | Medium | Free |
| Rasmio | Official DB | ⭐⭐⭐⭐ | Slow | Free |
| Codal | Official DB | ⭐⭐⭐⭐⭐ | Slow | Free |
| TSETMC | Stock Data | ⭐⭐⭐⭐ | Medium | Free |
| Linka | Directory | ⭐⭐⭐ | Fast | Free |

**Recommendation**: Use Tavily **alongside** other scrapers for best results.

---

## Support & Resources

- **Tavily Docs**: https://docs.tavily.com
- **API Reference**: https://docs.tavily.com/api-reference
- **Python SDK**: https://github.com/tavily-ai/tavily-python
- **Pricing**: https://tavily.com/pricing
- **GitHub Issues**: https://github.com/mh-rasouli/agents/issues

---

## Example Output

### Without Tavily
```
Successfully collected data from 6/7 sources
```

### With Tavily
```
[Tavily] AI Search enabled
[Tavily] Searching: دیجی‌کالا company information Iran
[Tavily] Found 23 results for دیجی‌کالا
Successfully collected data from 7/8 sources
```

---

## Disabling Tavily

To disable Tavily without uninstalling:

**Option 1**: Update `.env`
```bash
TAVILY_ENABLED=false
```

**Option 2**: Remove API key
```bash
# TAVILY_API_KEY=tvly-...  (comment out)
```

**Option 3**: Uninstall package
```bash
pip uninstall tavily-python
```

System will automatically skip Tavily scraper.

---

## Summary

✅ **Optional**: System works without it
✅ **Easy Setup**: Just add API key to `.env`
✅ **High Quality**: AI-filtered, structured results
✅ **Cost Effective**: 1,000 free searches/month
✅ **Zero Code Changes**: Auto-integrated with other scrapers

**Recommendation**: Try the free tier to see if Tavily adds value for your use case!

---

**Ready to enable Tavily?**

```bash
# 1. Get API key
Visit: https://tavily.com

# 2. Configure
echo "TAVILY_ENABLED=true" >> .env
echo "TAVILY_API_KEY=tvly-your-key" >> .env

# 3. Install
pip install -r requirements.txt

# 4. Run
python main.py --brand "دیجی‌کالا"
```

Enjoy enhanced AI-powered search! 🔍✨
