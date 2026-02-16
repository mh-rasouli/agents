"""Configuration - Settings and prompts for the system."""

from config.settings import Settings, settings
from config.prompts import (
    DATA_EXTRACTION_PROMPT,
    RELATIONSHIP_MAPPING_PROMPT,
    CATEGORIZATION_PROMPT,
    STRATEGIC_INSIGHTS_PROMPT,
)

__all__ = [
    # Settings
    "Settings",
    "settings",
    # Prompts
    "DATA_EXTRACTION_PROMPT",
    "RELATIONSHIP_MAPPING_PROMPT",
    "CATEGORIZATION_PROMPT",
    "STRATEGIC_INSIGHTS_PROMPT",
]

__version__ = "1.0.0"
