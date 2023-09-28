"""Helper functions."""
# pylint: disable=raise-missing-from
import json

from django.template import engines
from django.contrib import messages
from django.db.models import Q
from django.utils.html import format_html
from django.urls import reverse

from jinja2 import exceptions as jinja_errors
from jinja2.sandbox import SandboxedEnvironment
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.dcim.models import Device
from nautobot.utilities.utils import render_jinja2
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config import models
from nautobot_golden_config.utilities.constant import JINJA_ENV

FIELDS_PK = {
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

FIELDS_SLUG = {"tag", "status"}


def get_job_filter(data=None):
    """Helper function to return a the filterable list of OS's based on platform.slug and a specific custom value."""
    if not data:
        data = {}
    query = {}

    # Translate instances from FIELDS set to list of primary keys
    for field in FIELDS_PK:
        if data.get(field):
            query[f"{field}_id"] = data[field].values_list("pk", flat=True)

    # Translate instances from FIELDS set to list of slugs
    for field in FIELDS_SLUG:
        if data.get(field):
            query[f"{field}"] = data[field].values_list("slug", flat=True)

    # Handle case where object is from single device run all.
    if data.get("device") and isinstance(data["device"], Device):
        query.update({"id": [str(data["device"].pk)]})
    elif data.get("device"):
        query.update({"id": data["device"].values_list("pk", flat=True)})

    raw_qs = Q()
    # If scope is set to {} do not loop as all devices are in scope.
    if not models.GoldenConfigSetting.objects.filter(dynamic_group__filter__iexact="{}").exists():
        for obj in models.GoldenConfigSetting.objects.all():
            raw_qs = raw_qs | obj.dynamic_group.generate_query()

    base_qs = Device.objects.filter(raw_qs)

    if not base_qs.exists():
        raise NornirNautobotException(
            "The base queryset didn't find any devices. Please check the Golden Config Setting scope."
        )

    devices_filtered = DeviceFilterSet(data=query, queryset=base_qs)

    if not devices_filtered.qs.exists():
        raise NornirNautobotException(
            "The provided job parameters didn't match any devices detected by the Golden Config scope. Please check the scope defined within Golden Config Settings or select the correct job parameters to correctly match devices."
        )
    devices_no_platform = devices_filtered.qs.filter(platform__isnull=True)
    if devices_no_platform.exists():
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
        logger.log_failure(obj, error_msg)
        raise NornirNautobotException from error


def get_device_to_settings_map(queryset):
    """Helper function to map settings to devices."""
    device_to_settings_map = {}
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


def list_to_string(items):
    """Helper function to set the proper list of items sentence."""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def add_message(inbound):
    """Helper function to abstract the adding a message that the job is not enabled."""
    multiple_messages = []
    for item in inbound:
        job, request, feature_enabled = item
        if not job:
            continue
        if not isinstance(feature_enabled, list):
            feature_enabled = [feature_enabled]
        if not job.enabled and any(feature_enabled):
            multiple_messages.append(
                f"<a href='{reverse('extras:job_edit', kwargs={'slug': job.slug})}'>{job.name}</a>"
            )
    if multiple_messages:
        messages.warning(request, format_html(f"The Job(s) {list_to_string(multiple_messages)} are not yet enabled."))
