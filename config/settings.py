"""Configuration settings using Pydantic."""

import os
import warnings
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenRouter API Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    MODEL_NAME: str = "google/gemini-pro-1.5"  # Gemini 3 Pro via OpenRouter
    MAX_TOKENS: int = 8192  # Gemini supports longer context
    TEMPERATURE: float = 0.7

    # Scraper Configuration
    RATE_LIMIT_DELAY: float = 1.5  # seconds between requests
    SCRAPER_TIMEOUT: int = 30  # seconds
    USER_AGENT: str = "BrandIntelligenceBot/1.0"

    # Cache Configuration
    CACHE_TTL_HOURS: int = 24

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields

    def validate_api_key(self) -> bool:
        """Validate that API key is set.

        Returns:
            True if API key is valid, False otherwise
        """
        if not self.OPENROUTER_API_KEY or self.OPENROUTER_API_KEY == "your_api_key_here":
            return False
        return True

    def get_api_key_status(self) -> str:
        """Get API key status message.

        Returns:
            Status message string
        """
        if not self.OPENROUTER_API_KEY:
            return "[X] API key not set"
        elif self.OPENROUTER_API_KEY == "your_api_key_here":
            return "[!] API key is placeholder - please update .env file"
        else:
            return f"[OK] API key configured ({self.OPENROUTER_API_KEY[:8]}...)"


# Global settings instance
settings = Settings()

# Validate API key on import
if not settings.validate_api_key():
    warning_msg = f"""
{'='*70}
WARNING: OpenRouter API Key Not Configured
{'='*70}

The OPENROUTER_API_KEY is not set or is using the default placeholder.

The system will continue but LLM-based features will be DISABLED:
  - Data extraction from raw HTML will be limited
  - Relationship mapping will be skipped
  - Categorization will be basic
  - Strategic insights will not be generated
  - Only raw scraping data will be available

To enable full functionality:
  1. Copy .env.example to .env
  2. Add your OpenRouter API key:
     OPENROUTER_API_KEY=your_actual_key_here
  3. Get a key at: https://openrouter.ai/keys

Model: {settings.MODEL_NAME} (Gemini 3 Pro via OpenRouter)

{'='*70}
"""
    warnings.warn(warning_msg, UserWarning)
    try:
        print(warning_msg)
    except UnicodeEncodeError:
        # Fallback for consoles that don't support special characters
        print("WARNING: OpenRouter API Key Not Configured - LLM features will be disabled")
