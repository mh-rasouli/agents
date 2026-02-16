"""Scraper for codal.ir - Iranian financial statements and disclosures."""

from typing import Optional, Dict, Any
from urllib.parse import quote
import re
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)


class CodalScraper(BaseScraper):
    """Scraper for financial data from codal.ir (CODAL - Iran's disclosure system)."""

    def __init__(self):
        """Initialize the Codal scraper."""
        super().__init__("codal")
        self.base_url = "https://www.codal.ir"
        self.search_url = "https://search.codal.ir/api/search/v2/q"

    def scrape(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape financial statements and disclosure data from codal.ir.

        Codal uses an API for search. This scraper attempts to:
        1. Search for the company
        2. Find latest financial reports
        3. Extract key financial metrics

        Args:
            brand_name: Name of the brand/company to search
            **kwargs: Additional arguments

        Returns:
            Dictionary with financial data or None
        """
        data = {
            "source": self.source_name,
            "brand_name": brand_name,
            "manual_search_url": f"https://www.codal.ir/ReportList.aspx?search={quote(brand_name)}",
            "scraping_method": "automated",
            "data_available": False,
            "company_name": None,
            "symbol": None,
            "latest_reports": [],
            "revenue": None,
            "profit": None,
            "assets": None,
            "liabilities": None,
            "equity": None,
            "fiscal_year": None,
            "latest_report_date": None,
            "notes": []
        }

        try:
            logger.info(f"[{self.source_name}] Searching Codal for {brand_name}")

            # Codal has a search API
            # Try searching via the API
            api_url = f"{self.search_url}"

            # Codal API parameters (may need adjustment based on actual API)
            params = {
                "Keyword": brand_name,
                "PageNumber": 1,
                "PageSize": 10
            }

            response = self._make_request(
                api_url,
                method="GET",
                params=params
            )

            if not response:
                # Fallback to web search
                logger.warning(f"[{self.source_name}] API search failed, trying web interface")
                return self._scrape_web_interface(brand_name, data)

            # Try to parse JSON response
            try:
                search_results = response.json()

                if isinstance(search_results, dict) and "Letters" in search_results:
                    letters = search_results["Letters"]

                    if letters and len(letters) > 0:
                        # Get first few results
                        data["latest_reports"] = []

                        for letter in letters[:5]:
                            report = {
                                "title": letter.get("Title", ""),
                                "company": letter.get("CompanyName", ""),
                                "symbol": letter.get("Symbol", ""),
                                "publish_date": letter.get("PublishDateTime", ""),
                                "url": f"{self.base_url}/ViewLetter.aspx?LetterSerial={letter.get('TracingNo', '')}"
                            }
                            data["latest_reports"].append(report)

                        # Extract company info from first report
                        if letters[0]:
                            data["company_name"] = letters[0].get("CompanyName")
                            data["symbol"] = letters[0].get("Symbol")
                            data["latest_report_date"] = letters[0].get("PublishDateTime")
                            data["data_available"] = True

                        logger.info(f"[{self.source_name}] Found {len(letters)} reports for {brand_name}")

                    else:
                        data["notes"].append(f"No financial reports found for '{brand_name}'")
                        data["scraping_method"] = "manual_recommended"

            except Exception as json_err:
                logger.warning(f"[{self.source_name}] Failed to parse JSON: {json_err}")
                return self._scrape_web_interface(brand_name, data)

            return data

        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
            data["notes"].append(f"Error: {str(e)[:100]}")
            data["scraping_method"] = "failed"
            return data

    def _scrape_web_interface(
        self,
        brand_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback to scraping the web interface.

        Args:
            brand_name: Brand name
            data: Existing data dictionary

        Returns:
            Updated data dictionary
        """
        try:
            # Try regular web search
            search_url = f"{self.base_url}/ReportList.aspx"
            params = {"search": brand_name}

            response = self._make_request(search_url, params=params)

            if not response:
                data["notes"].append("Cannot access codal.ir. Try manual search.")
                data["scraping_method"] = "manual_required"
                return data

            soup = self._parse_html(response.text)
            if not soup:
                return data

            # Look for report table or list
            # Codal uses tables for displaying reports
            report_table = soup.find("table", id=lambda x: x and "table" in x.lower())

            if report_table:
                rows = report_table.find_all("tr")[1:]  # Skip header

                for row in rows[:5]:  # Get first 5 reports
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        report = {
                            "title": cols[0].get_text(strip=True) if len(cols) > 0 else "",
                            "company": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                            "date": cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        }

                        # Try to find report link
                        link = row.find("a", href=True)
                        if link:
                            report["url"] = self.base_url + link["href"]

                        data["latest_reports"].append(report)

                if data["latest_reports"]:
                    data["data_available"] = True
                    logger.info(f"[{self.source_name}] Extracted {len(data['latest_reports'])} reports")

            else:
                data["notes"].append("Report table not found on page")
                data["scraping_method"] = "manual_recommended"

        except Exception as e:
            logger.warning(f"[{self.source_name}] Web scraping failed: {e}")
            data["notes"].append(f"Web scraping error: {str(e)[:100]}")

        return data

    def get_manual_instructions(self, brand_name: str) -> Dict[str, str]:
        """Get manual search instructions for codal.ir.

        Args:
            brand_name: Brand name to search

        Returns:
            Dictionary with manual search instructions
        """
        return {
            "site": "codal.ir",
            "url": f"https://www.codal.ir/ReportList.aspx?search={quote(brand_name)}",
            "instructions_fa": f"""
مراحل جستجوی دستی در کدال:
1. به آدرس https://www.codal.ir بروید
2. در کادر جستجو عبارت "{brand_name}" را وارد کنید
3. روی گزارش‌های مالی کلیک کنید
4. اطلاعات زیر را از آخرین صورت‌های مالی یادداشت کنید:
   - درآمد (Revenue)
   - سود خالص (Net Profit)
   - جمع دارایی‌ها (Total Assets)
   - بدهی‌ها (Liabilities)
   - حقوق صاحبان سهام (Equity)
   - سال مالی

توجه: ممکنه نیاز به ثبت‌نام در سایت داشته باشید.
            """,
            "instructions_en": f"""
Manual search steps for codal.ir:
1. Go to https://www.codal.ir
2. Search for "{brand_name}"
3. Click on financial reports
4. Note from latest financial statements:
   - Revenue
   - Net Profit
   - Total Assets
   - Liabilities
   - Shareholders' Equity
   - Fiscal Year

Note: You may need to register on the site.
            """
        }
