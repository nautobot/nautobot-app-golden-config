"""Helper functions."""
# pylint: disable=raise-missing-from

from typing import Optional
from jinja2 import exceptions as jinja_errors

from django import template
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist

from django_jinja import library

from nornir_nautobot.exceptions import NornirNautobotException

from nautobot.users.models import User
from nautobot.dcim.models import Device
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.utilities.utils import render_jinja2
from nautobot.extras.models.secrets import SecretsGroup
from nautobot.extras.choices import SecretsGroupAccessTypeChoices
from nautobot.utilities.permissions import permission_is_exempt

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
register = template.Library()


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


def render_jinja_template(obj, logger, j2_template):
    """
    Helper function to render Jinja templates.

    Args:
        obj (Device): The Device object from Nautobot.
        logger (NornirLogger): Logger to log error messages to.
        j2_template (str): A Jinja2 template to be rendered.

    Returns:
        str: The ``template`` rendered.

    Raises:
        NornirNautobotException: When there is an error rendering the ``template``.
    """
    try:
        return render_jinja2(template_code=j2_template, context={"obj": obj})
    except jinja_errors.UndefinedError as error:
        error_msg = (
            "Jinja encountered and UndefinedError`, check the template for missing variable definitions.\n"
            f"Template:\n{j2_template}"
        )
        logger.log_failure(obj, error_msg)
        raise NornirNautobotException from error
    except jinja_errors.TemplateSyntaxError as error:  # Also catches subclass of TemplateAssertionError
        error_msg = (
            f"Jinja encountered a SyntaxError at line number {error.lineno},"
            f"check the template for invalid Jinja syntax.\nTemplate:\n{j2_template}"
        )
        logger.log_failure(obj, error_msg)
        raise NornirNautobotException from error
    # Intentionally not catching TemplateNotFound errors since template is passes as a string and not a filename
    except jinja_errors.TemplateError as error:  # Catches all remaining Jinja errors
        error_msg = (
            "Jinja encountered an unexpected TemplateError; check the template for correctness\n"
            f"Template:\n{j2_template}"
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


@library.filter()
@register.filter()
def get_secret(
    user: User,
    obj_id: str,
    obj_type: str,
    secret_type: str,
    secret_access_type: Optional[str] = SecretsGroupAccessTypeChoices.TYPE_GENERIC,
) -> Optional[str]:
    """Gets the secrets attached to an object based on an ORM relationship.

    We assume that there is only one secret group corresponding to a model.

    Args:
        user (User): User object that performs API call to render push template with secrets.
        obj_id (str): Primary key returned for the specific object in the template. The id needs to be part of the GraphQL query.
        obj_type (str): Type of the object in the form of <module_name>.<model_name>, for example: circuits.Circuit
        secret_type (str): Type of secret, such as "username", "password", "token", "secret", or "key".
        secret_access_type (Optional[str], optional): Type of secret such as "Generic", "gNMI", "HTTP(S)". Defaults to "Generic".

    .. rubric:: Example Jinja get_secret filter usage
    .. highlight:: jinja
    .. code-block:: jinja

    password {{ id | get_secret("dcim.Device", "password") | encrypt_type5 }}
    ppp pap sent-username {{ interface["connected_circuit_termination"]["circuit"]["id"] | get_secret("circuits.Circuit", "username") }} password {{ interface["connected_circuit_termination"]["circuit"]["id"] | get_secret("circuits.Circuit", "password") | encrypt_type7 }}

    Returns:
        Optional[str] : Secret value. None if there is no match. An error string if there is an error.
    """
    try:
        module_name, model_name = obj_type.split(".")
    except ValueError:  # not enough values to unpack (expected 2, got 1). We get this error if there is no "." in the obj_type
        return f"Incorrect object type format {obj_type}. The correct format is 'module_name.model_name'."
    try:
        model = apps.get_model(module_name, model_name)
    except ObjectDoesNotExist:
        return f"Model {model_name} does not exist."
    # get the object behind the model using the pk
    try:
        obj = model.objects.get(id=obj_id)
    except ObjectDoesNotExist:
        return f"Object wit ID {obj_id} does not exist."

    # Get user permissions, terminate early if they do not have permission to view
    app_label = obj._meta.app_label
    model_name = obj._meta.model_name
    permission_required = f"{app_label}.view_{model_name}"
    # Bypass restriction for superusers and exempt views
    if user.is_superuser or permission_is_exempt(permission_required):
        pass
    # User is anonymous or has not been granted the requisite permission
    elif not user.is_authenticated or permission_required not in user.get_all_permissions():
        return "You have no permission to read secrets. This incident will be reported."

    # look through the attributes of the model to find if it has an id relationship
    secrets_group = None
    secrets_group_id = obj.__dict__.get("secrets_group_id")
    if secrets_group_id:
        secrets_group = SecretsGroup.objects.get(id=secrets_group_id)

    # if the secret is not in the attributes, it may be in the relationships
    for value in obj.get_relationships_data()["destination"].values():
        # Find the relationship to secrets group
        if isinstance(value["value"], SecretsGroup):
            secrets_group = SecretsGroup.objects.get(slug=value["value"])
            break

    if secrets_group:
        return secrets_group.get_secret_value(
            access_type=secret_access_type,
            secret_type=secret_type,
            obj=obj,
        )

    return None
