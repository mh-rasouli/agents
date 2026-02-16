"""Categorization agent - classifies industries, products, and market positioning."""

import json
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import BrandIntelligenceState
from config.prompts import CATEGORIZATION_PROMPT
from utils.logger import get_logger

logger = get_logger(__name__)


class CategorizationAgent(BaseAgent):
    """Agent responsible for categorizing brands across multiple dimensions."""

    def __init__(self):
        """Initialize the categorization agent."""
        super().__init__("CategorizationAgent")

    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Categorize the brand across multiple dimensions.

        Args:
            state: Current workflow state

        Returns:
            Updated state with categorization populated
        """
        self._log_start()

        brand_name = state["brand_name"]
        raw_data = state.get("raw_data", {})
        relationships = state.get("relationships", {})

        # Check if we have data to analyze
        if not raw_data or not raw_data.get("structured"):
            logger.warning("No data available for categorization")
            self._add_error(state, "No data available for categorization")
            state["categorization"] = {}
            self._log_end(success=False)
            return state

        # Perform categorization using LLM
        categorization = self._categorize_brand(brand_name, raw_data, relationships)

        # Update state
        state["categorization"] = categorization

        self._log_end(success=True)
        return state

    def _categorize_brand(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        relationships: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Categorize brand using LLM or rule-based fallback.

        Args:
            brand_name: Name of the brand
            raw_data: Raw and structured data
            relationships: Relationship data

        Returns:
            Dictionary containing categorization data
        """
        # Try LLM if available
        if self.llm.is_available():
            try:
                # Prepare data for categorization
                analysis_input = self._prepare_categorization_data(
                    brand_name,
                    raw_data,
                    relationships
                )

                logger.info("Categorizing brand using LLM...")

                # Use LLM to categorize
                prompt = f"""Analyze the following brand data and provide comprehensive categorization.

Brand: {brand_name}

{analysis_input}

{CATEGORIZATION_PROMPT}"""

                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt="You are an industry categorization specialist for Iranian brands.",
                    json_mode=True
                )

                categorization = json.loads(response)
                logger.info("[OK] Successfully categorized brand")

                # Log key categorizations
                if categorization.get("primary_industry"):
                    logger.info(f"  Industry: {categorization['primary_industry'].get('name_fa', 'N/A')}")

                if categorization.get("business_model"):
                    logger.info(f"  Model: {categorization['business_model']}")

                if categorization.get("price_tier"):
                    logger.info(f"  Tier: {categorization['price_tier']}")

                return categorization

            except Exception as e:
                logger.error(f"LLM categorization failed: {e}")

        # Fallback: Rule-based categorization
        logger.info("Using rule-based categorization...")
        return self._rule_based_categorization(brand_name, raw_data, relationships)

    def _rule_based_categorization(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        relationships: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rule-based categorization using keywords and patterns.

        Args:
            brand_name: Name of the brand
            raw_data: Raw and structured data
            relationships: Relationship data

        Returns:
            Categorization data
        """
        categorization = {
            "primary_industry": {},
            "sub_industries": [],
            "product_categories": [],
            "business_model": "B2C",
            "price_tier": "mid",
            "target_audiences": [],
            "distribution_channels": [],
            "market_position": {}
        }

        # PRIORITY 1: Check if we have category from knowledge base via relationships
        sister_brands = relationships.get("sister_brands", [])
        if sister_brands:
            # Use category from first sister brand (they share same parent, likely same industry)
            for sister in sister_brands:
                if sister.get("industry_category"):
                    categorization["primary_industry"] = sister["industry_category"]
                    categorization["business_model"] = sister.get("business_model", "B2C")
                    logger.info(f"[Rule] Using category from knowledge base: {sister['industry_category'].get('name_en', 'N/A')}")
                    return categorization

        # Check parent company for industry info
        parent = relationships.get("parent_company", {})
        if parent.get("industry"):
            # Map industry string to category structure
            industry_name = parent.get("industry", "")
            if "Healthcare" in industry_name or "Mental" in industry_name:
                categorization["primary_industry"] = {
                    "name_en": "Healthcare_&_Medical_Services",
                    "name_fa": "خدمات بهداشت و درمان",
                    "isic_code": "8690",
                    "category_level_1": "Healthcare_Services",
                    "category_level_2": "Mental_Health_Services",
                    "category_level_3": "Online_Counseling_Platforms"
                }
                categorization["business_model"] = "B2C"
                logger.info(f"[Rule] Using category from parent company: Healthcare Services")
                return categorization

        # PRIORITY 2: Keyword-based matching from website content
        # Extract website description and title
        structured = raw_data.get("structured", {})
        website_info = structured.get("website_info") or {}
        title = (website_info.get("title") or "").lower()
        description = (website_info.get("meta_description") or "").lower()
        brand_lower = (brand_name or "").lower()

        # Combine text for keyword matching
        combined_text = f"{title} {description} {brand_lower}"

        # Industry classification based on keywords (English-only with underscores)
        industry_keywords = {
            "ride_hailing": {
                "keywords": ["تاکسی", "taxi", "ride", "snapp", "tap30"],
                "industry": {"name_en": "Transportation_&_Mobility", "category_l1": "Technology_Services", "category_l2": "On-Demand_Platforms", "category_l3": "Ride-Hailing", "isic_code": "4931"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "food_delivery": {
                "keywords": ["سفارش غذا", "food delivery", "restaurant", "snappfood"],
                "industry": {"name_en": "Food_Delivery_Services", "category_l1": "Technology_Services", "category_l2": "On-Demand_Platforms", "category_l3": "Food_Delivery", "isic_code": "5610"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "insurance_technology": {
                "keywords": ["بیمه", "insurance", "bimeh"],
                "industry": {"name_en": "Insurance_Technology", "category_l1": "Financial_Services", "category_l2": "Insurance", "category_l3": "Health_&_Auto_Insurance", "isic_code": "6512"},
                "business_model": "B2C",
                "price_tier": "varied"
            },
            "fintech_payments": {
                "keywords": ["پرداخت", "payment", "wallet", "کیف پول", "pay"],
                "industry": {"name_en": "Financial_Technology", "category_l1": "Financial_Services", "category_l2": "Fintech", "category_l3": "Digital_Payments", "isic_code": "6419"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "telemedicine": {
                "keywords": ["دکتر", "doctor", "مشاوره پزشکی", "medical consultation"],
                "industry": {"name_en": "Healthcare_Technology", "category_l1": "Healthcare_&_Life_Sciences", "category_l2": "Digital_Health", "category_l3": "Telemedicine", "isic_code": "8610"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "mental_health_counseling": {
                "keywords": ["مشاوره روانشناسی", "مشاوره", "روانشناس", "روانشناسی", "سلامت روان", "counseling", "psychologist", "psychology", "mental health", "therapy", "therapist"],
                "industry": {"name_en": "Healthcare_&_Medical_Services", "name_fa": "خدمات بهداشت و درمان", "category_l1": "Healthcare_Services", "category_l2": "Mental_Health_Services", "category_l3": "Online_Counseling_Platforms", "isic_code": "8690"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "travel_technology": {
                "keywords": ["سفر", "travel", "هتل", "hotel", "flight", "پرواز"],
                "industry": {"name_en": "Travel_Technology", "category_l1": "Technology_Services", "category_l2": "Travel_&_Hospitality", "category_l3": "Online_Travel_Booking", "isic_code": "7911"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "logistics_delivery": {
                "keywords": ["ارسال", "delivery", "logistics", "لجستیک", "box", "باکس"],
                "industry": {"name_en": "Logistics_&_Delivery", "category_l1": "Transportation_&_Logistics", "category_l2": "Last-Mile_Delivery", "category_l3": "Package_Delivery", "isic_code": "5320"},
                "business_model": "B2B_and_B2C",
                "price_tier": "mid"
            },
            "online_grocery": {
                "keywords": ["سوپرمارکت", "supermarket", "grocery", "مواد غذایی", "market"],
                "industry": {"name_en": "E-Commerce_Grocery", "category_l1": "Consumer_Services", "category_l2": "E-Commerce", "category_l3": "Online_Grocery", "isic_code": "4711"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "cleaning_products": {
                "keywords": ["ظرفشویی", "شوینده", "تاژ", "تمیزکننده", "dishwashing", "cleaner", "detergent", "tage"],
                "industry": {"name_en": "Cleaning_Products", "category_l1": "Consumer_Goods", "category_l2": "Home_Care", "category_l3": "Dishwashing_&_Surface_Cleaners", "isic_code": "2023"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "laundry_care": {
                "keywords": ["لباسشویی", "laundry", "persil", "پرسیل"],
                "industry": {"name_en": "Laundry_Care", "category_l1": "Consumer_Goods", "category_l2": "Home_Care", "category_l3": "Laundry_Detergents", "isic_code": "2023"},
                "business_model": "B2C",
                "price_tier": "mid_to_premium"
            },
            "confectionery_macaron": {
                "keywords": ["ماکارون", "شیرینی", "بیسکویت", "macaron", "بیسکویت", "کوکی", "cookie", "زر", "zar"],
                "industry": {"name_en": "Confectionery_&_Biscuits", "category_l1": "Food_&_Beverage", "category_l2": "Sweet_Snacks", "category_l3": "Macarons_&_Cookies", "isic_code": "1073"},
                "business_model": "B2C",
                "price_tier": "economy_to_mid"
            },
            "chocolate_manufacturing": {
                "keywords": ["شکلات", "chocolate"],
                "industry": {"name_en": "Chocolate_Manufacturing", "category_l1": "Food_&_Beverage", "category_l2": "Sweet_Snacks", "category_l3": "Chocolate_Products", "isic_code": "1082"},
                "business_model": "B2C",
                "price_tier": "mid"
            },
            "pharmaceutical_biotech": {
                "keywords": ["دارو", "داروسازی", "بیوتکنولوژی", "زیست", "سلول", "pharma", "biotech", "medicine", "drug", "biopharmaceutical", "orchid", "cinnagen"],
                "industry": {"name_en": "Pharmaceutical_&_Biotechnology", "category_l1": "Healthcare_&_Life_Sciences", "category_l2": "Biopharmaceuticals", "category_l3": "Biosimilar_Drugs", "isic_code": "2100"},
                "business_model": "B2B_and_B2C",
                "price_tier": "premium"
            },
            "industrial_manufacturing": {
                "keywords": ["صنعتی", "تولید", "manufacturing", "industrial"],
                "industry": {"name_en": "Industrial_Manufacturing", "category_l1": "Manufacturing", "category_l2": "General_Manufacturing", "category_l3": "Industrial_Products", "isic_code": "2500"},
                "business_model": "B2B",
                "price_tier": "mid"
            }
        }

        # Match industry
        for industry_key, industry_data in industry_keywords.items():
            for keyword in industry_data["keywords"]:
                if keyword in combined_text:
                    industry_info = industry_data["industry"]
                    categorization["primary_industry"] = {
                        "name_en": industry_info.get("name_en", "Unknown"),
                        "name_fa": "",  # Empty per user request (English-only)
                        "isic_code": industry_info.get("isic_code", ""),
                        "category_level_1": industry_info.get("category_l1", "Unknown"),
                        "category_level_2": industry_info.get("category_l2", "Unknown"),
                        "category_level_3": industry_info.get("category_l3", "Unknown")
                    }
                    categorization["business_model"] = industry_data["business_model"]
                    categorization["price_tier"] = industry_data["price_tier"]
                    logger.info(f"[Rule] دسته‌بندی: {industry_key}")
                    logger.info(f"[Rule] Levels: {industry_info.get('category_l1')} → {industry_info.get('category_l2')} → {industry_info.get('category_l3')}")
                    break
            if categorization["primary_industry"]:
                break

        # Use parent company industry if available
        if not categorization["primary_industry"] and relationships.get("parent_company"):
            parent_industry = relationships["parent_company"].get("industry")
            if parent_industry:
                categorization["primary_industry"] = {
                    "name_en": parent_industry,
                    "name_fa": parent_industry,
                    "source": "parent_company"
                }
                logger.info(f"[Rule] Used parent industry: {parent_industry}")

        # Determine target audience based on text
        audience_keywords = {
            "families": ["خانواده", "کودک", "family", "kids"],
            "urban_professionals": ["شهری", "شاغل", "آنلاین", "urban", "professional"],
            "women": ["بانوان", "زنان", "women"],
            "youth": ["جوان", "نوجوان", "youth", "teen"]
        }

        for audience, keywords in audience_keywords.items():
            if any(kw in combined_text for kw in keywords):
                categorization["target_audiences"].append(audience)

        if not categorization["target_audiences"]:
            categorization["target_audiences"] = ["general_public"]

        # Distribution channels
        if "آنلاین" in combined_text or "online" in combined_text:
            categorization["distribution_channels"].append("online")
        if "فروشگاه" in combined_text or "store" in combined_text:
            categorization["distribution_channels"].append("retail")
        if not categorization["distribution_channels"]:
            categorization["distribution_channels"] = ["retail", "online"]

        # Market position
        categorization["market_position"] = {
            "positioning": "unknown",
            "estimated_market_share": "unknown",
            "competitive_landscape": "competitive"
        }

        logger.info(f"[Rule] Categorization complete")
        return categorization

    def _prepare_categorization_data(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        relationships: Dict[str, Any]
    ) -> str:
        """Prepare data for categorization analysis.

        Args:
            brand_name: Name of the brand
            raw_data: Raw data from scrapers
            relationships: Relationship data

        Returns:
            Formatted string for LLM input
        """
        lines = []

        # Add structured data
        structured = raw_data.get("structured", {})
        if structured:
            lines.append("=== BRAND INFORMATION ===")
            lines.append(json.dumps(structured, ensure_ascii=False, indent=2))

        # Add relationship context
        if relationships:
            lines.append("\n=== CORPORATE RELATIONSHIPS ===")
            lines.append(json.dumps(relationships, ensure_ascii=False, indent=2))

        # Add social media data (useful for understanding audience)
        scraped = raw_data.get("scraped", {})
        if scraped.get("linka"):
            lines.append("\n=== SOCIAL MEDIA DATA ===")
            lines.append(json.dumps(scraped["linka"], ensure_ascii=False, indent=2))

        # Add financial data (helps determine price tier and market position)
        if scraped.get("codal"):
            lines.append("\n=== FINANCIAL DATA ===")
            lines.append(json.dumps(scraped["codal"], ensure_ascii=False, indent=2))

        # Add website data (useful for understanding products/services)
        if scraped.get("web_search"):
            lines.append("\n=== WEBSITE DATA ===")
            web_data = {k: v for k, v in scraped["web_search"].items()
                       if k not in ["raw_html"]}
            lines.append(json.dumps(web_data, ensure_ascii=False, indent=2))

        return "\n".join(lines)
