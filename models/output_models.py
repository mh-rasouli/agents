"""Pydantic v2 output models for all agents.

Validates agent outputs before storing in BrandIntelligenceState.
All models use extra="allow" to tolerate unexpected LLM fields.
validate_agent_output() never raises — logs warning and returns original dict on failure.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PriceTier(str, Enum):
    economy = "economy"
    economy_to_mid = "economy_to_mid"
    mid = "mid"
    mid_to_premium = "mid_to_premium"
    premium = "premium"
    luxury = "luxury"
    varied = "varied"


class SynergyScore(str, Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class BusinessModel(str, Enum):
    B2C = "B2C"
    B2B = "B2B"
    B2B_and_B2C = "B2B_and_B2C"
    B2G = "B2G"
    marketplace = "marketplace"


class MarketPosition(str, Enum):
    leader = "leader"
    challenger = "challenger"
    follower = "follower"
    niche = "niche"
    unknown = "unknown"


class CompetitiveStrength(str, Enum):
    strong = "strong"
    moderate = "moderate"
    weak = "weak"


class CrossSellPotential(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ShareholderType(str, Enum):
    institutional = "institutional"
    individual = "individual"
    government = "government"
    corporate = "corporate"


# ---------------------------------------------------------------------------
# Shared config mixin
# ---------------------------------------------------------------------------

_EXTRA_ALLOW = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Agent 1 — DataCollection
# ---------------------------------------------------------------------------

class ContactInfo(BaseModel):
    model_config = _EXTRA_ALLOW
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    addresses: List[str] = Field(default_factory=list)


class SocialMediaAccount(BaseModel):
    model_config = _EXTRA_ALLOW
    platform: str = ""
    url: str = ""
    followers: Optional[int] = None


class WebsiteInfo(BaseModel):
    model_config = _EXTRA_ALLOW
    title: Optional[str] = None
    meta_description: Optional[str] = None
    is_javascript_site: bool = False
    data_richness: float = 0.0
    headings: List[Any] = Field(default_factory=list)
    content_summary: str = ""
    about_us: str = ""
    internal_links: List[str] = Field(default_factory=list)


class StructuredData(BaseModel):
    model_config = _EXTRA_ALLOW
    sources_used: List[str] = Field(default_factory=list)
    contact_info: Union[ContactInfo, Dict[str, Any]] = Field(default_factory=dict)
    social_media: Dict[str, Any] = Field(default_factory=dict)
    website_info: Union[WebsiteInfo, Dict[str, Any]] = Field(default_factory=dict)


class RawDataOutput(BaseModel):
    """Output of Agent 1 (DataCollectionAgent) — stored in state['raw_data']."""
    model_config = _EXTRA_ALLOW
    scraped: Dict[str, Any] = Field(default_factory=dict)
    structured: Union[StructuredData, Dict[str, Any]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Agent 2 — Relationships
# ---------------------------------------------------------------------------

class ParentCompany(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    name_fa: str = ""
    stock_symbol: Optional[str] = None
    industry: str = ""
    relation_type: str = ""
    source: str = ""


class UltimateParent(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    name_fa: str = ""
    brand_name: str = ""
    established: str = ""
    headquarters: str = ""
    employees: Union[str, int] = ""
    description: str = ""
    description_en: str = ""
    website: str = ""
    market_cap: Union[str, int, None] = None
    total_brands: Optional[int] = None
    source: str = ""


class Subsidiary(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    name_fa: str = ""
    industry: str = ""
    stock_symbol: Optional[str] = None


class SisterBrand(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    name_fa: str = ""
    products: Optional[Any] = None
    category: str = ""
    # Kept as str (not enum) — LLM returns too many variants
    price_tier: str = ""
    target_audience: str = ""
    relation: str = ""
    synergy_score: str = ""
    synergy_potential: str = ""
    role: str = ""
    established: str = ""
    website: str = ""
    focus: str = ""
    focus_fa: str = ""
    industry: str = ""
    business_model: str = ""
    description: str = ""
    description_en: str = ""
    market_position: str = ""
    parent: str = ""


class Shareholder(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    share_percentage: Optional[float] = None
    shareholder_type: str = ""


class Affiliate(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    relationship: str = ""


class BrandFamilyMember(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    parent: str = ""
    category: str = ""
    relation: str = ""


class Competitor(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    market_share: Optional[str] = None


class SimilarBrand(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    similarity: str = ""


class ComplementaryBrand(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    complementary_reason: str = ""


class ParentCompanyVerification(BaseModel):
    model_config = _EXTRA_ALLOW
    status: str = ""
    user_provided: str = ""
    system_found: str = ""
    warning: str = ""
    message: str = ""
    corrected_to: str = ""


class RelationshipsOutput(BaseModel):
    """Output of Agent 2 (RelationshipMappingAgent) — stored in state['relationships']."""
    model_config = _EXTRA_ALLOW
    parent_company: Union[ParentCompany, Dict[str, Any]] = Field(default_factory=dict)
    ultimate_parent: Union[UltimateParent, Dict[str, Any]] = Field(default_factory=dict)
    subsidiaries: List[Union[Subsidiary, Dict[str, Any]]] = Field(default_factory=list)
    sister_brands: List[Union[SisterBrand, Dict[str, Any]]] = Field(default_factory=list)
    shareholders: List[Union[Shareholder, Dict[str, Any]]] = Field(default_factory=list)
    affiliates: List[Union[Affiliate, Dict[str, Any]]] = Field(default_factory=list)
    brand_family: List[Union[BrandFamilyMember, Dict[str, Any]]] = Field(default_factory=list)
    competitors: List[Union[Competitor, Dict[str, Any]]] = Field(default_factory=list)
    similar_brands: List[Union[SimilarBrand, Dict[str, Any]]] = Field(default_factory=list)
    complementary_brands: List[Union[ComplementaryBrand, Dict[str, Any]]] = Field(default_factory=list)
    parent_company_verification: Union[ParentCompanyVerification, Dict[str, Any]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Agent 3 — Categorization
# ---------------------------------------------------------------------------

class PrimaryIndustry(BaseModel):
    model_config = _EXTRA_ALLOW
    name_en: str = ""
    name_fa: str = ""
    isic_code: str = ""
    category_level_1: str = ""
    category_level_2: str = ""
    category_level_3: str = ""
    source: str = ""


class TargetAudienceSegment(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    description: str = ""


class MarketPositionInfo(BaseModel):
    model_config = _EXTRA_ALLOW
    positioning: str = "unknown"
    estimated_market_share: str = "unknown"
    competitive_landscape: str = "competitive"


class CategorizationOutput(BaseModel):
    """Output of Agent 3 (CategorizationAgent) — stored in state['categorization']."""
    model_config = _EXTRA_ALLOW
    primary_industry: Union[PrimaryIndustry, Dict[str, Any]] = Field(default_factory=dict)
    sub_industries: List[str] = Field(default_factory=list)
    product_categories: List[str] = Field(default_factory=list)
    business_model: str = "B2C"
    price_tier: str = "mid"
    # Accepts both plain strings (rule-based) and dicts with segment/description/size_estimate
    # (new LLM prompt format)
    target_audiences: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    distribution_channels: List[str] = Field(default_factory=list)
    market_position: Union[MarketPositionInfo, Dict[str, Any]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Agent 4 — ProductCatalog
# ---------------------------------------------------------------------------

class Product(BaseModel):
    model_config = _EXTRA_ALLOW
    product_name: str = ""
    name: str = ""
    name_fa: str = ""
    description: str = ""
    target_market: str = ""
    key_features: List[str] = Field(default_factory=list)
    category: str = ""
    type: str = ""
    availability: str = ""


class Service(BaseModel):
    model_config = _EXTRA_ALLOW
    name: str = ""
    name_fa: str = ""
    category: str = ""
    type: str = "service"
    availability: str = ""
    description: str = ""


class ProductCatalogOutput(BaseModel):
    """Output of Agent 4 (ProductCatalogAgent) — stored in state['product_catalog']."""
    model_config = _EXTRA_ALLOW
    extraction_method: str = ""
    total_products: int = 0
    categories: Union[Dict[str, Any], List[Any]] = Field(default_factory=dict)
    products: List[Union[Product, Dict[str, Any]]] = Field(default_factory=list)
    services: List[Union[Service, Dict[str, Any]]] = Field(default_factory=list)
    therapeutic_areas: List[str] = Field(default_factory=list)
    product_lines: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    market_intelligence: Dict[str, Any] = Field(default_factory=dict)
    product_statistics: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Agent 5 — Insights
# ---------------------------------------------------------------------------

class CrossPromotionOpportunity(BaseModel):
    model_config = _EXTRA_ALLOW
    partner_brand: Optional[str] = None
    synergy_level: str = ""
    priority: str = ""
    campaign_concept: str = ""
    target_audience: str = ""
    expected_benefit: str = ""
    implementation_difficulty: str = ""
    estimated_budget: str = ""


class CampaignTiming(BaseModel):
    model_config = _EXTRA_ALLOW
    optimal_periods: List[str] = Field(default_factory=list)
    seasonal_considerations: str = ""
    avoid_periods: Union[List[str], str] = Field(default_factory=list)
    quarterly_recommendations: Dict[str, str] = Field(default_factory=dict)


class AudienceInsights(BaseModel):
    model_config = _EXTRA_ALLOW
    # Accepts plain strings (rule-based) or dicts with name/characteristics/size_estimate
    # (new LLM prompt format)
    primary_segments: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    demographic_profile: str = ""
    psychographic_profile: str = ""
    digital_behavior: str = ""
    # Accepts plain strings or dicts with segment/opportunity/approach
    untapped_segments: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    overlap_with_sister_brands: str = ""


class CompetitiveStrategy(BaseModel):
    model_config = _EXTRA_ALLOW
    positioning: str = ""
    differentiation_points: List[str] = Field(default_factory=list)
    competitive_advantages_to_highlight: List[str] = Field(default_factory=list)
    messaging_pillars: List[str] = Field(default_factory=list)
    tone_of_voice: str = ""


class BudgetRecommendations(BaseModel):
    model_config = _EXTRA_ALLOW
    estimated_range_tomans: str = ""
    estimated_range_usd: str = ""
    allocation_by_channel: Dict[str, str] = Field(default_factory=dict)
    rationale: str = ""
    roi_expectations: str = ""


class ChannelRecommendation(BaseModel):
    model_config = _EXTRA_ALLOW
    channel: str = ""
    priority: str = ""
    rationale: str = ""
    content_type: str = ""
    budget_allocation: str = ""


class KeyMessage(BaseModel):
    model_config = _EXTRA_ALLOW
    message: str = ""
    target_audience: str = ""


class CreativeDirection(BaseModel):
    model_config = _EXTRA_ALLOW
    # Accepts plain strings (rule-based) or dicts with message_fa/message_en/target_segment
    # (new LLM prompt format)
    key_messages: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    tone_and_style: str = ""
    visual_recommendations: str = ""
    cultural_considerations: str = ""
    hashtag_strategy: List[str] = Field(default_factory=list)
    influencer_suggestions: str = ""
    content_themes: List[str] = Field(default_factory=list)
    storytelling_angle: str = ""


class SuccessMetrics(BaseModel):
    model_config = _EXTRA_ALLOW
    primary_kpis: List[str] = Field(default_factory=list)
    measurement_approach: str = ""
    benchmarks: str = ""


class InsightsOutput(BaseModel):
    """Output of Agent 5 (StrategicInsightsAgent) — stored in state['insights']."""
    model_config = _EXTRA_ALLOW
    executive_summary: str = ""
    cross_promotion_opportunities: List[Union[CrossPromotionOpportunity, Dict[str, Any]]] = Field(default_factory=list)
    campaign_timing: Union[CampaignTiming, Dict[str, Any]] = Field(default_factory=dict)
    audience_insights: Union[AudienceInsights, Dict[str, Any]] = Field(default_factory=dict)
    competitive_strategy: Union[CompetitiveStrategy, Dict[str, Any]] = Field(default_factory=dict)
    budget_recommendations: Union[BudgetRecommendations, Dict[str, Any]] = Field(default_factory=dict)
    channel_recommendations: List[Union[ChannelRecommendation, Dict[str, Any]]] = Field(default_factory=list)
    creative_direction: Union[CreativeDirection, Dict[str, Any]] = Field(default_factory=dict)
    success_metrics: Union[SuccessMetrics, Dict[str, Any]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Agent 6 — Formatter
# ---------------------------------------------------------------------------

class OutputsResult(BaseModel):
    """Output of Agent 6 (OutputFormatterAgent) — stored in state['outputs']."""
    model_config = _EXTRA_ALLOW
    executive_summary: str = ""
    complete_analysis_report: str = ""
    quick_reference: str = ""
    related_brands_csv: str = ""
    products_csv: str = ""
    opportunities_csv: str = ""


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------

def validate_agent_output(
    data: Any,
    model_class: type,
    agent_name: str,
) -> Tuple[Optional[BaseModel], Dict[str, Any]]:
    """Validate agent output against a Pydantic model.

    Never raises — logs warning and returns original dict on failure.

    Args:
        data: The raw output dict from the agent.
        model_class: The Pydantic model class to validate against.
        agent_name: Name of the agent (for logging).

    Returns:
        Tuple of (validated_model_or_None, warnings_dict).
        On success: (model_instance, {}).
        On failure: (None, {"agent": ..., "warning": ..., "errors": ...}).
    """
    if not isinstance(data, dict):
        warning = f"[{agent_name}] Output is not a dict (type={type(data).__name__}), skipping validation"
        logger.warning(warning)
        return None, {"agent": agent_name, "warning": warning, "errors": []}

    try:
        validated = model_class.model_validate(data)
        return validated, {}
    except Exception as exc:
        warning = f"[{agent_name}] Validation warning: {exc}"
        logger.warning(warning)
        return None, {
            "agent": agent_name,
            "warning": f"Output validation failed for {model_class.__name__}",
            "errors": str(exc),
        }
