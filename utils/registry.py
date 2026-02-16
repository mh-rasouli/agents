"""Brand processing registry for incremental updates."""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class BrandRegistry:
    """Registry to track brand processing history for incremental updates."""

    def __init__(self, registry_path: str = "state/registry.json"):
        """Initialize brand registry.

        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.registry = {}
        self._load_registry()

    def _load_registry(self):
        """Load registry from JSON file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self.registry = json.load(f)
                logger.info(f"[OK] Loaded registry with {len(self.registry)} brands")
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")
                self.registry = {}
        else:
            logger.info("No existing registry found, starting fresh")
            self.registry = {}

    def _save_registry(self):
        """Save registry to JSON file."""
        try:
            # Create directory if it doesn't exist
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)

            logger.debug(f"Registry saved to {self.registry_path}")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    @staticmethod
    def _compute_input_hash(brand_name: str, website: Optional[str], parent_company: Optional[str]) -> str:
        """Compute hash of brand inputs.

        Args:
            brand_name: Brand name
            website: Website URL (optional)
            parent_company: Parent company name (optional)

        Returns:
            SHA256 hash of inputs
        """
        # Normalize inputs
        normalized = {
            "brand_name": brand_name.strip(),
            "website": (website or "").strip(),
            "parent_company": (parent_company or "").strip()
        }

        # Create stable string representation
        input_string = json.dumps(normalized, sort_keys=True, ensure_ascii=False)

        # Compute hash
        return hashlib.sha256(input_string.encode('utf-8')).hexdigest()

    def needs_processing(
        self,
        brand_name: str,
        website: Optional[str],
        parent_company: Optional[str],
        force: bool = False
    ) -> tuple[bool, Optional[str]]:
        """Check if brand needs processing.

        Args:
            brand_name: Brand name
            website: Website URL (optional)
            parent_company: Parent company name (optional)
            force: Force reprocessing even if inputs haven't changed

        Returns:
            Tuple of (needs_processing, reason)
        """
        if force:
            return True, "forced"

        # Compute current input hash
        current_hash = self._compute_input_hash(brand_name, website, parent_company)

        # Check if brand exists in registry
        if brand_name not in self.registry:
            return True, "new_brand"

        brand_record = self.registry[brand_name]

        # Check if inputs changed
        if brand_record.get("last_input_hash") != current_hash:
            return True, "inputs_changed"

        # Check if last run failed
        if brand_record.get("status") == "failed":
            return True, "retry_failed"

        # Brand successfully processed and inputs haven't changed
        return False, "already_processed"

    def record_success(
        self,
        brand_name: str,
        website: Optional[str],
        parent_company: Optional[str],
        run_id: str,
        outputs: Optional[Dict[str, str]] = None
    ):
        """Record successful brand processing.

        Args:
            brand_name: Brand name
            website: Website URL (optional)
            parent_company: Parent company name (optional)
            run_id: Unique run identifier
            outputs: Output file paths (optional)
        """
        current_hash = self._compute_input_hash(brand_name, website, parent_company)
        timestamp = datetime.utcnow().isoformat()

        self.registry[brand_name] = {
            "last_input_hash": current_hash,
            "status": "success",
            "last_success_at": timestamp,
            "last_run_id": run_id,
            "outputs": outputs or {}
        }

        # Remove error fields if present
        self.registry[brand_name].pop("last_fail_at", None)
        self.registry[brand_name].pop("last_error", None)

        self._save_registry()
        logger.debug(f"Recorded success for {brand_name}")

    def record_failure(
        self,
        brand_name: str,
        website: Optional[str],
        parent_company: Optional[str],
        run_id: str,
        error: str
    ):
        """Record failed brand processing.

        Args:
            brand_name: Brand name
            website: Website URL (optional)
            parent_company: Parent company name (optional)
            run_id: Unique run identifier
            error: Error message
        """
        current_hash = self._compute_input_hash(brand_name, website, parent_company)
        timestamp = datetime.utcnow().isoformat()

        # Preserve last_success_at if it exists
        existing_record = self.registry.get(brand_name, {})

        self.registry[brand_name] = {
            "last_input_hash": current_hash,
            "status": "failed",
            "last_fail_at": timestamp,
            "last_run_id": run_id,
            "last_error": error[:500]  # Truncate long errors
        }

        # Preserve last success timestamp if it exists
        if "last_success_at" in existing_record:
            self.registry[brand_name]["last_success_at"] = existing_record["last_success_at"]

        self._save_registry()
        logger.debug(f"Recorded failure for {brand_name}")

    def get_brand_info(self, brand_name: str) -> Optional[Dict]:
        """Get registry information for a brand.

        Args:
            brand_name: Brand name

        Returns:
            Brand record dictionary or None if not found
        """
        return self.registry.get(brand_name)

    def get_stats(self) -> Dict:
        """Get registry statistics.

        Returns:
            Dictionary with total, success, failed counts
        """
        total = len(self.registry)
        success = sum(1 for r in self.registry.values() if r.get("status") == "success")
        failed = sum(1 for r in self.registry.values() if r.get("status") == "failed")

        return {
            "total": total,
            "success": success,
            "failed": failed
        }

    def clear(self):
        """Clear all registry data."""
        self.registry = {}
        self._save_registry()
        logger.info("Registry cleared")
