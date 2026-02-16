"""Unit tests for utilities."""

import pytest
from pathlib import Path
import json
from utils.helpers import (
    generate_timestamp,
    sanitize_filename,
    save_json,
    load_json,
    generate_cache_key,
    merge_dicts,
    flatten_dict
)
from utils.llm_client import ClaudeClient


class TestHelpers:
    """Test cases for helper functions."""

    def test_generate_timestamp(self):
        """Test timestamp generation."""
        timestamp = generate_timestamp()

        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS
        assert "_" in timestamp
        assert timestamp[:8].isdigit()  # Date part
        assert timestamp[9:].isdigit()  # Time part

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test with invalid characters
        result = sanitize_filename("test<>:file|name?.txt")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "|" not in result
        assert "?" not in result

        # Test with spaces
        result = sanitize_filename("test file name")
        assert " " not in result
        assert "_" in result

        # Test with Persian characters
        result = sanitize_filename("تست فایل")
        assert result  # Should handle Persian

        # Test multiple underscores
        result = sanitize_filename("test___file")
        assert "___" not in result

    def test_save_and_load_json(self, tmp_path):
        """Test JSON save and load."""
        test_data = {
            "name": "تست",
            "value": 123,
            "items": ["a", "b", "c"]
        }

        filepath = tmp_path / "test.json"

        # Save
        save_json(test_data, filepath)
        assert filepath.exists()

        # Load
        loaded_data = load_json(filepath)
        assert loaded_data == test_data
        assert loaded_data["name"] == "تست"

    def test_generate_cache_key(self):
        """Test cache key generation."""
        key1 = generate_cache_key("TestBrand", "web_search")
        key2 = generate_cache_key("TestBrand", "web_search")
        key3 = generate_cache_key("TestBrand", "codal")

        # Same inputs should generate same key
        assert key1 == key2

        # Different inputs should generate different keys
        assert key1 != key3

        # Should be valid MD5 hash (32 chars)
        assert len(key1) == 32

    def test_merge_dicts(self):
        """Test dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        dict3 = {"c": 5, "d": 6}

        result = merge_dicts(dict1, dict2, dict3)

        assert result["a"] == 1
        assert result["b"] == 3  # Later dict wins
        assert result["c"] == 5  # Later dict wins
        assert result["d"] == 6

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        nested = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3
                }
            },
            "f": ["list", "items"]
        }

        result = flatten_dict(nested)

        assert result["a"] == 1
        assert result["b_c"] == 2
        assert result["b_d_e"] == 3
        assert "f" in result  # List should be JSON-stringified

    def test_flatten_dict_with_custom_separator(self):
        """Test flattening with custom separator."""
        nested = {
            "a": {
                "b": {
                    "c": 1
                }
            }
        }

        result = flatten_dict(nested, sep=".")

        assert "a.b.c" in result
        assert result["a.b.c"] == 1


class TestClaudeClient:
    """Test cases for ClaudeClient."""

    def test_initialization_without_api_key(self):
        """Test client initialization without API key."""
        # This test assumes API key is not set
        from config.settings import settings

        # Temporarily clear API key
        original_key = settings.ANTHROPIC_API_KEY
        settings.ANTHROPIC_API_KEY = None

        client = ClaudeClient()

        assert not client.is_available()

        # Restore original key
        settings.ANTHROPIC_API_KEY = original_key

    def test_is_available(self):
        """Test availability check."""
        client = ClaudeClient()

        # Should return boolean
        result = client.is_available()
        assert isinstance(result, bool)

    def test_generate_without_api_key(self):
        """Test generate method without API key."""
        from config.settings import settings

        # Temporarily clear API key
        original_key = settings.ANTHROPIC_API_KEY
        settings.ANTHROPIC_API_KEY = None

        client = ClaudeClient()

        # Should return empty string or empty JSON
        result = client.generate("test prompt", json_mode=False)
        assert result == ""

        result_json = client.generate("test prompt", json_mode=True)
        assert result_json == "{}"

        # Restore original key
        settings.ANTHROPIC_API_KEY = original_key

    def test_extract_structured_data_without_api_key(self):
        """Test extract_structured_data without API key."""
        from config.settings import settings

        # Temporarily clear API key
        original_key = settings.ANTHROPIC_API_KEY
        settings.ANTHROPIC_API_KEY = None

        client = ClaudeClient()

        # Should return empty dict
        result = client.extract_structured_data(
            "test data",
            "extract this",
            "system prompt"
        )

        assert result == {}

        # Restore original key
        settings.ANTHROPIC_API_KEY = original_key


class TestLogger:
    """Test cases for logger."""

    def test_get_logger(self):
        """Test logger creation."""
        from utils.logger import get_logger

        logger = get_logger("test")

        assert logger is not None
        assert logger.name == "test"

    def test_logger_levels(self):
        """Test logger accepts different levels."""
        from utils.logger import get_logger

        logger = get_logger("test")

        # Should not raise exceptions
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
