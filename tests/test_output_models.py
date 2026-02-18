"""Tests for Pydantic output models and validate_agent_output helper."""

import sys
from pathlib import Path

# Ensure project root on path (avoids root __init__.py circular import issue)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from models.output_models import (
    # Enums
    PriceTier,
    SynergyScore,
    Priority,
    BusinessModel,
    # Agent models
    ContactInfo,
    WebsiteInfo,
    StructuredData,
    RawDataOutput,
    ParentCompany,
    UltimateParent,
    SisterBrand,
    RelationshipsOutput,
    PrimaryIndustry,
    CategorizationOutput,
    Product,
    Service,
    ProductCatalogOutput,
    CrossPromotionOpportunity,
    ChannelRecommendation,
    InsightsOutput,
    OutputsResult,
    # Helper
    validate_agent_output,
)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------

class TestEnums:
    def test_price_tier_values(self):
        assert PriceTier.economy == "economy"
        assert PriceTier.premium == "premium"

    def test_synergy_score_values(self):
        assert SynergyScore.VERY_HIGH == "VERY_HIGH"
        assert SynergyScore.LOW == "LOW"

    def test_priority_values(self):
        assert Priority.high == "high"

    def test_business_model_values(self):
        assert BusinessModel.B2C == "B2C"
        assert BusinessModel.B2B_and_B2C == "B2B_and_B2C"


# ---------------------------------------------------------------------------
# Agent 1 — RawDataOutput
# ---------------------------------------------------------------------------

class TestRawDataOutput:
    def test_empty_dict(self):
        model = RawDataOutput.model_validate({})
        assert model.scraped == {}
        assert model.structured == {}

    def test_rule_based_output(self):
        data = {
            "scraped": {"web_search": {"page_title": "Test"}},
            "structured": {
                "sources_used": ["web_search"],
                "contact_info": {"emails": ["a@b.com"], "phones": [], "addresses": []},
                "social_media": {},
                "website_info": {}
            }
        }
        model = RawDataOutput.model_validate(data)
        assert model.scraped["web_search"]["page_title"] == "Test"
        # structured can be a StructuredData or dict
        structured = model.structured
        if isinstance(structured, StructuredData):
            assert "web_search" in structured.sources_used
        else:
            assert "web_search" in structured["sources_used"]

    def test_extra_fields_preserved(self):
        data = {"scraped": {}, "structured": {}, "llm_metadata": {"tokens": 42}}
        model = RawDataOutput.model_validate(data)
        assert model.llm_metadata == {"tokens": 42}


# ---------------------------------------------------------------------------
# Agent 2 — RelationshipsOutput
# ---------------------------------------------------------------------------

class TestRelationshipsOutput:
    def test_empty_dict(self):
        model = RelationshipsOutput.model_validate({})
        assert model.sister_brands == []
        assert model.competitors == []

    def test_rule_based_output(self):
        data = {
            "parent_company": {
                "name": "Golrang Industrial Group",
                "name_fa": "گروه صنعتی گلرنگ",
                "industry": "Consumer Goods",
                "relation_type": "direct_parent"
            },
            "ultimate_parent": {"name": "Golrang", "name_fa": "گلرنگ"},
            "subsidiaries": [],
            "sister_brands": [
                {"name": "Avtive", "category": "cleaning", "price_tier": "mid", "synergy_score": "HIGH"},
                {"name": "Oila", "category": "food"}
            ],
            "shareholders": [],
            "affiliates": [],
            "brand_family": [],
            "competitors": [],
            "similar_brands": [],
            "complementary_brands": [],
            "parent_company_verification": {}
        }
        model = RelationshipsOutput.model_validate(data)
        assert len(model.sister_brands) == 2

    def test_llm_style_output_with_extras(self):
        data = {
            "parent_company": {"name": "Snapp Group", "founded": "2014"},
            "sister_brands": [{"name": "SnappFood", "extra_field": "value"}],
            "market_intelligence": {"trend": "growing"},
        }
        model = RelationshipsOutput.model_validate(data)
        assert model.market_intelligence == {"trend": "growing"}

    def test_sister_brand_price_tier_accepts_any_string(self):
        """Sister brand price_tier is str, not enum — LLM returns too many variants."""
        data = {"sister_brands": [{"name": "X", "price_tier": "ultra-premium-deluxe"}]}
        model = RelationshipsOutput.model_validate(data)
        sister = model.sister_brands[0]
        if isinstance(sister, SisterBrand):
            assert sister.price_tier == "ultra-premium-deluxe"


# ---------------------------------------------------------------------------
# Agent 3 — CategorizationOutput
# ---------------------------------------------------------------------------

class TestCategorizationOutput:
    def test_empty_dict(self):
        model = CategorizationOutput.model_validate({})
        assert model.business_model == "B2C"
        assert model.price_tier == "mid"

    def test_rule_based_output(self):
        data = {
            "primary_industry": {
                "name_en": "Cleaning_Products",
                "name_fa": "",
                "isic_code": "2023",
                "category_level_1": "Consumer_Goods",
                "category_level_2": "Home_Care",
                "category_level_3": "Dishwashing_&_Surface_Cleaners"
            },
            "sub_industries": [],
            "product_categories": [],
            "business_model": "B2C",
            "price_tier": "mid",
            "target_audiences": ["families"],
            "distribution_channels": ["retail", "online"],
            "market_position": {
                "positioning": "unknown",
                "estimated_market_share": "unknown",
                "competitive_landscape": "competitive"
            }
        }
        model = CategorizationOutput.model_validate(data)
        ind = model.primary_industry
        if isinstance(ind, PrimaryIndustry):
            assert ind.name_en == "Cleaning_Products"
        else:
            assert ind["name_en"] == "Cleaning_Products"

    def test_extra_fields_preserved(self):
        data = {"primary_industry": {}, "llm_confidence": 0.95}
        model = CategorizationOutput.model_validate(data)
        assert model.llm_confidence == 0.95


# ---------------------------------------------------------------------------
# Agent 4 — ProductCatalogOutput
# ---------------------------------------------------------------------------

class TestProductCatalogOutput:
    def test_empty_dict(self):
        model = ProductCatalogOutput.model_validate({})
        assert model.total_products == 0
        assert model.products == []

    def test_rule_based_output(self):
        data = {
            "extraction_method": "rule_based_healthcare",
            "total_products": 3,
            "categories": {"Mental Health Services": 3},
            "products": [],
            "services": [
                {"name": "Individual Counseling", "category": "Mental Health Services", "type": "service"},
                {"name": "Couple Therapy", "category": "Mental Health Services", "type": "service"},
                {"name": "Family Counseling", "category": "Mental Health Services", "type": "service"},
            ],
            "therapeutic_areas": []
        }
        model = ProductCatalogOutput.model_validate(data)
        assert model.total_products == 3
        assert len(model.services) == 3

    def test_categories_can_be_list(self):
        """LLM sometimes returns categories as a list of dicts instead of dict."""
        data = {
            "categories": [
                {"category_name": "Group A", "products": []}
            ]
        }
        model = ProductCatalogOutput.model_validate(data)
        assert isinstance(model.categories, list)


# ---------------------------------------------------------------------------
# Agent 5 — InsightsOutput
# ---------------------------------------------------------------------------

class TestInsightsOutput:
    def test_empty_dict(self):
        model = InsightsOutput.model_validate({})
        assert model.executive_summary == ""
        assert model.cross_promotion_opportunities == []

    def test_rule_based_output(self):
        data = {
            "executive_summary": "Summary text",
            "cross_promotion_opportunities": [
                {
                    "partner_brand": "BrandX",
                    "synergy_level": "HIGH",
                    "priority": "high",
                    "campaign_concept": "Joint campaign",
                    "target_audience": "families",
                    "expected_benefit": "More sales",
                    "implementation_difficulty": "low",
                    "estimated_budget": "50-100 million Tomans"
                }
            ],
            "campaign_timing": {
                "optimal_periods": ["Nowruz"],
                "seasonal_considerations": "Iranian cultural events",
                "avoid_periods": ["Muharram"],
                "quarterly_recommendations": {"Q1": "Nowruz campaigns"}
            },
            "channel_recommendations": [
                {"channel": "Instagram", "priority": "high", "rationale": "Popular", "content_type": "Stories", "budget_allocation": "35%"}
            ],
            "audience_insights": {"primary_segments": ["families"]},
            "competitive_strategy": {"positioning": "Premium quality"},
            "budget_recommendations": {"estimated_range_tomans": "500-1000 million Tomans"},
            "creative_direction": {"key_messages": ["Quality"]},
            "success_metrics": {"primary_kpis": ["Brand awareness lift"]}
        }
        model = InsightsOutput.model_validate(data)
        assert len(model.cross_promotion_opportunities) == 1
        assert len(model.channel_recommendations) == 1

    def test_null_values_handled(self):
        """Null values from LLM should not crash validation."""
        data = {
            "cross_promotion_opportunities": [
                {"partner_brand": None, "synergy_level": None, "priority": None}
            ],
        }
        model = InsightsOutput.model_validate(data)
        opp = model.cross_promotion_opportunities[0]
        if isinstance(opp, CrossPromotionOpportunity):
            assert opp.partner_brand is None


# ---------------------------------------------------------------------------
# Agent 6 — OutputsResult
# ---------------------------------------------------------------------------

class TestOutputsResult:
    def test_empty_dict(self):
        model = OutputsResult.model_validate({})
        assert model.executive_summary == ""

    def test_with_file_paths(self):
        data = {
            "executive_summary": "/output/brand/human_reports/executive_summary.md",
            "complete_analysis_report": "/output/brand/human_reports/complete_analysis_report.md",
            "quick_reference": "/output/brand/human_reports/quick_reference.json",
            "related_brands_csv": "/output/brand/human_reports/data_exports/brands.csv",
            "products_csv": "/output/brand/human_reports/data_exports/products.csv",
            "opportunities_csv": "/output/brand/human_reports/data_exports/opportunities.csv",
        }
        model = OutputsResult.model_validate(data)
        assert model.executive_summary.endswith(".md")


# ---------------------------------------------------------------------------
# validate_agent_output helper
# ---------------------------------------------------------------------------

class TestValidateAgentOutput:
    def test_valid_data_returns_model(self):
        data = {"scraped": {}, "structured": {}}
        model, warnings = validate_agent_output(data, RawDataOutput, "TestAgent")
        assert model is not None
        assert warnings == {}

    def test_empty_dict_returns_model(self):
        model, warnings = validate_agent_output({}, RelationshipsOutput, "TestAgent")
        assert model is not None
        assert warnings == {}

    def test_non_dict_returns_none(self):
        model, warnings = validate_agent_output("not a dict", RawDataOutput, "TestAgent")
        assert model is None
        assert "warning" in warnings

    def test_non_dict_list_returns_none(self):
        model, warnings = validate_agent_output([1, 2, 3], InsightsOutput, "TestAgent")
        assert model is None

    def test_extra_fields_do_not_fail(self):
        data = {"unexpected_field": "value", "another": 123}
        model, warnings = validate_agent_output(data, CategorizationOutput, "TestAgent")
        assert model is not None
        assert warnings == {}

    def test_never_raises(self):
        """validate_agent_output must never raise, even with pathological input."""
        for bad_input in [None, 42, True, [], "string"]:
            model, warnings = validate_agent_output(bad_input, RawDataOutput, "TestAgent")
            # Should not raise — returns None + warnings
            assert model is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
