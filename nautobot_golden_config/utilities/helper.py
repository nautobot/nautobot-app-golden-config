"""Helper functions."""

# pylint: disable=raise-missing-from
import json
from copy import deepcopy

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.template import engines
from django.urls import reverse
from django.utils.html import format_html
from jinja2 import exceptions as jinja_errors
from jinja2.sandbox import SandboxedEnvironment
from lxml import etree
from nautobot.core.utils.data import render_jinja2
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.dcim.models import Device
from nautobot.extras.choices import DynamicGroupTypeChoices
from nautobot.extras.models import Job
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config import config as app_config
from nautobot_golden_config import models
from nautobot_golden_config.error_codes import ERROR_CODES
from nautobot_golden_config.utilities import utils
from nautobot_golden_config.utilities.constant import JINJA_ENV

FRAMEWORK_METHODS = {
    "default": utils.default_framework,
    "get_config": utils.get_config_framework,
    "merge_config": utils.merge_config_framework,
    "replace_config_framework": utils.replace_config_framework,
}

FIELDS_PK = {
    "platform",
    "tenant_group",
    "tenant",
    "location",
    "role",
    "rack",
    "rack_group",
    "manufacturer",
    "device_type",
}

FIELDS_NAME = {"tags", "status"}


def get_job_filter(data=None):
    """Helper function to return a the filterable list of OS's based on platform.name and a specific custom value."""
    if not data:
        data = {}
    query = {}

    # Translate instances from FIELDS set to list of primary keys
    for field in FIELDS_PK:
        if data.get(field):
            query[field] = data[field].values_list("pk", flat=True)

    # Translate instances from FIELDS set to list of names
    for field in FIELDS_NAME:
        if data.get(field):
            query[field] = data[field].values_list("name", flat=True)

    # Handle case where object is from single device run all.
    if data.get("device") and isinstance(data["device"], Device):
        query.update({"id": [str(data["device"].pk)]})
    elif data.get("device"):
        query.update({"id": data["device"].values_list("pk", flat=True)})

    raw_qs = Q()
    # If scope is set to {} do not loop as all devices are in scope.
    if not models.GoldenConfigSetting.objects.filter(
        dynamic_group__filter__iexact="{}", dynamic_group__group_type=DynamicGroupTypeChoices.TYPE_DYNAMIC_FILTER
    ).exists():
        for obj in models.GoldenConfigSetting.objects.all():
            raw_qs = raw_qs | obj.dynamic_group.generate_query()

    base_qs = Device.objects.filter(raw_qs)

    if not base_qs.exists():
        raise NornirNautobotException(
            "`E3015:` The base queryset didn't find any devices. Please check the Golden Config Setting scope."
        )

    devices_filtered = DeviceFilterSet(data=query, queryset=base_qs)

    if not devices_filtered.qs.exists():
        raise NornirNautobotException(
            "`E3016:` The provided job parameters didn't match any devices detected by the Golden Config scope. Please check the scope defined within Golden Config Settings or select the correct job parameters to correctly match devices."
        )
    devices_no_platform = devices_filtered.qs.filter(platform__isnull=True)
    if devices_no_platform.exists():
        raise NornirNautobotException(
            f"`E3017:` The following device(s) {', '.join([device.name for device in devices_no_platform])} have no platform defined. Platform is required."
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
            error_msg = f"`E3018:` Missing the required global setting: `{item}`."
            logger.error(error_msg)
            raise NornirNautobotException(error_msg)


def get_django_env():
    """Load Django Jinja filters from the Django jinja template engine, and add them to the jinja_env.

    Returns:
        SandboxedEnvironment
    """
    # Use a custom Jinja2 environment instead of Django's to avoid HTML escaping
    jinja_env = SandboxedEnvironment(**JINJA_ENV)
    jinja_env.filters = engines["jinja"].env.filters
    return jinja_env


def render_jinja_template(obj, logger, template):
    """
    Helper function to render Jinja templates.

    Args:
        obj (Device): The Device object from Nautobot.
        logger (logging.logger): Logger to log error messages to.
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
            "`E3019:` Jinja encountered and UndefinedError`, check the template for missing variable definitions.\n"
            f"Template:\n{template}\n"
            f"Original Error: {error}"
        )
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)

    except jinja_errors.TemplateSyntaxError as error:  # Also catches subclass of TemplateAssertionError
        error_msg = (
            f"`E3020:` Jinja encountered a SyntaxError at line number {error.lineno},"
            f"check the template for invalid Jinja syntax.\nTemplate:\n{template}\n"
            f"Original Error: {error}"
        )
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)
    # Intentionally not catching TemplateNotFound errors since template is passes as a string and not a filename
    except jinja_errors.TemplateError as error:  # Catches all remaining Jinja errors
        error_msg = (
            "`E3021:` Jinja encountered an unexpected TemplateError; check the template for correctness\n"
            f"Template:\n{template}\n"
            f"Original Error: {error}"
        )
        logger.error(error_msg, extra={"object": obj})
        raise NornirNautobotException(error_msg)


def get_device_to_settings_map(queryset):
    """Helper function to map settings to devices."""
    device_to_settings_map = {}
    update_dynamic_groups_cache()
    for device in queryset:
        dynamic_group = device.dynamic_groups.exclude(golden_config_setting__isnull=True).order_by(
            "-golden_config_setting__weight"
        )
        if dynamic_group.exists():
            device_to_settings_map[device.id] = dynamic_group.first().golden_config_setting
    return device_to_settings_map


def get_json_config(config):
    """Helper to JSON load config files."""
    try:
        return json.loads(config)
    except json.decoder.JSONDecodeError:
        return None


def get_xml_config(config):
    """Helper to parse XML config files."""
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.fromstring(config, parser=parser)  # noqa: S320
    except etree.ParseError:
        return None


def list_to_string(items):
    """Helper function to set the proper list of items sentence."""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:  # noqa: PLR2004
        return " and ".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def add_message(combo_check, request):
    """Helper function to abstract the adding a message that the job is not enabled."""
    multiple_messages = []
    for item in combo_check:
        _job, feature_enabled = item
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name=_job).first()
        if not job:
            continue
        if not isinstance(feature_enabled, list):
            feature_enabled = [feature_enabled]
        if not job.enabled and any(feature_enabled):
            multiple_messages.append(f"<a href='{reverse('extras:job_edit', kwargs={'pk': job.pk})}'>{job.name}</a>")
    if multiple_messages:
        messages.warning(request, format_html(f"The Job(s) {list_to_string(multiple_messages)} are not yet enabled."))


def dispatch_params(method, platform, logger):
    """Utility method to map user defined platform network_driver to netutils named entity."""
    custom_dispatcher = settings.PLUGINS_CONFIG[app_config.name].get("custom_dispatcher", {})
    params = {"method": method}

    # If there is a custom driver we can simply return that
    if custom_dispatcher.get(platform):
        params["custom_dispatcher"] = custom_dispatcher[platform]
        params["framework"] = ""
        return params
    # Otherwise we are checking in order of:
    #   1. method & driver
    #   2. method & all
    #   3. default and driver
    #   4. default & all
    if FRAMEWORK_METHODS.get(method) and FRAMEWORK_METHODS[method]().get(platform):
        params["framework"] = FRAMEWORK_METHODS[method]()[platform]
    elif FRAMEWORK_METHODS.get(method) and FRAMEWORK_METHODS[method]().get("all"):
        params["framework"] = FRAMEWORK_METHODS[method]()["all"]
    elif utils.default_framework().get(platform):
        params["framework"] = utils.default_framework()[platform]
    elif utils.default_framework().get("all"):
        params["framework"] = utils.default_framework()["all"]
    if not params.get("framework"):
        error_msg = "`E3022:` Could not find a valid framework (e.g. netmiko) given a method (e.g. merge_config) and a driver (e.g. cisco_ios)."
        logger.error(error_msg)
        raise NornirNautobotException(error_msg)
    return params


def get_xml_subtree_with_full_path(config_xml, match_config):
    """
    Extracts a subtree from an XML configuration based on a provided XPath expression and rebuilds the full path from the root.

    Args:
        config_xml (etree.Element): The root of the XML configuration from which to extract the subtree.
        match_config (str): An XPath expression that specifies the elements to include in the subtree.

    Returns:
        str: The XML subtree as a string, including all elements specified by the XPath expression and their full paths from the root.
    """
    config_elements = config_xml.xpath(match_config)
    new_root = etree.Element(config_xml.tag)
    for element in config_elements:
        current_element = new_root
        for parent in reversed(list(element.iterancestors())):  # from root to parent
            if parent is config_xml:  # skip the root
                continue
            copied_parent = deepcopy(parent)
            copied_parent[:] = []  # remove children
            current_element.append(copied_parent)
            current_element = copied_parent
        current_element.append(deepcopy(element))
    return etree.tostring(new_root, encoding="unicode", pretty_print=True)


def update_dynamic_groups_cache():
    """Update dynamic group cache for all golden config dynamic groups."""
    if not settings.PLUGINS_CONFIG[app_config.name].get("_manual_dynamic_group_mgmt"):
        for setting in models.GoldenConfigSetting.objects.all():
            setting.dynamic_group.update_cached_members()


def get_error_message(error_code, **kwargs):
    """Get the error message for a given error code.

    Args:
        error_code (str): The error code.
        **kwargs: Any additional context data to be interpolated in the error message.

    Returns:
        str: The constructed error message.
    """
    try:
        error_message = ERROR_CODES.get(error_code, ERROR_CODES["E3XXX"]).error_message.format(**kwargs)
    except KeyError as missing_kwarg:
        error_message = f"Error Code was found, but failed to format, message expected kwarg `{missing_kwarg}`."
    except Exception:  # pylint: disable=broad-except
        error_message = "Error Code was found, but failed to format message, unknown cause."
    return f"{error_code}: {error_message}"
