"""Batch process brands from Google Sheets."""

import argparse
import time
from pathlib import Path
from typing import Dict, List
from utils.google_sheets_client import GoogleSheetsClient
from graph import run_workflow
from utils.logger import get_logger

logger = get_logger(__name__)


def process_brands_from_sheet(
    credentials_path: str,
    sheet_id: str,
    worksheet_name: str = None,
    update_sheet: bool = True,
    delay_between_brands: int = 5
) -> List[Dict]:
    """Process all brands from Google Sheet.

    Args:
        credentials_path: Path to service account JSON credentials
        sheet_id: Google Sheet ID
        worksheet_name: Name of worksheet (optional)
        update_sheet: Whether to update sheet with status/outputs
        delay_between_brands: Seconds to wait between processing brands

    Returns:
        List of processing results
    """
    logger.info("="*60)
    logger.info("BATCH BRAND PROCESSING FROM GOOGLE SHEETS")
    logger.info("="*60)

    # Initialize Google Sheets client
    try:
        sheets_client = GoogleSheetsClient(credentials_path)
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets client: {e}")
        return []

    # Read brands from sheet
    try:
        brands = sheets_client.get_brands_from_sheet(
            sheet_id=sheet_id,
            worksheet_name=worksheet_name
        )
    except Exception as e:
        logger.error(f"Failed to read brands from sheet: {e}")
        return []

    if not brands:
        logger.warning("No brands found in sheet")
        return []

    logger.info(f"\nFound {len(brands)} brands to process\n")

    # Process each brand
    results = []
    for idx, brand_info in enumerate(brands, 1):
        brand_name = brand_info["brand_name"]
        website = brand_info.get("website")
        parent_company = brand_info.get("parent_company")
        row_number = brand_info.get("row_number")

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing brand {idx}/{len(brands)}: {brand_name}")
        logger.info(f"{'='*60}")

        if website:
            logger.info(f"Website: {website}")
        if parent_company:
            logger.info(f"Parent Company: {parent_company}")

        # Update status to "Processing..."
        if update_sheet and row_number:
            try:
                sheets_client.update_status(
                    sheet_id=sheet_id,
                    row_number=row_number,
                    status="در حال پردازش... (Processing...)"
                )
            except Exception as e:
                logger.warning(f"Failed to update processing status: {e}")

        # Run workflow
        try:
            start_time = time.time()
            final_state = run_workflow(
                brand_name=brand_name,
                brand_website=website,
                parent_company=parent_company
            )
            processing_time = time.time() - start_time

            # Extract output paths
            output_paths = final_state.get("outputs", {})

            result = {
                "brand_name": brand_name,
                "success": True,
                "processing_time": processing_time,
                "output_paths": output_paths,
                "errors": final_state.get("errors", [])
            }

            logger.info(f"[OK] Brand processed successfully in {processing_time:.2f} seconds")

            # Update sheet with success status and output paths
            if update_sheet and row_number:
                try:
                    sheets_client.update_status(
                        sheet_id=sheet_id,
                        row_number=row_number,
                        status=f"✓ تکمیل شد ({processing_time:.1f}s)"
                    )

                    # Write output file paths
                    sheets_client.write_output_paths(
                        sheet_id=sheet_id,
                        row_number=row_number,
                        output_paths=output_paths
                    )
                except Exception as e:
                    logger.warning(f"Failed to update sheet with results: {e}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to process brand {brand_name}: {e}")

            result = {
                "brand_name": brand_name,
                "success": False,
                "error": str(e),
                "processing_time": 0,
                "output_paths": {}
            }

            # Update sheet with error status
            if update_sheet and row_number:
                try:
                    sheets_client.update_status(
                        sheet_id=sheet_id,
                        row_number=row_number,
                        status=f"✗ خطا (Error): {str(e)[:50]}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to update error status: {e}")

        results.append(result)

        # Delay between brands to avoid rate limiting
        if idx < len(brands):
            logger.info(f"\nWaiting {delay_between_brands} seconds before next brand...")
            time.sleep(delay_between_brands)

    # Print summary
    _print_summary(results)

    return results


def _print_summary(results: List[Dict]):
    """Print processing summary.

    Args:
        results: List of processing results
    """
    logger.info("\n" + "="*60)
    logger.info("BATCH PROCESSING SUMMARY")
    logger.info("="*60)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    logger.info(f"\nTotal brands processed: {len(results)}")
    logger.info(f"✓ Successful: {len(successful)}")
    logger.info(f"✗ Failed: {len(failed)}")

    if successful:
        total_time = sum(r["processing_time"] for r in successful)
        avg_time = total_time / len(successful)
        logger.info(f"\nTotal processing time: {total_time:.2f} seconds")
        logger.info(f"Average time per brand: {avg_time:.2f} seconds")

    if failed:
        logger.warning("\nFailed brands:")
        for result in failed:
            logger.warning(f"  - {result['brand_name']}: {result.get('error', 'Unknown error')}")

    logger.info("\n" + "="*60 + "\n")


def main():
    """CLI entry point for batch processing."""
    parser = argparse.ArgumentParser(
        description="Batch process brands from Google Sheets"
    )
    parser.add_argument(
        "--credentials",
        required=True,
        help="Path to Google service account JSON credentials file"
    )
    parser.add_argument(
        "--sheet-id",
        required=True,
        help="Google Sheet ID"
    )
    parser.add_argument(
        "--worksheet",
        default=None,
        help="Worksheet name (optional, uses first sheet if not specified)"
    )
    parser.add_argument(
        "--no-update",
        action="store_true",
        help="Don't update Google Sheet with status/results"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Delay in seconds between processing brands (default: 5)"
    )

    args = parser.parse_args()

    # Validate credentials file exists
    credentials_path = Path(args.credentials)
    if not credentials_path.exists():
        logger.error(f"Credentials file not found: {credentials_path}")
        return

    # Process brands
    process_brands_from_sheet(
        credentials_path=str(credentials_path),
        sheet_id=args.sheet_id,
        worksheet_name=args.worksheet,
        update_sheet=not args.no_update,
        delay_between_brands=args.delay
    )


if __name__ == "__main__":
    main()
