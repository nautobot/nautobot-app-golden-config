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


def cleanup_orphaned_hash_groups_for_rule(rule):
    """Remove ConfigHashGrouping records for a rule that no longer have any linked devices."""
    # Import here to avoid circular imports
    from nautobot_golden_config.models import ConfigComplianceHash, ConfigHashGrouping

    orphaned_groups = ConfigHashGrouping.objects.filter(rule=rule).exclude(
        id__in=ConfigComplianceHash.objects.filter(rule=rule, config_group__isnull=False).values_list(
            "config_group_id", flat=True
        )
    )

    orphaned_groups.delete()
