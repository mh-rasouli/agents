"""Relationship mapping agent - analyzes corporate structure and brand relationships."""

import json
from pathlib import Path
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from models.state import BrandIntelligenceState
from config.prompts import RELATIONSHIP_MAPPING_PROMPT
from models.output_models import RelationshipsOutput
from utils.logger import get_logger
from utils.helpers import load_json

logger = get_logger(__name__)


class RelationshipMappingAgent(BaseAgent):
    """Agent responsible for mapping brand relationships and corporate structure."""

    def __init__(self):
        """Initialize the relationship mapping agent."""
        super().__init__("RelationshipMappingAgent")

        # Load all knowledge bases
        self.knowledge_bases = {}

        knowledge_base_files = [
            ("golrang_brands_database.json", "golrang"),
            ("cinnagen_complete_catalog.json", "cinnagen"),
            ("snapp_group_complete.json", "snapp"),
            ("henkel_group_iran.json", "henkel"),
            ("zar_group_complete.json", "zar"),
            ("iran_novin_group.json", "iran_novin"),
            ("artin_pouya_pardaz_group.json", "artin_pouya_pardaz")
        ]

        for filename, key in knowledge_base_files:
            db_path = Path(f"data/{filename}")
            if db_path.exists():
                self.knowledge_bases[key] = load_json(db_path)
                logger.info(f"Loaded {key} knowledge base")
            else:
                logger.warning(f"{key} knowledge base not found")

        # Maintain backward compatibility
        self.golrang_db = self.knowledge_bases.get("golrang")

    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Analyze and map brand relationships.

        Args:
            state: Current workflow state

        Returns:
            Updated state with relationships populated
        """
        self._log_start()

        brand_name = state["brand_name"]
        parent_company = state.get("parent_company")  # Get parent company from user
        raw_data = state.get("raw_data", {})

        # Log parent company if provided
        if parent_company:
            logger.info(f"User-provided parent company: {parent_company}")

        # Check if we have data to analyze
        if not raw_data or not raw_data.get("structured"):
            logger.warning("No data available for relationship mapping")
            self._add_error(state, "No data available for relationship analysis")
            state["relationships"] = {}
            self._log_end(success=False)
            return state

        # Analyze relationships using LLM
        relationships = self._analyze_relationships(brand_name, raw_data, parent_company)

        # Update state (validated)
        self._validate_and_store(state, "relationships", relationships, RelationshipsOutput)

        self._log_end(success=True)
        return state

    def _analyze_relationships(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        parent_company: str = None
    ) -> Dict[str, Any]:
        """Analyze brand relationships using LLM or rule-based fallback.

        Args:
            brand_name: Name of the brand
            raw_data: Raw and structured data from previous agent
            parent_company: User-provided parent company name

        Returns:
            Dictionary containing relationship mappings
        """
        # Try LLM if available
        if self.llm.is_available():
            try:
                # Prepare data for analysis
                analysis_input = self._prepare_relationship_data(brand_name, raw_data)

                logger.info("Analyzing brand relationships using LLM...")

                # Use LLM to map relationships
                prompt_text = f"""Analyze the following brand data and identify corporate relationships.

Brand: {brand_name}"""

                if parent_company:
                    prompt_text += f"\nUser-Provided Parent Company: {parent_company}"

                prompt_text += f"""

{analysis_input}

{RELATIONSHIP_MAPPING_PROMPT}"""

                response = self.llm.generate(
                    prompt=prompt_text,
                    system_prompt="You are a corporate relationship analyst.",
                    json_mode=True
                )

                relationships = json.loads(response)
                logger.info("[OK] Successfully mapped brand relationships")

                # Log key findings
                if relationships.get("parent_company", {}).get("name"):
                    logger.info(f"  Parent company: {relationships['parent_company']['name']}")

                if relationships.get("subsidiaries"):
                    logger.info(f"  Subsidiaries: {len(relationships['subsidiaries'])}")

                if relationships.get("sister_brands"):
                    logger.info(f"  Sister brands: {len(relationships['sister_brands'])}")

                return relationships

            except Exception as e:
                logger.error(f"LLM relationship mapping failed: {e}")

        # Fallback: Rule-based relationship mapping
        logger.info("Using rule-based relationship mapping...")
        return self._rule_based_relationship_mapping(brand_name, raw_data, parent_company)

    def _rule_based_relationship_mapping(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        parent_company: str = None
    ) -> Dict[str, Any]:
        """Rule-based relationship mapping using database and scraped data.

        Args:
            brand_name: Name of the brand
            raw_data: Raw and structured data
            parent_company: User-provided parent company name

        Returns:
            Relationship mappings
        """
        relationships = {
            "parent_company": {},
            "ultimate_parent": {},
            "subsidiaries": [],
            "sister_brands": [],
            "shareholders": [],
            "affiliates": [],
            "brand_family": [],
            "competitors": [],
            "similar_brands": [],
            "complementary_brands": [],
            "parent_company_verification": {}
        }

        # Try knowledge base search first (priority)
        kb_result = self._search_all_knowledge_bases(brand_name, parent_company)

        if kb_result:
            relationships.update(kb_result)
            return relationships

        # Fallback to old Golrang/CinnaGen logic for backward compatibility
        if self.golrang_db:
            # List of corporate groups to check
            corporate_groups = [
                ("golrang_industrial_group", "Golrang Industrial Group", "گروه صنعتی گلرنگ"),
                ("cinnagen_biotech_group_complete", "CinnaGen Biotech Group", "گروه بیوتکنولوژی سیناژن")
            ]

            for group_key, group_name_en, group_name_fa in corporate_groups:
                group_data = self.golrang_db.get(group_key, {})

                if not group_data:
                    continue

                # Search for brand in this group's subsidiaries
                for subsidiary in group_data.get("subsidiaries", []):
                    for brand in subsidiary.get("brands", []):
                        # Match by brand name (case-insensitive, flexible)
                        if self._brand_name_matches(brand_name, brand.get("name", "")):
                            logger.info(f"[DB] Found {brand_name} in {group_key} database")

                            # Set parent company
                            relationships["parent_company"] = {
                                "name": subsidiary.get("company"),
                                "name_fa": subsidiary.get("company"),
                                "stock_symbol": subsidiary.get("stock_symbol"),
                                "industry": subsidiary.get("industry"),
                                "relation_type": "direct_parent"
                            }

                            # Set ultimate parent
                            relationships["ultimate_parent"] = {
                                "name": group_name_en,
                                "name_fa": group_name_fa,
                                "stock_symbol": group_data.get("stock_symbol"),
                                "description": group_data.get("description"),
                                "market_cap": group_data.get("market_cap_estimate"),
                                "total_brands": group_data.get("total_brands"),
                                "employees": group_data.get("employees")
                            }

                            # Get sister brands from same parent company
                            sister_brands = []
                            for sibling in subsidiary.get("brands", []):
                                if not self._brand_name_matches(brand_name, sibling.get("name", "")):
                                    sister_brands.append({
                                        "name": sibling.get("name"),
                                        "products": sibling.get("products"),
                                        "category": sibling.get("category"),
                                        "price_tier": sibling.get("price_tier"),
                                        "target_audience": sibling.get("target"),
                                        "relation": "same_parent",
                                        "synergy_score": self._calculate_synergy(brand, sibling)
                                    })

                            relationships["sister_brands"] = sister_brands

                            # Get all brands in this group for brand family
                            all_group_brands = []
                            for sub in group_data.get("subsidiaries", []):
                                for b in sub.get("brands", []):
                                    if not self._brand_name_matches(brand_name, b.get("name", "")):
                                        all_group_brands.append({
                                            "name": b.get("name"),
                                            "parent": sub.get("company"),
                                            "category": b.get("category"),
                                            "relation": f"{group_key}_family"
                                        })

                            relationships["brand_family"] = all_group_brands[:20]  # Limit to 20

                            logger.info(f"[DB] Found {len(sister_brands)} sister brands")
                            logger.info(f"[DB] {group_name_en} family: {len(all_group_brands)} total brands")

                            return relationships

        # If not in Golrang DB, try to extract from scraped data
        scraped = raw_data.get("scraped", {})

        # Check rasmio data for parent company
        if scraped.get("rasmio") and scraped["rasmio"].get("company_name"):
            relationships["parent_company"] = {
                "name": scraped["rasmio"].get("company_name"),
                "registration_number": scraped["rasmio"].get("registration_number"),
                "ceo": scraped["rasmio"].get("ceo_name"),
                "source": "rasmio"
            }
            logger.info(f"[Rasmio] Parent company: {relationships['parent_company']['name']}")

        # Check tsetmc data for shareholders
        if scraped.get("tsetmc"):
            tsetmc_data = scraped["tsetmc"]
            if tsetmc_data.get("company_name"):
                if not relationships["parent_company"]:
                    relationships["parent_company"] = {
                        "name": tsetmc_data.get("company_name"),
                        "stock_symbol": tsetmc_data.get("stock_symbol"),
                        "source": "tsetmc"
                    }

        logger.info("[Rule-based] Completed relationship mapping")
        return relationships

    def _search_all_knowledge_bases(
        self,
        brand_name: str,
        user_provided_parent: str = None
    ) -> Dict[str, Any]:
        """Search all knowledge bases for brand information.

        Args:
            brand_name: Brand name to search for
            user_provided_parent: Parent company name provided by user

        Returns:
            Relationship data if found, None otherwise
        """
        # Knowledge base configurations
        kb_configs = [
            ("snapp", "snapp_group_complete", "Snapp Group", "گروه اسنپ"),
            ("henkel", "henkel_group_iran", "Henkel AG & Co.", "هنکل"),
            ("zar", "zar_group_complete", "Zar Industrial Group", "گروه صنعتی زر"),
            ("iran_novin", "iran_novin_group", "Iran Novin Industrial Group", "گروه صنعتی ایران نوین"),
            ("cinnagen", "cinnagen_biotech_group_complete", "CinnaGen Biotech Group", "گروه بیوتکنولوژی سیناژن"),
            ("golrang", "golrang_industrial_group", "Golrang Industrial Group", "گروه صنعتی گلرنگ"),
            ("artin_pouya_pardaz", "artin_pouya_pardaz_group", "Artin Pouya Pardaz", "آرتین پویا پرداز")
        ]

        for kb_key, group_key, group_name_en, group_name_fa in kb_configs:
            if kb_key not in self.knowledge_bases:
                continue

            kb_data = self.knowledge_bases[kb_key]
            group_data = kb_data.get(group_key, {})

            if not group_data:
                continue

            # Search in subsidiaries
            result = self._search_group_subsidiaries(
                group_data,
                brand_name,
                group_key,
                group_name_en,
                group_name_fa,
                user_provided_parent
            )

            if result:
                return result

        return None

    def _search_group_subsidiaries(
        self,
        group_data: Dict,
        brand_name: str,
        group_key: str,
        group_name_en: str,
        group_name_fa: str,
        user_provided_parent: str = None
    ) -> Dict[str, Any]:
        """Search for brand in group subsidiaries.

        Args:
            group_data: Group data from knowledge base
            brand_name: Brand to search for
            group_key: Knowledge base group key
            group_name_en: Group name in English
            group_name_fa: Group name in Persian
            user_provided_parent: Parent company provided by user

        Returns:
            Relationship data if found, None otherwise
        """
        relationships = {
            "parent_company": {},
            "ultimate_parent": {},
            "subsidiaries": [],
            "sister_brands": [],
            "shareholders": [],
            "affiliates": [],
            "brand_family": [],
            "competitors": [],
            "similar_brands": [],
            "complementary_brands": [],
            "parent_company_verification": {}
        }

        # Get corporate structure
        corporate_structure = group_data.get("corporate_structure", {})
        ultimate_parent = corporate_structure.get("ultimate_parent", {})
        subsidiaries_section = corporate_structure.get("subsidiaries", {})

        # Search all subsidiary categories
        for category_key, category_brands in subsidiaries_section.items():
            if not isinstance(category_brands, list):
                continue

            for subsidiary in category_brands:
                company_name = subsidiary.get("company", "")
                company_name_fa = subsidiary.get("name_fa", "")

                # Check if THIS is the brand we're looking for
                if self._brand_name_matches(brand_name, company_name) or \
                   self._brand_name_matches(brand_name, company_name_fa):

                    logger.info(f"[KB] پیدا شد {brand_name} در پایگاه دانش {group_key}")

                    # Set ultimate parent (the group)
                    relationships["ultimate_parent"] = {
                        "name": ultimate_parent.get("name", group_name_en),
                        "name_fa": ultimate_parent.get("name_fa", group_name_fa),
                        "brand_name": ultimate_parent.get("brand_name", ""),
                        "established": ultimate_parent.get("established", ""),
                        "headquarters": ultimate_parent.get("headquarters", ""),
                        "employees": ultimate_parent.get("employees", ""),
                        "description": ultimate_parent.get("description", ""),
                        "description_en": ultimate_parent.get("description_en", ""),
                        "website": ultimate_parent.get("website", ""),
                        "market_cap": ultimate_parent.get("market_cap", ""),
                        "source": "knowledge_base"
                    }

                    # Set parent company (might be same as ultimate parent or a subsidiary)
                    relationships["parent_company"] = {
                        "name": ultimate_parent.get("name", group_name_en),
                        "name_fa": ultimate_parent.get("name_fa", group_name_fa),
                        "industry": subsidiary.get("industry", ""),
                        "relation_type": "direct_parent",
                        "source": "knowledge_base"
                    }

                    # Verify against user-provided parent
                    if user_provided_parent:
                        found_parent_name = ultimate_parent.get("name", group_name_en)
                        if not self._parent_name_matches(user_provided_parent, found_parent_name):
                            warning_msg = f"⚠️ PARENT MISMATCH: کاربر گفت '{user_provided_parent}' ولی سیستم پیدا کرد '{found_parent_name}'"
                            logger.warning(warning_msg)
                            relationships["parent_company_verification"] = {
                                "status": "MISMATCH",
                                "user_provided": user_provided_parent,
                                "system_found": found_parent_name,
                                "warning": warning_msg,
                                "corrected_to": found_parent_name
                            }
                            # Use the system-found parent (corrected)
                        else:
                            relationships["parent_company_verification"] = {
                                "status": "VERIFIED",
                                "user_provided": user_provided_parent,
                                "system_found": found_parent_name,
                                "message": "✓ تطابق دارد"
                            }

                    # Collect ALL sister brands from the same group
                    sister_brands = []
                    for cat_key, cat_list in subsidiaries_section.items():
                        if not isinstance(cat_list, list):
                            continue
                        for sibling in cat_list:
                            sibling_name = sibling.get("company", "")
                            sibling_name_fa = sibling.get("name_fa", "")

                            # Skip the brand itself
                            if self._brand_name_matches(brand_name, sibling_name) or \
                               self._brand_name_matches(brand_name, sibling_name_fa):
                                continue

                            # Add full sister brand information
                            sister_brands.append({
                                "name": sibling_name,
                                "name_fa": sibling_name_fa,
                                "role": sibling.get("role", ""),
                                "established": sibling.get("established", ""),
                                "website": sibling.get("website", ""),
                                "focus": sibling.get("focus", ""),
                                "focus_fa": sibling.get("focus_fa", ""),
                                "industry": sibling.get("industry", ""),
                                "business_model": sibling.get("business_model", ""),
                                "description": sibling.get("description", ""),
                                "description_en": sibling.get("description_en", ""),
                                "market_position": sibling.get("market_position", ""),
                                "relation": "sister_brand",
                                "parent": group_name_en,
                                "category": cat_key,
                                "synergy_potential": "high" if self._is_high_synergy(subsidiary, sibling) else "medium"
                            })

                    relationships["sister_brands"] = sister_brands

                    # Add cross-promotion opportunities if available
                    cross_promo = group_data.get("cross_promotion_opportunities", {})
                    if cross_promo:
                        relationships["cross_promotion_opportunities"] = cross_promo

                    # Add market intelligence
                    market_intel = group_data.get("market_intelligence", {})
                    if market_intel:
                        relationships["market_intelligence"] = market_intel

                    logger.info(f"[KB] پیدا شد {len(sister_brands)} شرکت خواهر")
                    logger.info(f"[KB] گروه {group_name_fa}: {len(sister_brands)} برند مرتبط")

                    return relationships

        return None

    def _parent_name_matches(self, name1: str, name2: str) -> bool:
        """Check if two parent company names match (flexible).

        Args:
            name1: First parent name
            name2: Second parent name

        Returns:
            True if names likely refer to same company
        """
        if not name1 or not name2:
            return False

        # Normalize
        n1 = name1.lower().replace("_", " ").replace("-", " ").strip()
        n2 = name2.lower().replace("_", " ").replace("-", " ").strip()

        # Direct match
        if n1 == n2:
            return True

        # Check if one contains the other (for cases like "Henkel" vs "Henkel AG & Co")
        if n1 in n2 or n2 in n1:
            return True

        # Check key parts (split by spaces and check overlap)
        parts1 = set(n1.split())
        parts2 = set(n2.split())

        # If 50%+ of significant words overlap
        common = parts1 & parts2
        if len(common) >= max(len(parts1), len(parts2)) * 0.5:
            return True

        return False

    def _is_high_synergy(self, brand1: Dict, brand2: Dict) -> bool:
        """Check if two brands have high synergy potential.

        Args:
            brand1: First brand data
            brand2: Second brand data

        Returns:
            True if high synergy
        """
        # Same business model = higher synergy
        if brand1.get("business_model") == brand2.get("business_model"):
            return True

        # Both B2C = high synergy
        if "B2C" in str(brand1.get("business_model", "")) and \
           "B2C" in str(brand2.get("business_model", "")):
            return True

        return False

    def _brand_name_matches(self, name1: str, name2: str) -> bool:
        """Check if two brand names match (flexible matching).

        Args:
            name1: First brand name
            name2: Second brand name

        Returns:
            True if names match
        """
        # Normalize: lowercase, remove spaces
        n1 = name1.lower().replace(" ", "").replace("-", "")
        n2 = name2.lower().replace(" ", "").replace("-", "")

        return n1 == n2 or n1 in n2 or n2 in n1

    def _calculate_synergy(self, brand1: Dict, brand2: Dict) -> str:
        """Calculate cross-promotion synergy between two brands.

        Args:
            brand1: First brand data
            brand2: Second brand data

        Returns:
            Synergy level: VERY_HIGH, HIGH, MEDIUM, LOW
        """
        # Same category = very high synergy
        if brand1.get("category") == brand2.get("category"):
            return "VERY_HIGH"

        # Same price tier = high synergy
        if brand1.get("price_tier") == brand2.get("price_tier"):
            return "HIGH"

        # Related categories
        related_categories = {
            "cleaning_products": ["laundry", "dishwashing", "services"],
            "laundry": ["cleaning_products", "dishwashing"],
            "services": ["cleaning_products"]
        }

        cat1 = brand1.get("category")
        cat2 = brand2.get("category")

        if cat2 in related_categories.get(cat1, []):
            return "HIGH"

        return "MEDIUM"

    def _prepare_relationship_data(
        self,
        brand_name: str,
        raw_data: Dict[str, Any]
    ) -> str:
        """Prepare data for relationship analysis.

        Args:
            brand_name: Name of the brand
            raw_data: Raw data from scrapers

        Returns:
            Formatted string for LLM input
        """
        lines = []

        # Add structured data
        structured = raw_data.get("structured", {})
        if structured:
            lines.append("=== STRUCTURED DATA ===")
            lines.append(json.dumps(structured, ensure_ascii=False, indent=2))

        # Add relevant raw data (focus on sources likely to have relationship info)
        scraped = raw_data.get("scraped", {})

        # Trademark data is valuable for finding sister brands
        if scraped.get("trademark"):
            lines.append("\n=== TRADEMARK DATA ===")
            lines.append(json.dumps(scraped["trademark"], ensure_ascii=False, indent=2))

        # Company registration may have parent company info
        if scraped.get("rasmio"):
            lines.append("\n=== REGISTRATION DATA ===")
            lines.append(json.dumps(scraped["rasmio"], ensure_ascii=False, indent=2))

        # Stock data may have shareholder information
        if scraped.get("tsetmc"):
            lines.append("\n=== STOCK DATA ===")
            lines.append(json.dumps(scraped["tsetmc"], ensure_ascii=False, indent=2))

        return "\n".join(lines)
