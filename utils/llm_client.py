"""OpenRouter API client wrapper for Gemini 3 Pro."""

import json
from typing import Optional, Dict, Any
from openai import OpenAI
from config.settings import settings
from utils.logger import get_logger
from utils.exceptions import APIKeyError

logger = get_logger(__name__)


class LLMClient:
    """Wrapper for OpenRouter API with Gemini 3 Pro."""

    def __init__(self):
        """Initialize the OpenRouter client."""
        self.api_key_valid = settings.validate_api_key()

        if self.api_key_valid:
            # OpenRouter uses OpenAI-compatible API
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
            )
            logger.info(f"OpenRouter API client initialized with model: {settings.MODEL_NAME}")
        else:
            self.client = None
            logger.warning("OpenRouter API client NOT initialized - API key missing or invalid")

        self.model = settings.MODEL_NAME
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE

    def is_available(self) -> bool:
        """Check if OpenRouter API is available.

        Returns:
            True if API key is valid and client is ready
        """
        return self.api_key_valid and self.client is not None

    def validate_api_key_with_test_call(self) -> None:
        """Validate API key by making a test call.

        Raises:
            APIKeyError: If API key is invalid or authentication fails
        """
        if not self.is_available():
            raise APIKeyError(
                message="API key is not configured or is invalid",
                provider="OpenRouter"
            )

        try:
            # Make a minimal test call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            logger.info("✅ API key validation successful")
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "authentication" in error_str.lower():
                raise APIKeyError(
                    message=f"Authentication failed: {error_str}",
                    provider="OpenRouter"
                )
            else:
                raise APIKeyError(
                    message=f"API test call failed: {error_str}",
                    provider="OpenRouter"
                )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> str:
        """Generate a response from Gemini via OpenRouter.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            json_mode: If True, ensures JSON output

        Returns:
            The generated response text

        Raises:
            Exception: If API call fails or API key is not available
        """
        # Check if API is available
        if not self.is_available():
            raise APIKeyError(
                message="Cannot generate: API key not configured or invalid",
                provider="OpenRouter"
            )

        try:
            messages = []

            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add user prompt
            messages.append({"role": "user", "content": prompt})

            # Build request parameters
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
            }

            # Add JSON mode instruction if requested
            if json_mode:
                # Append JSON instruction to the prompt
                messages[-1]["content"] = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON. No explanations, no markdown formatting, just pure JSON."

            logger.info(f"Calling OpenRouter API with model {self.model}")

            response = self.client.chat.completions.create(**kwargs)

            response_text = response.choices[0].message.content

            # Validate JSON if json_mode is enabled
            if json_mode:
                try:
                    json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON response, attempting to extract: {e}")
                    # Try to extract JSON from markdown code blocks
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    # Validate again
                    try:
                        json.loads(response_text)
                    except json.JSONDecodeError:
                        logger.error("Failed to extract valid JSON from response")
                        return "{}"

            logger.info("OpenRouter API call successful")
            return response_text

        except Exception as e:
            error_str = str(e)
            logger.error(f"OpenRouter API error: {e}")

            # Check for authentication errors (401)
            if "401" in error_str or "authentication" in error_str.lower() or "user not found" in error_str.lower():
                raise APIKeyError(
                    message=f"Authentication failed during API call: {error_str}",
                    provider="OpenRouter"
                )

            # Re-raise other errors
            raise

    def extract_structured_data(
        self,
        data: str,
        extraction_prompt: str,
        system_prompt: str
    ) -> Dict[str, Any]:
        """Extract structured data from unstructured text.

        Args:
            data: The unstructured data to process
            extraction_prompt: Instructions for extraction
            system_prompt: System prompt for the agent

        Returns:
            Extracted data as a dictionary (empty dict if API unavailable)
        """
        # Check if API is available
        if not self.is_available():
            logger.warning("Skipping LLM extraction - API not available")
            return {}

        try:
            full_prompt = f"{extraction_prompt}\n\nData to analyze:\n{data}"

            response = self.generate(
                prompt=full_prompt,
                system_prompt=system_prompt,
                json_mode=True
            )

            return json.loads(response) if response else {}

        except Exception as e:
            logger.error(f"Failed to extract structured data: {e}")
            return {}


# Global client instance
llm_client = LLMClient()

# Backwards compatibility alias
claude_client = llm_client
