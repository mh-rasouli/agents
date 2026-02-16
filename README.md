# Brand Intelligence Agent 🔍

A Multi-Agent System for comprehensive Iranian brand analysis, designed for advertising agencies to make data-driven campaign decisions.

## Overview

This system leverages **LangGraph** and **OpenRouter API (Gemini 3 Pro)** to orchestrate 6 specialized AI agents that collect, analyze, and synthesize brand intelligence from multiple Iranian data sources.

### Key Features

- 📊 **Multi-Source Data Collection**: Aggregates data from 7+ Iranian sources (rasmio, codal, tsetmc, linka, trademark registry, websites)
- 🔍 **AI-Powered Search**: Optional Tavily integration for enhanced search results
- 🔗 **Relationship Mapping**: Identifies parent companies, subsidiaries, sister brands, and shareholders
- 🏢 **Industry Categorization**: Classifies industries, products, audience segments, and price tiers
- 💡 **Strategic Insights**: Generates actionable advertising recommendations
- 📄 **Multi-Format Output**: Produces JSON, CSV, TXT (embedding-ready), and Markdown reports

## Architecture

### 5 Specialized Agents

1. **DataCollectionAgent** - Orchestrates web scraping from all sources
2. **RelationshipMappingAgent** - Analyzes corporate structure
3. **CategorizationAgent** - Classifies industries and market positioning
4. **StrategicInsightsAgent** - Generates advertising recommendations
5. **OutputFormatterAgent** - Produces multi-format outputs

### Workflow Pipeline

```
START → Data Collection → Relationship Mapping → Categorization → Strategic Insights → Output Formatting → END
```

## Installation

### Prerequisites

- Python 3.11 or higher
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))

### Setup

1. **Clone or download this repository**

2. **Create virtual environment**

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=your_api_key_here
# MODEL_NAME=google/gemini-pro-1.5
```

5. **(Optional) Install Playwright browsers** (for JavaScript-heavy sites)

```bash
playwright install
```

6. **(Optional) Enable Tavily AI Search** (for enhanced search results)

```bash
# Get API key from https://tavily.com (1,000 free searches/month)
# Add to .env:
TAVILY_ENABLED=true
TAVILY_API_KEY=tvly-your-api-key-here
```

See [TAVILY_INTEGRATION.md](TAVILY_INTEGRATION.md) for details.

## Usage

### Basic Usage

```bash
# Analyze a brand by name
python main.py --brand "دیجی‌کالا"

# Analyze with website URL
python main.py --brand "دیجی‌کالا" --website "https://www.digikala.com"
```

### Advanced Options

```bash
# Specify custom output directory
python main.py --brand "اسنپ" --output-dir "./reports"

# Select specific output formats
python main.py --brand "دیجی‌کالا" --formats json,md

# Verbose logging
python main.py --brand "اسنپ" --verbose
```

### Command-Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--brand` | `-b` | Brand name to analyze (required) | - |
| `--website` | `-w` | Brand website URL (optional) | - |
| `--output-dir` | `-o` | Output directory | `./output` |
| `--formats` | `-f` | Output formats (comma-separated) | `json,csv,txt,md` |
| `--verbose` | `-v` | Enable verbose logging | `False` |

## Output Formats

### 1. JSON (`.json`)
Structured nested data with all collected information, relationships, categorization, and insights.

```json
{
  "brand_name": "دیجی‌کالا",
  "data": {...},
  "relationships": {...},
  "categorization": {...},
  "insights": {...}
}
```

### 2. CSV (`.csv`)
Flattened tabular data suitable for spreadsheet analysis.

### 3. TXT (`.txt`)
Embedding-ready key-value format for vector databases:

```
brand_name: دیجی‌کالا
industry: E-commerce
business_model: B2C
...
```

### 4. Markdown (`.md`)
Executive summary report with formatted sections.

## Data Sources

| Source | Type | Data Collected |
|--------|------|----------------|
| **rasmio.com** | Company Registry | Legal name, registration number, capital |
| **codal.ir** | Financial Statements | Revenue, profit, assets, fiscal data |
| **tsetmc.com** | Stock Market | Ticker, market cap, stock price |
| **linka.ir** | Social Media | Follower counts, engagement metrics |
| **Trademark Registry** | Intellectual Property | Registered brands, parent company |
| **Official Website** | Web Scraping | About, products, contact info |

## Project Structure

```
brand-intelligence-agent/
├── agents/              # 5 specialized agents
│   ├── base_agent.py
│   ├── data_collection_agent.py
│   ├── relationship_agent.py
│   ├── categorization_agent.py
│   ├── insights_agent.py
│   └── formatter_agent.py
├── scrapers/            # 6 web scrapers
│   ├── base_scraper.py
│   ├── rasmio_scraper.py
│   ├── codal_scraper.py
│   ├── tsetmc_scraper.py
│   ├── linka_scraper.py
│   ├── trademark_scraper.py
│   └── web_search.py
├── models/              # State definitions
│   └── state.py
├── utils/               # Utilities
│   ├── llm_client.py
│   ├── logger.py
│   └── helpers.py
├── config/              # Configuration
│   ├── settings.py
│   └── prompts.py
├── output/              # Generated reports
├── data/                # Cached scraped data
├── graph.py             # LangGraph workflow
├── main.py              # CLI entry point
└── requirements.txt
```

## Configuration

Edit `.env` to customize settings:

```bash
# API Configuration
ANTHROPIC_API_KEY=your_key_here
MODEL_NAME=claude-sonnet-4-5-20250929
MAX_TOKENS=4096

# Scraper Settings
RATE_LIMIT_DELAY=1.5     # Seconds between requests
SCRAPER_TIMEOUT=30       # Request timeout
CACHE_TTL_HOURS=24       # Cache validity period

# Logging
LOG_LEVEL=INFO
```

## Features

### Intelligent Caching
- Scraped data is cached for 24 hours (configurable)
- Reduces redundant requests
- Speeds up repeated analyses

### Rate Limiting
- Respects robots.txt
- Configurable delays between requests
- Prevents server overload

### Error Handling
- Graceful degradation when scrapers fail
- Comprehensive error logging
- Continues processing with available data

### Multi-Format Export
- JSON for structured data
- CSV for spreadsheet analysis
- TXT for vector embeddings
- Markdown for executive reports

## Example Output

```bash
╔══════════════════════════════════════════════════════════════╗
║         Brand Intelligence Agent - Multi-Agent System        ║
║              Iranian Brand Analysis for Advertising          ║
╚══════════════════════════════════════════════════════════════╝

============================================================
ANALYSIS COMPLETE
============================================================

Brand: دیجی‌کالا

📁 Generated Reports:
  📊 JSON: output/digikala_20260215_143022.json
  📈 CSV: output/digikala_20260215_143022.csv
  📝 TXT: output/digikala_20260215_143022.txt
  📄 MARKDOWN: output/digikala_20260215_143022.md

🤝 Cross-Promotion Opportunities:
  • دیجی‌پی
  • دیجی‌کالا جت
  • فیدیبو

📢 Top Recommended Channels:
  🔴 Digital - Instagram, Telegram
  🟡 TV - National Networks
  🟢 Outdoor - Tehran Metro

🏢 Industry: تجارت الکترونیک
💼 Business Model: B2C
💰 Price Tier: mid-market

⏱️  Processing Time: 45.32 seconds
============================================================
```

## API Usage

You can also use the workflow programmatically:

```python
from graph import run_workflow

# Run analysis
result = run_workflow(
    brand_name="دیجی‌کالا",
    brand_website="https://www.digikala.com"
)

# Access results
insights = result["insights"]
relationships = result["relationships"]
```

## Limitations & Known Issues

1. **Placeholder Scrapers**: Current scraper implementations are placeholders. Actual scraping logic needs to be implemented based on each website's structure.

2. **Persian Number Parsing**: Some scrapers may need additional logic to parse Persian/Arabic numerals.

3. **CAPTCHA**: System cannot bypass CAPTCHA challenges (fails gracefully).

4. **Rate Limits**: Some websites may block requests if rate limits are exceeded.

## Future Enhancements

- [ ] Web dashboard (FastAPI + React)
- [ ] Database storage (PostgreSQL)
- [ ] Vector database integration (ChromaDB)
- [ ] Real-time monitoring
- [ ] Multi-brand batch processing
- [ ] Historical trend analysis
- [ ] API endpoint exposure

## Contributing

Contributions are welcome! Areas for improvement:

1. Implement actual scraping logic for each source
2. Add Persian number parsing utilities
3. Improve error handling
4. Add unit tests
5. Enhance LLM prompts

## License

MIT License - feel free to use and modify for your needs.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: [your-email@example.com]

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [Claude API](https://www.anthropic.com/claude)
- Designed for Iranian advertising agencies

---

**Made with ❤️ for the Iranian advertising industry**
