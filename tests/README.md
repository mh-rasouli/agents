# Tests

Unit tests for the Brand Intelligence Agent system.

## Running Tests

### Run all tests

```bash
pytest tests/ -v
```

### Run specific test file

```bash
pytest tests/test_scrapers.py -v
pytest tests/test_agents.py -v
pytest tests/test_utils.py -v
```

### Run with coverage

```bash
pytest tests/ --cov=. --cov-report=html
```

### Run specific test

```bash
pytest tests/test_scrapers.py::TestWebSearchScraper::test_extract_meta_data -v
```

## Test Structure

- `test_scrapers.py` - Tests for all web scrapers
- `test_agents.py` - Tests for all 5 agents
- `test_utils.py` - Tests for utility functions and LLM client
- `conftest.py` - Shared fixtures and pytest configuration

## Test Coverage

Current test coverage includes:

### Scrapers
- ✅ BaseScraper: cache key generation, rate limiting
- ✅ WebSearchScraper: meta extraction, contact info, social media, internal links

### Agents
- ✅ DataCollectionAgent: initialization, data preparation
- ✅ RelationshipMappingAgent: data preparation, execution
- ✅ CategorizationAgent: data preparation, execution
- ✅ StrategicInsightsAgent: data preparation, execution
- ✅ OutputFormatterAgent: JSON/CSV/TXT/MD generation

### Utils
- ✅ Helpers: timestamp, filename sanitization, JSON save/load, cache keys, dict operations
- ✅ LLM Client: initialization, availability check, graceful degradation
- ✅ Logger: creation, log levels

## Fixtures

### `sample_html`
Sample HTML with Persian content for scraper testing

### `sample_brand_data`
Sample brand data structure for agent testing

### `tmp_path` (pytest built-in)
Temporary directory for file operations

## Mocking

Tests use `unittest.mock` and `pytest-mock` for:
- HTTP requests
- LLM API calls
- File system operations

## Notes

- Tests are designed to run without requiring API keys
- All file operations use temporary directories
- Mock data simulates real Iranian brand scenarios
