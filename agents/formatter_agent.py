"""Output formatter agent - generates comprehensive multi-format outputs."""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import BaseAgent
from models.state import BrandIntelligenceState
from utils.logger import get_logger
from utils.helpers import (
    generate_timestamp,
    sanitize_filename,
    load_json
)

logger = get_logger(__name__)


class OutputFormatterAgent(BaseAgent):
    """Agent responsible for generating comprehensive outputs in 8 formats."""

    def __init__(self):
        """Initialize the output formatter agent."""
        super().__init__("OutputFormatterAgent")
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

        # Load knowledge base
        kb_path = Path("data/iranian_brands_knowledge.json")
        self.knowledge_base = load_json(kb_path) if kb_path.exists() else {}

        if self.knowledge_base:
            logger.info("Loaded Iranian brands knowledge base")

    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Generate comprehensive outputs in 8 formats.

        Args:
            state: Current workflow state

        Returns:
            Updated state with output file paths
        """
        self._log_start()

        brand_name = state["brand_name"]
        timestamp = generate_timestamp()

        # Create brand-specific output directory
        safe_brand_name = sanitize_filename(brand_name)
        brand_output_dir = self.output_dir / safe_brand_name
        brand_output_dir.mkdir(exist_ok=True)

        # Enrich state with knowledge base if needed
        state = self._enrich_with_knowledge(state)

        # Generate all 9 output files
        output_files = {}

        try:
            logger.info(f"Generating 9 comprehensive output files for {brand_name}...")

            # 0. Complete Master Report (TXT)
            master_path = self._generate_master_report(state, brand_output_dir, timestamp)
            output_files["master_report"] = str(master_path)
            logger.info(f"[OK] Master Report: {master_path.name}")

            # 1. Brand Profile (JSON)
            profile_path = self._generate_brand_profile(state, brand_output_dir, timestamp)
            output_files["brand_profile"] = str(profile_path)
            logger.info(f"[OK] Brand Profile: {profile_path.name}")

            # 2. Strategic Insights (JSON)
            insights_path = self._generate_strategic_insights(state, brand_output_dir, timestamp)
            output_files["strategic_insights"] = str(insights_path)
            logger.info(f"[OK] Strategic Insights: {insights_path.name}")

            # 3. Brands Database (CSV)
            csv_path = self._generate_brands_database(state, brand_output_dir, timestamp)
            output_files["brands_database"] = str(csv_path)
            logger.info(f"[OK] Brands Database: {csv_path.name}")

            # 4. Embedding Ready (TXT)
            embedding_path = self._generate_embedding_text(state, brand_output_dir, timestamp)
            output_files["embedding_ready"] = str(embedding_path)
            logger.info(f"[OK] Embedding Ready: {embedding_path.name}")

            # 5. Financial Intelligence (JSON)
            financial_path = self._generate_financial_intelligence(state, brand_output_dir, timestamp)
            output_files["financial_intelligence"] = str(financial_path)
            logger.info(f"[OK] Financial Intelligence: {financial_path.name}")

            # 6. Executive Summary (MD)
            summary_path = self._generate_executive_summary(state, brand_output_dir, timestamp)
            output_files["executive_summary"] = str(summary_path)
            logger.info(f"[OK] Executive Summary: {summary_path.name}")

            # 7. Complete Product Catalog (JSON) - NEW!
            product_catalog_path = self._generate_product_catalog(state, brand_output_dir, timestamp)
            output_files["product_catalog"] = str(product_catalog_path)
            logger.info(f"[OK] Product Catalog: {product_catalog_path.name}")

            # 8. All Data Aggregated (TXT) - Combines ALL previous files
            aggregated_path = self._generate_all_data_aggregated(
                state,
                brand_output_dir,
                timestamp,
                output_files
            )
            output_files["all_data_aggregated"] = str(aggregated_path)
            logger.info(f"[OK] All Data Aggregated: {aggregated_path.name}")

            state["outputs"] = output_files
            self._log_end(success=True)

        except Exception as e:
            logger.error(f"Failed to generate outputs: {e}")
            import traceback
            traceback.print_exc()
            self._add_error(state, f"Output generation failed: {e}")
            state["outputs"] = output_files
            self._log_end(success=False)

        return state

    def _enrich_with_knowledge(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Enrich state data with knowledge base information."""
        brand_name = state["brand_name"]

        # Check if Active Cleaners
        if "active" in brand_name.lower() and "clean" in brand_name.lower():
            kb_data = self.knowledge_base.get("active_cleaners_detailed", {})
            if kb_data:
                logger.info("[KB] Enriching with Active Cleaners knowledge")

                # Enrich relationships if empty
                if not state.get("relationships", {}).get("parent_company"):
                    if "relationships" not in state:
                        state["relationships"] = {}
                    state["relationships"]["kb_enriched"] = True

        return state

    def _generate_master_report(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate complete master report (TXT) - 0_complete_master_report.txt"""
        output_path = output_dir / "0_complete_master_report.txt"

        brand_name = state["brand_name"]

        lines = []
        lines.append("=" * 80)
        lines.append(f"گزارش جامع هوشمند برند")
        lines.append(f"برند: {brand_name}")
        lines.append(f"تاریخ تولید: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"شناسه گزارش: {timestamp}")
        lines.append("=" * 80)
        lines.append("")

        # بخش ۱: خلاصه اجرایی
        lines.append("بخش ۱: خلاصه اجرایی")
        lines.append("-" * 80)
        insights = state.get("insights", {})
        exec_summary = insights.get("executive_summary", "خلاصه اجرایی در دسترس نیست.")
        lines.append(exec_summary)
        lines.append("")

        # بخش ۲: پروفایل برند
        lines.append("بخش ۲: پروفایل برند")
        lines.append("-" * 80)
        lines.append(f"نام برند: {brand_name}")
        lines.append(f"وبسایت: {state.get('brand_website', 'نامشخص')}")

        structured = state.get("raw_data", {}).get("structured", {})
        website_info = structured.get("website_info", {})
        if website_info.get("title"):
            lines.append(f"عنوان وبسایت: {website_info['title']}")
        if website_info.get("meta_description"):
            lines.append(f"توضیحات: {website_info['meta_description']}")
        lines.append("")

        # بخش ۳: ساختار شرکتی
        lines.append("بخش ۳: ساختار شرکتی و روابط")
        lines.append("-" * 80)
        relationships = state.get("relationships", {})

        parent = relationships.get("parent_company", {})
        if parent and parent.get("name"):
            lines.append(f"شرکت مادر: {parent.get('name')}")
            if parent.get("stock_symbol"):
                lines.append(f"نماد بورس: {parent.get('stock_symbol')}")
            if parent.get("industry"):
                lines.append(f"صنعت: {parent.get('industry')}")

        ultimate = relationships.get("ultimate_parent", {})
        if ultimate and ultimate.get("name"):
            lines.append(f"\nشرکت مادر نهایی: {ultimate.get('name_fa', ultimate.get('name'))}")
            if ultimate.get("market_cap"):
                lines.append(f"ارزش بازار: {ultimate.get('market_cap')}")
            if ultimate.get("total_brands"):
                lines.append(f"تعداد کل برندها: {ultimate.get('total_brands')}")

        sister_brands = relationships.get("sister_brands", [])
        if sister_brands:
            lines.append(f"\nبرندهای خواهر ({len(sister_brands)}):")
            for brand in sister_brands[:10]:
                synergy = brand.get("synergy_score", "نامشخص")
                lines.append(f"  - {brand.get('name')}: {brand.get('products', 'نامشخص')} [هم‌افزایی: {synergy}]")

        lines.append("")

        # بخش ۴: دسته‌بندی بازار
        lines.append("بخش ۴: دسته‌بندی بازار")
        lines.append("-" * 80)
        categorization = state.get("categorization", {})

        industry = categorization.get("primary_industry", {})
        if industry:
            lines.append(f"صنعت: {industry.get('name_fa', industry.get('name_en', 'نامشخص'))}")
            if industry.get("isic_code"):
                lines.append(f"کد ISIC: {industry.get('isic_code')}")

        if categorization.get("business_model"):
            lines.append(f"مدل کسب‌وکار: {categorization['business_model']}")

        if categorization.get("price_tier"):
            lines.append(f"سطح قیمتی: {categorization['price_tier']}")

        target_audiences = categorization.get("target_audiences", [])
        if target_audiences:
            lines.append(f"مخاطبان هدف: {', '.join(target_audiences)}")

        channels = categorization.get("distribution_channels", [])
        if channels:
            lines.append(f"کانال‌های توزیع: {', '.join(channels)}")

        lines.append("")

        # بخش ۵: بینش‌ها و فرصت‌های استراتژیک
        lines.append("بخش ۵: بینش‌ها و فرصت‌های استراتژیک")
        lines.append("-" * 80)

        cross_promo = insights.get("cross_promotion_opportunities", [])
        if cross_promo:
            lines.append(f"فرصت‌های تبلیغات متقابل ({len(cross_promo)}):\n")
            for i, opp in enumerate(cross_promo, 1):
                lines.append(f"{i}. برند شریک: {opp.get('partner_brand')}")
                lines.append(f"   هم‌افزایی: {opp.get('synergy_level')} | اولویت: {opp.get('priority')}")
                lines.append(f"   بودجه: {opp.get('estimated_budget')}")
                lines.append(f"   مفهوم کمپین: {opp.get('campaign_concept')}")
                lines.append("")

        # بخش ۶: توصیه‌های زمان‌بندی کمپین
        lines.append("بخش ۶: توصیه‌های زمان‌بندی کمپین")
        lines.append("-" * 80)
        timing = insights.get("campaign_timing", {})

        optimal = timing.get("optimal_periods", [])
        if optimal:
            lines.append("دوره‌های بهینه:")
            for period in optimal:
                lines.append(f"  - {period}")

        avoid = timing.get("avoid_periods", [])
        if avoid:
            lines.append("\nدوره‌های اجتناب:")
            for period in avoid:
                lines.append(f"  - {period}")

        quarterly = timing.get("quarterly_recommendations", {})
        if quarterly:
            lines.append("\nتوصیه‌های فصلی:")
            for quarter, rec in quarterly.items():
                lines.append(f"  {quarter}: {rec}")

        lines.append("")

        # بخش ۷: بودجه و کانال‌های توصیه‌شده
        lines.append("بخش ۷: بودجه و کانال‌های توصیه‌شده")
        lines.append("-" * 80)
        budget = insights.get("budget_recommendations", {})

        if budget.get("estimated_range_tomans"):
            lines.append(f"بودجه تخمینی: {budget['estimated_range_tomans']}")
        if budget.get("estimated_range_usd"):
            lines.append(f"معادل دلار: {budget['estimated_range_usd']}")

        allocation = budget.get("allocation_by_channel", {})
        if allocation:
            lines.append("\nتخصیص کانال:")
            for channel, percent in allocation.items():
                lines.append(f"  - {channel}: {percent}")

        channel_recs = insights.get("channel_recommendations", [])
        if channel_recs:
            lines.append(f"\nجزئیات کانال‌ها ({len(channel_recs)} کانال):")
            for ch in channel_recs:
                lines.append(f"\n  {ch.get('channel')} - اولویت: {ch.get('priority')}")
                lines.append(f"  دلیل: {ch.get('rationale')}")
                lines.append(f"  بودجه: {ch.get('budget_allocation')}")

        lines.append("")

        # بخش ۸: جهت‌گیری خلاقیت
        lines.append("بخش ۸: جهت‌گیری خلاقیت")
        lines.append("-" * 80)
        creative = insights.get("creative_direction", {})

        messages = creative.get("key_messages", [])
        if messages:
            lines.append("پیام‌های کلیدی:")
            for msg in messages:
                lines.append(f"  - {msg}")

        if creative.get("tone_and_style"):
            lines.append(f"\nلحن و سبک: {creative['tone_and_style']}")

        if creative.get("visual_recommendations"):
            lines.append(f"توصیه‌های بصری: {creative['visual_recommendations']}")

        hashtags = creative.get("hashtag_strategy", [])
        if hashtags:
            lines.append(f"\nاستراتژی هشتگ: {' '.join(hashtags)}")

        themes = creative.get("content_themes", [])
        if themes:
            lines.append("\nتم‌های محتوایی:")
            for theme in themes:
                lines.append(f"  - {theme}")

        lines.append("")

        # بخش ۹: معیارهای موفقیت و شاخص‌های کلیدی
        lines.append("بخش ۹: معیارهای موفقیت و شاخص‌های کلیدی")
        lines.append("-" * 80)
        metrics = insights.get("success_metrics", {})

        kpis = metrics.get("primary_kpis", [])
        if kpis:
            lines.append("شاخص‌های کلیدی اصلی:")
            for kpi in kpis:
                lines.append(f"  - {kpi}")

        if metrics.get("measurement_approach"):
            lines.append(f"\nرویکرد اندازه‌گیری: {metrics['measurement_approach']}")

        if metrics.get("benchmarks"):
            lines.append(f"معیارهای مقایسه: {metrics['benchmarks']}")

        lines.append("")
        lines.append("=" * 80)
        lines.append("پایان گزارش")
        lines.append("=" * 80)

        # Write with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return output_path

    def _generate_brand_profile(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate brand profile JSON - 1_brand_profile.json"""
        output_path = output_dir / "1_brand_profile.json"

        brand_name = state["brand_name"]
        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})
        structured = state.get("raw_data", {}).get("structured", {})

        profile = {
            "brand_intelligence_report": {
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "brand_id": f"{sanitize_filename(brand_name)}_{timestamp}",
                "data_sources": structured.get("sources_used", []),
                "report_version": "1.0"
            },
            "basic_information": {
                "brand_name": brand_name,
                "brand_name_persian": brand_name if any('\u0600' <= c <= '\u06FF' for c in brand_name) else "",
                "website": state.get("brand_website", ""),
                "establishment_year": "Unknown",
                "business_model": categorization.get("business_model", "B2C"),
                "service_type": categorization.get("primary_industry", {}).get("name_fa", "")
            },
            "parent_company_structure": {
                "immediate_parent": relationships.get("parent_company", {}),
                "ultimate_parent": relationships.get("ultimate_parent", {}),
                "ownership_chain": []
            },
            "brand_relationship_map": {
                "sister_brands_same_parent": relationships.get("sister_brands", []),
                "brand_family": relationships.get("brand_family", []),
                "total_related_brands": len(relationships.get("brand_family", []))
            },
            "product_categorization": {
                "primary_industry": categorization.get("primary_industry", {}),
                "sub_industries": categorization.get("sub_industries", []),
                "product_categories": categorization.get("product_categories", []),
                "service_categories": [],
                "customer_segments": {
                    "primary": categorization.get("target_audiences", []),
                    "secondary": []
                },
                "price_positioning": categorization.get("price_tier", "")
            },
            "market_intelligence": {
                "competitive_advantages": [],
                "market_position": categorization.get("market_position", {}),
                "distribution_channels": categorization.get("distribution_channels", [])
            },
            "contact_information": structured.get("contact_info", {}),
            "social_media_presence": structured.get("social_media", {}),
            "website_intelligence": structured.get("website_info", {})
        }

        # Write with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

        return output_path

    def _generate_strategic_insights(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate strategic insights JSON - 2_strategic_insights.json"""
        output_path = output_dir / "2_strategic_insights.json"

        insights = state.get("insights", {})
        brand_name = state["brand_name"]

        strategic = {
            "strategic_intelligence_report": {
                "brand": brand_name,
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "analyst": "Brand Intelligence Agent",
                "confidence_level": "high" if insights else "low"
            },
            "executive_summary": {
                "key_insight": insights.get("executive_summary", ""),
                "primary_opportunities": [opp.get("partner_brand", "") for opp in insights.get("cross_promotion_opportunities", [])[:3]]
            },
            "tier_1_opportunities": {
                "description": "High-priority, high-impact opportunities",
                "recommendations": [
                    {
                        "opportunity_id": f"ST-{str(i+1).zfill(3)}",
                        **opp
                    }
                    for i, opp in enumerate(insights.get("cross_promotion_opportunities", []))
                ]
            },
            "campaign_timing_recommendations": insights.get("campaign_timing", {}),
            "channel_strategy": {
                "recommendations": insights.get("channel_recommendations", []),
                "budget_allocation": insights.get("budget_recommendations", {}).get("allocation_by_channel", {})
            },
            "audience_intelligence": insights.get("audience_insights", {}),
            "competitive_strategy": insights.get("competitive_strategy", {}),
            "budget_allocation_recommendation": insights.get("budget_recommendations", {}),
            "creative_direction": insights.get("creative_direction", {}),
            "kpi_tracking": insights.get("success_metrics", {})
        }

        # Write with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(strategic, f, ensure_ascii=False, indent=2)

        return output_path

    def _get_category_hierarchy(self, category: str) -> Dict[str, str]:
        """Map category to 3-level hierarchy.

        Returns:
            Dict with category_level_1 (broad), category_level_2 (mid), category_level_3 (specific)
        """
        # Category hierarchy mapping (English-only with underscores)
        hierarchy_map = {
            # Technology Services
            "ride_hailing": {
                "level_1": "Technology_Services",
                "level_2": "On-Demand_Platforms",
                "level_3": "Ride-Hailing"
            },
            "food_delivery": {
                "level_1": "Technology_Services",
                "level_2": "On-Demand_Platforms",
                "level_3": "Food_Delivery"
            },
            "travel_technology": {
                "level_1": "Technology_Services",
                "level_2": "Travel_&_Hospitality",
                "level_3": "Online_Travel_Booking"
            },

            # Financial Services
            "insurance_technology": {
                "level_1": "Financial_Services",
                "level_2": "Insurance",
                "level_3": "Health_&_Auto_Insurance"
            },
            "fintech_payments": {
                "level_1": "Financial_Services",
                "level_2": "Fintech",
                "level_3": "Digital_Payments"
            },

            # Healthcare
            "telemedicine": {
                "level_1": "Healthcare_&_Life_Sciences",
                "level_2": "Digital_Health",
                "level_3": "Telemedicine"
            },
            "pharmaceutical": {
                "level_1": "Healthcare_&_Life_Sciences",
                "level_2": "Biopharmaceuticals",
                "level_3": "Biosimilar_Drugs"
            },
            "biotech": {
                "level_1": "Healthcare_&_Life_Sciences",
                "level_2": "Biotechnology",
                "level_3": "Biotech_Products"
            },

            # Transportation & Logistics
            "logistics_delivery": {
                "level_1": "Transportation_&_Logistics",
                "level_2": "Last-Mile_Delivery",
                "level_3": "Package_Delivery"
            },
            "transportation": {
                "level_1": "Transportation_&_Logistics",
                "level_2": "Mobility_Services",
                "level_3": "Ride_Services"
            },

            # Consumer Goods
            "cleaning_products": {
                "level_1": "Consumer_Goods",
                "level_2": "Home_Care",
                "level_3": "Dishwashing_&_Surface_Cleaners"
            },
            "laundry_care": {
                "level_1": "Consumer_Goods",
                "level_2": "Home_Care",
                "level_3": "Laundry_Detergents"
            },
            "dishwashing": {
                "level_1": "Consumer_Goods",
                "level_2": "Home_Care",
                "level_3": "Dishwashing_Products"
            },

            # Food & Beverage
            "confectionery_macaron": {
                "level_1": "Food_&_Beverage",
                "level_2": "Sweet_Snacks",
                "level_3": "Macarons_&_Cookies"
            },
            "confectionery": {
                "level_1": "Food_&_Beverage",
                "level_2": "Sweet_Snacks",
                "level_3": "Sweets_&_Confectionery"
            },
            "chocolate_manufacturing": {
                "level_1": "Food_&_Beverage",
                "level_2": "Sweet_Snacks",
                "level_3": "Chocolate_Products"
            },
            "food": {
                "level_1": "Food_&_Beverage",
                "level_2": "Packaged_Foods",
                "level_3": "Food_Products"
            },

            # Consumer Services
            "online_grocery": {
                "level_1": "Consumer_Services",
                "level_2": "E-Commerce",
                "level_3": "Online_Grocery"
            },
            "ecommerce": {
                "level_1": "Consumer_Services",
                "level_2": "E-Commerce",
                "level_3": "Online_Marketplace"
            },

            # Manufacturing
            "industrial_manufacturing": {
                "level_1": "Manufacturing",
                "level_2": "General_Manufacturing",
                "level_3": "Industrial_Products"
            }
        }

        # Get hierarchy or return defaults
        category_lower = category.lower().replace(" ", "_").replace("-", "_")
        hierarchy = hierarchy_map.get(category_lower, {
            "level_1": "Consumer_Products",
            "level_2": "General_Products",
            "level_3": category.replace(" ", "_").replace("-", "_")
        })

        return {
            "category_level_1": hierarchy["level_1"],
            "category_level_2": hierarchy["level_2"],
            "category_level_3": hierarchy["level_3"]
        }

    def _generate_brands_database(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate brands database CSV - 3_brands_database.csv"""
        output_path = output_dir / "3_brands_database.csv"

        relationships = state.get("relationships", {})
        brand_name = state["brand_name"]

        # Build brands list
        brands = []

        # Add current brand
        categorization = state.get("categorization", {})
        primary_industry = categorization.get("primary_industry", {})
        current_category = primary_industry.get("name_en", "Unknown")

        # Use category levels from categorization if available, otherwise derive from hierarchy map
        if "category_level_1" in primary_industry:
            current_hierarchy = {
                "category_level_1": primary_industry["category_level_1"],
                "category_level_2": primary_industry["category_level_2"],
                "category_level_3": primary_industry["category_level_3"]
            }
        else:
            current_hierarchy = self._get_category_hierarchy(current_category)

        brands.append({
            "brand_name": brand_name,
            "parent_company": relationships.get("parent_company", {}).get("name", "Unknown"),
            "category": current_category,
            "category_level_1": current_hierarchy["category_level_1"],
            "category_level_2": current_hierarchy["category_level_2"],
            "category_level_3": current_hierarchy["category_level_3"],
            "cross_sell_potential": "SELF",
            "market_position": "Unknown",
            "price_tier": state.get("categorization", {}).get("price_tier", "Unknown")
        })

        # Add sister brands
        for brand in relationships.get("sister_brands", []):
            brand_category = brand.get("category", "Unknown")
            brand_hierarchy = self._get_category_hierarchy(brand_category)

            brands.append({
                "brand_name": brand.get("name"),
                "parent_company": relationships.get("parent_company", {}).get("name", "Unknown"),
                "category": brand_category,
                "category_level_1": brand_hierarchy["category_level_1"],
                "category_level_2": brand_hierarchy["category_level_2"],
                "category_level_3": brand_hierarchy["category_level_3"],
                "cross_sell_potential": brand.get("synergy_score", "MEDIUM"),
                "market_position": "Strong",
                "price_tier": brand.get("price_tier", "Unknown")
            })

        # Add brand family
        for brand in relationships.get("brand_family", []):
            brand_category = brand.get("category", "Unknown")
            brand_hierarchy = self._get_category_hierarchy(brand_category)

            brands.append({
                "brand_name": brand.get("name"),
                "parent_company": brand.get("parent", "Unknown"),
                "category": brand_category,
                "category_level_1": brand_hierarchy["category_level_1"],
                "category_level_2": brand_hierarchy["category_level_2"],
                "category_level_3": brand_hierarchy["category_level_3"],
                "cross_sell_potential": "LOW",
                "market_position": "Unknown",
                "price_tier": "Unknown"
            })

        # Write CSV with UTF-8 encoding
        if brands:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig for Excel compatibility
                fieldnames = [
                    "brand_name",
                    "parent_company",
                    "category",
                    "category_level_1",
                    "category_level_2",
                    "category_level_3",
                    "cross_sell_potential",
                    "market_position",
                    "price_tier"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(brands)

        return output_path

    def _generate_embedding_text(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate embedding-ready text - 4_embedding_ready.txt (2500+ words)"""
        output_path = output_dir / "4_embedding_ready.txt"

        brand_name = state["brand_name"]
        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})
        insights = state.get("insights", {})
        structured = state.get("raw_data", {}).get("structured", {})

        lines = []

        # مقدمه
        lines.append(f"پروفایل برند: {brand_name}")
        lines.append("")
        lines.append("اطلاعات پایه")
        lines.append(f"{brand_name} یک برند فعال در صنعت {categorization.get('primary_industry', {}).get('name_fa', 'بازار مصرف‌کننده')} است.")

        parent = relationships.get("parent_company", {})
        if parent and parent.get("name"):
            lines.append(f"این برند متعلق به {parent.get('name')} است که با نماد بورس {parent.get('stock_symbol', 'نامشخص')} فعالیت می‌کند.")

        ultimate = relationships.get("ultimate_parent", {})
        if ultimate and ultimate.get("name"):
            lines.append(f"شرکت مادر نهایی {ultimate.get('name_fa', ultimate.get('name'))} است، ")
            lines.append(f"یکی از بزرگترین گروه‌های صنعتی ایران با {ultimate.get('total_brands', 'چندین')} برند ")
            lines.append(f"و ارزش بازار تخمینی {ultimate.get('market_cap', 'قابل توجه')}.")

        lines.append("")

        # ساختار شرکتی
        lines.append("ساختار شرکتی")
        lines.append(f"ساختار شرکتی {brand_name} نشان‌دهنده یک سلسله‌مراتب پیچیده از مالکیت و مدیریت برند است.")

        if parent:
            lines.append(f"به عنوان یک شرکت تابعه مستقیم {parent.get('name')}، این برند از شبکه‌های توزیع مستقر، ")
            lines.append(f"تخصص عملیاتی و ثبات مالی بهره‌مند می‌شود. شرکت مادر در بخش {parent.get('industry', 'محصولات مصرفی')} فعالیت می‌کند ")
            lines.append("و هم‌راستایی استراتژیک و هم‌افزایی را در سبد برندها فراهم می‌آورد.")

        lines.append("")

        # خانواده برند
        lines.append("خانواده برند - برندهای خواهر")
        sister_brands = relationships.get("sister_brands", [])
        if sister_brands:
            lines.append(f"{brand_name} بخشی از خانواده‌ای متشکل از {len(sister_brands)} برند خواهر تحت شرکت مادر یکسان است.")
            lines.append("این برندهای خواهر فرصت‌های قابل توجهی برای تبلیغات متقابل و بازاریابی یکپارچه ایجاد می‌کنند:")
            lines.append("")

            for brand in sister_brands:
                lines.append(f"- {brand.get('name')}: تخصص در {brand.get('products', 'محصولات مصرفی')}، ")
                lines.append(f"  هدف‌گذاری به {brand.get('target_audience', 'مصرف‌کنندگان عمومی')} با امتیاز هم‌افزایی {brand.get('synergy_score', 'متوسط')}.")
                lines.append(f"  این برند در دسته {brand.get('category', 'مصرفی')} با قیمت‌گذاری {brand.get('price_tier', 'متوسط')} فعالیت می‌کند.")
                lines.append("")

        brand_family = relationships.get("brand_family", [])
        if brand_family:
            lines.append(f"خانواده گسترده‌تر برند شامل {len(brand_family)} برند در دسته‌های متعدد است:")
            for brand in brand_family[:15]:
                lines.append(f"- {brand.get('name')} (دسته {brand.get('category', 'مصرفی')}) تحت {brand.get('parent', 'مدیریت گروه')}")
            lines.append("")

        # موقعیت‌یابی بازار
        lines.append("موقعیت‌یابی بازار")
        lines.append(f"{brand_name} با مدل کسب‌وکار {categorization.get('business_model', 'B2C')} فعالیت می‌کند، ")
        lines.append(f"با هدف‌گذاری به {', '.join(categorization.get('target_audiences', ['مصرف‌کنندگان عمومی']))}.")
        lines.append(f"این برند در سطح قیمتی {categorization.get('price_tier', 'متوسط')} قرار دارد ")
        lines.append("و بین کیفیت و مقرون‌به‌صرفه بودن تعادل ایجاد می‌کند تا بیشترین سهم بازار را به دست آورد.")
        lines.append("")

        market_pos = categorization.get("market_position", {})
        if market_pos:
            lines.append(f"موقعیت بازار: {market_pos.get('positioning', 'رقابتی')}.")
            lines.append(f"چشم‌انداز رقابتی: {market_pos.get('competitive_landscape', 'پویا و رقابتی')}.")

        channels = categorization.get("distribution_channels", [])
        if channels:
            lines.append(f"کانال‌های توزیع شامل {', '.join(channels)} است، ")
            lines.append("که پوشش گسترده بازار و دسترسی به مصرف‌کنندگان هدف را تضمین می‌کند.")
        lines.append("")

        # فرصت‌های استراتژیک
        lines.append("فرصت‌های استراتژیک")
        cross_promo = insights.get("cross_promotion_opportunities", [])
        if cross_promo:
            lines.append(f"تحلیل نشان می‌دهد {len(cross_promo)} فرصت با پتانسیل بالا برای تبلیغات متقابل:")
            lines.append("")

            for i, opp in enumerate(cross_promo, 1):
                lines.append(f"{i}. همکاری با {opp.get('partner_brand')}")
                lines.append(f"   سطح هم‌افزایی: {opp.get('synergy_level')}")
                lines.append(f"   مفهوم کمپین: {opp.get('campaign_concept')}")
                lines.append(f"   مخاطب هدف: {opp.get('target_audience')}")
                lines.append(f"   بودجه تخمینی: {opp.get('estimated_budget')}")
                lines.append(f"   منافع مورد انتظار: {opp.get('expected_benefit')}")
                lines.append(f"   سختی اجرا: {opp.get('implementation_difficulty')}")
                lines.append("")

        # توصیه‌های زمان‌بندی کمپین
        lines.append("توصیه‌های زمان‌بندی کمپین")
        timing = insights.get("campaign_timing", {})
        optimal = timing.get("optimal_periods", [])
        if optimal:
            lines.append("دوره‌های بهینه کمپین برای حداکثر تأثیر:")
            for period in optimal:
                lines.append(f"- {period}: تعامل و هزینه بالای مصرف‌کننده")
            lines.append("")

        avoid = timing.get("avoid_periods", [])
        if avoid:
            lines.append("دوره‌هایی که باید از کمپین‌های تجاری اجتناب کرد:")
            for period in avoid:
                lines.append(f"- {period}")
            lines.append("")

        # توصیه‌های بودجه
        lines.append("توصیه‌های بودجه و سرمایه‌گذاری")
        budget = insights.get("budget_recommendations", {})
        if budget:
            lines.append(f"بودجه تبلیغاتی سالانه توصیه‌شده: {budget.get('estimated_range_tomans', '500M-1B تومان')}")
            lines.append(f"معادل دلار: {budget.get('estimated_range_usd', '$10K-$20K')}")
            lines.append(f"بازده مورد انتظار سرمایه: {budget.get('roi_expectations', '2-3 برابر در 6 ماه')}")
            lines.append("")

            allocation = budget.get("allocation_by_channel", {})
            if allocation:
                lines.append("تخصیص کانال توصیه‌شده:")
                for channel, percent in allocation.items():
                    lines.append(f"- {channel}: {percent}")
                lines.append("")

        # استراتژی کانال‌های بازاریابی
        lines.append("استراتژی کانال‌های بازاریابی")
        channel_recs = insights.get("channel_recommendations", [])
        if channel_recs:
            for ch in channel_recs:
                lines.append(f"{ch.get('channel')} (اولویت: {ch.get('priority')})")
                lines.append(f"  دلیل: {ch.get('rationale')}")
                lines.append(f"  نوع محتوا: {ch.get('content_type', 'محتوای ترکیبی')}")
                lines.append(f"  تخصیص بودجه: {ch.get('budget_allocation', 'نامشخص')}")
                lines.append("")

        # جهت‌گیری خلاقانه
        lines.append("جهت‌گیری خلاقانه و پیام‌رسانی")
        creative = insights.get("creative_direction", {})
        if creative:
            messages = creative.get("key_messages", [])
            if messages:
                lines.append("پیام‌های کلیدی برند:")
                for msg in messages:
                    lines.append(f"- {msg}")
                lines.append("")

            lines.append(f"لحن و سبک: {creative.get('tone_and_style', 'حرفه‌ای و جذاب')}")
            lines.append(f"توصیه‌های بصری: {creative.get('visual_recommendations', 'طراحی تمیز و مدرن')}")
            lines.append(f"ملاحظات فرهنگی: {creative.get('cultural_considerations', 'احترام به ارزش‌های ایرانی')}")
            lines.append("")

        # معیارهای موفقیت
        lines.append("معیارهای موفقیت و شاخص‌های کلیدی")
        metrics = insights.get("success_metrics", {})
        kpis = metrics.get("primary_kpis", [])
        if kpis:
            lines.append("شاخص‌های کلیدی اصلی برای موفقیت کمپین:")
            for kpi in kpis:
                lines.append(f"- {kpi}")
            lines.append("")

        lines.append(f"رویکرد اندازه‌گیری: {metrics.get('measurement_approach', 'ردیابی و گزارش‌دهی ماهانه')}")
        lines.append(f"معیارهای مقایسه: {metrics.get('benchmarks', 'استانداردهای صنعت و عملکرد تاریخی')}")

        # Write with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return output_path

    def _generate_financial_intelligence(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate financial intelligence JSON - 5_financial_intelligence.json"""
        output_path = output_dir / "5_financial_intelligence.json"

        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})

        parent = relationships.get("parent_company", {})
        ultimate = relationships.get("ultimate_parent", {})

        financial = {
            "financial_intelligence_report": {
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "data_sources": ["Parent company disclosures", "Market estimates", "Industry analysis"],
                "confidence_level": "medium"
            },
            "parent_company_overview": {
                "name": parent.get("name", "Unknown"),
                "stock_symbol": parent.get("stock_symbol", "N/A"),
                "market": "Tehran Stock Exchange" if parent.get("stock_symbol") else "Private",
                "industry": parent.get("industry", "Unknown")
            },
            "ownership_structure": {
                "immediate_parent": parent.get("name", "Unknown"),
                "ultimate_parent": ultimate.get("name_fa", "Unknown"),
                "ownership_percentage": ultimate.get("ownership_percentage", "Unknown"),
                "public_float": "Unknown"
            },
            "market_capitalization": {
                "estimate": ultimate.get("market_cap", "Unknown"),
                "currency": "Iranian Toman",
                "calculation_method": "Industry estimates"
            },
            "advertising_intelligence_framework": {
                "industry_standards": "2-5% of revenue for FMCG",
                "competitive_benchmarks": "Leading brands invest 3-7% of revenue",
                "recommended_range": categorization.get("price_tier", "mid") + " tier: 2-4% of estimated revenue"
            },
            "estimated_advertising_budget": {
                "annual_estimate_tomans": "500M-1B Tomans",
                "annual_estimate_usd": "$10K-$20K",
                "basis": "Industry standards and price tier positioning",
                "confidence": "medium"
            }
        }

        # Write with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(financial, f, ensure_ascii=False, indent=2)

        return output_path

    def _generate_executive_summary(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate executive summary MD - 6_executive_summary.md (1800+ words)"""
        output_path = output_dir / "6_executive_summary.md"

        brand_name = state["brand_name"]
        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})
        insights = state.get("insights", {})
        structured = state.get("raw_data", {}).get("structured", {})

        lines = []

        # سرصفحه
        lines.append(f"# گزارش هوشمند برند: {brand_name}")
        lines.append("")
        lines.append("## خلاصه اجرایی")
        lines.append("")
        lines.append(f"**تاریخ گزارش:** {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"**برند:** {brand_name}")
        lines.append(f"**صنعت:** {categorization.get('primary_industry', {}).get('name_fa', 'نامشخص')}")
        lines.append(f"**مدل کسب‌وکار:** {categorization.get('business_model', 'B2C')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # خلاصه استراتژیک
        lines.append("## 🎯 خلاصه استراتژیک")
        lines.append("")
        exec_summary = insights.get("executive_summary", "")
        if exec_summary:
            lines.append(exec_summary)
        else:
            lines.append(f"{brand_name} نماینده یک فرصت استراتژیک در بازار {categorization.get('primary_industry', {}).get('name_fa', 'مصرفی')} ایران است.")
        lines.append("")
        lines.append("---")
        lines.append("")

        # بررسی کلی برند
        lines.append("## 📊 بررسی کلی برند")
        lines.append("")
        lines.append("### هویت برند")
        lines.append("")
        lines.append(f"- **نام برند:** {brand_name}")
        website = state.get("brand_website", "")
        if website:
            lines.append(f"- **وبسایت:** [{website}]({website})")

        parent = relationships.get("parent_company", {})
        if parent and parent.get("name"):
            lines.append(f"- **شرکت مادر:** {parent.get('name')}")
            if parent.get("stock_symbol"):
                lines.append(f"- **نماد بورس:** {parent.get('stock_symbol')}")

        ultimate = relationships.get("ultimate_parent", {})
        if ultimate and ultimate.get("name"):
            lines.append(f"- **شرکت مادر نهایی:** {ultimate.get('name_fa', ultimate.get('name'))}")

        lines.append("")

        website_info = structured.get("website_info", {})
        if website_info.get("title"):
            lines.append(f"**عنوان وبسایت:** {website_info['title']}")
            lines.append("")

        if website_info.get("meta_description"):
            lines.append(f"**توضیحات:** {website_info['meta_description']}")
            lines.append("")

        # موقعیت بازار
        lines.append("### موقعیت‌یابی بازار")
        lines.append("")
        lines.append(f"- **صنعت:** {categorization.get('primary_industry', {}).get('name_fa', 'نامشخص')}")
        lines.append(f"- **سطح قیمتی:** {categorization.get('price_tier', 'نامشخص').replace('_', ' ').title()}")

        target_audiences = categorization.get("target_audiences", [])
        if target_audiences:
            lines.append(f"- **مخاطب هدف:** {', '.join(target_audiences).replace('_', ' ').title()}")

        channels = categorization.get("distribution_channels", [])
        if channels:
            lines.append(f"- **کانال‌های توزیع:** {', '.join(channels).title()}")

        lines.append("")
        lines.append("---")
        lines.append("")

        # ساختار شرکتی
        lines.append("## 🏢 ساختار شرکتی")
        lines.append("")

        if parent:
            lines.append("### شرکت مادر")
            lines.append("")
            lines.append(f"**{parent.get('name')}** به عنوان شرکت مادر مستقیم، موارد زیر را فراهم می‌کند:")
            lines.append("")
            lines.append("- پشتیبانی مالی و ثبات")
            lines.append("- شبکه‌های توزیع مستقر")
            lines.append("- تخصص عملیاتی و بهترین شیوه‌ها")
            lines.append(f"- دسترسی به زیرساخت بازار {parent.get('industry', 'محصولات مصرفی')}")
            lines.append("")

        if ultimate:
            lines.append("### گروه مادر نهایی")
            lines.append("")
            lines.append(f"**{ultimate.get('name_fa', ultimate.get('name'))}** نماینده سازمان مادر نهایی است:")
            lines.append("")
            if ultimate.get("description"):
                lines.append(f"- {ultimate['description']}")
            if ultimate.get("market_cap"):
                lines.append(f"- ارزش بازار: {ultimate['market_cap']}")
            if ultimate.get("total_brands"):
                lines.append(f"- سبد برندها: {ultimate['total_brands']} برند")
            if ultimate.get("employees"):
                lines.append(f"- نیروی کار: {ultimate['employees']} کارمند")
            lines.append("")

        lines.append("---")
        lines.append("")

        # برندهای خواهر
        lines.append("## 👨‍👩‍👧‍👦 خانواده برند و روابط")
        lines.append("")

        sister_brands = relationships.get("sister_brands", [])
        if sister_brands:
            lines.append(f"### برندهای خواهر ({len(sister_brands)} برند)")
            lines.append("")
            lines.append(f"{brand_name} شرکت مادر خود را با {len(sister_brands)} برند خواهر به اشتراک می‌گذارد،")
            lines.append("که فرصت‌های قابل توجهی برای تبلیغات متقابل و بازاریابی یکپارچه ایجاد می‌کند:")
            lines.append("")

            for brand in sister_brands:
                synergy = brand.get("synergy_score", "MEDIUM")
                synergy_emoji = {"VERY_HIGH": "⭐⭐⭐", "HIGH": "⭐⭐", "MEDIUM": "⭐", "LOW": "○"}.get(synergy, "○")

                lines.append(f"#### {brand.get('name')} {synergy_emoji}")
                lines.append("")
                lines.append(f"- **محصولات:** {brand.get('products', 'محصولات مصرفی')}")
                lines.append(f"- **دسته:** {brand.get('category', 'نامشخص').replace('_', ' ').title()}")
                lines.append(f"- **مخاطب هدف:** {brand.get('target_audience', 'مصرف‌کنندگان عمومی')}")
                lines.append(f"- **سطح قیمتی:** {brand.get('price_tier', 'نامشخص').replace('_', ' ').title()}")
                lines.append(f"- **هم‌افزایی فروش متقابل:** {synergy}")
                lines.append("")

        brand_family = relationships.get("brand_family", [])
        if brand_family:
            lines.append(f"### خانواده گسترده برند ({len(brand_family)} برند)")
            lines.append("")
            lines.append("سبد گسترده‌تر گروه شامل:")
            lines.append("")

            # گروه‌بندی بر اساس شرکت مادر
            by_parent = {}
            for brand in brand_family:
                parent_name = brand.get("parent", "نامشخص")
                if parent_name not in by_parent:
                    by_parent[parent_name] = []
                by_parent[parent_name].append(brand)

            for parent_name, brands in by_parent.items():
                lines.append(f"**{parent_name}:**")
                for brand in brands[:5]:  # محدود به 5 برند در هر مادر
                    lines.append(f"- {brand.get('name')} ({brand.get('category', 'مصرفی').replace('_', ' ').title()})")
                lines.append("")

        lines.append("---")
        lines.append("")

        # فرصت‌های استراتژیک
        lines.append("## 💡 فرصت‌های استراتژیک")
        lines.append("")

        cross_promo = insights.get("cross_promotion_opportunities", [])
        if cross_promo:
            lines.append(f"### {min(3, len(cross_promo))} فرصت برتر تبلیغات متقابل")
            lines.append("")

            for i, opp in enumerate(cross_promo[:3], 1):
                priority = opp.get("priority", "medium")
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

                lines.append(f"#### {i}. {opp.get('partner_brand')} {priority_emoji}")
                lines.append("")
                lines.append(f"**سطح هم‌افزایی:** {opp.get('synergy_level')}")
                lines.append(f"**اولویت:** {priority.upper()}")
                lines.append("")
                lines.append(f"**مفهوم کمپین:**")
                lines.append(f"{opp.get('campaign_concept')}")
                lines.append("")
                lines.append(f"**مخاطب هدف:** {opp.get('target_audience')}")
                lines.append(f"**بودجه تخمینی:** {opp.get('estimated_budget')}")
                lines.append(f"**منفعت مورد انتظار:** {opp.get('expected_benefit')}")
                lines.append(f"**اجرا:** سختی {opp.get('implementation_difficulty', 'متوسط').title()}")
                lines.append("")

        lines.append("---")
        lines.append("")

        # زمان‌بندی کمپین
        lines.append("## 📅 استراتژی زمان‌بندی کمپین")
        lines.append("")

        timing = insights.get("campaign_timing", {})

        optimal = timing.get("optimal_periods", [])
        if optimal:
            lines.append("### دوره‌های بهینه کمپین")
            lines.append("")
            for period in optimal:
                lines.append(f"- **{period}**")
            lines.append("")

        quarterly = timing.get("quarterly_recommendations", {})
        if quarterly:
            lines.append("### تفکیک فصلی")
            lines.append("")
            for quarter, rec in quarterly.items():
                lines.append(f"**{quarter}:** {rec}")
                lines.append("")

        avoid = timing.get("avoid_periods", [])
        if avoid:
            lines.append("### دوره‌های اجتناب")
            lines.append("")
            for period in avoid:
                lines.append(f"- {period}")
            lines.append("")

        seasonal = timing.get("seasonal_considerations")
        if seasonal:
            lines.append(f"**زمینه فرهنگی:** {seasonal}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # بودجه و کانال‌ها
        lines.append("## 💰 توصیه‌های بودجه و کانال")
        lines.append("")

        budget = insights.get("budget_recommendations", {})
        if budget:
            lines.append("### بودجه توصیه‌شده")
            lines.append("")
            if budget.get("estimated_range_tomans"):
                lines.append(f"- **بودجه سالانه:** {budget['estimated_range_tomans']}")
            if budget.get("estimated_range_usd"):
                lines.append(f"- **معادل دلار:** {budget['estimated_range_usd']}")
            if budget.get("roi_expectations"):
                lines.append(f"- **بازده مورد انتظار:** {budget['roi_expectations']}")
            lines.append("")

            if budget.get("rationale"):
                lines.append(f"**دلیل:** {budget['rationale']}")
                lines.append("")

        allocation = budget.get("allocation_by_channel", {})
        if allocation:
            lines.append("### تخصیص کانال")
            lines.append("")
            lines.append("| کانال | تخصیص |")
            lines.append("|---------|------------|")
            for channel, percent in allocation.items():
                lines.append(f"| {channel} | {percent} |")
            lines.append("")

        channel_recs = insights.get("channel_recommendations", [])
        if channel_recs:
            lines.append("### جزئیات استراتژی کانال")
            lines.append("")

            for ch in channel_recs:
                priority = ch.get("priority", "medium")
                priority_badge = {"high": "🔴 بالا", "medium": "🟡 متوسط", "low": "🟢 پایین"}.get(priority, "⚪ نامشخص")

                lines.append(f"#### {ch.get('channel')} - {priority_badge}")
                lines.append("")
                lines.append(f"**دلیل:** {ch.get('rationale')}")
                lines.append(f"**نوع محتوا:** {ch.get('content_type')}")
                lines.append(f"**تخصیص بودجه:** {ch.get('budget_allocation')}")
                lines.append("")

        lines.append("---")
        lines.append("")

        # جهت‌گیری خلاقانه
        lines.append("## 🎨 جهت‌گیری خلاقیت")
        lines.append("")

        creative = insights.get("creative_direction", {})

        messages = creative.get("key_messages", [])
        if messages:
            lines.append("### پیام‌های کلیدی برند")
            lines.append("")
            for msg in messages:
                lines.append(f"- {msg}")
            lines.append("")

        if creative.get("tone_and_style"):
            lines.append(f"**لحن و سبک:** {creative['tone_and_style']}")
            lines.append("")

        if creative.get("visual_recommendations"):
            lines.append(f"**راهنمای بصری:** {creative['visual_recommendations']}")
            lines.append("")

        if creative.get("cultural_considerations"):
            lines.append(f"**ملاحظات فرهنگی:** {creative['cultural_considerations']}")
            lines.append("")

        hashtags = creative.get("hashtag_strategy", [])
        if hashtags:
            lines.append("**استراتژی هشتگ:**")
            lines.append("")
            lines.append(" ".join(hashtags))
            lines.append("")

        themes = creative.get("content_themes", [])
        if themes:
            lines.append("### تم‌های محتوایی")
            lines.append("")
            for theme in themes:
                lines.append(f"- {theme}")
            lines.append("")

        if creative.get("storytelling_angle"):
            lines.append(f"**داستان برند:** {creative['storytelling_angle']}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # معیارهای موفقیت
        lines.append("## 📈 معیارهای موفقیت و شاخص‌های کلیدی")
        lines.append("")

        metrics = insights.get("success_metrics", {})

        kpis = metrics.get("primary_kpis", [])
        if kpis:
            lines.append("### شاخص‌های کلیدی اصلی")
            lines.append("")
            for kpi in kpis:
                lines.append(f"- {kpi}")
            lines.append("")

        if metrics.get("measurement_approach"):
            lines.append(f"**رویکرد اندازه‌گیری:** {metrics['measurement_approach']}")
            lines.append("")

        if metrics.get("benchmarks"):
            lines.append(f"**معیارهای مقایسه:** {metrics['benchmarks']}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # استراتژی رقابتی
        lines.append("## 🎯 استراتژی رقابتی")
        lines.append("")

        competitive = insights.get("competitive_strategy", {})

        if competitive.get("positioning"):
            lines.append(f"**موقعیت‌یابی:** {competitive['positioning']}")
            lines.append("")

        diff_points = competitive.get("differentiation_points", [])
        if diff_points:
            lines.append("### نقاط تمایز")
            lines.append("")
            for point in diff_points:
                lines.append(f"- {point}")
            lines.append("")

        advantages = competitive.get("competitive_advantages_to_highlight", [])
        if advantages:
            lines.append("### مزایای رقابتی")
            lines.append("")
            for adv in advantages:
                lines.append(f"- {adv}")
            lines.append("")

        pillars = competitive.get("messaging_pillars", [])
        if pillars:
            lines.append("### ستون‌های پیام‌رسانی")
            lines.append("")
            for pillar in pillars:
                lines.append(f"1. {pillar}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # نتیجه‌گیری
        lines.append("## 🎬 نتیجه‌گیری و مراحل بعدی")
        lines.append("")
        lines.append(f"این تحلیل جامع از {brand_name} فرصت‌های قابل توجهی برای رشد را آشکار می‌سازد ")
        lines.append("از طریق مشارکت‌های استراتژیک برند، زمان‌بندی هدفمند کمپین و رویکردهای بازاریابی چندکاناله.")
        lines.append("")
        lines.append("**اقدامات فوری توصیه‌شده:**")
        lines.append("")
        lines.append("1. آغاز مذاکرات با 3 برند خواهر برتر برای کمپین‌های تبلیغات متقابل")
        lines.append("2. توسعه برنامه‌های تفصیلی کمپین برای دوره‌های فصلی بهینه")
        lines.append("3. تخصیص بودجه بازاریابی طبق توزیع کانال توصیه‌شده")
        lines.append("4. پیاده‌سازی زیرساخت ردیابی شاخص‌های کلیدی برای سنجش کمپین")
        lines.append("5. آغاز توسعه خلاقانه همراستا با ستون‌های پیام‌رسانی برند")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"*گزارش تولیدشده توسط عامل هوشمند برند در {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        # Write with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return output_path

    def _generate_product_catalog(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate complete product catalog JSON - 7_product_catalog.json"""
        output_path = output_dir / "7_product_catalog.json"

        brand_name = state["brand_name"]
        product_catalog = state.get("product_catalog", {})
        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})

        # Build comprehensive catalog
        catalog_output = {
            "brand_intelligence_product_catalog": {
                "brand_name": brand_name,
                "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "report_id": timestamp,
                "extraction_method": product_catalog.get("extraction_method", "automated"),
                "data_quality": "comprehensive" if product_catalog.get("total_products", 0) > 0 else "limited"
            },
            "catalog_summary": {
                "total_products": product_catalog.get("total_products", 0),
                "total_therapeutic_areas": len(product_catalog.get("therapeutic_areas", [])),
                "total_categories": len(product_catalog.get("categories", {})),
                "product_lines": product_catalog.get("product_lines", [])
            },
            "therapeutic_areas": product_catalog.get("therapeutic_areas", []),
            "product_categories": product_catalog.get("categories", {}),
            "complete_product_list": product_catalog.get("products", []),
            "services_list": product_catalog.get("services", []),  # Include services
            "market_intelligence": product_catalog.get("market_intelligence", {}),
            "metadata": product_catalog.get("metadata", {}),  # Include metadata (counselors count, etc.)
            "corporate_relationships": {
                "parent_company": relationships.get("parent_company", {}).get("name", "Unknown"),
                "ultimate_parent": relationships.get("ultimate_parent", {}).get("name_fa", "Unknown"),
                "manufacturing_subsidiaries": self._extract_manufacturing_subsidiaries(relationships),
                "marketing_distribution_role": self._extract_marketing_role(brand_name, relationships)
            },
            "industry_classification": {
                "primary_industry": categorization.get("primary_industry", {}),
                "sub_industries": categorization.get("sub_industries", []),
                "business_model": categorization.get("business_model", "Unknown")
            }
        }

        # Add product statistics if available
        if "product_statistics" in product_catalog:
            catalog_output["product_statistics"] = product_catalog["product_statistics"]

        # Write with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(catalog_output, f, ensure_ascii=False, indent=2)

        return output_path

    def _extract_manufacturing_subsidiaries(self, relationships: Dict) -> List[str]:
        """Extract manufacturing subsidiaries from relationships."""
        subs = []
        for brand in relationships.get("sister_brands", []):
            if "manufacturing" in brand.get("products", "").lower() or "manufacturer" in brand.get("role", "").lower():
                subs.append(brand.get("name"))
        return subs if subs else ["Unknown"]

    def _extract_marketing_role(self, brand_name: str, relationships: Dict) -> Dict[str, Any]:
        """Determine if this brand is a marketing/distribution entity."""
        # Check if brand name suggests marketing role
        marketing_keywords = ["pharmed", "distribution", "marketing", "pakhsh", "پخش"]

        is_marketing_entity = any(kw in brand_name.lower() for kw in marketing_keywords)

        if is_marketing_entity:
            return {
                "role": "Marketing & Distribution",
                "handles_brands": [b.get("name") for b in relationships.get("sister_brands", [])],
                "description": f"{brand_name} handles marketing and distribution for group brands"
            }
        else:
            return {
                "role": "Manufacturing/Product Brand",
                "description": f"{brand_name} is a product/manufacturing brand"
            }

    def _generate_all_data_aggregated(
        self,
        state: Dict,
        output_dir: Path,
        timestamp: str,
        output_files: Dict[str, str]
    ) -> Path:
        """Generate aggregated file containing ALL data from all other files.

        This creates a comprehensive text file that includes:
        - All JSON files (formatted as readable text)
        - All CSV files (formatted as tables)
        - All TXT files
        - All MD files

        Args:
            state: Workflow state
            output_dir: Output directory path
            timestamp: Timestamp string
            output_files: Dictionary of already generated file paths

        Returns:
            Path to generated aggregated file
        """
        output_path = output_dir / "7_all_data_aggregated.txt"

        brand_name = state["brand_name"]

        lines = []
        lines.append("=" * 100)
        lines.append("تجمیع کامل داده‌ها - ترکیب تمام فایل‌ها")
        lines.append("=" * 100)
        lines.append(f"برند: {brand_name}")
        lines.append(f"تاریخ تولید: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"شناسه گزارش: {timestamp}")
        lines.append("")
        lines.append("این فایل شامل تمام داده‌ها از تمام فایل‌های خروجی تولید شده است:")
        lines.append("  - 0_complete_master_report.txt")
        lines.append("  - 1_brand_profile.json")
        lines.append("  - 2_strategic_insights.json")
        lines.append("  - 3_brands_database.csv")
        lines.append("  - 4_embedding_ready.txt")
        lines.append("  - 5_financial_intelligence.json")
        lines.append("  - 6_executive_summary.md")
        lines.append("  - 7_product_catalog.json")
        lines.append("=" * 100)
        lines.append("")
        lines.append("")

        # بخش ۱: گزارش جامع
        lines.append("#" * 100)
        lines.append("# فایل ۰: گزارش جامع (TXT)")
        lines.append("#" * 100)
        lines.append("")

        master_report_path = output_files.get("master_report")
        if master_report_path and Path(master_report_path).exists():
            with open(master_report_path, 'r', encoding='utf-8') as f:
                lines.append(f.read())
        else:
            lines.append("[گزارش جامع در دسترس نیست]")

        lines.append("")
        lines.append("")

        # بخش ۲: پروفایل برند JSON
        lines.append("#" * 100)
        lines.append("# فایل ۱: پروفایل برند (JSON)")
        lines.append("#" * 100)
        lines.append("")

        profile_path = output_files.get("brand_profile")
        if profile_path and Path(profile_path).exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)

            lines.append("پروفایل برند - داده‌های ساختاریافته")
            lines.append("-" * 100)
            lines.append("")

            # Full JSON
            lines.append("JSON کامل:")
            lines.append(json.dumps(profile_data, ensure_ascii=False, indent=2))
        else:
            lines.append("[پروفایل برند در دسترس نیست]")

        lines.append("")
        lines.append("")

        # بخش ۳: بینش‌های استراتژیک JSON
        lines.append("#" * 100)
        lines.append("# فایل ۲: بینش‌های استراتژیک (JSON)")
        lines.append("#" * 100)
        lines.append("")

        insights_path = output_files.get("strategic_insights")
        if insights_path and Path(insights_path).exists():
            with open(insights_path, 'r', encoding='utf-8') as f:
                insights_data = json.load(f)

            lines.append("بینش‌های استراتژیک - توصیه‌های جامع")
            lines.append("-" * 100)
            lines.append("")
            lines.append("JSON کامل:")
            lines.append(json.dumps(insights_data, ensure_ascii=False, indent=2))
        else:
            lines.append("[بینش‌های استراتژیک در دسترس نیست]")

        lines.append("")
        lines.append("")

        # بخش ۴: پایگاه داده برندها CSV
        lines.append("#" * 100)
        lines.append("# فایل ۳: پایگاه داده برندها (CSV)")
        lines.append("#" * 100)
        lines.append("")

        csv_path = output_files.get("brands_database")
        if csv_path and Path(csv_path).exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()

            lines.append("پایگاه داده برندها - جدول برندهای مرتبط")
            lines.append("-" * 100)
            lines.append("")
            lines.append(csv_content)
        else:
            lines.append("[پایگاه داده برندها در دسترس نیست]")

        lines.append("")
        lines.append("")

        # بخش ۵: متن آماده Embedding
        lines.append("#" * 100)
        lines.append("# فایل ۴: متن آماده Embedding")
        lines.append("#" * 100)
        lines.append("")

        embedding_path = output_files.get("embedding_ready")
        if embedding_path and Path(embedding_path).exists():
            with open(embedding_path, 'r', encoding='utf-8') as f:
                lines.append(f.read())
        else:
            lines.append("[متن embedding در دسترس نیست]")

        lines.append("")
        lines.append("")

        # بخش ۶: هوشمندی مالی JSON
        lines.append("#" * 100)
        lines.append("# فایل ۵: هوشمندی مالی (JSON)")
        lines.append("#" * 100)
        lines.append("")

        financial_path = output_files.get("financial_intelligence")
        if financial_path and Path(financial_path).exists():
            with open(financial_path, 'r', encoding='utf-8') as f:
                financial_data = json.load(f)

            lines.append("هوشمندی مالی - تحلیل شرکت مادر")
            lines.append("-" * 100)
            lines.append("")
            lines.append("JSON کامل:")
            lines.append(json.dumps(financial_data, ensure_ascii=False, indent=2))
        else:
            lines.append("[هوشمندی مالی در دسترس نیست]")

        lines.append("")
        lines.append("")

        # بخش ۷: خلاصه اجرایی Markdown
        lines.append("#" * 100)
        lines.append("# فایل ۶: خلاصه اجرایی (MARKDOWN)")
        lines.append("#" * 100)
        lines.append("")

        summary_path = output_files.get("executive_summary")
        if summary_path and Path(summary_path).exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                lines.append(f.read())
        else:
            lines.append("[خلاصه اجرایی در دسترس نیست]")

        lines.append("")
        lines.append("")

        # بخش ۸: کاتالوگ محصولات
        lines.append("#" * 100)
        lines.append("# فایل ۷: کاتالوگ کامل محصولات (JSON)")
        lines.append("#" * 100)
        lines.append("")

        product_catalog_path = output_files.get("product_catalog")
        if product_catalog_path and Path(product_catalog_path).exists():
            with open(product_catalog_path, 'r', encoding='utf-8') as f:
                catalog_data = json.load(f)

            lines.append("کاتالوگ کامل محصولات")
            lines.append("-" * 100)
            lines.append("")
            lines.append("JSON کامل:")
            lines.append(json.dumps(catalog_data, ensure_ascii=False, indent=2))
        else:
            lines.append("[کاتالوگ محصولات در دسترس نیست]")

        lines.append("")
        lines.append("")
        lines.append("=" * 100)
        lines.append("پایان فایل تجمیع داده‌ها")
        lines.append("=" * 100)
        lines.append(f"تعداد کل بخش‌ها: ترکیب 9 فایل")
        lines.append(f"تاریخ تولید: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 100)

        # Write with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return output_path
