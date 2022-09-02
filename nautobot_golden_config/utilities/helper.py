"""Helper functions."""
# pylint: disable=raise-missing-from
from functools import partial
from typing import Optional
import jinja2
from jinja2 import exceptions as jinja_errors

from django.db.models import Q
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist

from nautobot.dcim.models import Device
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.utilities.utils import render_jinja2
from nautobot.users.models import User
from nautobot.extras.models.secrets import SecretsGroup
from nautobot.extras.choices import SecretsGroupAccessTypeChoices
from nautobot.utilities.permissions import permission_is_exempt

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

    # Translate instances from FIELDS set to list of primary keys
    for field in FIELDS:
        if data.get(field):
            query[f"{field}_id"] = data[field].values_list("pk", flat=True)

    # Build tag query based on slug values for each instance
    if data.get("tag"):
        query.update({"tag": data["tag"].values_list("slug", flat=True)})

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
    for device in queryset:
        dynamic_group = device.dynamic_groups.exclude(golden_config_setting__isnull=True).order_by(
            "-golden_config_setting__weight"
        )
        if dynamic_group.exists():
            device_to_settings_map[device.id] = dynamic_group.first().golden_config_setting
    return device_to_settings_map


def get_secret(
    user: User,
    obj_id: str,
    obj_type: str,
    secret_type: str,
    secret_access_type: Optional[str] = SecretsGroupAccessTypeChoices.TYPE_GENERIC,
) -> Optional[str]:
    """Gets the secrets attached to an object based on an ORM relationship. To be used as a Jinja filter.

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


def render_secrets(config_to_render: str, user: User):
    """Renders secrets."""
    jinja_env = jinja2.Environment(autoescape=True)

    # Wrapper for get_secret filter that includes user argument to ensure
    # that secrets are only rendered by authorized users.
    user_gets_secret = partial(get_secret, user)

    jinja_env.filters["get_secret"] = user_gets_secret
    template = jinja_env.from_string(config_to_render)
    return template.render()
