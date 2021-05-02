"""Helper functions."""
# pylint: disable=raise-missing-from

from jinja2 import Template, StrictUndefined, UndefinedError
from jinja2.exceptions import TemplateError, TemplateSyntaxError
from django.db.models import Q

from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher import _DEFAULT_DRIVERS_MAPPING
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.dcim.models import Device, Platform

from nautobot_golden_config import models
from nautobot_golden_config.utilities.constant import ALLOWED_OS, PLUGIN_CFG


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
    # TODO: Determine if there is a simpler way to filter dynamically within FilterSet
    filter_query = Q(platform__slug__in=_allowed_os)
    gc_settings = models.GoldenConfigSettings.objects.first()
    if gc_settings.only_primary_ip:
        # TODO: include ip6
        filter_query = filter_query & Q(primary_ip4__isnull=False)
    if gc_settings.exclude_chassis_members:
        filter_query = filter_query & ~Q(Q(virtual_chassis__isnull=False) & Q(vc_master_for__isnull=True))
    return DeviceFilterSet(data=query, queryset=Device.objects.filter(filter_query)).qs


def get_allowed_os_from_nested():
    """Helper method to filter out only in scope OS's."""
    if "all" in ALLOWED_OS:
        filter_query = Q(device__platform__slug__in=Platform.objects.values_list("slug", flat=True))
    else:
        filter_query = Q(device__platform__slug__in=ALLOWED_OS)

    gc_settings = models.GoldenConfigSettings.objects.first()
    if gc_settings.only_primary_ip:
        filter_query = filter_query & Q(device__primary_ip4__isnull=False)
    if gc_settings.exclude_chassis_members:
        filter_query = filter_query & ~Q(
            Q(device__virtual_chassis__isnull=False) & Q(device__vc_master_for__isnull=True)
        )
    return filter_query


def get_dispatcher():
    """Helper method to load the dispatcher from nautobot nornir or config if defined."""
    if PLUGIN_CFG.get("dispatcher_mapping"):
        return PLUGIN_CFG["dispatcher_mapping"]
    return _DEFAULT_DRIVERS_MAPPING


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
