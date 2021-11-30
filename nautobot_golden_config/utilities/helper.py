"""Helper functions."""
# pylint: disable=raise-missing-from

from jinja2 import exceptions as jinja_errors

from nornir_nautobot.exceptions import NornirNautobotException
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.dcim.models import Device
from nautobot.utilities.utils import render_jinja2

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

    base_qs = models.GoldenConfigSetting.objects.first().get_queryset()
    if DeviceFilterSet(data=query, queryset=base_qs).qs.filter(platform__isnull=True).count() > 0:
        raise NornirNautobotException(
            f"The following device(s) {', '.join([device.name for device in DeviceFilterSet(data=query, queryset=base_qs).qs.filter(platform__isnull=True)])} have no platform defined. Platform is required."
        )

    return DeviceFilterSet(data=query, queryset=base_qs).qs


def null_to_empty(val):
    """Convert to empty string if the value is currently null."""
    if not val:
        return ""
    return val


def verify_global_settings(logger, global_settings, attrs):
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
