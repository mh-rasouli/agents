"""Example scraper for testing with static HTML sites."""

from typing import Optional, Dict, Any
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)


class ExampleScraper(BaseScraper):
    """Example scraper that works with Wikipedia and other static sites."""

    def __init__(self):
        """Initialize the Example scraper."""
        super().__init__("example")

    def scrape(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape example data from Wikipedia or other static sources.

        Args:
            brand_name: Name of the brand/company to search
            **kwargs: Additional arguments

        Returns:
            Dictionary with example data or None
        """
        try:
            # Try searching Wikipedia for the brand
            wikipedia_url = f"https://en.wikipedia.org/wiki/{brand_name.replace(' ', '_')}"

            logger.info(f"[{self.source_name}] Searching Wikipedia for {brand_name}")

            response = self._make_request(wikipedia_url)

            if not response:
                # Try Persian Wikipedia
                persian_url = f"https://fa.wikipedia.org/wiki/{brand_name.replace(' ', '_')}"
                response = self._make_request(persian_url)

            data = {
                "source": self.source_name,
                "brand_name": brand_name,
                "found_on_wikipedia": False,
                "summary": None,
                "infobox_data": {},
                "categories": [],
                "external_links": []
            }

            if response and response.status_code == 200:
                soup = self._parse_html(response.text)

                if soup:
                    data["found_on_wikipedia"] = True

                    # Extract first paragraph as summary
                    first_para = soup.find("p", class_="")
                    if first_para:
                        data["summary"] = first_para.get_text(strip=True)[:500]

                    # Extract infobox data
                    infobox = soup.find("table", class_="infobox")
                    if infobox:
                        for row in infobox.find_all("tr"):
                            header = row.find("th")
                            value = row.find("td")
                            if header and value:
                                key = header.get_text(strip=True)
                                val = value.get_text(strip=True)
                                data["infobox_data"][key] = val

                    # Extract categories
                    catlinks = soup.find(id="mw-normal-catlinks")
                    if catlinks:
                        cats = catlinks.find_all("a")
                        data["categories"] = [c.get_text(strip=True) for c in cats][:5]

                    # Extract external links
                    external_section = soup.find(id="External_links")
                    if external_section:
                        ext_list = external_section.find_next("ul")
                        if ext_list:
                            links = ext_list.find_all("a", href=True)
                            data["external_links"] = [
                                {
                                    "text": link.get_text(strip=True),
                                    "url": link["href"]
                                }
                                for link in links[:5]
                            ]

                    logger.info(f"[{self.source_name}] Found Wikipedia page for {brand_name}")

            else:
                logger.warning(f"[{self.source_name}] No Wikipedia page found for {brand_name}")

            return data

        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
            return None
