"""Strategic insights agent - generates advertising and marketing recommendations."""

import json
from pathlib import Path
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from models.state import BrandIntelligenceState
from config.prompts import STRATEGIC_INSIGHTS_PROMPT
from models.output_models import InsightsOutput
from utils.logger import get_logger
from utils.helpers import load_json

logger = get_logger(__name__)


class StrategicInsightsAgent(BaseAgent):
    """Agent responsible for generating strategic advertising insights."""

    def __init__(self):
        """Initialize the strategic insights agent."""
        super().__init__("StrategicInsightsAgent")

        # Load Golrang database for cross-promotion insights
        db_path = Path("data/golrang_brands_database.json")
        self.golrang_db = load_json(db_path) if db_path.exists() else None

    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Generate strategic insights for advertising.

        Args:
            state: Current workflow state

        Returns:
            Updated state with insights populated
        """
        self._log_start()

        brand_name = state["brand_name"]
        raw_data = state.get("raw_data", {})
        relationships = state.get("relationships", {})
        categorization = state.get("categorization", {})

        # Check if we have sufficient data
        if not any([raw_data, relationships, categorization]):
            logger.warning("Insufficient data for insights generation")
            self._add_error(state, "Insufficient data for strategic analysis")
            state["insights"] = {}
            self._log_end(success=False)
            return state

        # Generate insights using LLM
        insights = self._generate_insights(
            brand_name,
            raw_data,
            relationships,
            categorization
        )

        # Update state (validated)
        self._validate_and_store(state, "insights", insights, InsightsOutput)

        self._log_end(success=True)
        return state

    def _generate_insights(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        relationships: Dict[str, Any],
        categorization: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate strategic insights using LLM or rule-based fallback.

        Args:
            brand_name: Name of the brand
            raw_data: Raw and structured data
            relationships: Relationship data
            categorization: Categorization data

        Returns:
            Dictionary containing strategic insights
        """
        # Try LLM if available
        if self.llm.is_available():
            try:
                # Prepare comprehensive data for analysis
                analysis_input = self._prepare_insights_data(
                    brand_name,
                    raw_data,
                    relationships,
                    categorization
                )

                logger.info("Generating strategic insights using LLM...")

                # Use LLM to generate insights
                prompt = f"""Analyze all available brand intelligence data and generate actionable advertising insights.

Brand: {brand_name}

{analysis_input}

{STRATEGIC_INSIGHTS_PROMPT}"""

                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt="You are a strategic advertising consultant specializing in Iranian brands.",
                    json_mode=True,
                    temperature=0.8  # Higher temperature for creative insights
                )

                insights = json.loads(response)
                logger.info("[OK] Successfully generated strategic insights")

                # Log key insights
                if insights.get("cross_promotion_opportunities"):
                    logger.info(f"  Cross-promotion opportunities: {len(insights['cross_promotion_opportunities'])}")

                if insights.get("campaign_timing", {}).get("optimal_periods"):
                    logger.info(f"  Optimal periods: {', '.join(insights['campaign_timing']['optimal_periods'])}")

                if insights.get("channel_recommendations"):
                    top_channels = [ch['channel'] for ch in insights['channel_recommendations'][:3]]
                    logger.info(f"  Top channels: {', '.join(top_channels)}")

                return insights

            except Exception as e:
                logger.error(f"LLM insights generation failed: {e}")

        # Fallback: Rule-based insights generation
        logger.info("Generating strategic insights using rule-based approach...")
        return self._rule_based_insights(brand_name, raw_data, relationships, categorization)

    def _rule_based_insights(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        relationships: Dict[str, Any],
        categorization: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive strategic insights using rule-based approach.

        Args:
            brand_name: Name of the brand
            raw_data: Raw and structured data
            relationships: Relationship data
            categorization: Categorization data

        Returns:
            Comprehensive strategic insights
        """
        insights = {
            "executive_summary": "",
            "cross_promotion_opportunities": [],
            "campaign_timing": {},
            "audience_insights": {},
            "competitive_strategy": {},
            "budget_recommendations": {},
            "channel_recommendations": [],
            "creative_direction": {},
            "success_metrics": {}
        }

        # Generate cross-promotion opportunities (from sister brands)
        sister_brands = relationships.get("sister_brands", [])
        if sister_brands:
            insights["cross_promotion_opportunities"] = self._generate_cross_promotion_opps(
                brand_name,
                sister_brands,
                categorization
            )
            logger.info(f"[Rule] Generated {len(insights['cross_promotion_opportunities'])} cross-promotion opportunities")

        # Campaign timing recommendations
        insights["campaign_timing"] = self._generate_campaign_timing(categorization)

        # Channel recommendations
        insights["channel_recommendations"] = self._generate_channel_recommendations(categorization)

        # Audience insights
        insights["audience_insights"] = self._generate_audience_insights(categorization, relationships)

        # Budget recommendations
        insights["budget_recommendations"] = self._generate_budget_recommendations(categorization, relationships)

        # Competitive strategy
        insights["competitive_strategy"] = self._generate_competitive_strategy(brand_name, categorization)

        # Creative direction
        insights["creative_direction"] = self._generate_creative_direction(brand_name, categorization)

        # Success metrics
        insights["success_metrics"] = self._generate_success_metrics(categorization)

        # Executive summary
        insights["executive_summary"] = self._generate_executive_summary(
            brand_name,
            insights,
            relationships
        )

        logger.info("[Rule] Generated comprehensive strategic insights")
        return insights

    def _generate_cross_promotion_opps(
        self,
        brand_name: str,
        sister_brands: List[Dict],
        categorization: Dict
    ) -> List[Dict]:
        """Generate cross-promotion opportunities with sister brands."""
        opportunities = []

        for brand in sister_brands[:8]:  # Top 8 brands
            synergy = brand.get("synergy_score", "MEDIUM")
            priority = {"VERY_HIGH": "high", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(synergy, "medium")

            opp = {
                "partner_brand": brand.get("name"),
                "synergy_level": synergy,
                "priority": priority,
                "campaign_concept": f"Joint campaign highlighting complementary products between {brand_name} and {brand.get('name')}",
                "target_audience": brand.get("target_audience", "families"),
                "expected_benefit": "Increased brand awareness and cross-selling",
                "implementation_difficulty": "low" if synergy in ["VERY_HIGH", "HIGH"] else "medium",
                "estimated_budget": "50-100 million Tomans" if priority == "high" else "20-50 million Tomans"
            }
            opportunities.append(opp)

        return opportunities

    def _generate_campaign_timing(self, categorization: Dict) -> Dict:
        """Generate campaign timing recommendations."""
        return {
            "optimal_periods": ["Nowruz (March)", "Back to School (September)", "Yalda Night (December)"],
            "seasonal_considerations": "Iranian cultural events drive consumer spending",
            "avoid_periods": ["Muharram (August-September)", "Ramadan fasting hours"],
            "quarterly_recommendations": {
                "Q1": "Nowruz campaigns - highest consumer spending",
                "Q2": "Summer cleaning campaigns",
                "Q3": "Back-to-school promotions",
                "Q4": "Winter and Yalda campaigns"
            }
        }

    def _generate_channel_recommendations(self, categorization: Dict) -> List[Dict]:
        """Generate marketing channel recommendations."""
        business_model = categorization.get("business_model", "B2C")

        channels = [
            {
                "channel": "Instagram",
                "priority": "high",
                "rationale": "Primary social media platform in Iran with highest engagement",
                "content_type": "Visual stories, product demonstrations, user-generated content",
                "budget_allocation": "35%"
            },
            {
                "channel": "Telegram",
                "priority": "high",
                "rationale": "Wide adoption for announcements and customer service",
                "content_type": "Promotions, customer support, exclusive deals",
                "budget_allocation": "20%"
            },
            {
                "channel": "TV (IRIB)",
                "priority": "medium",
                "rationale": "Broad reach for brand awareness",
                "content_type": "30-second commercials during prime time",
                "budget_allocation": "25%"
            },
            {
                "channel": "Out-of-Home (Billboards)",
                "priority": "medium",
                "rationale": "High visibility in urban areas",
                "content_type": "Brand awareness campaigns in Tehran metro",
                "budget_allocation": "15%"
            },
            {
                "channel": "LinkedIn",
                "priority": "low" if business_model == "B2C" else "high",
                "rationale": "Professional networking for B2B",
                "content_type": "Thought leadership, industry insights",
                "budget_allocation": "5%"
            }
        ]

        return channels

    def _generate_audience_insights(self, categorization: Dict, relationships: Dict) -> Dict:
        """Generate audience insights."""
        target_audiences = categorization.get("target_audiences", ["general_public"])

        return {
            "primary_segments": target_audiences,
            "demographic_profile": "Urban families aged 25-45, middle to upper-middle class",
            "psychographic_profile": "Value-conscious, quality-seeking, brand-loyal",
            "digital_behavior": "Active on Instagram and Telegram, increasing e-commerce adoption",
            "untapped_segments": ["Gen Z consumers", "Rural markets"],
            "overlap_with_sister_brands": "High overlap with sister brands targeting families"
        }

    def _generate_budget_recommendations(self, categorization: Dict, relationships: Dict) -> Dict:
        """Generate budget recommendations."""
        price_tier = categorization.get("price_tier", "mid")

        budget_ranges = {
            "economy": ("200-500 million Tomans", "$4,000-$10,000"),
            "mid": ("500-1000 million Tomans", "$10,000-$20,000"),
            "premium": ("1-3 billion Tomans", "$20,000-$60,000")
        }

        estimated_range = budget_ranges.get(price_tier, ("500-1000 million Tomans", "$10,000-$20,000"))

        return {
            "estimated_range_tomans": estimated_range[0],
            "estimated_range_usd": estimated_range[1],
            "allocation_by_channel": {
                "Digital (Instagram, Telegram)": "55%",
                "Traditional (TV, Billboard)": "40%",
                "Events & Sponsorships": "5%"
            },
            "rationale": f"Budget based on {price_tier} price tier and industry standards",
            "roi_expectations": "2-3x return on investment expected within 6 months"
        }

    def _generate_competitive_strategy(self, brand_name: str, categorization: Dict) -> Dict:
        """Generate competitive strategy."""
        return {
            "positioning": "Premium quality with competitive pricing",
            "differentiation_points": [
                "Strong parent company backing (Golrang Group)",
                "Established brand heritage",
                "Quality assurance and certifications"
            ],
            "competitive_advantages_to_highlight": [
                "Iranian-made with international standards",
                "Wide distribution network",
                "Family of trusted brands"
            ],
            "messaging_pillars": [
                "Quality you can trust",
                "Made for Iranian families",
                "Part of a proud heritage"
            ],
            "tone_of_voice": "Warm, trustworthy, family-oriented"
        }

    def _generate_creative_direction(self, brand_name: str, categorization: Dict) -> Dict:
        """Generate creative direction."""
        return {
            "key_messages": [
                f"{brand_name} - Quality for your family",
                "Trusted by Iranian families",
                "Experience the difference"
            ],
            "tone_and_style": "Warm, authentic, family-oriented",
            "visual_recommendations": "Bright colors, family imagery, clean modern design",
            "cultural_considerations": "Respect for Iranian values, family-centric messaging",
            "hashtag_strategy": ["#کیفیت_برتر", "#برای_خانواده", f"#{brand_name}"],
            "influencer_suggestions": "Family lifestyle influencers, home management accounts",
            "content_themes": [
                "Behind-the-scenes manufacturing",
                "Customer testimonials",
                "Product demonstrations",
                "Family moments"
            ],
            "storytelling_angle": "From our family to yours - a story of Iranian quality"
        }

    def _generate_success_metrics(self, categorization: Dict) -> Dict:
        """Generate success metrics."""
        return {
            "primary_kpis": [
                "Brand awareness lift (+20% target)",
                "Social media engagement rate (+50% target)",
                "Sales growth (+30% target)",
                "Customer acquisition cost (CAC reduction of 15%)"
            ],
            "measurement_approach": "Monthly tracking via social listening, sales data, and surveys",
            "benchmarks": "Compare against sister brands and industry averages"
        }

    def _generate_executive_summary(
        self,
        brand_name: str,
        insights: Dict,
        relationships: Dict
    ) -> str:
        """Generate executive summary."""
        parent = relationships.get("parent_company", {}).get("name", "Unknown")
        num_opportunities = len(insights.get("cross_promotion_opportunities", []))

        summary = f"""
Strategic analysis for {brand_name} reveals {num_opportunities} high-potential cross-promotion opportunities
with sister brands under {parent}. Primary recommendation: Leverage family brand synergy through
integrated campaigns targeting urban Iranian families. Focus on Instagram and Telegram for digital
engagement, with traditional TV for mass awareness. Estimated campaign budget: 500M-1B Tomans
for comprehensive multi-channel approach.
""".strip()

        return summary

    def _extract_tavily_insights(self, raw_data: Dict[str, Any]) -> str:
        """Extract key insights from Tavily AI search results.

        Args:
            raw_data: Raw data including Tavily results

        Returns:
            Formatted string of Tavily insights
        """
        insights = []
        tavily_data = raw_data.get("scraped_data", {}).get("tavily", {})

        if tavily_data:
            # Extract AI summaries
            ai_summaries = tavily_data.get("ai_summaries", [])
            if ai_summaries:
                insights.append("TAVILY AI INSIGHTS:")
                for idx, summary in enumerate(ai_summaries[:3], 1):
                    insights.append(f"{idx}. {summary}")
                insights.append("")

            # Extract top results
            top_results = tavily_data.get("top_results", [])
            if top_results:
                insights.append("KEY FINDINGS FROM WEB:")
                for result in top_results[:5]:
                    title = result.get("title", "")
                    content = result.get("content", "")[:200]
                    if title and content:
                        insights.append(f"- {title}: {content}...")
                insights.append("")

        return "\n".join(insights) if insights else "No Tavily data available."

    def _prepare_insights_data(
        self,
        brand_name: str,
        raw_data: Dict[str, Any],
        relationships: Dict[str, Any],
        categorization: Dict[str, Any]
    ) -> str:
        """Prepare comprehensive data for insights generation.

        Args:
            brand_name: Name of the brand
            raw_data: Raw data from scrapers
            relationships: Relationship data
            categorization: Categorization data

        Returns:
            Formatted string for LLM input
        """
        lines = []

        # Add Tavily AI insights FIRST (highest quality, AI-generated)
        tavily_insights = self._extract_tavily_insights(raw_data)
        if tavily_insights and "No Tavily data available" not in tavily_insights:
            lines.append("=== TAVILY AI INTELLIGENCE (USE THIS FIRST) ===")
            lines.append(tavily_insights)
            lines.append("")

        # Add structured brand data
        structured = raw_data.get("structured", {})
        if structured:
            lines.append("=== BRAND DATA ===")
            lines.append(json.dumps(structured, ensure_ascii=False, indent=2))

        # Add relationships (critical for cross-promotion)
        if relationships:
            lines.append("\n=== RELATIONSHIPS ===")
            lines.append(json.dumps(relationships, ensure_ascii=False, indent=2))

        # Add categorization (critical for targeting)
        if categorization:
            lines.append("\n=== CATEGORIZATION ===")
            lines.append(json.dumps(categorization, ensure_ascii=False, indent=2))

        # Add financial context
        scraped = raw_data.get("scraped", {})
        if scraped.get("codal"):
            lines.append("\n=== FINANCIAL CONTEXT ===")
            financial_summary = {
                "revenue": scraped["codal"].get("revenue"),
                "profit": scraped["codal"].get("profit"),
                "fiscal_year": scraped["codal"].get("fiscal_year")
            }
            lines.append(json.dumps(financial_summary, ensure_ascii=False, indent=2))

        # Add market data
        if scraped.get("tsetmc"):
            lines.append("\n=== MARKET DATA ===")
            market_summary = {
                "stock_ticker": scraped["tsetmc"].get("stock_ticker"),
                "market_cap": scraped["tsetmc"].get("market_cap"),
                "last_price": scraped["tsetmc"].get("last_price")
            }
            lines.append(json.dumps(market_summary, ensure_ascii=False, indent=2))

        # Add social media presence
        if scraped.get("linka"):
            lines.append("\n=== SOCIAL MEDIA PRESENCE ===")
            social_summary = scraped["linka"].get("social_media", {})
            lines.append(json.dumps(social_summary, ensure_ascii=False, indent=2))

        return "\n".join(lines)
