"""Parallel batch processor for efficient brand processing."""

import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Warning: tqdm not installed. Install with: pip install tqdm")

from utils import get_logger, BrandRegistry, RunLogger, GoogleSheetsClient
from utils.exceptions import APIKeyError, BudgetExceededError

logger = get_logger(__name__)


class ParallelBatchProcessor:
    """Efficient parallel batch processor for brand intelligence."""

    def __init__(
        self,
        sheets_credentials: str,
        sheets_id: str,
        max_workers: int = 8,
        chunk_size: int = 50,
        budget_limit: Optional[float] = None
    ):
        """Initialize the parallel batch processor.

        Args:
            sheets_credentials: Path to Google service account credentials
            sheets_id: Google Sheets ID
            max_workers: Number of parallel workers (default: 8)
            chunk_size: Brands per chunk for memory management (default: 50)
            budget_limit: Optional budget limit in dollars
        """
        self.sheets_credentials = sheets_credentials
        self.sheets_id = sheets_id
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.budget_limit = budget_limit

        # Initialize clients
        self.sheets_client = GoogleSheetsClient(sheets_credentials)
        self.registry = BrandRegistry()
        self.run_logger = RunLogger()

        # Track results
        self.results = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        # Cost tracking
        self.total_cost = 0.0
        self.cost_per_brand = 0.05  # Estimate: $0.05 per brand

    def process_batch(self, force: bool = False, limit: Optional[int] = None) -> Dict[str, Any]:
        """Process all brands from Google Sheets in parallel.

        Args:
            force: Force reprocessing of all brands (ignore registry)
            limit: Optional limit on number of brands to process (for testing)

        Returns:
            Dictionary with processing results
        """
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("PARALLEL BATCH MODE - OPTIMIZED PROCESSING")
        logger.info("=" * 60)

        # Load registry stats
        registry_stats = self.registry.get_stats()
        logger.info(f"[REGISTRY] Loaded: {registry_stats['total']} brands tracked "
                    f"({registry_stats['success']} success, {registry_stats['failed']} failed)")

        if force:
            logger.info("[FORCE] All brands will be reprocessed")

        # Load brands from Google Sheets
        try:
            brands = self.sheets_client.get_brands_from_sheet(
                sheet_id=self.sheets_id,
                start_row=2  # Skip header
            )
        except Exception as e:
            logger.error(f"Failed to read brands from Google Sheets: {e}")
            raise

        if not brands:
            logger.warning("No brands found in Google Sheets")
            return self.results

        # Apply limit if specified (for testing)
        if limit:
            brands = brands[:limit]
            logger.info(f"[LIMIT] Processing only first {limit} brands")

        logger.info(f"Found {len(brands)} brands in sheet")

        # Filter brands that need processing
        brands_to_process = []
        for brand_data in brands:
            needs_proc, reason = self.registry.needs_processing(
                brand_data.get("brand_name", ""),
                brand_data.get("website"),
                brand_data.get("parent_company"),
                force=force
            )

            if needs_proc:
                brand_data["_reason"] = reason
                brands_to_process.append(brand_data)
            else:
                # Track skipped brands
                self.results["skipped"].append({
                    "brand": brand_data.get("brand_name", ""),
                    "row": brand_data.get("row_number"),
                    "reason": reason
                })

        logger.info(f"Brands to process: {len(brands_to_process)}/{len(brands)}")
        logger.info(f"Skipped (unchanged): {len(self.results['skipped'])}")

        if not brands_to_process:
            logger.info("No brands need processing. All brands are up to date!")
            return self.results

        # Display configuration
        logger.info(f"\n[CONFIG] Parallel Processing Configuration:")
        logger.info(f"  Workers: {self.max_workers} parallel")
        logger.info(f"  Chunk size: {self.chunk_size} brands")
        if self.budget_limit:
            logger.info(f"  Budget limit: ${self.budget_limit:.2f}")
        else:
            logger.info(f"  Budget limit: Unlimited")

        # Estimate time and cost
        estimated_time_sequential = len(brands_to_process) * 40  # 40s per brand
        estimated_time_parallel = estimated_time_sequential / self.max_workers
        estimated_cost = len(brands_to_process) * self.cost_per_brand

        logger.info(f"\n[ESTIMATE] Processing Estimates:")
        logger.info(f"  Brands: {len(brands_to_process)}")
        logger.info(f"  Sequential time: {estimated_time_sequential/60:.1f} minutes")
        logger.info(f"  Parallel time: {estimated_time_parallel/60:.1f} minutes (est.)")
        logger.info(f"  Speedup: ~{self.max_workers:.1f}× faster")
        logger.info(f"  Estimated cost: ${estimated_cost:.2f}")

        if self.budget_limit and estimated_cost > self.budget_limit:
            logger.warning(f"  ⚠️ WARNING: Estimated cost (${estimated_cost:.2f}) "
                          f"exceeds budget limit (${self.budget_limit:.2f})")
            logger.warning(f"  Processing may stop early when budget is reached")

        logger.info("\n[START] Beginning parallel processing...\n")

        # Process in chunks
        total_brands = len(brands_to_process)
        processed_count = 0

        for chunk_start in range(0, total_brands, self.chunk_size):
            chunk_end = min(chunk_start + self.chunk_size, total_brands)
            chunk = brands_to_process[chunk_start:chunk_end]

            logger.info(f"[CHUNK {chunk_start//self.chunk_size + 1}] "
                        f"Processing brands {chunk_start + 1}-{chunk_end}/{total_brands}")

            # Process chunk in parallel
            chunk_results = self._process_chunk_parallel(chunk, processed_count)

            # Update results
            self.results["success"].extend(chunk_results["success"])
            self.results["failed"].extend(chunk_results["failed"])

            processed_count += len(chunk)

            # Save checkpoint after each chunk
            self._save_checkpoint(processed_count, "chunk_complete")

            # Check budget
            if self.budget_limit:
                self.total_cost = processed_count * self.cost_per_brand
                if self.total_cost >= self.budget_limit:
                    logger.warning(f"\n[BUDGET] Budget limit reached: ${self.total_cost:.2f} / ${self.budget_limit:.2f}")
                    logger.warning(f"Stopping processing. Processed {processed_count}/{total_brands} brands")
                    break

        # Calculate final metrics
        elapsed_time = time.time() - start_time

        # Print summary
        self._print_summary(elapsed_time, estimated_time_sequential)

        return self.results

    def _process_chunk_parallel(self, chunk: List[Dict], offset: int) -> Dict[str, List]:
        """Process a chunk of brands in parallel.

        Args:
            chunk: List of brand data dictionaries
            offset: Number of brands already processed (for progress tracking)

        Returns:
            Dictionary with success and failed lists
        """
        chunk_results = {"success": [], "failed": []}

        # Initialize progress bar
        if TQDM_AVAILABLE:
            progress = tqdm(
                total=len(chunk),
                desc=f"Processing chunk",
                unit="brand",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
                position=0,
                leave=True
            )
        else:
            progress = None

        # Process in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_brand = {
                executor.submit(
                    self._process_single_brand,
                    brand_data
                ): brand_data for brand_data in chunk
            }

            # Collect results as they complete
            for future in as_completed(future_to_brand):
                brand_data = future_to_brand[future]
                brand_name = brand_data.get("brand_name", "Unknown")

                try:
                    result = future.result()

                    if result["status"] == "success":
                        chunk_results["success"].append(result)
                    else:
                        chunk_results["failed"].append(result)

                    # Update progress bar
                    if progress:
                        success_count = len(self.results["success"]) + len(chunk_results["success"])
                        failed_count = len(self.results["failed"]) + len(chunk_results["failed"])
                        current_cost = (success_count + failed_count) * self.cost_per_brand

                        progress.set_postfix({
                            "✓": success_count,
                            "✗": failed_count,
                            "💰": f"${current_cost:.2f}"
                        })
                        progress.update(1)

                except Exception as e:
                    logger.error(f"Unexpected error processing {brand_name}: {e}")
                    chunk_results["failed"].append({
                        "brand": brand_name,
                        "row": brand_data.get("row_number"),
                        "error": f"Unexpected error: {str(e)}"
                    })

                    if progress:
                        progress.update(1)

        if progress:
            progress.close()

        return chunk_results

    def _process_single_brand(self, brand_data: Dict) -> Dict[str, Any]:
        """Process a single brand (worker function).

        Args:
            brand_data: Dictionary with brand information

        Returns:
            Result dictionary with status, brand, outputs, errors
        """
        brand_name = brand_data.get("brand_name", "")
        website = brand_data.get("website") or None
        parent = brand_data.get("parent_company") or None
        row_number = brand_data.get("row_number")
        reason = brand_data.get("_reason", "new_brand")

        # Start logging this run
        run_id = self.run_logger.start(brand_name, row_number, website, parent)

        try:
            # Import here to avoid circular dependency
            from graph import run_workflow

            # Run workflow for this brand (skip API validation since we validated once at batch start)
            final_state = run_workflow(
                brand_name=brand_name,
                brand_website=website,
                parent_company=parent,
                google_sheets_credentials=self.sheets_credentials,
                google_sheets_id=self.sheets_id,
                skip_api_validation=True  # Already validated at batch start
            )

            # Check if successful
            if final_state.get("errors"):
                error_summary = "; ".join([e.get("error", "Unknown") for e in final_state["errors"][:3]])

                # Log failure
                self.run_logger.fail(run_id, error_summary)

                # Record failure in registry
                self.registry.record_failure(
                    brand_name=brand_name,
                    website=website,
                    parent_company=parent,
                    run_id=run_id,
                    error=error_summary
                )

                # Update status in sheet
                try:
                    self.sheets_client.update_status(self.sheets_id, row_number, status="Failed")
                except:
                    pass

                return {
                    "status": "failed",
                    "brand": brand_name,
                    "row": row_number,
                    "errors": final_state.get("errors", [])
                }
            else:
                # Log success
                self.run_logger.success(run_id, final_state.get("outputs", {}))

                # Record success in registry
                self.registry.record_success(
                    brand_name=brand_name,
                    website=website,
                    parent_company=parent,
                    run_id=run_id,
                    outputs=final_state.get("outputs", {})
                )

                # Update status in sheet
                try:
                    self.sheets_client.update_status(self.sheets_id, row_number, status="Completed")

                    # Write output paths to sheet
                    if final_state.get("outputs"):
                        self.sheets_client.write_output_paths(
                            self.sheets_id,
                            row_number,
                            final_state["outputs"]
                        )
                except:
                    pass

                return {
                    "status": "success",
                    "brand": brand_name,
                    "row": row_number,
                    "outputs": final_state.get("outputs", {}),
                    "processing_time": final_state.get("processing_time", 0)
                }

        except APIKeyError as e:
            # API key error - this should have been caught at batch start
            logger.error(f"API key error for {brand_name}: {e}")
            self.run_logger.fail(run_id, "API key error")

            return {
                "status": "failed",
                "brand": brand_name,
                "row": row_number,
                "error": "API key error"
            }

        except Exception as e:
            # Log failure
            self.run_logger.fail(run_id, str(e))

            # Record failure in registry
            self.registry.record_failure(
                brand_name=brand_name,
                website=website,
                parent_company=parent,
                run_id=run_id,
                error=str(e)
            )

            # Update status in sheet
            try:
                self.sheets_client.update_status(
                    self.sheets_id,
                    row_number,
                    status=f"Error: {str(e)[:50]}"
                )
            except:
                pass

            return {
                "status": "failed",
                "brand": brand_name,
                "row": row_number,
                "error": str(e)
            }

    def _save_checkpoint(self, processed_count: int, reason: str = "auto"):
        """Save processing checkpoint.

        Args:
            processed_count: Number of brands processed so far
            reason: Reason for checkpoint (auto, error, complete)
        """
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "processed_count": processed_count,
            "results": self.results,
            "total_cost": self.total_cost
        }

        checkpoint_file = Path("state/checkpoint_latest.json")
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        # Also save timestamped backup
        backup_file = Path(f"state/checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"[CHECKPOINT] Saved at {processed_count} brands")

    def _print_summary(self, elapsed_time: float, estimated_sequential_time: float):
        """Print batch processing summary.

        Args:
            elapsed_time: Actual elapsed time in seconds
            estimated_sequential_time: Estimated sequential time in seconds
        """
        total_processed = len(self.results["success"]) + len(self.results["failed"])
        total_brands = total_processed + len(self.results["skipped"])

        print("\n" + "=" * 60)
        print("PARALLEL BATCH PROCESSING SUMMARY")
        print("=" * 60)

        print(f"\n[TOTALS]")
        print(f"  Total brands in sheet: {total_brands}")
        print(f"  Processed: {total_processed}")
        print(f"  Skipped (unchanged): {len(self.results['skipped'])}")

        print(f"\n[RESULTS]")
        print(f"  ✓ Success: {len(self.results['success'])} "
              f"({len(self.results['success'])/total_processed*100 if total_processed > 0 else 0:.1f}%)")
        print(f"  ✗ Failed: {len(self.results['failed'])} "
              f"({len(self.results['failed'])/total_processed*100 if total_processed > 0 else 0:.1f}%)")

        print(f"\n[PERFORMANCE]")
        print(f"  Elapsed time: {elapsed_time/60:.1f} minutes ({elapsed_time:.1f}s)")
        if total_processed > 0:
            print(f"  Average per brand: {elapsed_time/total_processed:.1f} seconds")
            print(f"  Estimated sequential time: {estimated_sequential_time/60:.1f} minutes")
            speedup = estimated_sequential_time / elapsed_time if elapsed_time > 0 else 0
            print(f"  ⚡ Speedup: {speedup:.1f}× faster than sequential")

        print(f"\n[COST]")
        actual_cost = total_processed * self.cost_per_brand
        print(f"  Estimated cost: ${actual_cost:.2f}")
        if self.budget_limit:
            print(f"  Budget limit: ${self.budget_limit:.2f}")
            print(f"  Budget used: {actual_cost/self.budget_limit*100:.1f}%")

        if self.results["failed"]:
            print(f"\n[FAILED BRANDS]")
            for item in self.results["failed"][:5]:  # Show first 5
                brand = item.get("brand", "Unknown")
                error = item.get("error", "Unknown error")
                print(f"  - {brand}: {error[:60]}...")
            if len(self.results["failed"]) > 5:
                print(f"  ... and {len(self.results['failed']) - 5} more")

        print(f"\n[LOGS]")
        print(f"  Daily log: {self.run_logger.daily_log}")
        print(f"  Structured log: {self.run_logger.structured_log}")
        print(f"  Checkpoint: state/checkpoint_latest.json")

        print("=" * 60 + "\n")
