"""Test script for Iranian brands using the Brand Intelligence Agent."""

import sys
from pathlib import Path
from graph import run_workflow
from utils.logger import get_logger

logger = get_logger(__name__)


# Test brands with their websites
TEST_BRANDS = [
    {
        "name": "دیجی‌کالا",
        "name_en": "Digikala",
        "website": "https://www.digikala.com",
        "description": "Iran's largest e-commerce platform",
        "expected_industry": "E-commerce",
        "expected_model": "B2C"
    },
    {
        "name": "اسنپ",
        "name_en": "Snapp",
        "website": "https://snapp.ir",
        "description": "Iranian ride-hailing and delivery platform",
        "expected_industry": "Transportation / On-demand services",
        "expected_model": "B2C"
    },
    {
        "name": "Active Cleaners",
        "name_en": "Active Cleaners",
        "website": None,  # No website provided
        "description": "Iranian cleaning products brand",
        "expected_industry": "Consumer Goods / Cleaning Products",
        "expected_model": "B2C"
    }
]


def test_single_brand(brand_info: dict, verbose: bool = False) -> dict:
    """Test analysis for a single brand.

    Args:
        brand_info: Dictionary containing brand information
        verbose: If True, print detailed logs

    Returns:
        Analysis results
    """
    print(f"\n{'='*70}")
    print(f"Testing: {brand_info['name']} ({brand_info['name_en']})")
    print(f"Description: {brand_info['description']}")
    if brand_info['website']:
        print(f"Website: {brand_info['website']}")
    else:
        print("Website: Not provided (testing without website)")
    print(f"{'='*70}\n")

    try:
        # Run the workflow
        result = run_workflow(
            brand_name=brand_info["name"],
            brand_website=brand_info.get("website")
        )

        # Print summary
        print_test_summary(brand_info, result)

        return result

    except Exception as e:
        logger.error(f"Test failed for {brand_info['name']}: {e}")
        print(f"❌ Test FAILED: {e}\n")
        return None


def print_test_summary(brand_info: dict, result: dict):
    """Print test summary and validation.

    Args:
        brand_info: Original brand information
        result: Analysis results
    """
    print("\n" + "="*70)
    print(f"TEST RESULTS: {brand_info['name']}")
    print("="*70)

    # Check data collection
    raw_data = result.get("raw_data", {})
    structured = raw_data.get("structured", {})

    print("\n📊 Data Collection:")
    scraped = raw_data.get("scraped", {})
    for source, data in scraped.items():
        status = "✅" if data else "❌"
        print(f"  {status} {source}")

    # Check categorization
    categorization = result.get("categorization", {})

    print("\n🏢 Categorization:")
    if categorization.get("primary_industry"):
        industry = categorization["primary_industry"]
        print(f"  Industry: {industry.get('name_fa', 'N/A')} / {industry.get('name_en', 'N/A')}")
        print(f"  Expected: {brand_info['expected_industry']}")

    if categorization.get("business_model"):
        print(f"  Model: {categorization['business_model']}")
        print(f"  Expected: {brand_info['expected_model']}")

    if categorization.get("price_tier"):
        print(f"  Price Tier: {categorization['price_tier']}")

    # Check relationships
    relationships = result.get("relationships", {})

    print("\n🔗 Relationships:")
    if relationships.get("parent_company", {}).get("name"):
        print(f"  Parent: {relationships['parent_company']['name']}")

    subsidiaries = relationships.get("subsidiaries", [])
    if subsidiaries:
        print(f"  Subsidiaries: {len(subsidiaries)}")
        for sub in subsidiaries[:3]:
            print(f"    - {sub.get('name', 'N/A')}")

    sister_brands = relationships.get("sister_brands", [])
    if sister_brands:
        print(f"  Sister Brands: {len(sister_brands)}")
        for sister in sister_brands[:3]:
            print(f"    - {sister.get('name', 'N/A')}")

    # Check insights
    insights = result.get("insights", {})

    print("\n💡 Strategic Insights:")

    cross_promo = insights.get("cross_promotion_opportunities", [])
    if cross_promo:
        print(f"  Cross-promotion opportunities: {len(cross_promo)}")
        for opp in cross_promo[:2]:
            print(f"    - {opp.get('partner_brand', 'N/A')}: {opp.get('rationale', 'N/A')[:60]}...")

    channels = insights.get("channel_recommendations", [])
    if channels:
        print(f"  Recommended channels: {', '.join([c.get('channel', 'N/A') for c in channels[:3]])}")

    # Check outputs
    outputs = result.get("outputs", {})

    print("\n📁 Generated Files:")
    for format_type, filepath in outputs.items():
        if Path(filepath).exists():
            size = Path(filepath).stat().st_size
            print(f"  ✅ {format_type.upper()}: {filepath} ({size} bytes)")
        else:
            print(f"  ❌ {format_type.upper()}: File not found!")

    # Errors
    errors = result.get("errors", [])
    if errors:
        print(f"\n⚠️  Errors/Warnings: {len(errors)}")
        for error in errors[:3]:
            print(f"  - [{error.get('agent', 'Unknown')}] {error.get('error', 'N/A')}")

    # Processing time
    print(f"\n⏱️  Processing Time: {result.get('processing_time', 0):.2f} seconds")

    # Overall validation
    print("\n" + "="*70)
    validation_passed = (
        len(scraped) > 0 and
        categorization.get("primary_industry") is not None and
        len(outputs) > 0
    )

    if validation_passed:
        print("✅ TEST PASSED")
    else:
        print("⚠️  TEST COMPLETED WITH WARNINGS")

    print("="*70 + "\n")


def test_all_brands(verbose: bool = False):
    """Test all brands sequentially.

    Args:
        verbose: If True, print detailed logs
    """
    print("\n" + "="*70)
    print("BRAND INTELLIGENCE AGENT - IRANIAN BRANDS TEST SUITE")
    print("="*70)
    print(f"\nTesting {len(TEST_BRANDS)} Iranian brands:\n")

    for idx, brand in enumerate(TEST_BRANDS, 1):
        print(f"[{idx}/{len(TEST_BRANDS)}] {brand['name']}")

    print("\n" + "="*70 + "\n")

    results = []

    for brand_info in TEST_BRANDS:
        result = test_single_brand(brand_info, verbose=verbose)
        results.append({
            "brand": brand_info["name"],
            "result": result,
            "success": result is not None
        })

        # Small delay between tests
        import time
        time.sleep(2)

    # Final summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)

    successful = sum(1 for r in results if r["success"])
    print(f"\nTests Passed: {successful}/{len(results)}")

    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['brand']}")

    print("\n" + "="*70 + "\n")


def main():
    """Main test entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Brand Intelligence Agent with Iranian brands")

    parser.add_argument(
        "--brand",
        "-b",
        choices=["digikala", "snapp", "active", "all"],
        default="all",
        help="Which brand to test (default: all)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Map brand names
    brand_map = {
        "digikala": TEST_BRANDS[0],
        "snapp": TEST_BRANDS[1],
        "active": TEST_BRANDS[2]
    }

    if args.brand == "all":
        test_all_brands(verbose=args.verbose)
    else:
        brand_info = brand_map[args.brand]
        test_single_brand(brand_info, verbose=args.verbose)


if __name__ == "__main__":
    main()
