"""Helper functions."""
# pylint: disable=raise-missing-from

from jinja2 import exceptions as jinja_errors

from nautobot.dcim.models import Device
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.utilities.utils import render_jinja2

from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config import models

FIELDS = {
    "platform",
    "tenant_group",
    "tenant",
    "region",
    "site",
    "role",
    "rack",
    "rack_group",
    "manufacturer",
    "device_type",
}


def get_job_filter(data=None):
    """Helper function to return a the filterable list of OS's based on platform.slug and a specific custom value."""
    if not data:
        data = {}
    query = {}
    for field in FIELDS:
        if data.get(field):
            query[f"{field}_id"] = data[field].values_list("pk", flat=True)
    # Handle case where object is from single device run all.
    if data.get("device") and isinstance(data["device"], Device):
        query.update({"id": [str(data["device"].pk)]})
    elif data.get("device"):
        query.update({"id": data["device"].values_list("pk", flat=True)})

    base_qs = Device.objects.none()
    for obj in models.GoldenConfigSetting.objects.all():
        base_qs = base_qs | obj.get_queryset().distinct()

    if base_qs.count() == 0:
        raise NornirNautobotException(
            "The base queryset didn't find any devices. Please check the Golden Config Setting scope."
        )
    devices_filtered = DeviceFilterSet(data=query, queryset=base_qs)
    if devices_filtered.qs.count() == 0:
        raise NornirNautobotException(
            "The provided job parameters didn't match any devices detected by the Golden Config scope. Please check the scope defined within Golden Config Settings or select the correct job parameters to correctly match devices."
        )
    devices_no_platform = devices_filtered.qs.filter(platform__isnull=True)
    if devices_no_platform.count() > 0:
        raise NornirNautobotException(
            f"The following device(s) {', '.join([device.name for device in devices_no_platform])} have no platform defined. Platform is required."
        )

    return devices_filtered.qs


def null_to_empty(val):
    """Convert to empty string if the value is currently null."""
    if not val:
        return ""
    return val


def verify_settings(logger, global_settings, attrs):
    """Helper function to verify required attributes are set before a Nornir play start."""
    for item in attrs:
        if not getattr(global_settings, item):
            logger.log_failure(None, f"Missing the required global setting: `{item}`.")
            raise NornirNautobotException()


def render_jinja_template(obj, logger, template):
    """
    Helper function to render Jinja templates.

    Args:
        obj (Device): The Device object from Nautobot.
        logger (NornirLogger): Logger to log error messages to.
        template (str): A Jinja2 template to be rendered.

    Returns:
        str: The ``template`` rendered.

    Raises:
        NornirNautobotException: When there is an error rendering the ``template``.
    """
    try:
        return render_jinja2(template_code=template, context={"obj": obj})
    except jinja_errors.UndefinedError as error:
        error_msg = (
            "Jinja encountered and UndefinedError`, check the template for missing variable definitions.\n"
            f"Template:\n{template}"
        )
        logger.log_failure(obj, error_msg)
        raise NornirNautobotException from error
    except jinja_errors.TemplateSyntaxError as error:  # Also catches subclass of TemplateAssertionError
        error_msg = (
            f"Jinja encountered a SyntaxError at line number {error.lineno},"
            f"check the template for invalid Jinja syntax.\nTemplate:\n{template}"
        )
        logger.log_failure(obj, error_msg)
        raise NornirNautobotException from error
    # Intentionally not catching TemplateNotFound errors since template is passes as a string and not a filename
    except jinja_errors.TemplateError as error:  # Catches all remaining Jinja errors
        error_msg = (
            "Jinja encountered an unexpected TemplateError; check the template for correctness\n"
            f"Template:\n{template}"
        )
        logger.log_failure(error_msg)
        raise NornirNautobotException from error


def get_device_to_settings_map(queryset):
    """Helper function to map settings to devices."""
    device_to_settings_map = {}
    queryset_ids = queryset.values_list("id", flat=True)
    for golden_config_setting in models.GoldenConfigSetting.objects.all():
        for device_id in golden_config_setting.get_queryset().values_list("id", flat=True):
            if (device_id in queryset_ids) and (device_id not in device_to_settings_map):
                device_to_settings_map[device_id] = golden_config_setting

    return device_to_settings_map
