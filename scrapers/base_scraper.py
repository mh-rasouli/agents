"""Base scraper class with common functionality."""

import time
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

from config.settings import settings
from utils.logger import get_logger
from utils.helpers import save_json, load_json, generate_cache_key

logger = get_logger(__name__)


class BaseScraper(ABC):
    """Base class for all web scrapers with rate limiting and caching."""

    def __init__(self, source_name: str):
        """Initialize the scraper.

        Args:
            source_name: Name of the data source
        """
        self.source_name = source_name
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_request_time = 0
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fa,en;q=0.9",
        }

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < settings.RATE_LIMIT_DELAY:
            time.sleep(settings.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _get_cache_path(self, brand_name: str) -> Path:
        """Get the cache file path for a brand.

        Args:
            brand_name: Name of the brand

        Returns:
            Path to cache file
        """
        cache_key = generate_cache_key(brand_name, self.source_name)
        return self.cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached data is still valid.

        Args:
            cache_path: Path to cache file

        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_path.exists():
            return False

        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        max_age = timedelta(hours=settings.CACHE_TTL_HOURS)

        return cache_age < max_age

    def _get_cached_data(self, brand_name: str) -> Optional[Dict[str, Any]]:
        """Get cached data if available and valid.

        Args:
            brand_name: Name of the brand

        Returns:
            Cached data or None
        """
        cache_path = self._get_cache_path(brand_name)

        if self._is_cache_valid(cache_path):
            logger.info(f"[{self.source_name}] Using cached data for {brand_name}")
            try:
                return load_json(cache_path)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Failed to load cache: {e}")

        return None

    def _cache_data(self, brand_name: str, data: Dict[str, Any]) -> None:
        """Cache scraped data.

        Args:
            brand_name: Name of the brand
            data: Data to cache
        """
        cache_path = self._get_cache_path(brand_name)
        try:
            save_json(data, cache_path)
            logger.info(f"[{self.source_name}] Cached data for {brand_name}")
        except Exception as e:
            logger.warning(f"[{self.source_name}] Failed to cache data: {e}")

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[httpx.Response]:
        """Make an HTTP request with error handling.

        Args:
            url: URL to request
            method: HTTP method
            **kwargs: Additional arguments for httpx

        Returns:
            Response object or None on failure
        """
        self._rate_limit()

        try:
            logger.info(f"[{self.source_name}] Requesting {url}")

            with httpx.Client(
                headers=self.headers,
                timeout=settings.SCRAPER_TIMEOUT,
                follow_redirects=True
            ) as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                return response

        except httpx.HTTPStatusError as e:
            logger.error(f"[{self.source_name}] HTTP error {e.response.status_code}: {url}")
        except httpx.TimeoutException:
            logger.error(f"[{self.source_name}] Timeout: {url}")
        except Exception as e:
            logger.error(f"[{self.source_name}] Request failed: {e}")

        return None

    def _parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """Parse HTML content.

        Args:
            html: HTML string

        Returns:
            BeautifulSoup object or None
        """
        try:
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"[{self.source_name}] HTML parsing failed: {e}")
            return None

    @abstractmethod
    def scrape(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape data for a brand.

        This method must be implemented by subclasses.

        Args:
            brand_name: Name of the brand to scrape
            **kwargs: Additional scraper-specific arguments

        Returns:
            Scraped data as a dictionary, or None on failure
        """
        pass

    def scrape_with_cache(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape data with caching support.

        Args:
            brand_name: Name of the brand to scrape
            **kwargs: Additional scraper-specific arguments

        Returns:
            Scraped data as a dictionary, or None on failure
        """
        # Check cache first
        cached_data = self._get_cached_data(brand_name)
        if cached_data:
            return cached_data

        # Scrape fresh data
        logger.info(f"[{self.source_name}] Scraping fresh data for {brand_name}")
        data = self.scrape(brand_name, **kwargs)

        # Cache if successful
        if data:
            self._cache_data(brand_name, data)

        return data
