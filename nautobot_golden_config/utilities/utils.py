"""Utility functions."""

from nautobot_golden_config.utilities.constant import PLUGIN_CFG


def get_platform(platform):
    """Utility method to map user defined platform slug to netutils named entity."""
    if not PLUGIN_CFG.get("platform_slug_map"):
        return platform
    return PLUGIN_CFG.get("platform_slug_map").get(platform, platform)
