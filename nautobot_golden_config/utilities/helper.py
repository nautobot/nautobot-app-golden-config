"""Helper functions."""

# pylint: disable=raise-missing-from
import json
from copy import deepcopy

from django.conf import settings
from django.contrib import messages
from django.db.models import OuterRef, Q, Subquery
from django.db.utils import ProgrammingError
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
from nautobot_golden_config.utilities.constant import ENABLE_SOTAGG, JINJA_ENV

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


def get_inscope_settings_from_device_qs(queryset):
    """Wrapper function to return a queryset of GoldenConfigSettings that are in scope for the provided queryset."""
    inscope_gcs = []
    for gc in models.GoldenConfigSetting.objects.all():
        common_objects_queryset = queryset.intersection(gc.dynamic_group.members)
        if common_objects_queryset.count() > 0:
            inscope_gcs.append(gc)
    return inscope_gcs


def get_device_to_settings_map(queryset, job_name):
    """Helper function to map heightest weighted GC settings to devices."""
    update_dynamic_groups_cache()
    annotated_queryset = queryset.all().annotate(
        gc_settings=Subquery(
            models.GoldenConfigSetting.objects.filter(
                dynamic_group__static_group_associations__associated_object_id=OuterRef("id"),
                dynamic_group__static_group_associations__associated_object_type__app_label="dcim",
                dynamic_group__static_group_associations__associated_object_type__model="device",
            )
            .order_by("-weight")
            # [:1] is a ORM/DB "limit 1" query, not a python slice.
            .values("id")[:1]
        )
    )
    gcs = {gc.id: gc for gc in models.GoldenConfigSetting.objects.all()}
    if job_name == "all":
        job_name = ["backup", "intended", "compliance"]
    else:
        job_name = [job_name]
    settings_filters2 = {setting: {True: {}, False: {}} for setting in job_name}
    for device in annotated_queryset:
        for setting in settings_filters2:
            is_enabled = getattr(gcs[device.gc_settings], f"{setting}_enabled", False)
            settings_filters2[setting][is_enabled][device.id] = gcs[device.gc_settings]
    return settings_filters2


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


class GoldenConfigDefaults:
    """Lightweight stand-in for GoldenConfigSetting rows if none exist or DB is unmigrated."""

    def __init__(self, defaults_dict):
        """Store each default key as an attribute on self, so that code can use `gc_settings.backup_enabled` as normal."""
        settings_mapper = {
            "enable_backup": "backup_enabled",
            "enable_intended": "intended_enabled",
            "enable_compliance": "compliance_enabled",
            "enable_plan": "plan_enabled",
            "enable_deploy": "deploy_enabled",
        }
        for key, value in defaults_dict.items():
            if settings_mapper.get(key):
                setattr(self, settings_mapper.get(key), value)

    def __str__(self):
        """GoldenConfigDefaults string repreentation."""
        return "<GoldenConfigDefaults fallback>"


def get_golden_config_settings():
    """Return the first GoldenConfigSetting in the database if it exists; otherwise return a fallback object that uses GoldenConfig.default_settings."""
    try:
        db_instance = models.GoldenConfigSetting.objects.first()
        if db_instance:
            return db_instance
    except ProgrammingError:
        # Table doesn't exist yet, or other DB issues
        pass

    # Fall back to default settings if no DB row is available
    return GoldenConfigDefaults(app_config.default_settings)


def verify_feature_enabled(logger, feature_name, gc_settings, required_settings=None):
    """Verify if a feature is enabled and has required settings.

    Args:
        logger: Logger instance
        feature_name: Name of the feature to check (backup, intended, compliance, etc)
        gc_settings: GoldenConfigSetting instance
        required_settings: List of required setting attributes for this feature

    Raises:
        NornirNautobotException: If feature is disabled or missing required settings
    """
    feature_enabled = getattr(gc_settings, f"{feature_name}_enabled", False)
    if not feature_enabled:
        error_msg = f"`E3038:` The {feature_name} feature is disabled in Golden Config settings."
        logger.error(error_msg)
        raise NornirNautobotException(error_msg)

    if required_settings:
        missing_settings = []
        for setting in required_settings:
            if not getattr(gc_settings, setting, None):
                missing_settings.append(setting)

        if missing_settings:
            if feature_name == "intended" and "sot_agg_query" in missing_settings and not ENABLE_SOTAGG:
                # Skip SOT aggregation query check if the feature is disabled
                missing_settings.remove("sot_agg_query")

            if missing_settings:  # Check again in case we removed the only missing setting
                error_msg = f"`E3039:` Missing required settings for {feature_name}: {', '.join(missing_settings)}"
                logger.error(error_msg)
                raise NornirNautobotException(error_msg)


def verify_config_plan_eligibility(logger, device, gc_settings):
    """Verify if a device is eligible for config plan operations.

    Args:
        logger: Logger instance
        device: Device instance
        gc_settings: GoldenConfigSetting instance

    Raises:
        NornirNautobotException: If device is not eligible for config plans
    """
    if not gc_settings.plan_enabled:
        error_msg = "`E3034:` Config plan creation is disabled in Golden Config settings."
        logger.error(error_msg)
        raise NornirNautobotException(error_msg)

    # Check if device is in scope
    device_settings = get_device_to_settings_map(device)
    if not device_settings:
        error_msg = f"`E3035:` Device {device.name} is not in scope for config plans."
        logger.error(error_msg)
        raise NornirNautobotException(error_msg)


def verify_deployment_eligibility(logger, config_plan, gc_settings):
    """Verify if a config plan is eligible for deployment.

    Args:
        logger: Logger instance
        config_plan: ConfigPlan instance
        gc_settings: GoldenConfigSetting instance

    Raises:
        NornirNautobotException: If deployment is not allowed
    """
    if not gc_settings.deploy_enabled:
        error_msg = "`E3036:` Configuration deployment is disabled in Golden Config settings."
        logger.error(error_msg)
        raise NornirNautobotException(error_msg)

    # Check if device is still in scope
    device_settings = get_device_to_settings_map(config_plan.device)
    if not device_settings:
        error_msg = f"`E3037:` Device {config_plan.device.name} is no longer in scope for deployments."
        logger.error(error_msg)
        raise NornirNautobotException(error_msg)


# class GCSettingsDeviceFilterSet:
#     """Helper class to filter and group devices based on their Golden Config settings."""

#     def __init__(self, queryset):
#         """Initialize with a job device queryset.

#         Args:
#             queryset: Django queryset of Device objects
#         """
#         self.queryset = queryset
#         # self.device_to_settings_map = get_device_to_settings_map(self.queryset)
#         self.settings_filters = {
#             setting: {True: {}, False: {}} for setting in ["backup", "intended", "compliance", "plan", "deploy"]
#         }
#         self._populate_filters()

#     def _populate_filters(self):
#         """Populate filters for each setting."""
#         for device, gc_settings in get_device_to_settings_map(self.queryset).items():
#             for setting in self.settings_filters:
#                 is_enabled = getattr(gc_settings, f"{setting}_enabled", False)
#                 self.settings_filters[setting][is_enabled][device] = gc_settings

#     def get_filtered_querysets(self, setting_type):
#         """Return the filtered querysets for a given setting type."""
#         enabled_devices = self.settings_filters[setting_type][True].keys()
#         disabled_devices = self.settings_filters[setting_type][False].keys()
#         return self.queryset.filter(pk__in=enabled_devices), self.queryset.filter(pk__in=disabled_devices)


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
