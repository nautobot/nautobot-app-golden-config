"""Utility functions."""

from nautobot.extras.choices import SecretsGroupAccessTypeChoices
from nautobot.extras.models.secrets import SecretsGroupAssociation
from nautobot_golden_config.utilities.constant import PLUGIN_CFG

from django.conf import settings
from constance import config

_APPLICATION = __package__.split(".")[0]


def get_plugin_settings_or_config(variable_name, application):
    """Get a value from Django settings (if specified there) or Constance configuration (otherwise)."""
    # Explicitly set in settings.py or nautobot_config.py PLUGIN_CONFIG takes precedence, for now
    if settings.PLUGINS_CONFIG.get(application, {}).get(variable_name.lower()):
        return settings.PLUGINS_CONFIG[application][variable_name.lower()]
    return getattr(config, f"{application}__{variable_name.upper()}")


def default_framework():
    return get_plugin_settings_or_config("default_framework", _APPLICATION)


def get_config_framework():
    return get_plugin_settings_or_config("get_config_framework", _APPLICATION)


def merge_config_framework():
    return get_plugin_settings_or_config("merge_config_framework", _APPLICATION)


def replace_config_framework():
    return get_plugin_settings_or_config("replace_config_framework", _APPLICATION)


def get_platform(platform_network_driver):
    """Utility method to map user defined platform network_driver to netutils named entity."""
    if not PLUGIN_CFG.get("platform_network_driver_map"):
        return platform_network_driver
    return PLUGIN_CFG.get("platform_network_driver_map").get(platform_network_driver, platform_network_driver)


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
