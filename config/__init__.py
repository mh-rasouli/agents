"""Configuration - Settings and prompts for the system."""

from config.settings import Settings, settings
from config.prompts import (
    DATA_EXTRACTION_PROMPT,
    RELATIONSHIP_MAPPING_PROMPT,
    CATEGORIZATION_PROMPT,
    PRODUCT_CATALOG_PROMPT,
    INSIGHTS_GENERATION_PROMPT,
)

__all__ = [
    # Settings
    "Settings",
    "settings",
    # Prompts
    "DATA_EXTRACTION_PROMPT",
    "RELATIONSHIP_MAPPING_PROMPT",
    "CATEGORIZATION_PROMPT",
    "PRODUCT_CATALOG_PROMPT",
    "INSIGHTS_GENERATION_PROMPT",
]

__version__ = "1.0.0"
