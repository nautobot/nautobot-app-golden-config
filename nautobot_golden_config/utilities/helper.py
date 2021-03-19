"""Helper functions."""
# pylint: disable=raise-missing-from

from jinja2 import Template, StrictUndefined, UndefinedError
from jinja2.exceptions import TemplateError, TemplateSyntaxError

from nornir_nautobot.exceptions import NornirNautobotException
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.dcim.models import Device, Platform

from .constant import ALLOWED_OS

FIELDS = {
    "platform",
    "tenant_group",
    "tenant",
    "region",
    "site",
    "platform",
    "role",
    "rack",
    "rack_group",
    "manufacturer",
    "device_type",
}


def get_allowed_os(data=None):
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

    if "all" in ALLOWED_OS:
        _allowed_os = Platform.objects.values_list("slug", flat=True)
    else:
        _allowed_os = ALLOWED_OS
    return DeviceFilterSet(data=query, queryset=Device.objects.filter(platform__slug__in=_allowed_os)).qs


def get_allowed_os_from_nested():
    """Helper method to filter out only in scope OS's."""
    if "all" in ALLOWED_OS:
        return {"device__platform__slug__in": Platform.objects.values_list("slug", flat=True)}
    return {"device__platform__slug__in": ALLOWED_OS}


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
