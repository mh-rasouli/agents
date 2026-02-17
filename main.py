"""CLI entry point for Brand Intelligence Agent."""

import argparse
import sys
from pathlib import Path

# Modular imports
from graph import run_workflow
from config import settings
from utils import get_logger
from utils.exceptions import APIKeyError

logger = get_logger(__name__)


def run_single_brand(args):
    """Run analysis for a single brand.

    Args:
        args: Command-line arguments
    """
    # Validate brand name
    if not args.brand.strip():
        logger.error("Brand name cannot be empty")
        sys.exit(1)

    logger.info(f"Analyzing brand: {args.brand}")

    if args.website:
        logger.info(f"Website: {args.website}")

    if args.parent:
        logger.info(f"Parent Company: {args.parent}")

    # Google Sheets parameters
    google_sheets_credentials = None
    google_sheets_id = None

    if args.google_sheets:
        google_sheets_credentials = args.sheets_credentials
        google_sheets_id = args.sheets_id
        logger.info(f"[OK] Customer Intelligence enabled from Google Sheets")
        logger.info(f"  Credentials: {google_sheets_credentials}")
        logger.info(f"  Sheet ID: {google_sheets_id}")

    try:
        final_state = run_workflow(
            brand_name=args.brand,
            brand_website=args.website,
            parent_company=args.parent,
            google_sheets_credentials=google_sheets_credentials,
            google_sheets_id=google_sheets_id
        )

        # Print results
        print_results(final_state)

        # Exit with appropriate code
        if final_state.get("errors"):
            sys.exit(1)
        else:
            sys.exit(0)

    except APIKeyError as e:
        # Clear, formatted error message
        print(str(e))
        sys.exit(1)


def run_batch_mode(args):
    """Run analysis for all brands from Google Sheets.

    Args:
        args: Command-line arguments
    """
    import time
    from utils import ParallelBatchProcessor, llm_client
    from utils.exceptions import APIKeyError

    # ONE-TIME API VALIDATION (Fail Fast at Batch Level)
    logger.info("=" * 60)
    logger.info("VALIDATING API KEYS")
    logger.info("=" * 60)

    try:
        llm_client.validate_api_key_with_test_call()
        logger.info("✅ OpenRouter API key valid\n")
    except APIKeyError as e:
        logger.error("❌ OpenRouter API key invalid\n")
        print(str(e))
        sys.exit(1)

    # Check if parallel mode is enabled
    use_parallel = getattr(args, 'workers', 0) > 1

    if use_parallel:
        # Use new parallel batch processor
        logger.info("Using PARALLEL processing mode")

        processor = ParallelBatchProcessor(
            sheets_credentials=args.sheets_credentials,
            sheets_id=args.sheets_id,
            max_workers=args.workers,
            chunk_size=getattr(args, 'chunk_size', 50),
            budget_limit=getattr(args, 'budget', None)
        )

        try:
            results = processor.process_batch(
                force=getattr(args, 'force', False),
                limit=getattr(args, 'limit', None)
            )

            # Exit with appropriate code
            if results["failed"]:
                sys.exit(1)
            else:
                sys.exit(0)

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    else:
        # Use original sequential processing (for backwards compatibility)
        logger.info("Using SEQUENTIAL processing mode (legacy)")
        logger.info("TIP: Use --workers 8 for 6× faster processing\n")
        _run_batch_mode_sequential(args)


def _run_batch_mode_sequential(args):
    """Run batch mode with sequential processing (legacy mode).

    Args:
        args: Command-line arguments
    """
    import time
    from utils import GoogleSheetsClient, BrandRegistry, RunLogger

    # Initialize run logger
    run_logger = RunLogger()

    # Initialize registry
    registry = BrandRegistry()
    registry_stats = registry.get_stats()
    logger.info(f"[REGISTRY] Loaded: {registry_stats['total']} brands tracked "
                f"({registry_stats['success']} success, {registry_stats['failed']} failed)")

    force = getattr(args, 'force', False)
    if force:
        logger.info("[FORCE] All brands will be reprocessed")

    # Initialize Google Sheets client
    try:
        sheets_client = GoogleSheetsClient(args.sheets_credentials)
        brands = sheets_client.get_brands_from_sheet(
            sheet_id=args.sheets_id,
            start_row=2  # Skip header
        )
    except Exception as e:
        logger.error(f"Failed to read brands from Google Sheets: {e}")
        sys.exit(1)

    if not brands:
        logger.warning("No brands found in Google Sheets")
        sys.exit(0)

    logger.info(f"Found {len(brands)} brands in sheet\n")

    # Track results
    results = {
        "success": [],
        "failed": [],
        "skipped": []
    }

    start_time = time.time()

    # Process each brand
    for idx, brand_data in enumerate(brands, 1):
        brand_name = brand_data.get("brand_name", "")
        website = brand_data.get("website") or None
        parent = brand_data.get("parent_company") or None
        row_number = brand_data.get("row_number", idx)

        logger.info(f"\n[{idx}/{len(brands)}] {brand_name}")

        # Check if brand needs processing
        needs_proc, reason = registry.needs_processing(brand_name, website, parent, force=force)

        if not needs_proc:
            # Generate run_id for skip event
            run_id = run_logger.start(brand_name, idx, website, parent)
            run_logger.skip(run_id, reason)

            results["skipped"].append({
                "brand": brand_name,
                "row": row_number,
                "reason": reason
            })
            continue

        # Start logging this run
        run_id = run_logger.start(brand_name, idx, website, parent)

        logger.info(f"  [RUN] Reason: {reason}")
        if website:
            logger.info(f"  Website: {website}")
        if parent:
            logger.info(f"  Parent: {parent}")

        try:
            # Run workflow for this brand
            final_state = run_workflow(
                brand_name=brand_name,
                brand_website=website,
                parent_company=parent,
                google_sheets_credentials=args.sheets_credentials,
                google_sheets_id=args.sheets_id
            )

            # Check if successful
            if final_state.get("errors"):
                logger.warning(f"  [PARTIAL] Completed with {len(final_state['errors'])} errors")
                error_summary = "; ".join([e.get("error", "Unknown") for e in final_state["errors"][:3]])

                results["failed"].append({
                    "brand": brand_name,
                    "row": row_number,
                    "errors": final_state.get("errors", [])
                })

                # Log failure
                run_logger.fail(run_id, error_summary)

                # Record failure in registry
                registry.record_failure(
                    brand_name=brand_name,
                    website=website,
                    parent_company=parent,
                    run_id=run_id,
                    error=error_summary
                )

                # Update status in sheet
                sheets_client.update_status(args.sheets_id, row_number, status="Failed")
            else:
                results["success"].append({
                    "brand": brand_name,
                    "row": row_number,
                    "outputs": final_state.get("outputs", {})
                })

                # Log success
                run_logger.success(run_id, final_state.get("outputs", {}))

                # Record success in registry
                registry.record_success(
                    brand_name=brand_name,
                    website=website,
                    parent_company=parent,
                    run_id=run_id,
                    outputs=final_state.get("outputs", {})
                )

                # Update status in sheet
                sheets_client.update_status(args.sheets_id, row_number, status="Completed")

                # Write output paths to sheet
                if final_state.get("outputs"):
                    sheets_client.write_output_paths(
                        args.sheets_id,
                        row_number,
                        final_state["outputs"]
                    )

        except APIKeyError as e:
            # API Key error - stop immediately and save progress
            logger.error("=" * 60)
            logger.error("API KEY ERROR - STOPPING BATCH PROCESSING")
            logger.error("=" * 60)
            logger.error(f"Failed on brand {idx}/{len(brands)}: {brand_name}")
            logger.error(f"Processed {idx-1} brands before error")

            # Save checkpoint with current progress
            checkpoint_file = Path("state/checkpoint.json")
            checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

            import json
            from datetime import datetime
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "error": "API_KEY_ERROR",
                "failed_brand": brand_name,
                "failed_brand_index": idx,
                "processed_count": idx - 1,
                "results": results
            }

            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)

            logger.info(f"Progress saved to: {checkpoint_file}")

            # Print clear error message
            print(str(e))

            # Exit immediately
            sys.exit(1)

        except Exception as e:
            results["failed"].append({
                "brand": brand_name,
                "row": row_number,
                "error": str(e)
            })

            # Log failure
            run_logger.fail(run_id, str(e))

            # Record failure in registry
            registry.record_failure(
                brand_name=brand_name,
                website=website,
                parent_company=parent,
                run_id=run_id,
                error=str(e)
            )

            # Update status in sheet
            try:
                sheets_client.update_status(args.sheets_id, row_number, status=f"Error: {str(e)[:50]}")
            except:
                pass

    # Print summary
    elapsed_time = time.time() - start_time
    print_batch_summary(results, elapsed_time, run_logger)

    # Exit with appropriate code
    if results["failed"]:
        sys.exit(1)
    else:
        sys.exit(0)


def print_batch_summary(results: dict, elapsed_time: float, run_logger=None):
    """Print batch processing summary.

    Args:
        results: Dictionary with success/failed/skipped lists
        elapsed_time: Total processing time in seconds
        run_logger: RunLogger instance (optional)
    """
    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)

    total = len(results["success"]) + len(results["failed"]) + len(results["skipped"])
    processed = len(results["success"]) + len(results["failed"])

    print(f"\n[TOTAL] {total} brands in sheet")
    print(f"[PROCESSED] {processed} brands ran in this batch")
    print(f"  [OK] {len(results['success'])} successful")
    print(f"  [FAIL] {len(results['failed'])} failed")
    print(f"[SKIP] {len(results['skipped'])} skipped (unchanged)")

    if results["skipped"]:
        print(f"\n[INFO] Skipped brands (use --force to reprocess):")
        for item in results["skipped"][:5]:  # Show first 5
            brand = item.get("brand", "Unknown")
            reason = item.get("reason", "unknown")
            print(f"  - {brand} ({reason})")
        if len(results["skipped"]) > 5:
            print(f"  ... and {len(results['skipped']) - 5} more")

    if results["failed"]:
        print("\n[!] Failed brands:")
        for item in results["failed"]:
            brand = item.get("brand", "Unknown")
            row = item.get("row", "?")
            error = item.get("error", "Unknown error")
            print(f"  - Row {row}: {brand} - {error[:80]}")

    print(f"\n[TIME] Total processing time: {elapsed_time:.2f} seconds")
    if processed > 0:
        print(f"[AVG] Average per processed brand: {elapsed_time/processed:.2f} seconds")

    # Show log file locations
    if run_logger:
        print(f"\n[LOGS] Log files created:")
        print(f"  Daily log: {run_logger.daily_log}")
        print(f"  Structured log: {run_logger.structured_log}")

    print("=" * 60 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Brand Intelligence Agent - Analyze Iranian brands for advertising insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a brand by name
  python main.py --brand "دیجی‌کالا"

  # Analyze a brand with website
  python main.py --brand "دیجی‌کالا" --website "https://www.digikala.com"

  # Specify custom output directory
  python main.py --brand "اسنپ" --output-dir "./reports"
        """
    )

    parser.add_argument(
        "--brand",
        "-b",
        help="Name of the brand to analyze (Persian or English). If omitted with --google-sheets, runs batch mode."
    )

    parser.add_argument(
        "--website",
        "-w",
        help="Optional website URL of the brand"
    )

    parser.add_argument(
        "--parent",
        "-p",
        help="Optional parent company name"
    )

    parser.add_argument(
        "--google-sheets",
        action="store_true",
        help="Enable customer intelligence from Google Sheets"
    )

    parser.add_argument(
        "--sheets-credentials",
        default="C:/Users/TrendAgency/Downloads/claude-agents-487515-27f459372fd6.json",
        help="Path to Google service account credentials JSON"
    )

    parser.add_argument(
        "--sheets-id",
        default="1PJ3jvnYNj33fyC_wkqCEImbJI_qYJdWVFm2QC-NdukA",
        help="Google Sheets ID for customer intelligence data"
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        default="./output",
        help="Directory for output files (default: ./output)"
    )

    parser.add_argument(
        "--formats",
        "-f",
        default="json,csv,txt,md",
        help="Output formats (comma-separated): json,csv,txt,md (default: all)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing all brands (ignore registry cache)"
    )

    # Parallel processing options
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for batch mode (default: 1, recommended: 8)"
    )

    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        help="Budget limit in dollars (e.g., 50.0). Processing stops when budget is reached."
    )

    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Limit number of brands to process (useful for testing, e.g., --limit 10)"
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50,
        help="Brands per chunk for memory management (default: 50)"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Determine mode: batch or single-brand
    batch_mode = args.google_sheets and not args.brand

    if not batch_mode and not args.brand:
        logger.error("Either --brand or --google-sheets (for batch mode) must be provided")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if batch_mode:
            # Batch mode: read all brands from Google Sheets
            run_batch_mode(args)
        else:
            # Single-brand mode (original behavior)
            run_single_brand(args)

    except KeyboardInterrupt:
        logger.info("\nAnalysis interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_banner():
    """Print application banner."""
    banner = """
==================================================================
       Brand Intelligence Agent - Multi-Agent System
            Iranian Brand Analysis for Advertising
==================================================================
    """
    try:
        print(banner)
    except UnicodeEncodeError:
        print("Brand Intelligence Agent - Multi-Agent System")
        print("Iranian Brand Analysis for Advertising")
        print("=" * 60)

    # Show API key status
    api_status = settings.get_api_key_status()
    print(f"API Status: {api_status}")

    if not settings.validate_api_key():
        print("\n[!] Running in LIMITED mode - LLM features disabled")
        print("    Only raw scraping data will be available\n")


def print_results(state: dict):
    """Print analysis results summary.

    Args:
        state: Final workflow state
    """
    # Ensure stdout uses UTF-8 encoding
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

    print(f"\nBrand: {state['brand_name']}")

    if state.get("outputs"):
        print("\n[DIR] Generated Reports:")
        for format_type, filepath in state["outputs"].items():
            icon = {
                "json": "[JSON]",
                "csv": "[CSV]",
                "txt": "[TXT]",
                "markdown": "[MD]"
            }.get(format_type, "[FILE]")

            print(f"  {icon} {format_type.upper()}: {filepath}")

    # Print key insights
    insights = state.get("insights", {})

    if insights.get("cross_promotion_opportunities"):
        print("\n[+] Cross-Promotion Opportunities:")
        for opp in insights["cross_promotion_opportunities"][:3]:
            print(f"  - {opp.get('partner_brand', 'N/A')}")

    if insights.get("channel_recommendations"):
        print("\n[*] Top Recommended Channels:")
        for channel in insights["channel_recommendations"][:3]:
            priority_icon = {
                "high": "[HIGH]",
                "medium": "[MED]",
                "low": "[LOW]"
            }.get(channel.get("priority", "medium").lower(), "[---]")

            print(f"  {priority_icon} {channel.get('channel', 'N/A')}")

    # Print categorization
    categorization = state.get("categorization", {})

    if categorization.get("primary_industry"):
        industry = categorization["primary_industry"]
        print(f"\n[INDUSTRY] {industry.get('name_fa', 'N/A')}")

    if categorization.get("business_model"):
        print(f"[MODEL] Business Model: {categorization['business_model']}")

    if categorization.get("price_tier"):
        print(f"[PRICE] Price Tier: {categorization['price_tier']}")

    # Print customer intelligence results
    customer_intelligence = state.get("customer_intelligence", {})
    if customer_intelligence.get("status") == "completed":
        print(f"\n[CUSTOMER INTEL] Customer Intelligence Report Generated")
        print(f"  Transactions: {customer_intelligence.get('transaction_count', 0)}")
        print(f"  Campaigns: {customer_intelligence.get('campaign_count', 0)}")
        revenue = customer_intelligence.get('total_revenue', 0)
        if revenue > 0:
            print(f"  Total Revenue: {revenue:,.0f} Tomans")
        print(f"  Report: {customer_intelligence.get('report_path', 'N/A')}")

    # Print warnings/errors
    if state.get("errors"):
        print(f"\n[!] Warnings: {len(state['errors'])} issues encountered")
        for error in state["errors"][:3]:
            print(f"  - [{error.get('agent', 'Unknown')}] {error.get('error', 'Unknown')}")

    print(f"\n[TIME] Processing Time: {state.get('processing_time', 0):.2f} seconds")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
