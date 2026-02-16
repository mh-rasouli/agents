"""Data collection agent - orchestrates web scraping from all sources."""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from models.state import BrandIntelligenceState
from scrapers.rasmio_scraper import RasmioScraper
from scrapers.codal_scraper import CodalScraper
from scrapers.tsetmc_scraper import TsetmcScraper
from scrapers.linka_scraper import LinkaScraper
from scrapers.trademark_scraper import TrademarkScraper
from scrapers.web_search import WebSearchScraper
from scrapers.example_scraper import ExampleScraper
from scrapers.tavily_scraper import TavilyScraper
from config.prompts import DATA_EXTRACTION_PROMPT
from utils.logger import get_logger

logger = get_logger(__name__)


class DataCollectionAgent(BaseAgent):
    """Agent responsible for collecting data from all sources."""

    def __init__(self):
        """Initialize the data collection agent."""
        super().__init__("DataCollectionAgent")

        # Initialize all scrapers
        self.scrapers = {
            "example": ExampleScraper(),  # Works with Wikipedia
            "web_search": WebSearchScraper(),
            "tavily": TavilyScraper(),  # AI-powered search (optional)
            "rasmio": RasmioScraper(),
            "codal": CodalScraper(),
            "tsetmc": TsetmcScraper(),
            "linka": LinkaScraper(),
            "trademark": TrademarkScraper()
        }

    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Execute data collection from all sources.

        Args:
            state: Current workflow state

        Returns:
            Updated state with raw_data populated
        """
        self._log_start()

        brand_name = state["brand_name"]
        brand_website = state.get("brand_website")

        logger.info(f"Collecting data for: {brand_name}")
        if brand_website:
            logger.info(f"Website: {brand_website}")

        # Collect data from all sources in parallel
        raw_data = self._scrape_all_sources(brand_name, brand_website)

        # Extract structured data using LLM
        structured_data = self._extract_structured_data(raw_data)

        # Update state
        state["raw_data"] = {
            "scraped": raw_data,
            "structured": structured_data
        }

        # Check if we got any data
        successful_sources = [k for k, v in raw_data.items() if v is not None]
        logger.info(f"Successfully collected data from {len(successful_sources)}/{len(self.scrapers)} sources")

        if len(successful_sources) == 0:
            self._add_error(state, "Failed to collect data from any source")
            self._log_end(success=False)
        else:
            self._log_end(success=True)

        return state

    def _scrape_all_sources(
        self,
        brand_name: str,
        brand_website: Optional[str]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Scrape data from all sources in parallel.

        Args:
            brand_name: Name of the brand
            brand_website: Optional website URL

        Returns:
            Dictionary mapping source names to scraped data
        """
        results = {}

        # Use ThreadPoolExecutor for parallel scraping
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all scraping tasks
            future_to_source = {}

            for source_name, scraper in self.scrapers.items():
                if source_name == "web_search" and brand_website:
                    future = executor.submit(
                        scraper.scrape_with_cache,
                        brand_name,
                        website_url=brand_website
                    )
                else:
                    future = executor.submit(scraper.scrape_with_cache, brand_name)

                future_to_source[future] = source_name

            # Collect results as they complete
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    data = future.result()
                    results[source_name] = data

                    if data:
                        logger.info(f"[OK] {source_name}: Success")
                    else:
                        logger.warning(f"[X] {source_name}: No data")

                except Exception as e:
                    logger.error(f"[X] {source_name}: Error - {e}")
                    results[source_name] = None

        return results

    def _extract_structured_data(
        self,
        raw_data: Dict[str, Optional[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Extract structured data from raw scraped data.

        Uses LLM if available, otherwise does basic extraction.

        Args:
            raw_data: Raw scraped data from all sources

        Returns:
            Structured and normalized data
        """
        # First try LLM extraction if available
        if self.llm.is_available():
            try:
                # Prepare data for LLM
                data_summary = self._prepare_data_for_llm(raw_data)

                # Use LLM to extract structured information
                logger.info("Extracting structured data using LLM...")

                structured_data = self.llm.extract_structured_data(
                    data=data_summary,
                    extraction_prompt=DATA_EXTRACTION_PROMPT,
                    system_prompt="You are a data extraction specialist."
                )

                if structured_data:
                    logger.info("[LLM] Successfully extracted structured data")
                    return structured_data

            except Exception as e:
                logger.error(f"LLM extraction failed: {e}")

        # Fallback: Basic extraction without LLM
        logger.info("Using basic extraction (no LLM)")
        return self._basic_extraction(raw_data)

    def _basic_extraction(self, raw_data: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
        """Perform basic data extraction without LLM.

        Args:
            raw_data: Raw scraped data

        Returns:
            Basic structured data
        """
        structured = {
            "sources_used": [],
            "contact_info": {
                "emails": [],
                "phones": [],
                "addresses": []
            },
            "social_media": {},
            "website_info": {}
        }

        for source, data in raw_data.items():
            if not data:
                continue

            structured["sources_used"].append(source)

            # Extract contact info
            if "contact_info" in data:
                contact = data["contact_info"]
                if "emails" in contact:
                    structured["contact_info"]["emails"].extend(contact["emails"])
                if "phones" in contact:
                    structured["contact_info"]["phones"].extend(contact["phones"])
                if "addresses" in contact:
                    structured["contact_info"]["addresses"].extend(contact["addresses"])

            # Extract social media
            if "social_media" in data:
                structured["social_media"].update(data["social_media"])

            # Extract website info
            if source == "web_search":
                structured["website_info"] = {
                    "title": data.get("page_title"),
                    "meta_description": data.get("meta_data", {}).get("description"),
                    "is_javascript_site": data.get("is_javascript_site", False),
                    "data_richness": data.get("data_richness_score", 0.0),
                    "headings": data.get("headings", []),
                    "content_summary": data.get("content_summary", ""),
                    "about_us": data.get("about_us", ""),
                    "internal_links": data.get("internal_links", [])
                }

                # Extract products/services from headings and content
                headings = data.get("headings", [])
                content = data.get("content_summary", "")

                # Look for product/service keywords in headings
                service_keywords = ["خدمات", "محصولات", "services", "products", "مشاوره", "counseling", "therapy", "درمان"]
                for heading in headings:
                    if isinstance(heading, str):  # Only process string headings
                        for keyword in service_keywords:
                            if keyword in heading.lower():
                                if "products_services" not in structured:
                                    structured["products_services"] = []
                                structured["products_services"].append(heading)
                                break

                # Extract business description from content
                if content and len(content) > 100:
                    structured["business_description"] = content[:500]  # First 500 chars

            # Extract Wikipedia summary if available
            if source == "example" and data.get("found_on_wikipedia"):
                structured["wikipedia_summary"] = data.get("summary")
                structured["wikipedia_infobox"] = data.get("infobox_data", {})

        # Deduplicate lists
        structured["contact_info"]["emails"] = list(set(structured["contact_info"]["emails"]))
        structured["contact_info"]["phones"] = list(set(structured["contact_info"]["phones"]))

        logger.info(f"[Basic] Extracted data from {len(structured['sources_used'])} sources")

        return structured

    def _prepare_data_for_llm(
        self,
        raw_data: Dict[str, Optional[Dict[str, Any]]]
    ) -> str:
        """Prepare scraped data for LLM processing.

        Args:
            raw_data: Raw scraped data

        Returns:
            Formatted string for LLM input
        """
        lines = []

        for source, data in raw_data.items():
            if data:
                lines.append(f"\n=== {source.upper()} ===")

                # Add relevant fields (exclude raw HTML)
                for key, value in data.items():
                    if key not in ["raw_html", "raw_data"] and value:
                        lines.append(f"{key}: {value}")

        return "\n".join(lines)
