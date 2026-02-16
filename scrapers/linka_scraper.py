"""Scraper for linka.ir - Iranian social media analytics."""

from typing import Optional, Dict, Any
from urllib.parse import quote
import re
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)


class LinkaScraper(BaseScraper):
    """Scraper for social media analytics data from linka.ir."""

    def __init__(self):
        """Initialize the Linka scraper."""
        super().__init__("linka")
        self.base_url = "https://www.linka.ir"
        self.search_url = "https://www.linka.ir/search"

    def scrape(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape social media analytics data from linka.ir.

        Linka.ir provides analytics for Iranian brands' social media presence.
        May require authentication or have rate limiting.

        Args:
            brand_name: Name of the brand/company to search
            **kwargs: Additional arguments (e.g., instagram_handle)

        Returns:
            Dictionary with social media data or None
        """
        data = {
            "source": self.source_name,
            "brand_name": brand_name,
            "manual_search_url": f"{self.search_url}?q={quote(brand_name)}",
            "scraping_method": "automated",
            "data_available": False,
            "instagram_handle": kwargs.get("instagram_handle"),
            "social_media": {
                "instagram": {
                    "handle": None,
                    "followers": None,
                    "engagement_rate": None,
                    "posts_count": None,
                    "average_likes": None,
                    "average_comments": None
                },
                "telegram": {
                    "handle": None,
                    "members": None,
                    "posts_count": None
                },
                "twitter": {
                    "handle": None,
                    "followers": None
                },
                "linkedin": {
                    "handle": None,
                    "followers": None
                },
                "aparat": {
                    "handle": None,
                    "subscribers": None
                }
            },
            "notes": []
        }

        try:
            logger.info(f"[{self.source_name}] Searching Linka for {brand_name}")

            # Try to search for the brand
            search_url = f"{self.search_url}?q={quote(brand_name)}"
            response = self._make_request(search_url)

            if not response:
                data["notes"].append(
                    "Cannot access linka.ir. May require VPN or authentication."
                )
                data["scraping_method"] = "manual_required"
                logger.warning(f"[{self.source_name}] Cannot access linka.ir")
                return data

            soup = self._parse_html(response.text)
            if not soup:
                data["scraping_method"] = "manual_required"
                return data

            # Look for brand profiles or results
            # Linka typically shows brand cards with social media stats

            # Try to find brand cards/results
            brand_cards = soup.find_all(
                "div",
                class_=["brand-card", "profile-card", "search-result", "brand-item"]
            )

            if brand_cards:
                # Process first result
                card = brand_cards[0]

                # Extract Instagram data
                instagram_section = card.find(string=re.compile("instagram", re.I))
                if instagram_section:
                    parent = instagram_section.find_parent(["div", "section"])
                    if parent:
                        # Try to extract follower count
                        follower_pattern = r'([\d,]+)\s*(follower|دنبال\s*کننده)'
                        follower_match = re.search(follower_pattern, parent.get_text(), re.I)
                        if follower_match:
                            followers_str = follower_match.group(1).replace(',', '')
                            data["social_media"]["instagram"]["followers"] = int(followers_str)

                        # Try to extract handle
                        handle_elem = parent.find("a", href=re.compile("instagram.com"))
                        if handle_elem:
                            handle = handle_elem.get("href", "").split("/")[-1]
                            data["social_media"]["instagram"]["handle"] = handle

                # Extract Telegram data
                telegram_section = card.find(string=re.compile("telegram", re.I))
                if telegram_section:
                    parent = telegram_section.find_parent(["div", "section"])
                    if parent:
                        # Try to extract member count
                        member_pattern = r'([\d,]+)\s*(member|عضو)'
                        member_match = re.search(member_pattern, parent.get_text(), re.I)
                        if member_match:
                            members_str = member_match.group(1).replace(',', '')
                            data["social_media"]["telegram"]["members"] = int(members_str)

                        # Try to extract handle
                        handle_elem = parent.find("a", href=re.compile("t.me"))
                        if handle_elem:
                            handle = handle_elem.get("href", "").split("/")[-1]
                            data["social_media"]["telegram"]["handle"] = handle

                # Check if we got any data
                has_data = any([
                    data["social_media"]["instagram"]["followers"],
                    data["social_media"]["telegram"]["members"]
                ])

                if has_data:
                    data["data_available"] = True
                    logger.info(f"[{self.source_name}] Extracted social media data for {brand_name}")
                else:
                    data["notes"].append("Found results but couldn't extract social media metrics")
                    data["scraping_method"] = "manual_recommended"

            else:
                # Try alternative: look for direct Instagram/Telegram links and stats
                stats_extracted = self._extract_social_stats_from_page(soup, data)

                if stats_extracted:
                    data["data_available"] = True
                else:
                    data["notes"].append(f"No social media data found for '{brand_name}'")
                    data["scraping_method"] = "manual_recommended"

            return data

        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
            data["notes"].append(f"Error: {str(e)[:100]}")
            data["scraping_method"] = "failed"
            return data

    def _extract_social_stats_from_page(
        self,
        soup,
        data: Dict[str, Any]
    ) -> bool:
        """Try to extract social media stats from any page structure.

        Args:
            soup: BeautifulSoup object
            data: Data dictionary to update

        Returns:
            True if any data was extracted
        """
        extracted = False

        # Look for Instagram links
        instagram_links = soup.find_all("a", href=re.compile("instagram.com"))
        for link in instagram_links:
            handle = link.get("href", "").split("/")[-1]
            if handle and handle != "instagram.com":
                data["social_media"]["instagram"]["handle"] = handle
                extracted = True

                # Try to find follower count near the link
                parent = link.find_parent(["div", "li", "section"])
                if parent:
                    text = parent.get_text()
                    follower_match = re.search(r'([\d,]+)\s*(follower|دنبال)', text, re.I)
                    if follower_match:
                        data["social_media"]["instagram"]["followers"] = (
                            int(follower_match.group(1).replace(',', ''))
                        )
                break

        # Look for Telegram links
        telegram_links = soup.find_all("a", href=re.compile("t.me|telegram.me"))
        for link in telegram_links:
            handle = link.get("href", "").split("/")[-1]
            if handle:
                data["social_media"]["telegram"]["handle"] = handle
                extracted = True

                # Try to find member count near the link
                parent = link.find_parent(["div", "li", "section"])
                if parent:
                    text = parent.get_text()
                    member_match = re.search(r'([\d,]+)\s*(member|عضو)', text, re.I)
                    if member_match:
                        data["social_media"]["telegram"]["members"] = (
                            int(member_match.group(1).replace(',', ''))
                        )
                break

        return extracted

    def get_manual_instructions(self, brand_name: str) -> Dict[str, str]:
        """Get manual search instructions for linka.ir.

        Args:
            brand_name: Brand name to search

        Returns:
            Dictionary with manual search instructions
        """
        return {
            "site": "linka.ir",
            "url": f"{self.search_url}?q={quote(brand_name)}",
            "instructions_fa": f"""
مراحل جستجوی دستی در لینکا:
1. به آدرس {self.base_url} بروید
2. در کادر جستجو عبارت "{brand_name}" را وارد کنید
3. روی برند مورد نظر کلیک کنید
4. اطلاعات زیر را یادداشت کنید:

شبکه‌های اجتماعی:
📱 اینستاگرام:
   - هندل (Username)
   - تعداد فالوور
   - نرخ تعامل (Engagement Rate)
   - تعداد پست‌ها

✈️ تلگرام:
   - هندل کانال/گروه
   - تعداد اعضا
   - تعداد پست‌ها

🐦 توییتر:
   - هندل
   - تعداد فالوور

💼 لینکدین:
   - صفحه شرکت
   - تعداد فالوور

توجه: ممکنه نیاز به ثبت‌نام یا VPN داشته باشید.
            """,
            "instructions_en": f"""
Manual search steps for linka.ir:
1. Go to {self.base_url}
2. Search for "{brand_name}"
3. Click on the target brand
4. Note the following information:

Social Media:
📱 Instagram:
   - Username/Handle
   - Follower count
   - Engagement rate
   - Posts count

✈️ Telegram:
   - Channel/Group handle
   - Member count
   - Posts count

🐦 Twitter:
   - Handle
   - Follower count

💼 LinkedIn:
   - Company page
   - Follower count

Note: May require registration or VPN.
            """
        }
