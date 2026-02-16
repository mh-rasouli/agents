"""Web search utility for general brand information."""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
from scrapers.base_scraper import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)


class WebSearchScraper(BaseScraper):
    """General web search scraper for brand information."""

    def __init__(self):
        """Initialize the WebSearch scraper."""
        super().__init__("web_search")

        # Common patterns for finding specific content
        self.about_patterns = [
            r'about[-_\s]us',
            r'درباره[-_\s]ما',
            r'about',
            r'درباره',
            r'who[-_\s]we[-_\s]are',
            r'our[-_\s]story',
            r'معرفی'
        ]

        self.contact_patterns = [
            r'contact[-_\s]us',
            r'تماس[-_\s]با[-_\s]ما',
            r'contact',
            r'تماس',
            r'ارتباط'
        ]

    def scrape(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Scrape general web information about a brand.

        Args:
            brand_name: Name of the brand/company to search
            **kwargs: Additional arguments (e.g., website_url)

        Returns:
            Dictionary with web data or None
        """
        try:
            website_url = kwargs.get("website_url")

            data = {
                "source": self.source_name,
                "brand_name": brand_name,
                "website_url": website_url,
                "meta_data": {},
                "page_title": None,
                "headings": [],
                "about_us": None,
                "contact_info": {},
                "social_media": {},
                "products_services": [],
                "internal_links": [],
                "raw_html": None,
                "is_javascript_site": False,
                "scraping_notes": []
            }

            # If website URL is provided, scrape it
            if website_url:
                response = self._make_request(website_url)
                if response:
                    soup = self._parse_html(response.text)
                    if soup:
                        # Check if this is a JavaScript-heavy site
                        js_indicators = self._detect_javascript_site(soup, response.text)
                        data["is_javascript_site"] = js_indicators["is_js_heavy"]

                        if js_indicators["is_js_heavy"]:
                            data["scraping_notes"].append(
                                f"JavaScript-heavy site detected ({js_indicators['framework']}). "
                                "Limited data available from static HTML."
                            )
                            logger.warning(
                                f"[{self.source_name}] {brand_name} appears to be a {js_indicators['framework']} site. "
                                "Consider using Playwright for full scraping."
                            )

                        # Extract all metadata
                        data["meta_data"] = self._extract_meta_data(soup)

                        # Extract title
                        data["page_title"] = self._extract_title(soup)

                        # Extract headings
                        data["headings"] = self._extract_headings(soup)

                        # Extract contact information
                        data["contact_info"] = self._extract_contact_info(soup, response.text)

                        # Extract social media links
                        data["social_media"] = self._extract_social_media(soup)

                        # Find about us page link
                        data["about_us_link"] = self._find_about_link(soup, website_url)

                        # Find contact page link
                        data["contact_link"] = self._find_contact_link(soup, website_url)

                        # Extract internal links for further exploration
                        data["internal_links"] = self._extract_internal_links(soup, website_url)[:10]

                        # Extract text content summary
                        data["content_summary"] = self._extract_content_summary(soup)

                        # Store raw HTML for LLM analysis (first 10000 chars)
                        data["raw_html"] = response.text[:10000]

                        # Calculate data richness score
                        richness_score = self._calculate_data_richness(data)
                        data["data_richness_score"] = richness_score

                        if richness_score < 0.3:
                            data["scraping_notes"].append(
                                "Low data richness. Website may be dynamic or require authentication."
                            )

                        logger.info(
                            f"[{self.source_name}] Scraped {brand_name} "
                            f"(richness: {richness_score:.2f}, JS-site: {js_indicators['is_js_heavy']})"
                        )

                        # If we found about us link and data is sparse, try scraping it
                        if data["about_us_link"] and richness_score < 0.5:
                            data["about_us"] = self._scrape_about_page(data["about_us_link"])

                        # Try contact page too if data is sparse
                        if data["contact_link"] and richness_score < 0.5:
                            contact_data = self._scrape_contact_page(data["contact_link"])
                            if contact_data:
                                # Merge contact data
                                for key in ['emails', 'phones', 'addresses']:
                                    data["contact_info"][key].extend(contact_data.get(key, []))

            return data

        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
            return None

    def _extract_meta_data(self, soup) -> Dict[str, Any]:
        """Extract all meta tags from page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary of meta data
        """
        meta_data = {}

        # Standard meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")

            if name and content:
                meta_data[name] = content

        return meta_data

    def _extract_title(self, soup) -> Optional[str]:
        """Extract page title.

        Args:
            soup: BeautifulSoup object

        Returns:
            Page title or None
        """
        title = soup.find("title")
        return title.text.strip() if title else None

    def _extract_headings(self, soup) -> List[Dict[str, str]]:
        """Extract all headings (h1-h3).

        Args:
            soup: BeautifulSoup object

        Returns:
            List of headings with level and text
        """
        headings = []

        for level in ["h1", "h2", "h3"]:
            for heading in soup.find_all(level):
                text = heading.get_text(strip=True)
                if text:
                    headings.append({
                        "level": level,
                        "text": text
                    })

        return headings

    def _extract_contact_info(self, soup, html_text: str) -> Dict[str, Any]:
        """Extract contact information (email, phone, address).

        Args:
            soup: BeautifulSoup object
            html_text: Raw HTML text

        Returns:
            Dictionary with contact information
        """
        contact_info = {
            "emails": [],
            "phones": [],
            "addresses": []
        }

        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, html_text)
        contact_info["emails"] = list(set(emails))[:5]  # Limit to 5 unique emails

        # Extract phone numbers (Iranian and international formats)
        phone_patterns = [
            r'\+98[-\s]?\d{10}',  # +98 format
            r'0\d{10}',  # Iranian 11-digit
            r'\d{3}[-\s]?\d{8}',  # xxx-xxxxxxxx
            r'\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}'  # (xxx) xxx-xxxx
        ]

        for pattern in phone_patterns:
            phones = re.findall(pattern, html_text)
            contact_info["phones"].extend(phones)

        contact_info["phones"] = list(set(contact_info["phones"]))[:5]

        # Try to find address (look for common address indicators)
        address_keywords = ["address", "آدرس", "نشانی", "location"]
        for keyword in address_keywords:
            address_tags = soup.find_all(string=re.compile(keyword, re.I))
            for tag in address_tags[:3]:
                parent = tag.parent
                if parent:
                    address_text = parent.get_text(strip=True)
                    if len(address_text) > 20 and len(address_text) < 500:
                        contact_info["addresses"].append(address_text)

        return contact_info

    def _extract_social_media(self, soup) -> Dict[str, str]:
        """Extract social media links.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary mapping platform to URL
        """
        social_media = {}

        social_patterns = {
            "instagram": r'instagram\.com/([^/\s"\']+)',
            "twitter": r'twitter\.com/([^/\s"\']+)',
            "linkedin": r'linkedin\.com/(company|in)/([^/\s"\']+)',
            "facebook": r'facebook\.com/([^/\s"\']+)',
            "telegram": r't\.me/([^/\s"\']+)',
            "youtube": r'youtube\.com/(channel|c|user)/([^/\s"\']+)'
        }

        # Get all links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")

            for platform, pattern in social_patterns.items():
                match = re.search(pattern, href, re.I)
                if match:
                    social_media[platform] = href
                    break

        return social_media

    def _find_about_link(self, soup, base_url: str) -> Optional[str]:
        """Find 'About Us' page link.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            About page URL or None
        """
        for pattern in self.about_patterns:
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)

                if re.search(pattern, href, re.I) or re.search(pattern, text, re.I):
                    return urljoin(base_url, href)

        return None

    def _find_contact_link(self, soup, base_url: str) -> Optional[str]:
        """Find 'Contact Us' page link.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            Contact page URL or None
        """
        for pattern in self.contact_patterns:
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)

                if re.search(pattern, href, re.I) or re.search(pattern, text, re.I):
                    return urljoin(base_url, href)

        return None

    def _extract_internal_links(self, soup, base_url: str) -> List[str]:
        """Extract internal links from page.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for filtering

        Returns:
            List of internal URLs
        """
        internal_links = []
        base_domain = urlparse(base_url).netloc

        for link in soup.find_all("a", href=True):
            href = link.get("href")
            full_url = urljoin(base_url, href)

            # Check if it's an internal link
            if urlparse(full_url).netloc == base_domain:
                if full_url not in internal_links and full_url != base_url:
                    internal_links.append(full_url)

        return internal_links

    def _extract_content_summary(self, soup) -> str:
        """Extract text content summary.

        Args:
            soup: BeautifulSoup object

        Returns:
            Text summary
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        # Get text
        text = soup.get_text(separator=" ", strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)

        # Return first 2000 characters
        return text[:2000]

    def _detect_javascript_site(self, soup, html_text: str) -> Dict[str, Any]:
        """Detect if website is JavaScript-heavy.

        Args:
            soup: BeautifulSoup object
            html_text: Raw HTML text

        Returns:
            Dictionary with detection results
        """
        indicators = {
            "is_js_heavy": False,
            "framework": "unknown",
            "confidence": 0.0
        }

        # Check for common JS frameworks
        frameworks = {
            "Next.js": ["__NEXT_DATA__", "/_next/static/"],
            "React": ["react", "react-dom"],
            "Vue": ["vue", "nuxt"],
            "Angular": ["ng-app", "angular"],
            "Gatsby": ["gatsby"],
        }

        for framework, patterns in frameworks.items():
            matches = sum(1 for p in patterns if p.lower() in html_text.lower())
            if matches > 0:
                indicators["framework"] = framework
                indicators["confidence"] = min(matches / len(patterns), 1.0)
                break

        # Additional indicators
        script_count = len(soup.find_all("script"))
        body_text_length = len(soup.get_text(strip=True))

        # If lots of scripts but minimal body text, likely JS-heavy
        if script_count > 10 and body_text_length < 500:
            indicators["is_js_heavy"] = True
            if indicators["framework"] == "unknown":
                indicators["framework"] = "Unknown JS Framework"

        # Check for single-page app indicators
        if soup.find(id="__next") or soup.find(id="root") or soup.find(id="app"):
            indicators["is_js_heavy"] = True

        return indicators

    def _calculate_data_richness(self, data: Dict[str, Any]) -> float:
        """Calculate how much useful data was extracted.

        Args:
            data: Scraped data dictionary

        Returns:
            Richness score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 10.0

        # Title
        if data.get("page_title"):
            score += 1.0

        # Headings
        if len(data.get("headings", [])) > 0:
            score += min(len(data["headings"]) / 5, 2.0)

        # Contact info
        if data.get("contact_info"):
            if data["contact_info"].get("emails"):
                score += 1.5
            if data["contact_info"].get("phones"):
                score += 1.5
            if data["contact_info"].get("addresses"):
                score += 1.0

        # Social media
        if len(data.get("social_media", {})) > 0:
            score += min(len(data["social_media"]) / 3, 1.5)

        # Content
        if data.get("content_summary") and len(data["content_summary"]) > 100:
            score += 1.5

        # Meta data
        if len(data.get("meta_data", {})) > 2:
            score += 1.0

        return min(score / max_score, 1.0)

    def _scrape_contact_page(self, url: str) -> Optional[Dict[str, List[str]]]:
        """Scrape the contact page.

        Args:
            url: Contact page URL

        Returns:
            Contact information or None
        """
        try:
            logger.info(f"[{self.source_name}] Scraping contact page: {url}")
            response = self._make_request(url)

            if response:
                soup = self._parse_html(response.text)
                if soup:
                    return self._extract_contact_info(soup, response.text)

        except Exception as e:
            logger.warning(f"[{self.source_name}] Failed to scrape contact page: {e}")

        return None

    def _scrape_about_page(self, url: str) -> Optional[str]:
        """Scrape the about us page.

        Args:
            url: About page URL

        Returns:
            About page content or None
        """
        try:
            logger.info(f"[{self.source_name}] Scraping about page: {url}")
            response = self._make_request(url)

            if response:
                soup = self._parse_html(response.text)
                if soup:
                    # Remove unwanted elements
                    for element in soup(["script", "style", "nav", "header", "footer"]):
                        element.decompose()

                    # Get main content
                    text = soup.get_text(separator=" ", strip=True)
                    text = re.sub(r'\s+', ' ', text)

                    return text[:3000]  # Return first 3000 chars

        except Exception as e:
            logger.warning(f"[{self.source_name}] Failed to scrape about page: {e}")

        return None

    def scrape_multiple_pages(
        self,
        brand_name: str,
        urls: List[str]
    ) -> Dict[str, Any]:
        """Scrape multiple pages for comprehensive brand information.

        Args:
            brand_name: Name of the brand
            urls: List of URLs to scrape

        Returns:
            Aggregated data from all pages
        """
        logger.info(f"[{self.source_name}] Scraping {len(urls)} pages for {brand_name}")

        aggregated_data = {
            "brand_name": brand_name,
            "pages_scraped": 0,
            "all_content": [],
            "all_contacts": {
                "emails": [],
                "phones": [],
                "addresses": []
            },
            "all_social_media": {},
            "all_headings": []
        }

        for url in urls[:5]:  # Limit to 5 pages to avoid overload
            try:
                page_data = self.scrape(brand_name, website_url=url)

                if page_data:
                    aggregated_data["pages_scraped"] += 1

                    # Aggregate contact info
                    if page_data.get("contact_info"):
                        contact = page_data["contact_info"]
                        aggregated_data["all_contacts"]["emails"].extend(contact.get("emails", []))
                        aggregated_data["all_contacts"]["phones"].extend(contact.get("phones", []))
                        aggregated_data["all_contacts"]["addresses"].extend(contact.get("addresses", []))

                    # Aggregate social media
                    if page_data.get("social_media"):
                        aggregated_data["all_social_media"].update(page_data["social_media"])

                    # Aggregate headings
                    if page_data.get("headings"):
                        aggregated_data["all_headings"].extend(page_data["headings"])

                    # Store content summaries
                    if page_data.get("content_summary"):
                        aggregated_data["all_content"].append({
                            "url": url,
                            "content": page_data["content_summary"]
                        })

            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")

        # Deduplicate contact info
        aggregated_data["all_contacts"]["emails"] = list(set(aggregated_data["all_contacts"]["emails"]))
        aggregated_data["all_contacts"]["phones"] = list(set(aggregated_data["all_contacts"]["phones"]))

        logger.info(f"[{self.source_name}] Scraped {aggregated_data['pages_scraped']} pages successfully")

        return aggregated_data
