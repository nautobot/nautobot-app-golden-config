"""Utility functions."""

from nautobot.extras.choices import SecretsGroupAccessTypeChoices
from nautobot.extras.models.secrets import SecretsGroupAssociation
from nautobot_golden_config.utilities.constant import PLUGIN_CFG


def get_platform(platform):
    """Utility method to map user defined platform slug to netutils named entity."""
    if not PLUGIN_CFG.get("platform_slug_map"):
        return platform
    return PLUGIN_CFG.get("platform_slug_map").get(platform, platform)


def get_secret_value(secret_type, git_obj):
    """Get value for a secret based on secret type and device.

    Args:
        secret_type (SecretsGroupSecretTypeChoices): Type of secret to check.
        git_obj (extras.GitRepository): Nautobot git object.

    Returns:
        str: Secret value.
    """
    try:
        value = git_obj.secrets_group.get_secret_value(
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=secret_type,
            obj=git_obj,
        )
    except SecretsGroupAssociation.DoesNotExist:
        value = None
    return value
