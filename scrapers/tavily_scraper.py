"""Tavily AI Search scraper - Enhanced search for AI agents."""

from typing import Optional, Dict, Any, List
from scrapers.base_scraper import BaseScraper
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class TavilyScraper(BaseScraper):
    """Scraper using Tavily AI Search API for enhanced brand intelligence."""

    def __init__(self):
        """Initialize the Tavily scraper."""
        super().__init__("Tavily")
        self.client = None
        self.enabled = settings.TAVILY_ENABLED

        # Initialize Tavily client if enabled and API key is set
        if self.enabled and settings.TAVILY_API_KEY:
            try:
                from tavily import TavilyClient
                self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)
                logger.info("[Tavily] AI Search enabled")
            except ImportError:
                logger.warning("[Tavily] tavily-python package not installed. Run: pip install tavily-python")
                self.enabled = False
            except Exception as e:
                logger.warning(f"[Tavily] Failed to initialize: {e}")
                self.enabled = False
        else:
            if not settings.TAVILY_ENABLED:
                logger.info("[Tavily] AI Search disabled (TAVILY_ENABLED=false)")
            else:
                logger.info("[Tavily] AI Search disabled (no API key)")

    def scrape(self, brand_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Search for brand information using Tavily AI Search.

        Args:
            brand_name: Name of the brand to search for
            **kwargs: Additional arguments (brand_website, etc.)

        Returns:
            Structured search results or None
        """
        if not self.enabled or not self.client:
            logger.info("[Tavily] Skipping - not enabled or no API key")
            return None

        try:
            brand_website = kwargs.get("brand_website")

            # Build search queries
            queries = self._build_search_queries(brand_name, brand_website)

            # Perform searches
            all_results = []
            for query in queries:
                results = self._search(query)
                if results:
                    all_results.extend(results)

            if not all_results:
                logger.warning(f"[Tavily] No results found for {brand_name}")
                return None

            # Structure the results
            structured_data = self._structure_results(brand_name, all_results)

            logger.info(f"[Tavily] Found {len(all_results)} results for {brand_name}")
            return structured_data

        except Exception as e:
            logger.error(f"[Tavily] Search failed: {e}")
            return None

    def _build_search_queries(self, brand_name: str, brand_website: Optional[str] = None) -> List[str]:
        """Build optimized search queries for brand intelligence.

        Args:
            brand_name: Brand name
            brand_website: Optional brand website

        Returns:
            List of search queries
        """
        queries = [
            # Core brand information
            f"{brand_name} company information Iran",
            f"{brand_name} products services",

            # Business intelligence
            f"{brand_name} parent company shareholders",
            f"{brand_name} industry category market",

            # Digital presence
            f"{brand_name} website social media",
        ]

        # Add website-specific query if available
        if brand_website:
            queries.append(f"site:{brand_website} about products")

        return queries

    def _search(self, query: str, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Perform a single Tavily search.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results or None
        """
        try:
            logger.info(f"[Tavily] Searching: {query}")

            # Tavily search with context extraction
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",  # Use advanced search for better results
                include_answer=True,  # Get AI-generated answer
                include_raw_content=False,  # Don't need raw HTML
                include_domains=[],  # No domain restrictions
                exclude_domains=[],
            )

            results = []

            # Extract results
            if response.get("results"):
                for result in response["results"]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        "score": result.get("score", 0),
                        "published_date": result.get("published_date"),
                    })

            # Add AI-generated answer if available
            if response.get("answer"):
                results.insert(0, {
                    "title": f"AI Summary: {query}",
                    "url": "",
                    "content": response["answer"],
                    "score": 1.0,
                    "type": "ai_summary"
                })

            return results

        except Exception as e:
            logger.error(f"[Tavily] Search error for '{query}': {e}")
            return None

    def _structure_results(self, brand_name: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure raw search results into organized data.

        Args:
            brand_name: Brand name
            results: Raw search results

        Returns:
            Structured data dictionary
        """
        # Separate AI summaries from regular results
        ai_summaries = [r for r in results if r.get("type") == "ai_summary"]
        web_results = [r for r in results if r.get("type") != "ai_summary"]

        # Sort by score
        web_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "brand_name": brand_name,
            "source": "Tavily AI Search",
            "ai_summaries": [r["content"] for r in ai_summaries],
            "top_results": web_results[:10],  # Top 10 results
            "total_results": len(web_results),
            "insights": {
                "has_ai_summary": len(ai_summaries) > 0,
                "high_confidence_results": len([r for r in web_results if r.get("score", 0) > 0.7]),
                "recent_results": len([r for r in web_results if r.get("published_date")]),
            }
        }


# Example usage
if __name__ == "__main__":
    scraper = TavilyScraper()
    if scraper.enabled:
        results = scraper.scrape_with_cache("دیجی‌کالا")
        if results:
            print(f"Found {results['total_results']} results")
            if results['ai_summaries']:
                print(f"\nAI Summary:\n{results['ai_summaries'][0][:200]}...")
    else:
        print("Tavily is not enabled. Set TAVILY_ENABLED=true and TAVILY_API_KEY in .env")
