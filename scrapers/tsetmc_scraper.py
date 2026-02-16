"""Scraper for tsetmc.com - Tehran Stock Exchange data."""

from typing import Optional, Dict, Any
from urllib.parse import quote
import re
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)


class TsetmcScraper(BaseScraper):
    """Scraper for stock market data from tsetmc.com (Tehran Stock Exchange)."""

    def __init__(self):
        """Initialize the TSETMC scraper."""
        super().__init__("tsetmc")
        self.base_url = "http://www.tsetmc.com"
        self.new_url = "https://www.tsetmc.com"  # New TSETMC site
        self.search_api = "https://search.tsetmc.com/api/search"

    def scrape(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape stock market data from TSETMC.

        TSETMC has both old (tsetmc.com) and new (search.tsetmc.com) interfaces.
        This scraper tries both.

        Args:
            brand_name: Name of the brand/company to search
            **kwargs: Additional arguments (e.g., stock_symbol)

        Returns:
            Dictionary with stock data or None
        """
        data = {
            "source": self.source_name,
            "brand_name": brand_name,
            "manual_search_url": f"{self.new_url}/search?term={quote(brand_name)}",
            "scraping_method": "automated",
            "data_available": False,
            "stock_symbol": kwargs.get("stock_symbol"),
            "stock_code": None,
            "company_name": None,
            "last_price": None,
            "price_change": None,
            "price_change_percent": None,
            "market_cap": None,
            "volume": None,
            "value": None,
            "trades_count": None,
            "pe_ratio": None,
            "eps": None,
            "notes": []
        }

        try:
            logger.info(f"[{self.source_name}] Searching TSETMC for {brand_name}")

            # Try new API first
            api_result = self._search_via_api(brand_name, data)
            if api_result and api_result.get("data_available"):
                return api_result

            # Fallback to old TSETMC search
            old_result = self._search_old_tsetmc(brand_name, data)
            if old_result:
                return old_result

            # If both failed, provide manual instructions
            data["notes"].append(
                "Automated search failed. Please search manually or provide stock symbol."
            )
            data["scraping_method"] = "manual_recommended"

            return data

        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
            data["notes"].append(f"Error: {str(e)[:100]}")
            data["scraping_method"] = "failed"
            return data

    def _search_via_api(
        self,
        brand_name: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Search using TSETMC search API.

        Args:
            brand_name: Brand name
            data: Existing data dictionary

        Returns:
            Updated data dictionary or None
        """
        try:
            # Try new search API
            search_url = f"{self.search_api}"
            params = {
                "term": brand_name,
                "type": "company"
            }

            response = self._make_request(search_url, params=params)

            if not response:
                return None

            # Try to parse JSON
            try:
                results = response.json()

                if isinstance(results, list) and len(results) > 0:
                    # Get first match
                    first_result = results[0]

                    data["company_name"] = first_result.get("name", first_result.get("lVal30"))
                    data["stock_symbol"] = first_result.get("symbol", first_result.get("lVal18"))
                    data["stock_code"] = first_result.get("code", first_result.get("insCode"))

                    # If we have stock code, get detailed data
                    if data["stock_code"]:
                        detail_data = self._get_stock_details(data["stock_code"])
                        if detail_data:
                            data.update(detail_data)
                            data["data_available"] = True

                    logger.info(f"[{self.source_name}] Found stock: {data.get('stock_symbol')}")
                    return data

            except Exception as json_err:
                logger.warning(f"[{self.source_name}] JSON parse failed: {json_err}")

        except Exception as e:
            logger.warning(f"[{self.source_name}] API search failed: {e}")

        return None

    def _search_old_tsetmc(
        self,
        brand_name: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Search using old TSETMC interface.

        Args:
            brand_name: Brand name
            data: Existing data dictionary

        Returns:
            Updated data dictionary or None
        """
        try:
            # Old TSETMC search endpoint
            search_url = f"{self.base_url}/tsev2/data/search.aspx"
            params = {"skey": brand_name}

            response = self._make_request(search_url, params=params)

            if not response:
                return None

            # Old TSETMC returns data in format: code,name,symbol,...
            # Example: 12345678901234567,شرکت نمونه,نمونه,100,1000,5
            content = response.text.strip()

            if content and len(content) > 10:
                lines = content.split("\n")
                if lines:
                    # Parse first result
                    parts = lines[0].split(",")

                    if len(parts) >= 3:
                        data["stock_code"] = parts[0]
                        data["company_name"] = parts[1]
                        data["stock_symbol"] = parts[2]

                        # Try to get more details
                        if data["stock_code"]:
                            detail_data = self._get_stock_details(data["stock_code"])
                            if detail_data:
                                data.update(detail_data)

                        data["data_available"] = True
                        logger.info(f"[{self.source_name}] Found via old API: {data.get('stock_symbol')}")
                        return data

        except Exception as e:
            logger.warning(f"[{self.source_name}] Old API search failed: {e}")

        return None

    def _get_stock_details(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information using stock code.

        Args:
            stock_code: Stock instrument code

        Returns:
            Dictionary with stock details or None
        """
        try:
            # TSETMC detail page
            detail_url = f"{self.base_url}/Loader.aspx?ParTree=151311&i={stock_code}"

            response = self._make_request(detail_url)
            if not response:
                return None

            soup = self._parse_html(response.text)
            if not soup:
                return None

            details = {}

            # Try to extract price data from page
            # TSETMC uses specific div IDs for data
            price_elem = soup.find(id="plast")  # Last price
            if price_elem:
                details["last_price"] = price_elem.get_text(strip=True)

            change_elem = soup.find(id="pchange")  # Price change
            if change_elem:
                details["price_change"] = change_elem.get_text(strip=True)

            volume_elem = soup.find(id="qvol")  # Volume
            if volume_elem:
                details["volume"] = volume_elem.get_text(strip=True)

            value_elem = soup.find(id="qval")  # Trade value
            if value_elem:
                details["value"] = value_elem.get_text(strip=True)

            logger.info(f"[{self.source_name}] Extracted stock details")
            return details

        except Exception as e:
            logger.warning(f"[{self.source_name}] Failed to get stock details: {e}")
            return None

    def get_manual_instructions(self, brand_name: str) -> Dict[str, str]:
        """Get manual search instructions for TSETMC.

        Args:
            brand_name: Brand name to search

        Returns:
            Dictionary with manual search instructions
        """
        return {
            "site": "tsetmc.com",
            "url": f"{self.new_url}/search?term={quote(brand_name)}",
            "instructions_fa": f"""
مراحل جستجوی دستی در سایت بورس تهران (TSETMC):
1. به آدرس {self.new_url} بروید
2. در کادر جستجو عبارت "{brand_name}" یا نماد سهم را وارد کنید
3. روی نماد مورد نظر کلیک کنید
4. اطلاعات زیر را یادداشت کنید:
   - نماد (Symbol)
   - آخرین قیمت (Last Price)
   - تغییر قیمت (Price Change)
   - ارزش بازار (Market Cap)
   - حجم معاملات (Volume)
   - ارزش معاملات (Value)
   - P/E (نسبت قیمت به درآمد)
   - EPS (سود هر سهم)

توجه: ممکنه نیاز به ثبت‌نام داشته باشید.
            """,
            "instructions_en": f"""
Manual search steps for TSETMC (Tehran Stock Exchange):
1. Go to {self.new_url}
2. Search for "{brand_name}" or stock symbol
3. Click on the target symbol
4. Note the following information:
   - Symbol
   - Last Price
   - Price Change
   - Market Cap
   - Volume
   - Trade Value
   - P/E Ratio
   - EPS

Note: Registration may be required.
            """
        }
