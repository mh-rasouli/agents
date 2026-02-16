"""Web Scrapers - Data collection from multiple Iranian sources."""

from scrapers.base_scraper import BaseScraper
from scrapers.example_scraper import ExampleScraper
from scrapers.web_search import WebSearchScraper
from scrapers.tavily_scraper import TavilyScraper
from scrapers.rasmio_scraper import RasmioScraper
from scrapers.codal_scraper import CodalScraper
from scrapers.tsetmc_scraper import TsetmcScraper
from scrapers.linka_scraper import LinkaScraper
from scrapers.trademark_scraper import TrademarkScraper

__all__ = [
    "BaseScraper",
    "ExampleScraper",
    "WebSearchScraper",
    "TavilyScraper",
    "RasmioScraper",
    "CodalScraper",
    "TsetmcScraper",
    "LinkaScraper",
    "TrademarkScraper",
]

__version__ = "1.0.0"
