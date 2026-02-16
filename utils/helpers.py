"""Common utility functions."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def generate_timestamp() -> str:
    """Generate a timestamp string for file naming.

    Returns:
        Timestamp in YYYYMMDD_HHMMSS format
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use in filenames.

    Args:
        name: The string to sanitize

    Returns:
        Sanitized filename-safe string
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')

    # Replace spaces with underscores
    name = name.replace(' ', '_')

    # Remove consecutive underscores
    while '__' in name:
        name = name.replace('__', '_')

    return name.strip('_').lower()


def save_json(data: Dict[str, Any], filepath: Path) -> None:
    """Save data as JSON file.

    Args:
        data: Dictionary to save
        filepath: Path to save to
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load data from JSON file.

    Args:
        filepath: Path to load from

    Returns:
        Loaded dictionary
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_cache_key(brand_name: str, source: str) -> str:
    """Generate a cache key for scraped data.

    Args:
        brand_name: Name of the brand
        source: Data source name

    Returns:
        MD5 hash for cache key
    """
    key_string = f"{brand_name}_{source}"
    return hashlib.md5(key_string.encode()).hexdigest()


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later dicts taking precedence.

    Args:
        *dicts: Variable number of dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, json.dumps(v, ensure_ascii=False)))
        else:
            items.append((new_key, v))
    return dict(items)
