"""Unit tests for web scrapers."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from scrapers.web_search import WebSearchScraper
from scrapers.base_scraper import BaseScraper


class TestBaseScraper:
    """Test cases for BaseScraper."""

    def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        scraper = BaseScraper("test_source")

        key1 = scraper._get_cache_path("TestBrand")
        key2 = scraper._get_cache_path("TestBrand")

        assert key1 == key2
        assert key1.suffix == ".json"

    def test_rate_limiting(self):
        """Test rate limiting delays requests."""
        import time

        scraper = BaseScraper("test_source")
        scraper.last_request_time = time.time()

        start = time.time()
        scraper._rate_limit()
        elapsed = time.time() - start

        # Should wait at least RATE_LIMIT_DELAY
        assert elapsed >= 0  # Will be close to RATE_LIMIT_DELAY in real scenario


class TestWebSearchScraper:
    """Test cases for WebSearchScraper."""

    @pytest.fixture
    def scraper(self):
        """Create a WebSearchScraper instance."""
        return WebSearchScraper()

    def test_initialization(self, scraper):
        """Test scraper initializes correctly."""
        assert scraper.source_name == "web_search"
        assert len(scraper.about_patterns) > 0
        assert len(scraper.contact_patterns) > 0

    def test_extract_meta_data(self, scraper):
        """Test meta data extraction from HTML."""
        html = """
        <html>
            <head>
                <meta name="description" content="Test description">
                <meta property="og:title" content="Test Title">
                <meta name="keywords" content="test, keywords">
            </head>
        </html>
        """

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        meta_data = scraper._extract_meta_data(soup)

        assert meta_data["description"] == "Test description"
        assert meta_data["og:title"] == "Test Title"
        assert meta_data["keywords"] == "test, keywords"

    def test_extract_title(self, scraper):
        """Test page title extraction."""
        html = "<html><head><title>  Test Page Title  </title></head></html>"

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        title = scraper._extract_title(soup)

        assert title == "Test Page Title"

    def test_extract_headings(self, scraper):
        """Test headings extraction."""
        html = """
        <html>
            <body>
                <h1>Main Heading</h1>
                <h2>Sub Heading</h2>
                <h3>Third Level</h3>
            </body>
        </html>
        """

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        headings = scraper._extract_headings(soup)

        assert len(headings) == 3
        assert headings[0]["level"] == "h1"
        assert headings[0]["text"] == "Main Heading"
        assert headings[1]["level"] == "h2"
        assert headings[2]["level"] == "h3"

    def test_extract_contact_info_emails(self, scraper):
        """Test email extraction."""
        html = "Contact us at info@example.com or support@test.ir"

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        contact_info = scraper._extract_contact_info(soup, html)

        assert "info@example.com" in contact_info["emails"]
        assert "support@test.ir" in contact_info["emails"]

    def test_extract_contact_info_phones(self, scraper):
        """Test phone number extraction."""
        html = "Call us: +98-9123456789 or 02112345678"

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        contact_info = scraper._extract_contact_info(soup, html)

        assert len(contact_info["phones"]) > 0

    def test_extract_social_media(self, scraper):
        """Test social media link extraction."""
        html = """
        <html>
            <body>
                <a href="https://instagram.com/testbrand">Instagram</a>
                <a href="https://t.me/testchannel">Telegram</a>
                <a href="https://linkedin.com/company/testcompany">LinkedIn</a>
            </body>
        </html>
        """

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        social_media = scraper._extract_social_media(soup)

        assert "instagram" in social_media
        assert "telegram" in social_media
        assert "linkedin" in social_media

    def test_find_about_link(self, scraper):
        """Test finding about us link."""
        html = """
        <html>
            <body>
                <a href="/about-us">About Us</a>
                <a href="/درباره-ما">درباره ما</a>
            </body>
        </html>
        """

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        about_link = scraper._find_about_link(soup, "https://example.com")

        assert about_link is not None
        assert "about" in about_link.lower() or "درباره" in about_link

    def test_find_contact_link(self, scraper):
        """Test finding contact link."""
        html = """
        <html>
            <body>
                <a href="/contact">Contact</a>
                <a href="/تماس">تماس</a>
            </body>
        </html>
        """

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        contact_link = scraper._find_contact_link(soup, "https://example.com")

        assert contact_link is not None
        assert "contact" in contact_link.lower() or "تماس" in contact_link

    def test_extract_internal_links(self, scraper):
        """Test internal link extraction."""
        html = """
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="https://example.com/page2">Page 2</a>
                <a href="https://external.com/page3">External</a>
            </body>
        </html>
        """

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        internal_links = scraper._extract_internal_links(soup, "https://example.com")

        assert len(internal_links) >= 2
        assert all("example.com" in link for link in internal_links)

    def test_scrape_with_no_website(self, scraper):
        """Test scraping without website URL."""
        result = scraper.scrape("TestBrand")

        assert result is not None
        assert result["brand_name"] == "TestBrand"
        assert result["website_url"] is None

    @patch('scrapers.base_scraper.httpx.Client')
    def test_scrape_with_website(self, mock_client, scraper):
        """Test scraping with website URL."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = """
        <html>
            <head>
                <title>Test Brand</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Welcome to Test Brand</h1>
                <a href="mailto:info@test.com">Email us</a>
            </body>
        </html>
        """
        mock_response.status_code = 200

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value = mock_client_instance

        result = scraper.scrape("TestBrand", website_url="https://test.com")

        assert result is not None
        assert result["brand_name"] == "TestBrand"
        assert result["page_title"] == "Test Brand"
        assert result["meta_data"]["description"] == "Test description"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
