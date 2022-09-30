"""Signal handler for validating DynamicGroups are valid."""
import logging

from django.core.exceptions import ValidationError


LOGGER = logging.getLogger("nautobot_golden_config.signals")


def dynamic_group_validation_callback(*args, **kwargs):
    """Callback function triggered by the nautobot_database_ready signal when the Nautobot database is fully ready.

    This function is connected to that signal in GoldenConfig.ready().

    During migration from <1.2.0 to 1.2.0 of GoldenConfig the DynamicGroups are created from the
    scope attribute. If a scope would not a valid filter this will cause issue with DynamicGroups.
    This callback is meant to raise an error IF the created DynamicGroup is invalid.

    Args:
        sender (PluginConfig): The GoldenConfig instance that was registered for this callback
        apps (django.apps.apps.Apps): Use this to look up model classes as needed
        **kwargs: See https://docs.djangoproject.com/en/3.1/ref/signals/#post-migrate for additional args
    """
    from nautobot.extras.models import DynamicGroup  # pylint: disable=import-outside-toplevel

    for group in DynamicGroup.objects.exclude(golden_config_setting__isnull=True):
        try:
            group.clean_filter()
        except ValidationError as err:
            LOGGER.exception(
                "DynamicGroup %s failed filter validate. Please fix the DynamicGroup manually.", group.name
            )
            raise err
    LOGGER.debug("All DynamicGroups for GoldenConfig pass validation.")
