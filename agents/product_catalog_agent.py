"""Product Catalog Agent - extracts complete product portfolios for brands."""

import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from models.state import BrandIntelligenceState
from utils.logger import get_logger

logger = get_logger(__name__)


class ProductCatalogAgent(BaseAgent):
    """Agent responsible for extracting complete product catalogs."""

    def __init__(self):
        """Initialize the product catalog agent."""
        super().__init__("ProductCatalogAgent")

    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Extract complete product catalog for the brand.

        Args:
            state: Current workflow state

        Returns:
            Updated state with product catalog populated
        """
        self._log_start()

        brand_name = state["brand_name"]
        raw_data = state.get("raw_data", {})
        categorization = state.get("categorization", {})
        relationships = state.get("relationships", {})

        # Extract product catalog
        product_catalog = self._extract_product_catalog(
            brand_name,
            raw_data,
            categorization,
            relationships
        )

        # Update state
        state["product_catalog"] = product_catalog

        self._log_end(success=True)
        return state

    def _extract_product_catalog(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        categorization: Dict[str, Any],
        relationships: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract complete product catalog.

        Args:
            brand_name: Name of the brand
            raw_data: Raw scraped data
            categorization: Brand categorization
            relationships: Brand relationships

        Returns:
            Complete product catalog
        """
        # Try LLM-based extraction first
        if self.llm.is_available():
            try:
                return self._llm_based_extraction(brand_name, raw_data, categorization)
            except Exception as e:
                logger.error(f"LLM extraction failed: {e}")

        # Fallback: Rule-based extraction
        logger.info("Using rule-based product catalog extraction...")
        return self._rule_based_extraction(brand_name, raw_data, categorization, relationships)

    def _llm_based_extraction(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        categorization: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to extract product catalog from website data.

        Args:
            brand_name: Brand name
            raw_data: Raw scraped data
            categorization: Brand categorization

        Returns:
            Product catalog extracted by LLM
        """
        structured = raw_data.get("structured", {})
        website_info = structured.get("website_info", {})

        # Extract Tavily insights for products
        tavily_data = raw_data.get("scraped_data", {}).get("tavily", {})
        tavily_insights = []

        if tavily_data:
            # Extract AI summaries
            for summary in tavily_data.get("ai_summaries", [])[:2]:
                if summary:
                    tavily_insights.append(summary[:500])

            # Extract relevant product mentions from top results
            for result in tavily_data.get("top_results", [])[:5]:
                content = result.get("content", "")
                if any(keyword in content.lower() for keyword in ["product", "service", "offer", "محصول", "خدمات"]):
                    tavily_insights.append(content[:300])

        # Prepare comprehensive data for LLM
        context = {
            "brand": brand_name,
            "industry": categorization.get("primary_industry", {}).get("name_fa", ""),
            "website_title": website_info.get("title", ""),
            "website_description": website_info.get("meta_description", ""),
            "website_text": website_info.get("text_content", "")[:5000],  # First 5000 chars
            "tavily_intelligence": "\n\n".join(tavily_insights) if tavily_insights else "No additional market intelligence available"
        }

        prompt = f"""Extract COMPLETE and COMPREHENSIVE product/service catalog from ALL available data sources.

Brand: {context['brand']}
Industry: {context['industry']}

=== TAVILY AI MARKET INTELLIGENCE ===
{context['tavily_intelligence']}

=== WEBSITE INFORMATION ===
Title: {context['website_title']}
Description: {context['website_description']}

Content:
{context['website_text']}

CRITICAL REQUIREMENTS:
- Extract AT LEAST 10-15 products/services (more if available)
- Include ALL products/services mentioned in ANY data source
- If exact details are missing, infer based on industry standards
- For each product/service, provide:
  * Product/service name (specific, not generic)
  * Category (organize into logical groups)
  * Description (detailed, 20+ words)
  * Target market (specific demographics)
  * Key features or benefits

Return as structured JSON with this EXACT format:
{{
  "categories": [
    {{
      "category_name": "Category Name",
      "products": [
        {{
          "product_name": "Specific Product Name",
          "description": "Detailed description of the product or service",
          "target_market": "Specific target audience",
          "key_features": ["feature 1", "feature 2"]
        }}
      ]
    }}
  ]
}}

Extract comprehensively - users need rich, detailed product data."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt="You are a product catalog extraction specialist.",
            json_mode=True
        )

        catalog = json.loads(response)
        logger.info(f"[LLM] Extracted {len(catalog.get('products', []))} products")

        return catalog

    def _rule_based_extraction(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        categorization: Dict[str, Any],
        relationships: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rule-based product catalog extraction.

        Args:
            brand_name: Brand name
            raw_data: Raw data
            categorization: Categorization data
            relationships: Relationship data

        Returns:
            Product catalog
        """
        catalog = {
            "extraction_method": "rule_based",
            "total_products": 0,
            "categories": {},
            "products": [],
            "therapeutic_areas": [],
            "product_lines": []
        }

        # Check if comprehensive catalog exists in knowledge base
        catalog_data = self._load_comprehensive_catalog(brand_name)
        if catalog_data:
            logger.info(f"[KB] Loaded comprehensive catalog for {brand_name}")
            return catalog_data

        # Extract from website text
        structured = raw_data.get("structured", {})
        website_info = structured.get("website_info", {})

        # Combine all available text content from scraped data
        text_parts = []
        if website_info.get("content_summary"):
            text_parts.append(str(website_info["content_summary"]))
        if website_info.get("about_us"):
            text_parts.append(str(website_info["about_us"]))
        if website_info.get("meta_description"):
            text_parts.append(str(website_info["meta_description"]))
        if website_info.get("title"):
            text_parts.append(str(website_info["title"]))
        if website_info.get("headings"):
            # Filter only string headings
            for h in website_info["headings"]:
                if isinstance(h, str):
                    text_parts.append(h)

        text_content = " ".join(text_parts).lower()

        logger.info(f"[Rule] Analyzing {len(text_content)} chars of scraped content")

        # Industry-specific extraction
        industry = categorization.get("primary_industry", {}).get("name_en", "")

        if "pharmaceutical" in industry.lower() or "biotech" in industry.lower():
            catalog = self._extract_pharmaceutical_products(text_content, brand_name)
        elif "food" in industry.lower():
            catalog = self._extract_food_products(text_content, brand_name)
        elif "cleaning" in industry.lower():
            catalog = self._extract_cleaning_products(text_content, brand_name)
        elif "healthcare" in industry.lower() or "mental" in industry.lower() or "counseling" in industry.lower():
            catalog = self._extract_healthcare_services(text_content, brand_name, website_info)
        else:
            catalog = self._extract_generic_products(text_content, brand_name)

        logger.info(f"[Rule] Extracted {catalog.get('total_products', 0)} products/services from scraped content")
        return catalog

    def _extract_healthcare_services(self, text: str, brand_name: str, website_info: Dict) -> Dict[str, Any]:
        """Extract healthcare/counseling services from text.

        Args:
            text: Combined text from website
            brand_name: Brand name
            website_info: Website information dict

        Returns:
            Service catalog
        """
        catalog = {
            "extraction_method": "rule_based_healthcare",
            "total_products": 0,
            "categories": {},
            "products": [],
            "services": [],
            "therapeutic_areas": []
        }

        # Service keywords to look for
        service_keywords = {
            "individual_counseling": ["مشاوره فردی", "individual counseling", "personal therapy"],
            "couple_therapy": ["زوج درمانی", "couple therapy", "marriage counseling"],
            "family_counseling": ["مشاوره خانواده", "family counseling", "family therapy"],
            "career_counseling": ["مشاوره شغلی", "career counseling", "career guidance"],
            "educational_counseling": ["مشاوره تحصیلی", "educational counseling", "academic counseling"],
            "child_psychology": ["روانشناسی کودک", "child psychology", "pediatric psychology"],
            "addiction_counseling": ["مشاوره اعتیاد", "addiction counseling", "substance abuse"],
            "stress_management": ["مدیریت استرس", "stress management", "anxiety therapy"],
            "depression_therapy": ["درمان افسردگی", "depression therapy", "depression treatment"],
            "online_counseling": ["مشاوره آنلاین", "online counseling", "teletherapy"]
        }

        services_found = []
        for service_name, keywords in service_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    services_found.append({
                        "name": service_name.replace("_", " ").title(),
                        "name_fa": keywords[0],  # First keyword is usually Persian
                        "category": "Mental Health Services",
                        "type": "service",
                        "availability": "Available"
                    })
                    break

        # Extract number of counselors if mentioned
        import re
        counselor_match = re.search(r'(\d+)[\+\s]*(?:مشاور|متخصص|counselor|specialist)', text)
        if counselor_match:
            num_counselors = counselor_match.group(1)
            catalog["metadata"] = {"total_counselors": num_counselors}

        # Extract specialization areas if mentioned
        specialty_match = re.search(r'(\d+)[\s]*(?:حوزه|حوزه تخصصی|specialized area|field)', text)
        if specialty_match:
            num_specialties = specialty_match.group(1)
            if "metadata" not in catalog:
                catalog["metadata"] = {}
            catalog["metadata"]["specialization_areas"] = num_specialties

        catalog["services"] = services_found
        catalog["total_products"] = len(services_found)
        catalog["categories"]["Mental Health Services"] = len(services_found)

        return catalog

    def _load_comprehensive_catalog(self, brand_name: str) -> Dict[str, Any]:
        """Load comprehensive catalog from knowledge base.

        Args:
            brand_name: Brand name

        Returns:
            Catalog data or empty dict
        """
        try:
            # Try loading brand-specific catalog ONLY if brand name matches
            catalog_files = [
                (f"data/cinnagen_complete_catalog.json", ["cinnagen", "orchid"]),
                (f"data/golrang_complete_catalog.json", ["golrang", "golha", "kalleh", "tak"]),
                (f"data/{brand_name.lower()}_catalog.json", [brand_name.lower()])
            ]

            brand_lower = brand_name.lower().replace("_", " ")

            for file_path, brand_keywords in catalog_files:
                # Only load if brand name matches keywords
                should_load = any(keyword in brand_lower for keyword in brand_keywords)

                if not should_load:
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Search for brand in catalog
                    for group_key, group_data in data.items():
                        if "complete_product_catalog" in group_data:
                            logger.info(f"[KB] Loading catalog from {file_path}")
                            return self._format_catalog_from_kb(group_data)

                except FileNotFoundError:
                    continue

        except Exception as e:
            logger.error(f"Error loading catalog: {e}")

        return {}

    def _format_catalog_from_kb(self, group_data: Dict) -> Dict[str, Any]:
        """Format catalog data from knowledge base.

        Args:
            group_data: Group data from knowledge base

        Returns:
            Formatted catalog
        """
        catalog = group_data.get("complete_product_catalog", {})

        total_products = 0
        therapeutic_areas = []
        all_products = []

        for area_key, area_data in catalog.items():
            if isinstance(area_data, dict) and "products" in area_data:
                products = area_data["products"]
                total_products += len(products)
                therapeutic_areas.append(area_data.get("therapeutic_area", area_key))
                all_products.extend(products)

        return {
            "extraction_method": "knowledge_base",
            "total_products": total_products,
            "therapeutic_areas": therapeutic_areas,
            "categories": catalog,
            "products": all_products,
            "market_intelligence": group_data.get("market_intelligence", {}),
            "product_statistics": group_data.get("product_statistics", {})
        }

    def _extract_pharmaceutical_products(self, text: str, brand_name: str) -> Dict[str, Any]:
        """Extract pharmaceutical products from text.

        Args:
            text: Text content
            brand_name: Brand name

        Returns:
            Product catalog
        """
        # Common pharmaceutical keywords
        pharma_keywords = {
            "oncology": ["cancer", "tumor", "lymphoma", "leukemia", "سرطان", "تومور"],
            "cardiology": ["heart", "cardiac", "قلب", "قلبی"],
            "immunology": ["immune", "arthritis", "ایمنی", "روماتیسم"],
            "neurology": ["neuro", "brain", "مغز", "عصبی"],
            "endocrinology": ["diabetes", "insulin", "دیابت", "انسولین"]
        }

        catalog = {
            "extraction_method": "rule_based_pharmaceutical",
            "total_products": 0,
            "therapeutic_areas": [],
            "products": []
        }

        # Detect therapeutic areas
        for area, keywords in pharma_keywords.items():
            if any(kw in text for kw in keywords):
                catalog["therapeutic_areas"].append(area)

        catalog["total_products"] = len(catalog["therapeutic_areas"])

        return catalog

    def _extract_food_products(self, text: str, brand_name: str) -> Dict[str, Any]:
        """Extract food products."""
        return {
            "extraction_method": "rule_based_food",
            "total_products": 0,
            "categories": ["food"],
            "products": []
        }

    def _extract_cleaning_products(self, text: str, brand_name: str) -> Dict[str, Any]:
        """Extract cleaning products."""
        return {
            "extraction_method": "rule_based_cleaning",
            "total_products": 0,
            "categories": ["cleaning"],
            "products": []
        }

    def _extract_generic_products(self, text: str, brand_name: str) -> Dict[str, Any]:
        """Extract generic products."""
        return {
            "extraction_method": "rule_based_generic",
            "total_products": 0,
            "products": []
        }
