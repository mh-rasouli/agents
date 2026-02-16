"""Scraper for rasmio.com - Iranian company registration data."""

from typing import Optional, Dict, Any
from urllib.parse import quote
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)


class RasmioScraper(BaseScraper):
    """Scraper for company registration data from rasmio.com."""

    def __init__(self):
        """Initialize the Rasmio scraper."""
        super().__init__("rasmio")
        self.base_url = "https://www.rasmio.com"
        self.search_url = "https://www.rasmio.com/company"

    def scrape(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape company registration data from rasmio.com.

        Note: Rasmio.com may be blocked or require special access.
        This scraper provides manual search URLs if automated scraping fails.

        Args:
            brand_name: Name of the brand/company to search
            **kwargs: Additional arguments

        Returns:
            Dictionary with registration data or manual search info
        """
        data = {
            "source": self.source_name,
            "brand_name": brand_name,
            "manual_search_url": f"{self.search_url}?search={quote(brand_name)}",
            "scraping_method": "automated",
            "data_available": False,
            "legal_name": None,
            "registration_number": None,
            "registration_date": None,
            "company_type": None,
            "registered_capital": None,
            "address": None,
            "ceo_name": None,
            "notes": []
        }

        try:
            logger.info(f"[{self.source_name}] Attempting to scrape {brand_name}")

            # Try to access search page
            search_url = f"{self.search_url}?search={quote(brand_name)}"
            response = self._make_request(search_url)

            if not response:
                data["notes"].append(
                    "Automated scraping failed. Site may be blocked or require VPN."
                )
                data["scraping_method"] = "manual_required"
                logger.warning(
                    f"[{self.source_name}] Cannot access rasmio.com. "
                    f"Manual search URL: {data['manual_search_url']}"
                )
                return data

            soup = self._parse_html(response.text)
            if not soup:
                data["scraping_method"] = "manual_required"
                return data

            # Try to find company information
            # Note: These selectors are examples and may need adjustment
            # based on actual rasmio.com HTML structure

            # Look for company cards or results
            company_cards = soup.find_all("div", class_=["company-card", "search-result", "company-item"])

            if company_cards:
                # Take first result
                card = company_cards[0]

                # Extract company name
                name_elem = card.find(["h2", "h3", "strong", "a"], class_=["company-name", "title"])
                if name_elem:
                    data["legal_name"] = name_elem.get_text(strip=True)

                # Extract registration number
                reg_patterns = ["شناسه ملی", "شماره ثبت", "registration", "id"]
                for pattern in reg_patterns:
                    reg_elem = card.find(string=lambda x: x and pattern in x.lower() if x else False)
                    if reg_elem:
                        parent = reg_elem.parent
                        if parent:
                            data["registration_number"] = parent.get_text(strip=True).split(":")[-1].strip()
                            break

                # Extract other details from card
                details = card.find_all(["p", "div", "span"])
                for detail in details:
                    text = detail.get_text(strip=True)

                    if "آدرس" in text or "address" in text.lower():
                        data["address"] = text

                    if "سرمایه" in text or "capital" in text.lower():
                        data["registered_capital"] = text

                    if "مدیرعامل" in text or "ceo" in text.lower():
                        data["ceo_name"] = text

                data["data_available"] = True
                logger.info(f"[{self.source_name}] Successfully extracted data for {brand_name}")

            else:
                # No results found
                data["notes"].append(
                    f"No company found with name '{brand_name}'. Try manual search."
                )
                data["scraping_method"] = "manual_recommended"
                logger.warning(f"[{self.source_name}] No results found for {brand_name}")

            return data

        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
            data["notes"].append(f"Error during scraping: {str(e)[:100]}")
            data["scraping_method"] = "failed"
            return data

    def get_manual_instructions(self, brand_name: str) -> Dict[str, str]:
        """Get manual search instructions for rasmio.com.

        Args:
            brand_name: Brand name to search

        Returns:
            Dictionary with manual search instructions
        """
        return {
            "site": "rasmio.com",
            "url": f"{self.search_url}?search={quote(brand_name)}",
            "instructions_fa": f"""
مراحل جستجوی دستی در رسمی‌او:
1. به آدرس {self.base_url} بروید
2. در کادر جستجو عبارت "{brand_name}" را وارد کنید
3. روی شرکت مورد نظر کلیک کنید
4. اطلاعات زیر را یادداشت کنید:
   - نام قانونی شرکت
   - شناسه ملی / شماره ثبت
   - تاریخ ثبت
   - سرمایه ثبت شده
   - آدرس
   - نام مدیرعامل
            """,
            "instructions_en": f"""
Manual search steps for rasmio.com:
1. Go to {self.base_url}
2. Search for "{brand_name}"
3. Click on the target company
4. Note the following information:
   - Legal company name
   - National ID / Registration number
   - Registration date
   - Registered capital
   - Address
   - CEO name
            """
        }
