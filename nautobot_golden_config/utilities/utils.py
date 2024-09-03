"""Utility functions."""

from constance import config as constance_name
from django.conf import settings
from nautobot.extras.choices import SecretsGroupAccessTypeChoices
from nautobot.extras.models.secrets import SecretsGroupAssociation

from nautobot_golden_config import config


def normalize_setting(app_name, variable_name):
    """Get a value from Django settings (if specified there) or Constance configuration (otherwise)."""
    # Explicitly set in settings.py or nautobot_config.py takes precedence, for now
    if variable_name.lower() in settings.PLUGINS_CONFIG[app_name]:
        return settings.PLUGINS_CONFIG[app_name][variable_name.lower()]
    return getattr(constance_name, f"{app_name}__{variable_name.upper()}")


def default_framework():
    """Function to get near constant so the data is fresh for `default_framework`."""
    return normalize_setting(config.name, "default_framework")


def get_config_framework():
    """Function to get near constant so the data is fresh for `get_config_framework`."""
    return normalize_setting(config.name, "get_config_framework")


def merge_config_framework():
    """Function to get near constant so the data is fresh for `merge_config_framework`."""
    return normalize_setting(config.name, "merge_config_framework")


def replace_config_framework():
    """Function to get near constant so the data is fresh for `replace_config_framework`."""
    return normalize_setting(config.name, "replace_config_framework")


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
