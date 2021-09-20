"""Helper functions."""
# pylint: disable=raise-missing-from

from jinja2 import Template, StrictUndefined, UndefinedError
from jinja2.exceptions import TemplateError, TemplateSyntaxError

from nornir_nautobot.exceptions import NornirNautobotException
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.dcim.models import Device

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


def check_jinja_template(obj, logger, template):
    """Helper function to catch Jinja based issues and raise with proper NornirException."""
    try:
        template_rendered = Template(template, undefined=StrictUndefined).render(obj=obj)
        return template_rendered
    except UndefinedError as error:
        logger.log_failure(obj, f"Jinja `{template}` has an error of `{error}`.")
        raise NornirNautobotException()
    except TemplateSyntaxError as error:
        logger.log_failure(obj, f"Jinja `{template}` has an error of `{error}`.")
        raise NornirNautobotException()
    except TemplateError as error:
        logger.log_failure(obj, f"Jinja `{template}` has an error of `{error}`.")
        raise NornirNautobotException()
