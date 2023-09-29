"""Utility functions."""

from nautobot.extras.choices import SecretsGroupAccessTypeChoices
from nautobot.extras.models.secrets import SecretsGroupAssociation
from nautobot.apps.config import get_app_settings_or_config

from nautobot_golden_config import config


def default_framework():
    """Function to get near constant so the data is fresh for `default_framework`."""
    return get_app_settings_or_config(config.name, "default_framework")


def get_config_framework():
    """Function to get near constant so the data is fresh for `get_config_framework`."""
    return get_app_settings_or_config(config.name, "get_config_framework")


def merge_config_framework():
    """Function to get near constant so the data is fresh for `merge_config_framework`."""
    return get_app_settings_or_config(config.name, "merge_config_framework")


def replace_config_framework():
    """Function to get near constant so the data is fresh for `replace_config_framework`."""
    return get_app_settings_or_config(config.name, "replace_config_framework")


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
