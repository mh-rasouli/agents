"""Data Models - State and type definitions for the workflow."""

from models.state import BrandIntelligenceState
from models.output_models import (
    # Enums
    PriceTier,
    SynergyScore,
    Priority,
    BusinessModel,
    MarketPosition,
    CompetitiveStrength,
    CrossSellPotential,
    ShareholderType,
    # Agent 1 — DataCollection
    ContactInfo,
    SocialMediaAccount,
    WebsiteInfo,
    StructuredData,
    RawDataOutput,
    # Agent 2 — Relationships
    ParentCompany,
    UltimateParent,
    Subsidiary,
    SisterBrand,
    Shareholder,
    Affiliate,
    BrandFamilyMember,
    Competitor,
    SimilarBrand,
    ComplementaryBrand,
    ParentCompanyVerification,
    RelationshipsOutput,
    # Agent 3 — Categorization
    PrimaryIndustry,
    TargetAudienceSegment,
    MarketPositionInfo,
    CategorizationOutput,
    # Agent 4 — ProductCatalog
    Product,
    Service,
    ProductCatalogOutput,
    # Agent 5 — Insights
    CrossPromotionOpportunity,
    CampaignTiming,
    AudienceInsights,
    CompetitiveStrategy,
    BudgetRecommendations,
    ChannelRecommendation,
    KeyMessage,
    CreativeDirection,
    SuccessMetrics,
    InsightsOutput,
    # Agent 6 — Formatter
    OutputsResult,
    # Helper
    validate_agent_output,
)

__all__ = [
    "BrandIntelligenceState",
    # Enums
    "PriceTier",
    "SynergyScore",
    "Priority",
    "BusinessModel",
    "MarketPosition",
    "CompetitiveStrength",
    "CrossSellPotential",
    "ShareholderType",
    # Agent 1
    "ContactInfo",
    "SocialMediaAccount",
    "WebsiteInfo",
    "StructuredData",
    "RawDataOutput",
    # Agent 2
    "ParentCompany",
    "UltimateParent",
    "Subsidiary",
    "SisterBrand",
    "Shareholder",
    "Affiliate",
    "BrandFamilyMember",
    "Competitor",
    "SimilarBrand",
    "ComplementaryBrand",
    "ParentCompanyVerification",
    "RelationshipsOutput",
    # Agent 3
    "PrimaryIndustry",
    "TargetAudienceSegment",
    "MarketPositionInfo",
    "CategorizationOutput",
    # Agent 4
    "Product",
    "Service",
    "ProductCatalogOutput",
    # Agent 5
    "CrossPromotionOpportunity",
    "CampaignTiming",
    "AudienceInsights",
    "CompetitiveStrategy",
    "BudgetRecommendations",
    "ChannelRecommendation",
    "KeyMessage",
    "CreativeDirection",
    "SuccessMetrics",
    "InsightsOutput",
    # Agent 6
    "OutputsResult",
    # Helper
    "validate_agent_output",
]

__version__ = "1.1.0"
