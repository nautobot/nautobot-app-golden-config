"""Hash computation utilities for nautobot_golden_config."""

import hashlib
import json


def normalize_config_content(content):
    """Normalize configuration content for consistent hashing."""
    if not content:
        return ""

    if isinstance(content, dict):
        return json.dumps(content, sort_keys=True)

    if isinstance(content, list):
        return json.dumps(content, sort_keys=True)

    if isinstance(content, str):
        return content.strip()

    return str(content).strip()


def compute_config_hash(content):
    """Compute SHA-256 hash of configuration content."""
    normalized_content = normalize_config_content(content)
    return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
