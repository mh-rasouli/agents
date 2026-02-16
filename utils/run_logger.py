"""Run logger for tracking brand processing events."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import re
from utils.logger import get_logger

logger = get_logger(__name__)


class RunLogger:
    """Logger for tracking individual brand processing runs."""

    def __init__(self, logs_dir: str = "logs"):
        """Initialize run logger.

        Args:
            logs_dir: Directory for log files
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize log files
        self.batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.daily_log = self._get_daily_log_path()
        self.structured_log = self._get_structured_log_path()

        # Track runs in memory
        self.runs = {}

        logger.info(f"[LOGGER] Daily log: {self.daily_log}")
        logger.info(f"[LOGGER] Structured log: {self.structured_log}")

    def _get_daily_log_path(self) -> Path:
        """Get path to daily log file."""
        date_str = datetime.now().strftime("%Y%m%d")
        return self.logs_dir / f"batch_{date_str}.log"

    def _get_structured_log_path(self) -> Path:
        """Get path to structured JSON Lines log file."""
        return self.logs_dir / f"run_{self.batch_timestamp}.jsonl"

    @staticmethod
    def _sanitize_brand_name(brand_name: str) -> str:
        """Convert brand name to safe filename component.

        Args:
            brand_name: Original brand name

        Returns:
            Sanitized brand name
        """
        # Remove non-alphanumeric characters
        sanitized = re.sub(r'[^\w\s-]', '', brand_name)
        # Replace spaces/underscores with hyphens
        sanitized = re.sub(r'[\s_]+', '-', sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        # Limit length
        return sanitized[:50].lower()

    def _make_run_id(self, brand_name: str, idx: int) -> str:
        """Generate unique run ID for a brand.

        Args:
            brand_name: Brand name
            idx: Index in batch

        Returns:
            Unique run ID
        """
        sanitized = self._sanitize_brand_name(brand_name)
        return f"{self.batch_timestamp}_{idx:03d}_{sanitized}"

    def _write_log(self, event: str, run_id: str, brand_name: str, details: Optional[str] = None):
        """Write log entry to both daily and structured logs.

        Args:
            event: Event type (START, SKIP, SUCCESS, FAIL)
            run_id: Unique run identifier
            brand_name: Brand name
            details: Optional details string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format for daily log
        daily_entry = f"[{timestamp}] [{run_id}] [{event:8s}] {brand_name}"
        if details:
            daily_entry += f" | {details}"

        # Write to daily log
        try:
            with open(self.daily_log, 'a', encoding='utf-8') as f:
                f.write(daily_entry + "\n")
        except Exception as e:
            logger.error(f"Failed to write to daily log: {e}")

        # Format for structured log (JSON Lines)
        structured_entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": run_id,
            "event": event,
            "brand_name": brand_name
        }

        if details:
            structured_entry["details"] = details

        # Add duration if available
        if run_id in self.runs and "start_time" in self.runs[run_id]:
            duration = (datetime.now() - self.runs[run_id]["start_time"]).total_seconds()
            structured_entry["duration_seconds"] = round(duration, 2)

        # Write to structured log
        try:
            with open(self.structured_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(structured_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to structured log: {e}")

    def start(self, brand_name: str, idx: int, website: Optional[str] = None, parent: Optional[str] = None) -> str:
        """Log brand processing start.

        Args:
            brand_name: Brand name
            idx: Index in batch
            website: Website URL (optional)
            parent: Parent company (optional)

        Returns:
            Generated run_id
        """
        run_id = self._make_run_id(brand_name, idx)

        # Track in memory
        self.runs[run_id] = {
            "brand_name": brand_name,
            "start_time": datetime.now(),
            "website": website,
            "parent": parent
        }

        # Build details
        details_parts = []
        if website:
            details_parts.append(f"website={website}")
        if parent:
            details_parts.append(f"parent={parent}")

        details = " | ".join(details_parts) if details_parts else None

        self._write_log("START", run_id, brand_name, details)
        logger.info(f"  [START] run_id={run_id}")

        return run_id

    def skip(self, run_id: str, reason: str):
        """Log brand processing skip.

        Args:
            run_id: Run identifier
            reason: Skip reason
        """
        if run_id not in self.runs:
            logger.warning(f"Unknown run_id: {run_id}")
            return

        brand_name = self.runs[run_id]["brand_name"]
        self._write_log("SKIP", run_id, brand_name, f"reason={reason}")
        logger.info(f"  [SKIP] {reason}")

        # Clean up
        del self.runs[run_id]

    def success(self, run_id: str, outputs: Optional[Dict[str, str]] = None):
        """Log brand processing success.

        Args:
            run_id: Run identifier
            outputs: Output file paths (optional)
        """
        if run_id not in self.runs:
            logger.warning(f"Unknown run_id: {run_id}")
            return

        brand_name = self.runs[run_id]["brand_name"]
        start_time = self.runs[run_id]["start_time"]
        duration = (datetime.now() - start_time).total_seconds()

        details = f"duration={duration:.2f}s"
        if outputs:
            output_count = len(outputs)
            details += f" | outputs={output_count}"

        self._write_log("SUCCESS", run_id, brand_name, details)
        logger.info(f"  [SUCCESS] {duration:.2f}s")

        # Clean up
        del self.runs[run_id]

    def fail(self, run_id: str, error: str):
        """Log brand processing failure.

        Args:
            run_id: Run identifier
            error: Error message
        """
        if run_id not in self.runs:
            logger.warning(f"Unknown run_id: {run_id}")
            return

        brand_name = self.runs[run_id]["brand_name"]
        start_time = self.runs[run_id]["start_time"]
        duration = (datetime.now() - start_time).total_seconds()

        # Truncate long errors
        error_short = error[:200] if len(error) > 200 else error

        details = f"duration={duration:.2f}s | error={error_short}"

        self._write_log("FAIL", run_id, brand_name, details)
        logger.error(f"  [FAIL] {duration:.2f}s - {error_short}")

        # Clean up
        del self.runs[run_id]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current batch run.

        Returns:
            Dictionary with batch statistics
        """
        # Read structured log to compute stats
        stats = {
            "start": 0,
            "skip": 0,
            "success": 0,
            "fail": 0,
            "total_duration": 0.0
        }

        if not self.structured_log.exists():
            return stats

        try:
            with open(self.structured_log, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line)
                    event = entry.get("event", "").lower()

                    if event in stats:
                        stats[event] += 1

                    if event in ["success", "fail"]:
                        duration = entry.get("duration_seconds", 0)
                        stats["total_duration"] += duration

        except Exception as e:
            logger.error(f"Failed to read structured log for summary: {e}")

        return stats
