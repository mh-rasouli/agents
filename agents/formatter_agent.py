"""Output formatter agent - generates comprehensive multi-format outputs."""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import BaseAgent
from models.state import BrandIntelligenceState
from models.output_models import OutputsResult
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
        """Generate a single unified JSON report containing all brand intelligence data.

        Writes one file:
        - human_reports/brand_report.json : All content consolidated into one JSON

        Args:
            state: Current workflow state

        Returns:
            Updated state with output file path
        """
        self._log_start()

        brand_name = state["brand_name"]
        timestamp = generate_timestamp()

        safe_brand_name = sanitize_filename(brand_name)
        brand_output_dir = self.output_dir / safe_brand_name
        brand_output_dir.mkdir(exist_ok=True)

        # Temporary directories used internally by helper methods
        human_reports_dir = brand_output_dir / "human_reports"
        human_reports_dir.mkdir(exist_ok=True)
        human_exports_dir = human_reports_dir / "data_exports"
        human_exports_dir.mkdir(exist_ok=True)

        state = self._enrich_with_knowledge(state)

        output_files = {}

        try:
            logger.info(f"Generating unified JSON report for {brand_name}...")
            logger.info("=" * 60)

            # Generate intermediate files using existing helper methods
            exec_summary_path = self._generate_executive_summary(state, human_reports_dir, timestamp)
            complete_report_path = self._generate_complete_analysis_report(state, human_reports_dir, timestamp)
            quick_ref_path = self._generate_quick_reference(state, human_reports_dir, timestamp)
            brands_csv_path = self._generate_brands_database(state, human_exports_dir, timestamp)
            products_csv_path = self._generate_products_export(state, human_exports_dir, timestamp)
            opps_csv_path = self._generate_opportunities_export(state, human_exports_dir, timestamp)

            # Read content back from intermediate files
            with open(exec_summary_path, encoding='utf-8') as f:
                executive_summary_text = f.read()

            with open(complete_report_path, encoding='utf-8') as f:
                complete_report_text = f.read()

            with open(quick_ref_path, encoding='utf-8') as f:
                quick_reference = json.load(f)

            with open(brands_csv_path, encoding='utf-8-sig', newline='') as f:
                brands_database = list(csv.DictReader(f))

            with open(products_csv_path, encoding='utf-8-sig', newline='') as f:
                product_catalog_rows = list(csv.DictReader(f))

            with open(opps_csv_path, encoding='utf-8-sig', newline='') as f:
                campaign_opportunities = list(csv.DictReader(f))

            # Remove intermediate files and empty data_exports dir
            for path in [exec_summary_path, complete_report_path, quick_ref_path,
                         brands_csv_path, products_csv_path, opps_csv_path]:
                path.unlink(missing_ok=True)
            try:
                human_exports_dir.rmdir()
            except OSError:
                pass

            # Build and write the single unified report
            report_path = human_reports_dir / "brand_report.json"

            unified_report = {
                "brand_name": brand_name,
                "brand_id": quick_reference.get("brand_id", f"{safe_brand_name}_{timestamp}"),
                "generated_date": quick_reference.get("generated_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                # Formatted reports (Markdown)
                "executive_summary": executive_summary_text,
                "complete_analysis_report": complete_report_text,
                # Structured agent outputs (raw JSON from each agent)
                "structured_data": state.get("raw_data", {}).get("structured", {}),
                "relationships": state.get("relationships", {}),
                "categorization": state.get("categorization", {}),
                "insights": state.get("insights", {}),
                "product_catalog_structured": state.get("product_catalog", {}),
                # Tabular exports and summary
                "quick_reference": quick_reference,
                "brands_database": brands_database,
                "product_catalog": product_catalog_rows,
                "campaign_opportunities": campaign_opportunities,
            }

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(unified_report, f, ensure_ascii=False, indent=2)

            output_files["brand_report"] = str(report_path)

            logger.info(f"  ✓ Unified report: {report_path.name}")
            logger.info("=" * 60)
            logger.info("[SUCCESS] Output generation complete!")
            logger.info(f"  Report: {report_path}")

            self._validate_and_store(state, "outputs", output_files, OutputsResult)
            self._log_end(success=True)

        except Exception as e:
            logger.error(f"Failed to generate outputs: {e}")
            import traceback
            traceback.print_exc()
            self._add_error(state, f"Output generation failed: {e}")
            self._validate_and_store(state, "outputs", output_files, OutputsResult)
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
            # Handle both string and dict formats
            audience_strings = []
            for aud in target_audiences:
                if isinstance(aud, dict):
                    # Extract segment or name field from dict
                    audience_strings.append(aud.get("segment") or aud.get("name") or str(aud))
                else:
                    audience_strings.append(str(aud))
            lines.append(f"مخاطبان هدف: {', '.join(audience_strings)}")

        channels = categorization.get("distribution_channels", [])
        if channels:
            # Handle both string and dict formats
            channel_strings = []
            for ch in channels:
                if isinstance(ch, dict):
                    channel_strings.append(ch.get("channel") or ch.get("name") or str(ch))
                else:
                    channel_strings.append(str(ch))
            lines.append(f"کانال‌های توزیع: {', '.join(channel_strings)}")

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
        insights = state.get("insights", {})
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
            "relationship_type": "SELF",
            "parent_company": relationships.get("parent_company", {}).get("name", "Unknown"),
            "category": current_category,
            "category_level_1": current_hierarchy["category_level_1"],
            "category_level_2": current_hierarchy["category_level_2"],
            "category_level_3": current_hierarchy["category_level_3"],
            "cross_sell_potential": "SELF",
            "market_position": categorization.get("market_position", {}).get("market_share_estimate", "Unknown"),
            "price_tier": state.get("categorization", {}).get("price_tier", "Unknown")
        })

        # Add sister brands
        for brand in relationships.get("sister_brands", []):
            brand_category = brand.get("category", "Unknown")
            brand_hierarchy = self._get_category_hierarchy(brand_category)

            brands.append({
                "brand_name": brand.get("name"),
                "relationship_type": "SISTER",
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
                "relationship_type": "FAMILY",
                "parent_company": brand.get("parent", "Unknown"),
                "category": brand_category,
                "category_level_1": brand_hierarchy["category_level_1"],
                "category_level_2": brand_hierarchy["category_level_2"],
                "category_level_3": brand_hierarchy["category_level_3"],
                "cross_sell_potential": "LOW",
                "market_position": "Unknown",
                "price_tier": "Unknown"
            })

        # Add competitors
        for brand in relationships.get("competitors", []):
            brand_category = brand.get("category", "Unknown")
            brand_hierarchy = self._get_category_hierarchy(brand_category)

            brands.append({
                "brand_name": brand.get("name"),
                "relationship_type": "COMPETITOR",
                "parent_company": "Unknown",
                "category": brand_category,
                "category_level_1": brand_hierarchy["category_level_1"],
                "category_level_2": brand_hierarchy["category_level_2"],
                "category_level_3": brand_hierarchy["category_level_3"],
                "cross_sell_potential": "NONE",
                "market_position": brand.get("market_position", "Unknown"),
                "price_tier": brand.get("price_tier", "Unknown")
            })

        # Add similar brands
        for brand in relationships.get("similar_brands", []):
            brand_category = brand.get("category", "Unknown")
            brand_hierarchy = self._get_category_hierarchy(brand_category)

            brands.append({
                "brand_name": brand.get("name"),
                "relationship_type": "SIMILAR",
                "parent_company": "Unknown",
                "category": brand_category,
                "category_level_1": brand_hierarchy["category_level_1"],
                "category_level_2": brand_hierarchy["category_level_2"],
                "category_level_3": brand_hierarchy["category_level_3"],
                "cross_sell_potential": "LOW",
                "market_position": "Unknown",
                "price_tier": brand.get("price_tier", "Unknown")
            })

        # Add complementary brands from relationships
        for brand in relationships.get("complementary_brands", []):
            brand_category = brand.get("category", "Unknown")
            brand_hierarchy = self._get_category_hierarchy(brand_category)

            brands.append({
                "brand_name": brand.get("name"),
                "relationship_type": "COMPLEMENTARY",
                "parent_company": "Unknown",
                "category": brand_category,
                "category_level_1": brand_hierarchy["category_level_1"],
                "category_level_2": brand_hierarchy["category_level_2"],
                "category_level_3": brand_hierarchy["category_level_3"],
                "cross_sell_potential": brand.get("cross_sell_potential", "HIGH").upper(),
                "market_position": "Unknown",
                "price_tier": brand.get("price_tier", "Unknown")
            })

        # Add complementary brands from insights (cross-promotion opportunities)
        cross_promo = insights.get("cross_promotion_opportunities", [])
        if not cross_promo:
            # Try tier_1_opportunities from insights
            tier_1 = insights.get("tier_1_opportunities", {})
            cross_promo = tier_1.get("recommendations", [])

        for opp in cross_promo:
            partner_name = opp.get("partner_brand") or opp.get("brand_name")
            if partner_name and partner_name not in [b["brand_name"] for b in brands]:
                # Extract category from partner_brand name if possible
                brand_category = "Unknown"
                brand_hierarchy = self._get_category_hierarchy(brand_category)

                brands.append({
                    "brand_name": partner_name,
                    "relationship_type": "COMPLEMENTARY",
                    "parent_company": "Unknown",
                    "category": brand_category,
                    "category_level_1": brand_hierarchy["category_level_1"],
                    "category_level_2": brand_hierarchy["category_level_2"],
                    "category_level_3": brand_hierarchy["category_level_3"],
                    "cross_sell_potential": "HIGH",
                    "market_position": "Unknown",
                    "price_tier": "Unknown"
                })

        # Write CSV with UTF-8 encoding
        if brands:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig for Excel compatibility
                fieldnames = [
                    "brand_name",
                    "relationship_type",
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

        # Handle target_audiences (can be list of strings or dicts)
        target_auds = categorization.get('target_audiences', ['مصرف‌کنندگان عمومی'])
        aud_strings = []
        for aud in target_auds:
            if isinstance(aud, dict):
                aud_strings.append(aud.get("segment") or aud.get("name") or "مصرف‌کنندگان عمومی")
            else:
                aud_strings.append(str(aud))

        lines.append(f"با هدف‌گذاری به {', '.join(aud_strings)}.")
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
            # Handle both string and dict formats
            aud_strs = []
            for aud in target_audiences:
                if isinstance(aud, dict):
                    aud_strs.append((aud.get("segment") or aud.get("name") or str(aud)).replace('_', ' ').title())
                else:
                    aud_strs.append(str(aud).replace('_', ' ').title())
            lines.append(f"- **مخاطب هدف:** {', '.join(aud_strs)}")

        channels = categorization.get("distribution_channels", [])
        if channels:
            # Handle both string and dict formats
            ch_strs = []
            for ch in channels:
                if isinstance(ch, dict):
                    ch_strs.append((ch.get("channel") or ch.get("name") or str(ch)).title())
                else:
                    ch_strs.append(str(ch).title())
            lines.append(f"- **کانال‌های توزیع:** {', '.join(ch_strs)}")

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
                synergy = brand.get("synergy_score") or "MEDIUM"
                synergy_emoji = {"VERY_HIGH": "⭐⭐⭐", "HIGH": "⭐⭐", "MEDIUM": "⭐", "LOW": "○"}.get(synergy, "○")

                lines.append(f"#### {brand.get('name')} {synergy_emoji}")
                lines.append("")
                products = brand.get("products")
                if products and str(products) not in ("None", "null", ""):
                    lines.append(f"- **محصولات:** {products}")
                lines.append(f"- **دسته:** {brand.get('category', 'نامشخص').replace('_', ' ').title()}")
                target_aud = brand.get("target_audience")
                if target_aud and str(target_aud) not in ("None", "null", ""):
                    lines.append(f"- **مخاطب هدف:** {target_aud}")
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

            for i, opp in enumerate(cross_promo[:5], 1):
                priority = opp.get("priority") or "medium"
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

                lines.append(f"#### {i}. {opp.get('partner_brand')} {priority_emoji}")
                lines.append("")
                if opp.get("synergy_level"):
                    lines.append(f"**سطح هم‌افزایی:** {opp['synergy_level']}")
                lines.append(f"**اولویت:** {priority.upper()}")
                lines.append("")
                concept = opp.get("campaign_concept") or opp.get("recommended_approach")
                if concept:
                    lines.append(f"**مفهوم کمپین:**")
                    lines.append(concept)
                    lines.append("")
                if opp.get("target_audience"):
                    lines.append(f"**مخاطب هدف:** {opp['target_audience']}")
                if opp.get("estimated_budget"):
                    lines.append(f"**بودجه تخمینی:** {opp['estimated_budget']}")
                if opp.get("expected_benefit"):
                    lines.append(f"**منفعت مورد انتظار:** {opp['expected_benefit']}")
                if opp.get("potential_reach"):
                    lines.append(f"**دسترسی تخمینی:** {opp['potential_reach']}")
                if opp.get("timing"):
                    lines.append(f"**زمان‌بندی:** {opp['timing']}")
                diff = opp.get("implementation_difficulty")
                if diff:
                    lines.append(f"**اجرا:** سختی {diff.title()}")
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
                if ch.get("rationale"):
                    lines.append(f"**دلیل:** {ch['rationale']}")
                content = ch.get("content_type") or ch.get("content_suggestions")
                if content:
                    lines.append(f"**نوع محتوا:** {content}")
                if ch.get("budget_allocation"):
                    lines.append(f"**تخصیص بودجه:** {ch['budget_allocation']}")
                if ch.get("estimated_reach"):
                    lines.append(f"**دسترسی تخمینی:** {ch['estimated_reach']}")
                if ch.get("estimated_cost"):
                    lines.append(f"**هزینه تخمینی:** {ch['estimated_cost']}")
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
                if isinstance(msg, dict):
                    fa = msg.get("message_fa") or msg.get("message_en") or ""
                    en = msg.get("message_en", "")
                    seg = msg.get("target_segment", "")
                    if fa:
                        line = f"- **{fa}**"
                        if en and en != fa:
                            line += f" / {en}"
                        if seg:
                            line += f" *(مخاطب: {seg})*"
                        lines.append(line)
                else:
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

    # ========== NEW METHODS FOR DUAL-OUTPUT STRUCTURE ==========

    def _generate_complete_analysis_report(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate complete analysis report (MD) combining all insights."""
        output_path = output_dir / "complete_analysis_report.md"

        brand_name = state["brand_name"]
        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})
        insights = state.get("insights", {})

        lines = []
        lines.append(f"# تحلیل جامع برند: {brand_name}")
        lines.append("")
        lines.append(f"**تاریخ گزارش:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**شناسه:** {timestamp}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # بخش ۱: پروفایل برند
        lines.append("## 📋 پروفایل برند")
        lines.append("")
        lines.append(f"**نام:** {brand_name}")
        lines.append(f"**وبسایت:** {state.get('brand_website', 'نامشخص')}")

        parent = relationships.get("parent_company", {})
        if parent and parent.get("name"):
            lines.append(f"**شرکت مادر:** {parent.get('name')}")

        lines.append(f"**صنعت:** {categorization.get('primary_industry', {}).get('name_fa', 'نامشخص')}")
        lines.append(f"**مدل کسب‌وکار:** {categorization.get('business_model', 'B2C')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # بخش ۲: روابط شرکتی
        lines.append("## 🏢 ساختار شرکتی و روابط")
        lines.append("")

        sister_brands = relationships.get("sister_brands", [])
        if sister_brands:
            lines.append(f"### برندهای خواهر ({len(sister_brands)} برند)")
            lines.append("")
            for brand in sister_brands[:10]:
                synergy = brand.get("synergy_score", "MEDIUM")
                lines.append(f"- **{brand.get('name')}** ({brand.get('category', 'نامشخص')}) - هم‌افزایی: {synergy}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # بخش ۳: فرصت‌های استراتژیک
        lines.append("## 💡 فرصت‌های تبلیغات متقابل")
        lines.append("")

        cross_promo = insights.get("cross_promotion_opportunities", [])
        if cross_promo:
            for i, opp in enumerate(cross_promo[:5], 1):
                lines.append(f"### {i}. {opp.get('partner_brand')}")
                lines.append("")
                if opp.get("synergy_level"):
                    lines.append(f"- **هم‌افزایی:** {opp['synergy_level']}")
                concept = opp.get("campaign_concept") or opp.get("recommended_approach")
                if concept:
                    lines.append(f"- **مفهوم کمپین:** {concept}")
                if opp.get("target_audience"):
                    lines.append(f"- **مخاطب هدف:** {opp['target_audience']}")
                if opp.get("estimated_budget"):
                    lines.append(f"- **بودجه تخمینی:** {opp['estimated_budget']}")
                if opp.get("potential_reach"):
                    lines.append(f"- **دسترسی:** {opp['potential_reach']}")
                if opp.get("timing"):
                    lines.append(f"- **زمان‌بندی:** {opp['timing']}")
                lines.append("")

        lines.append("---")
        lines.append("")

        # بخش ۴: استراتژی کانال
        lines.append("## 📺 استراتژی کانال‌های بازاریابی")
        lines.append("")

        channel_recs = insights.get("channel_recommendations", [])
        if channel_recs:
            for ch in channel_recs:
                lines.append(f"### {ch.get('channel')}")
                if ch.get("priority"):
                    lines.append(f"- **اولویت:** {ch['priority']}")
                if ch.get("rationale"):
                    lines.append(f"- **دلیل:** {ch['rationale']}")
                content = ch.get("content_type") or ch.get("content_suggestions")
                if content:
                    lines.append(f"- **نوع محتوا:** {content}")
                if ch.get("budget_allocation"):
                    lines.append(f"- **بودجه:** {ch['budget_allocation']}")
                if ch.get("estimated_reach"):
                    lines.append(f"- **دسترسی:** {ch['estimated_reach']}")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*تولید شده توسط Brand Intelligence Agent*")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return output_path

    def _generate_quick_reference(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate quick reference JSON for dashboards/APIs."""
        output_path = output_dir / "quick_reference.json"

        brand_name = state["brand_name"]
        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})
        insights = state.get("insights", {})

        quick_ref = {
            "brand_id": f"{sanitize_filename(brand_name)}_{timestamp}",
            "brand_name": brand_name,
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "industry": categorization.get("primary_industry", {}).get("name_fa", "نامشخص"),
                "business_model": categorization.get("business_model", "B2C"),
                "price_tier": categorization.get("price_tier", "نامشخص"),
                "parent_company": relationships.get("parent_company", {}).get("name", "نامشخص")
            },
            "relationships": {
                "sister_brands_count": len(relationships.get("sister_brands", [])),
                "top_sister_brands": [
                    {
                        "name": b.get("name"),
                        "synergy": b.get("synergy_score")
                    }
                    for b in relationships.get("sister_brands", [])[:5]
                ]
            },
            "opportunities": {
                "cross_promotion_count": len(insights.get("cross_promotion_opportunities", [])),
                "top_opportunities": [
                    {
                        "partner": o.get("partner_brand"),
                        "rationale": o.get("rationale", "")[:100] + "..." if len(o.get("rationale", "")) > 100 else o.get("rationale", ""),
                        "reach": o.get("potential_reach", ""),
                        "timing": o.get("timing", "")
                    }
                    for o in insights.get("cross_promotion_opportunities", [])[:3]
                ]
            },
            "channels": {
                "recommended_count": len(insights.get("channel_recommendations", [])),
                "top_channels": [
                    {
                        "name": c.get("channel"),
                        "priority": c.get("priority")
                    }
                    for c in insights.get("channel_recommendations", [])[:3]
                ]
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(quick_ref, f, ensure_ascii=False, indent=2)

        return output_path

    def _extract_products_from_categories(self, categories_data) -> List[Dict]:
        """Extract products from various category structures.

        Args:
            categories_data: Can be dict or list of categories

        Returns:
            List of products with category info
        """
        products = []

        if isinstance(categories_data, dict):
            # Dict structure: {category_key: {products: [...], category_name: "..."}}
            for category_key, category_data in categories_data.items():
                if isinstance(category_data, dict):
                    category_name = category_data.get("category_name", category_key)
                    # Try both "products" and "services" keys
                    items = category_data.get("products", category_data.get("services", []))
                    for product in items:
                        product_with_category = product.copy() if isinstance(product, dict) else {"product_name": str(product)}
                        product_with_category["category"] = category_name
                        products.append(product_with_category)
        elif isinstance(categories_data, list):
            # List structure: [{category_name: "...", products: [...]}] or [{category: "...", services: [...]}]
            for category in categories_data:
                if isinstance(category, dict):
                    # Try different key names for category
                    category_name = category.get("category_name", category.get("category", "Unknown"))
                    # Try both "products" and "services" keys
                    items = category.get("products", category.get("services", []))
                    for product in items:
                        product_with_category = product.copy() if isinstance(product, dict) else {"product_name": str(product)}
                        product_with_category["category"] = category_name
                        products.append(product_with_category)

        return products

    def _generate_products_export(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate products export CSV."""
        output_path = output_dir / "product_catalog.csv"
        brand_output_dir = output_dir.parent  # Go up to brand directory

        product_catalog = state.get("product_catalog", {})

        # Handle nested product_catalog key (common LLM pattern where data is wrapped)
        # e.g., {brand: "...", industry: "...", product_catalog: {...}} or {product_catalog: [...]}
        if 'product_catalog' in product_catalog:
            nested_val = product_catalog['product_catalog']
            if isinstance(nested_val, dict):
                # Nested dict - unwrap it
                product_catalog = nested_val
            elif isinstance(nested_val, list):
                # Nested list - move to 'catalog' key for extraction
                product_catalog['catalog'] = nested_val
                del product_catalog['product_catalog']

        # If state is empty but JSON file exists, read from JSON file as fallback
        if not product_catalog or (
            not product_catalog.get("products") and
            not product_catalog.get("product_categories") and
            not product_catalog.get("services") and
            not product_catalog.get("catalog") and
            not product_catalog.get("categories")
        ):
            json_file = brand_output_dir / "7_product_catalog.json"
            if json_file.exists():
                try:
                    import json
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    # Extract product_categories from JSON structure
                    if "product_categories" in json_data:
                        product_catalog = {"product_categories": json_data["product_categories"]}
                    elif "complete_product_list" in json_data:
                        product_catalog = {"products": json_data["complete_product_list"]}
                    elif "services_list" in json_data:
                        product_catalog = {"services": json_data["services_list"]}
                except Exception as e:
                    logger.error(f"Error reading JSON file for products export: {e}")

        # Extract products from multiple possible locations
        # LLM may return different structures: products, services, catalog, categories, product_categories
        products = product_catalog.get("products", [])

        # Try catalog structure (list or dict of categories)
        if not products and "catalog" in product_catalog:
            catalog = product_catalog["catalog"]
            if isinstance(catalog, dict):
                # Check if catalog has categories inside it
                if "categories" in catalog:
                    products = self._extract_products_from_categories(catalog["categories"])
                # Check if catalog itself is the categories structure
                elif any(isinstance(v, dict) and ("products" in v or "category_name" in v or "services" in v) for v in catalog.values()):
                    products = self._extract_products_from_categories(catalog)
            elif isinstance(catalog, list):
                # catalog is a list of categories
                products = self._extract_products_from_categories(catalog)

        # Try categories structure (direct from state)
        if not products and "categories" in product_catalog:
            products = self._extract_products_from_categories(product_catalog["categories"])

        # Try product_categories structure
        if not products and "product_categories" in product_catalog:
            products = self._extract_products_from_categories(product_catalog["product_categories"])

        # Try services array (for healthcare/counseling brands)
        if not products and "services" in product_catalog:
            products = []
            for service in product_catalog.get("services", []):
                # Map service fields to product fields
                products.append({
                    "product_name": service.get("name", service.get("name_fa", "")),
                    "category": service.get("category", "Services"),
                    "description": service.get("type", service.get("availability", "")),
                    "target_market": service.get("availability", "Available")
                })

        if products:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ["product_name", "category", "description", "target_market"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for product in products:
                    writer.writerow({
                        "product_name": product.get("product_name", product.get("service_name", product.get("name", ""))),
                        "category": product.get("category", ""),
                        "description": product.get("description", ""),
                        "target_market": product.get("target_market", "")
                    })
        else:
            # Empty CSV with headers
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=["product_name", "category", "description", "target_market"])
                writer.writeheader()

        return output_path

    def _generate_opportunities_export(self, state: Dict, output_dir: Path, timestamp: str) -> Path:
        """Generate campaign opportunities export CSV."""
        output_path = output_dir / "campaign_opportunities.csv"

        insights = state.get("insights", {})
        opportunities = insights.get("cross_promotion_opportunities", [])

        if opportunities:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = [
                    "partner_brand",
                    "rationale",
                    "potential_reach",
                    "recommended_approach",
                    "timing"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for opp in opportunities:
                    writer.writerow({
                        "partner_brand": opp.get("partner_brand", ""),
                        "rationale": opp.get("rationale", ""),
                        "potential_reach": opp.get("potential_reach", ""),
                        "recommended_approach": opp.get("recommended_approach", ""),
                        "timing": opp.get("timing", "")
                    })
        else:
            # Empty CSV with headers
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ["partner_brand", "rationale", "potential_reach", "recommended_approach", "timing"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

        return output_path

    def _generate_semantic_chunks(self, state: Dict, chunks_dir: Path, timestamp: str) -> List[str]:
        """Generate 12 semantic chunks for vector database (500-1000 words each)."""
        brand_name = state["brand_name"]
        chunk_files = []

        # Define chunk topics and their content generators
        chunks_config = [
            ("001_brand_overview", self._generate_chunk_brand_overview),
            ("002_corporate_structure", self._generate_chunk_corporate_structure),
            ("003_sister_brands", self._generate_chunk_sister_brands),
            ("004_market_positioning", self._generate_chunk_market_positioning),
            ("005_product_catalog", self._generate_chunk_product_catalog),
            ("006_strategic_opportunities", self._generate_chunk_strategic_opportunities),
            ("007_campaign_timing", self._generate_chunk_campaign_timing),
            ("008_channel_strategy", self._generate_chunk_channel_strategy),
            ("009_budget_recommendations", self._generate_chunk_budget_recommendations),
            ("010_creative_direction", self._generate_chunk_creative_direction),
            ("011_success_metrics", self._generate_chunk_success_metrics),
            ("012_customer_intelligence", self._generate_chunk_customer_intelligence),
        ]

        for chunk_filename, generator_func in chunks_config:
            chunk_path = chunks_dir / f"{chunk_filename}.txt"
            content = generator_func(state, brand_name, timestamp)

            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(content)

            chunk_files.append(str(chunk_path))

        return chunk_files

    def _generate_chunk_brand_overview(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate brand overview chunk."""
        categorization = state.get("categorization", {})
        relationships = state.get("relationships", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Category: {categorization.get('primary_industry', {}).get('name_en', 'Consumer Products')}")
        lines.append(f"Parent: {relationships.get('parent_company', {}).get('name', 'Unknown')}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[BRAND OVERVIEW]")
        lines.append("")
        lines.append(f"{brand_name} is a brand operating in the {categorization.get('primary_industry', {}).get('name_en', 'consumer products')} industry. ")

        parent = relationships.get("parent_company", {})
        if parent and parent.get("name"):
            lines.append(f"The brand is owned by {parent.get('name')}, ")
            if parent.get("stock_symbol"):
                lines.append(f"which trades under the stock symbol {parent.get('stock_symbol')} on the Tehran Stock Exchange. ")

        ultimate = relationships.get("ultimate_parent", {})
        if ultimate and ultimate.get("name"):
            lines.append(f"The ultimate parent company is {ultimate.get('name_fa', ultimate.get('name'))}, ")
            if ultimate.get('total_brands'):
                lines.append(f"which manages a portfolio of {ultimate.get('total_brands')} brands ")
            if ultimate.get('market_cap'):
                lines.append(f"with an estimated market capitalization of {ultimate.get('market_cap')}. ")

        lines.append(f"The brand operates under a {categorization.get('business_model', 'B2C')} business model, ")
        lines.append(f"positioned in the {categorization.get('price_tier', 'mid')} price tier. ")

        website = state.get('brand_website', '')
        if website:
            lines.append(f"The official website is {website}. ")

        return "\n".join(lines)

    def _generate_chunk_corporate_structure(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate corporate structure chunk."""
        relationships = state.get("relationships", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[CORPORATE STRUCTURE]")
        lines.append("")

        parent = relationships.get("parent_company", {})
        ultimate = relationships.get("ultimate_parent", {})

        lines.append(f"The corporate structure of {brand_name} represents a complex hierarchy of ownership and brand management. ")

        if parent and parent.get("name"):
            lines.append(f"As a direct subsidiary of {parent.get('name')}, the brand benefits from established distribution networks, ")
            lines.append(f"operational expertise, and financial stability. The parent company operates in the {parent.get('industry', 'consumer products')} sector, ")
            lines.append("providing strategic alignment and synergies across the brand portfolio. ")

        if ultimate and ultimate.get("name"):
            lines.append(f"The ultimate parent organization, {ultimate.get('name_fa', ultimate.get('name'))}, ")
            if ultimate.get('description'):
                lines.append(f"is {ultimate.get('description')}. ")
            if ultimate.get('employees'):
                lines.append(f"With a workforce of {ultimate.get('employees')} employees ")
            if ultimate.get('market_cap'):
                lines.append(f"and market capitalization of {ultimate.get('market_cap')}, ")
            lines.append("the group provides substantial resources and market presence. ")

        brand_family = relationships.get("brand_family", [])
        if brand_family:
            lines.append(f"The broader brand family includes {len(brand_family)} brands across various categories, ")
            lines.append("creating opportunities for cross-promotion and integrated marketing campaigns. ")

        return "\n".join(lines)

    def _generate_chunk_sister_brands(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate sister brands chunk."""
        relationships = state.get("relationships", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[SISTER BRANDS AND RELATIONSHIPS]")
        lines.append("")

        sister_brands = relationships.get("sister_brands", [])

        if sister_brands:
            lines.append(f"{brand_name} is part of a family of {len(sister_brands)} sister brands under the same parent company. ")
            lines.append("These sister brands create significant opportunities for cross-promotion and integrated marketing:")
            lines.append("")

            for brand in sister_brands:
                lines.append(f"- {brand.get('name')}: Specializes in {brand.get('products', 'consumer products')}, ")
                lines.append(f"  targeting {brand.get('target_audience', 'general consumers')} with a synergy score of {brand.get('synergy_score', 'MEDIUM')}. ")
                lines.append(f"  This brand operates in the {brand.get('category', 'consumer')} category with {brand.get('price_tier', 'mid')} pricing. ")
                lines.append("")

        competitors = relationships.get("competitors", [])
        if competitors:
            lines.append("Key competitors in the market include: ")
            for comp in competitors[:5]:
                lines.append(f"- {comp.get('name')} ({comp.get('category', 'same category')})")
            lines.append("")

        return "\n".join(lines)

    def _generate_chunk_market_positioning(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate market positioning chunk."""
        categorization = state.get("categorization", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[MARKET POSITIONING]")
        lines.append("")

        lines.append(f"{brand_name} operates with a {categorization.get('business_model', 'B2C')} business model, ")

        target_audiences = categorization.get('target_audiences', [])
        if target_audiences:
            aud_strs = []
            for aud in target_audiences:
                if isinstance(aud, dict):
                    aud_strs.append(aud.get("segment") or aud.get("name") or "general consumers")
                else:
                    aud_strs.append(str(aud))
            lines.append(f"targeting {', '.join(aud_strs)}. ")

        lines.append(f"The brand is positioned in the {categorization.get('price_tier', 'mid')} price tier, ")
        lines.append("balancing quality and affordability to capture maximum market share. ")

        market_position = categorization.get("market_position", {})
        if market_position:
            lines.append(f"Market position: {market_position.get('positioning', 'competitive')}. ")
            lines.append(f"Competitive landscape: {market_position.get('competitive_landscape', 'dynamic and competitive')}. ")

        channels = categorization.get("distribution_channels", [])
        if channels:
            lines.append(f"Distribution channels include {', '.join([str(c) for c in channels])}, ")
            lines.append("ensuring broad market coverage and accessibility to target consumers. ")

        return "\n".join(lines)

    def _generate_chunk_product_catalog(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate comprehensive product catalog chunk (min 300 words)."""
        product_catalog = state.get("product_catalog", {})
        categorization = state.get("categorization", {})
        raw_data = state.get("raw_data", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("PRODUCT & SERVICE CATALOG")
        lines.append("=" * 60)
        lines.append("")

        # Add industry context
        industry = categorization.get("primary_industry", {}).get("name_en", "Various")
        business_model = categorization.get("business_model", "B2C")
        price_tier = categorization.get("price_tier", "mid-market")

        lines.append(f"BRAND POSITIONING:")
        lines.append(f"Industry: {industry}")
        lines.append(f"Business Model: {business_model}")
        lines.append(f"Price Tier: {price_tier}")
        lines.append("")

        # Extract all products using the helper method
        all_products = []

        # Try all possible structures
        for key in ['products', 'catalog', 'categories', 'product_categories']:
            if key in product_catalog:
                if key in ['catalog', 'categories', 'product_categories']:
                    extracted = self._extract_products_from_categories(product_catalog[key])
                    all_products.extend(extracted)
                elif isinstance(product_catalog[key], list):
                    all_products.extend(product_catalog[key])

        # Also check for services
        services = product_catalog.get("services", [])
        if services:
            all_products.extend(services)

        if all_products:
            lines.append(f"CATALOG OVERVIEW:")
            lines.append(f"{brand_name} offers {len(all_products)} products/services in the {industry} sector.")
            lines.append("")

            # Group by category
            by_category = {}
            for product in all_products:
                cat = product.get('category', 'Uncategorized')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(product)

            lines.append(f"PRODUCT CATEGORIES ({len(by_category)} categories):")
            lines.append("")

            for category, items in by_category.items():
                lines.append(f"[{category}] - {len(items)} items")
                lines.append("-" * 50)

                for item in items[:10]:  # Top 10 per category
                    name = item.get('product_name', item.get('service_name', item.get('name', 'Product')))
                    desc = item.get('description', 'Premium offering')
                    target = item.get('target_market', 'General consumers')

                    lines.append(f"• {name}")
                    lines.append(f"  Description: {desc}")
                    lines.append(f"  Target: {target}")
                    lines.append("")

        else:
            # Provide substantial fallback content
            lines.append(f"PRODUCT INTELLIGENCE FOR {brand_name}:")
            lines.append("")
            lines.append(f"Based on analysis of {brand_name} in the {industry} sector,")
            lines.append(f"the brand operates with a {business_model} business model,")
            lines.append(f"positioned in the {price_tier} price tier.")
            lines.append("")

            # Add Tavily insights if available
            tavily_data = raw_data.get("scraped_data", {}).get("tavily", {})
            if tavily_data and tavily_data.get("top_results"):
                lines.append("MARKET INTELLIGENCE:")
                for result in tavily_data["top_results"][:3]:
                    if result.get("content"):
                        lines.append(f"- {result['content'][:150]}...")
                lines.append("")

            lines.append("TYPICAL PRODUCT CATEGORIES IN THIS INDUSTRY:")
            lines.append(f"Products and services are being cataloged based on {industry}")
            lines.append("market standards and competitive analysis.")

        # Add value propositions
        lines.append("")
        lines.append("BRAND VALUE PROPOSITIONS:")
        positioning = categorization.get("market_position", {})
        advantages = positioning.get("competitive_advantages", [
            f"Established presence in {industry}",
            f"Proven {business_model} delivery model",
            f"Competitive positioning in {price_tier} segment"
        ])

        for adv in advantages[:5]:
            lines.append(f"✓ {adv}")

        return "\n".join(lines)

    def _generate_chunk_strategic_opportunities(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate comprehensive strategic opportunities chunk (min 300 words)."""
        insights = state.get("insights", {})
        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("=" * 60)
        lines.append("STRATEGIC CROSS-PROMOTION OPPORTUNITIES")
        lines.append("=" * 60)
        lines.append("")

        # Add context
        industry = categorization.get("primary_industry", {}).get("name_en", "Various")
        business_model = categorization.get("business_model", "B2C")
        lines.append(f"MARKET CONTEXT:")
        lines.append(f"Industry: {industry}")
        lines.append(f"Business Model: {business_model}")
        lines.append(f"Sister Brands: {len(relationships.get('sister_brands', []))}")
        lines.append(f"Complementary Brands: {len(relationships.get('complementary_brands', []))}")
        lines.append("")

        cross_promo = insights.get("cross_promotion_opportunities", [])

        if cross_promo:
            lines.append(f"IDENTIFIED OPPORTUNITIES ({len(cross_promo)} partnerships):")
            lines.append("")

            for i, opp in enumerate(cross_promo, 1):
                partner = opp.get('partner_brand', 'Unknown Partner')
                lines.append(f"{i}. PARTNERSHIP: {brand_name} × {partner}")
                lines.append("-" * 50)

                # Rationale
                rationale = opp.get('rationale', 'Strategic partnership opportunity')
                lines.append(f"STRATEGIC RATIONALE:")
                lines.append(f"{rationale}")
                lines.append("")

                # Reach and Impact
                reach = opp.get('potential_reach', 'Significant market reach')
                lines.append(f"POTENTIAL REACH: {reach}")
                lines.append("")

                # Campaign Approach
                approach = opp.get('recommended_approach', 'Collaborative marketing campaign')
                lines.append(f"RECOMMENDED CAMPAIGN APPROACH:")
                lines.append(f"{approach}")
                lines.append("")

                # Timing
                timing = opp.get('timing', 'Year-round opportunity')
                lines.append(f"OPTIMAL TIMING: {timing}")
                lines.append("")

                # Add value proposition
                lines.append(f"EXPECTED VALUE:")
                lines.append(f"- Enhanced brand visibility through partner network")
                lines.append(f"- Access to {partner}'s customer base")
                lines.append(f"- Shared marketing costs and resources")
                lines.append(f"- Strengthened market position in {industry}")
                lines.append("")

        else:
            # Even if no opportunities, provide substantial content
            lines.append("OPPORTUNITY DEVELOPMENT IN PROGRESS:")
            lines.append("")
            lines.append(f"For {brand_name}, strategic partnership opportunities are being")
            lines.append(f"evaluated based on market position, audience overlap, and brand synergy.")
            lines.append("")
            lines.append("RECOMMENDED PARTNERSHIP CRITERIA:")
            lines.append(f"1. Brands serving similar demographics in {industry}")
            lines.append(f"2. Complementary product/service offerings")
            lines.append(f"3. Shared values and brand positioning")
            lines.append(f"4. Compatible customer acquisition channels")
            lines.append("")

            # Add sister brands as opportunities if available
            sister_brands = relationships.get("sister_brands", [])
            if sister_brands:
                lines.append(f"SISTER BRAND OPPORTUNITIES ({len(sister_brands)} brands):")
                for brand in sister_brands[:5]:
                    lines.append(f"- {brand.get('name')}: {brand.get('industry', 'Related industry')}")

        # Add conclusion
        lines.append("")
        lines.append("IMPLEMENTATION CONSIDERATIONS:")
        lines.append("- Partnership agreements and revenue sharing models")
        lines.append("- Joint marketing budget allocation")
        lines.append("- Brand guidelines and co-branding standards")
        lines.append("- Performance metrics and success criteria")
        lines.append("- Timeline and rollout strategy for Iranian market")

        return "\n".join(lines)

    def _generate_chunk_campaign_timing(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate campaign timing chunk."""
        insights = state.get("insights", {})
        timing = insights.get("campaign_timing", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[CAMPAIGN TIMING RECOMMENDATIONS]")
        lines.append("")

        optimal = timing.get("optimal_periods", [])
        if optimal:
            lines.append("Optimal campaign periods for maximum impact:")
            for period in optimal:
                lines.append(f"- {period}: High consumer engagement and spending")
            lines.append("")

        avoid = timing.get("avoid_periods", [])
        if avoid:
            lines.append("Periods to avoid for commercial campaigns:")
            for period in avoid:
                lines.append(f"- {period}")
            lines.append("")

        quarterly = timing.get("quarterly_recommendations", {})
        if quarterly:
            lines.append("Quarterly breakdown:")
            for quarter, rec in quarterly.items():
                lines.append(f"{quarter}: {rec}")
            lines.append("")

        seasonal = timing.get("seasonal_considerations")
        if seasonal:
            lines.append(f"Cultural context: {seasonal}")
            lines.append("")

        return "\n".join(lines)

    def _generate_chunk_channel_strategy(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate channel strategy chunk."""
        insights = state.get("insights", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[MARKETING CHANNEL STRATEGY]")
        lines.append("")

        channel_recs = insights.get("channel_recommendations", [])

        if channel_recs:
            for ch in channel_recs:
                lines.append(f"{ch.get('channel')} (Priority: {ch.get('priority')})")
                lines.append(f"  Rationale: {ch.get('rationale')}")
                lines.append(f"  Content Type: {ch.get('content_type', 'mixed content')}")
                lines.append(f"  Budget Allocation: {ch.get('budget_allocation', 'TBD')}")
                lines.append("")

        return "\n".join(lines)

    def _generate_chunk_budget_recommendations(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate budget recommendations chunk."""
        insights = state.get("insights", {})
        budget = insights.get("budget_recommendations", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[BUDGET AND INVESTMENT RECOMMENDATIONS]")
        lines.append("")

        if budget:
            if budget.get('estimated_range_tomans'):
                lines.append(f"Recommended annual advertising budget: {budget.get('estimated_range_tomans')}")
            if budget.get('estimated_range_usd'):
                lines.append(f"USD equivalent: {budget.get('estimated_range_usd')}")
            if budget.get('roi_expectations'):
                lines.append(f"Expected return on investment: {budget.get('roi_expectations')}")
            lines.append("")

            allocation = budget.get("allocation_by_channel", {})
            if allocation:
                lines.append("Recommended channel allocation:")
                for channel, percent in allocation.items():
                    lines.append(f"- {channel}: {percent}")
                lines.append("")

        return "\n".join(lines)

    def _generate_chunk_creative_direction(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate creative direction chunk."""
        insights = state.get("insights", {})
        creative = insights.get("creative_direction", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[CREATIVE DIRECTION AND MESSAGING]")
        lines.append("")

        if creative:
            messages = creative.get("key_messages", [])
            if messages:
                lines.append("Key brand messages:")
                for msg in messages:
                    lines.append(f"- {msg}")
                lines.append("")

            if creative.get("tone_and_style"):
                lines.append(f"Tone and style: {creative['tone_and_style']}")
            if creative.get("visual_recommendations"):
                lines.append(f"Visual recommendations: {creative['visual_recommendations']}")
            if creative.get("cultural_considerations"):
                lines.append(f"Cultural considerations: {creative['cultural_considerations']}")
            lines.append("")

            hashtags = creative.get("hashtag_strategy", [])
            if hashtags:
                lines.append(f"Hashtag strategy: {' '.join(hashtags)}")
                lines.append("")

        return "\n".join(lines)

    def _generate_chunk_success_metrics(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate success metrics chunk."""
        insights = state.get("insights", {})
        metrics = insights.get("success_metrics", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[SUCCESS METRICS AND KEY PERFORMANCE INDICATORS]")
        lines.append("")

        kpis = metrics.get("primary_kpis", [])
        if kpis:
            lines.append("Primary KPIs for campaign success:")
            for kpi in kpis:
                lines.append(f"- {kpi}")
            lines.append("")

        if metrics.get("measurement_approach"):
            lines.append(f"Measurement approach: {metrics['measurement_approach']}")
        if metrics.get("benchmarks"):
            lines.append(f"Benchmarks: {metrics['benchmarks']}")
        lines.append("")

        return "\n".join(lines)

    def _generate_chunk_customer_intelligence(self, state: Dict, brand_name: str, timestamp: str) -> str:
        """Generate customer intelligence chunk."""
        customer_intel = state.get("customer_intelligence", {})

        lines = []
        lines.append(f"Brand: {brand_name}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("[CUSTOMER INTELLIGENCE]")
        lines.append("")

        if customer_intel.get("status") == "completed":
            lines.append(f"Customer intelligence data is available for {brand_name}. ")
            lines.append(f"Transaction count: {customer_intel.get('transaction_count', 0)}")
            lines.append(f"Campaign count: {customer_intel.get('campaign_count', 0)}")
            if customer_intel.get('total_revenue'):
                lines.append(f"Total revenue: {customer_intel.get('total_revenue'):,.0f} Tomans")
            lines.append("")
            lines.append("This data provides insights into past campaign performance, ")
            lines.append("customer engagement patterns, and revenue generation. ")
        else:
            lines.append(f"Customer intelligence data for {brand_name} is not currently available. ")
            lines.append("This information would include transaction history, campaign performance, ")
            lines.append("and customer engagement metrics. ")

        return "\n".join(lines)

    def _generate_metadata(self, state: Dict, vector_db_dir: Path, timestamp: str, chunk_files: List[str]) -> Path:
        """Generate metadata.json for vector database filtering."""
        output_path = vector_db_dir / "metadata.json"

        brand_name = state["brand_name"]
        categorization = state.get("categorization", {})
        relationships = state.get("relationships", {})
        primary_industry = categorization.get("primary_industry", {})

        # Build chunks metadata
        chunks_metadata = []
        chunk_topics = [
            "brand_overview", "corporate_structure", "sister_brands", "market_positioning",
            "product_catalog", "strategic_opportunities", "campaign_timing", "channel_strategy",
            "budget_recommendations", "creative_direction", "success_metrics", "customer_intelligence"
        ]

        for idx, chunk_file in enumerate(chunk_files):
            chunk_path = Path(chunk_file)
            # Read chunk to get word count
            with open(chunk_path, 'r', encoding='utf-8') as f:
                content = f.read()
                word_count = len(content.split())

            chunks_metadata.append({
                "chunk_id": f"{idx+1:03d}",
                "filename": chunk_path.name,
                "topic": chunk_topics[idx] if idx < len(chunk_topics) else "misc",
                "word_count": word_count,
                "language": "mixed_fa_en",
                "tags": [chunk_topics[idx]] if idx < len(chunk_topics) else []
            })

        metadata = {
            "brand_id": f"{sanitize_filename(brand_name)}_{timestamp}",
            "brand_name": brand_name,
            "brand_name_en": brand_name,  # Could add translation logic
            "parent_company": relationships.get("parent_company", {}).get("name", "Unknown"),
            "industry": primary_industry.get("name_en", "Unknown"),
            "industry_code": primary_industry.get("isic_code", ""),
            "category_l1": primary_industry.get("category_level_1", "Consumer_Products"),
            "category_l2": primary_industry.get("category_level_2", "General_Products"),
            "category_l3": primary_industry.get("category_level_3", "Products"),
            "business_model": categorization.get("business_model", "B2C"),
            "price_tier": categorization.get("price_tier", "mid"),
            "total_sister_brands": len(relationships.get("sister_brands", [])),
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "data_sources": ["web", "knowledge_base"],
            "has_customer_data": state.get("customer_intelligence", {}).get("status") == "completed",
            "chunks": chunks_metadata
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return output_path

    def _generate_entities(self, state: Dict, vector_db_dir: Path, timestamp: str) -> Path:
        """Generate entities.jsonl for knowledge graphs."""
        output_path = vector_db_dir / "entities.jsonl"

        brand_name = state["brand_name"]
        categorization = state.get("categorization", {})
        relationships = state.get("relationships", {})
        product_catalog = state.get("product_catalog", {})

        entities = []

        # Add main brand entity
        entities.append({
            "entity_id": f"brand_{sanitize_filename(brand_name).lower()}",
            "type": "brand",
            "name": brand_name,
            "name_en": brand_name,
            "industry": categorization.get("primary_industry", {}).get("name_en", ""),
            "parent": f"company_{sanitize_filename(relationships.get('parent_company', {}).get('name', 'unknown')).lower()}"
        })

        # Add parent company entity
        parent = relationships.get("parent_company", {})
        if parent and parent.get("name"):
            entities.append({
                "entity_id": f"company_{sanitize_filename(parent['name']).lower()}",
                "type": "company",
                "name": parent.get("name"),
                "stock_symbol": parent.get("stock_symbol", ""),
                "industry": parent.get("industry", "")
            })

        # Add sister brands
        for sister in relationships.get("sister_brands", []):
            entities.append({
                "entity_id": f"brand_{sanitize_filename(sister.get('name', '')).lower()}",
                "type": "brand",
                "name": sister.get("name"),
                "parent": f"company_{sanitize_filename(parent.get('name', 'unknown')).lower()}",
                "relation": "sister",
                "category": sister.get("category", "")
            })

        # Add products
        for product in product_catalog.get("products", [])[:50]:  # Limit to 50
            entities.append({
                "entity_id": f"product_{sanitize_filename(product.get('name', '')).lower()}",
                "type": "product",
                "name": product.get("name"),
                "brand": f"brand_{sanitize_filename(brand_name).lower()}",
                "category": product.get("category", "")
            })

        # Write as JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for entity in entities:
                f.write(json.dumps(entity, ensure_ascii=False) + "\n")

        return output_path

    def _generate_relationships_graph(self, state: Dict, vector_db_dir: Path, timestamp: str) -> Path:
        """Generate relationships.json for brand relationship graph."""
        output_path = vector_db_dir / "relationships.json"

        brand_name = state["brand_name"]
        relationships = state.get("relationships", {})
        insights = state.get("insights", {})

        # Build cross-promotion partners
        cross_promo_partners = []
        for opp in insights.get("cross_promotion_opportunities", []):
            cross_promo_partners.append({
                "brand": opp.get("partner_brand"),
                "synergy": opp.get("synergy_level", "MEDIUM").upper(),
                "opportunity": opp.get("campaign_concept", "")
            })

        # Build graph nodes and edges
        nodes = []
        edges = []

        # Main brand node
        nodes.append({
            "id": sanitize_filename(brand_name).lower(),
            "type": "brand",
            "label": brand_name
        })

        # Parent company node
        parent = relationships.get("parent_company", {})
        if parent and parent.get("name"):
            parent_id = sanitize_filename(parent["name"]).lower()
            nodes.append({
                "id": parent_id,
                "type": "parent",
                "label": parent.get("name")
            })
            edges.append({
                "from": sanitize_filename(brand_name).lower(),
                "to": parent_id,
                "type": "owned_by"
            })

        # Sister brands
        for sister in relationships.get("sister_brands", []):
            sister_id = sanitize_filename(sister.get("name", "")).lower()
            nodes.append({
                "id": sister_id,
                "type": "sister",
                "label": sister.get("name")
            })
            edges.append({
                "from": sanitize_filename(brand_name).lower(),
                "to": sister_id,
                "type": "sister_brand",
                "synergy": sister.get("synergy_score", "MEDIUM")
            })

        # Competitors
        for comp in relationships.get("competitors", [])[:5]:
            comp_id = sanitize_filename(comp.get("name", "")).lower()
            nodes.append({
                "id": comp_id,
                "type": "competitor",
                "label": comp.get("name")
            })
            edges.append({
                "from": sanitize_filename(brand_name).lower(),
                "to": comp_id,
                "type": "competes_with"
            })

        graph_data = {
            "brand": brand_name,
            "relationships": {
                "parent_of": [],
                "child_of": [parent.get("name")] if parent and parent.get("name") else [],
                "sister_of": [s.get("name") for s in relationships.get("sister_brands", [])],
                "competes_with": [c.get("name") for c in relationships.get("competitors", [])],
                "partners_with": [],
                "cross_promotion_with": cross_promo_partners
            },
            "graph": {
                "nodes": nodes,
                "edges": edges
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        return output_path

    def _generate_embedding_manifest(self, state: Dict, vector_db_dir: Path, timestamp: str, chunk_files: List[str]) -> Path:
        """Generate embedding_manifest.json for embedding pipeline."""
        output_path = vector_db_dir / "embedding_manifest.json"

        brand_name = state["brand_name"]

        files_list = []
        for chunk_file in chunk_files:
            chunk_path = Path(chunk_file)
            files_list.append({
                "path": f"chunks/{chunk_path.name}",
                "should_embed": True,
                "priority": "high"
            })

        manifest = {
            "manifest_version": "1.0",
            "brand": brand_name,
            "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "embedding_config": {
                "model": "text-embedding-3-large",
                "dimensions": 3072,
                "chunk_strategy": "semantic_topic",
                "chunk_size_words": "500-1000",
                "overlap_words": 50,
                "languages": ["fa", "en"]
            },
            "vector_database": {
                "recommended_provider": "pinecone|qdrant|weaviate",
                "index_name": "brand_intelligence",
                "namespace": f"{sanitize_filename(brand_name).lower()}_{timestamp}",
                "metadata_fields": [
                    "brand_name",
                    "industry",
                    "category_l1",
                    "category_l2",
                    "topic",
                    "analysis_date"
                ]
            },
            "files": files_list
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        return output_path
