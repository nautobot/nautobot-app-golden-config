"""Functions related to prepare configuration with postprocessing."""
from functools import partial
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from django.utils.module_loading import import_string
from jinja2 import exceptions as jinja_errors
from jinja2.sandbox import SandboxedEnvironment
from nautobot.dcim.models import Device
from nautobot.extras.choices import SecretsGroupAccessTypeChoices
from nautobot.extras.models.secrets import SecretsGroup
from nautobot.users.models import User
from netutils.utils import jinja2_convenience_function
from nautobot_golden_config import models
from nautobot_golden_config.exceptions import RenderConfigToPushError
from nautobot_golden_config.utilities.constant import ENABLE_POSTPROCESSING, PLUGIN_CFG
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import get_device_to_settings_map


def get_secret_by_secret_group_slug(
    user: User,
    secrets_group_slug: str,
    secret_type: str,
    secret_access_type: Optional[str] = SecretsGroupAccessTypeChoices.TYPE_GENERIC,
    **kwargs,
) -> Optional[str]:
    """Gets the secret from a Secret Group slug. To be used as a Jinja filter.

    Args:
        user (User): User object that performs API call to render push template with secrets.
        secrets_group_slug (str): Secrets Group slug. It needs to be part of the GraphQL query.
        secret_type (str): Type of secret, such as "username", "password", "token", "secret", or "key".
        secret_access_type (Optional[str], optional): Type of secret such as "Generic", "gNMI", "HTTP(S)". Defaults to "Generic".

    Returns:
        Optional[str] : Secret value. None if there is no match. An error string if there is an error.
    """
    try:
        secrets_group = SecretsGroup.objects.get(slug=secrets_group_slug)
    except ObjectDoesNotExist:
        return f"{secrets_group_slug} doesn't exist."

    if not user.has_perm("extras.view_secretsgroup", secrets_group):
        return f"You have no permission to read this secret {secrets_group_slug}."

    return secrets_group.get_secret_value(
        access_type=secret_access_type,
        secret_type=secret_type,
        **kwargs,
    )


def _get_device_agg_data(device, request):
    """Helper method to retrieve GraphQL data from a device."""
    settings = get_device_to_settings_map(Device.objects.filter(pk=device.pk))[device.id]
    _, device_data = graph_ql_query(request, device, settings.sot_agg_query.query)
    return device_data


def render_secrets(config_postprocessing: str, configs: models.GoldenConfig, request: HttpRequest) -> str:
    """Renders secrets using the get_secrets filter.

    This method is defined to render an already rendered intended configuration, but which have used the Jinja
    `{% raw %}` tag to skip the first render (because the first one gets persisted, and for secrets we don't want it).
    It also support chaining with some Netutils encrypt filters.

    .. rubric:: Example Jinja render_secrets filters usage
    .. highlight:: jinja
    .. code-block:: jinja
        ppp pap sent-username {{ secrets_group["slug"] | get_secret_by_secret_group_slug("password") | encrypt_type7 }}

    Returns:
        str : Return a string, with the rendered intended configuration with secrets, or an error message.

    """
    if not config_postprocessing:
        return ""

    # Based on https://docs.nautobot.com/projects/golden-config/en/latest/dev/dev_adr/#renders-secrets
    # the Jinja2 environment that starts with Nautobot should not be used.
    jinja_env = SandboxedEnvironment(autoescape=True)

    # This can only be done safely since the Jinja2 environment does not persist beyond this function.
    # If the code is changed to use the Nautobot Jinja2 environment, then the request's user must be passed
    # in via the template code.
    jinja_env.filters["get_secret_by_secret_group_slug"] = partial(get_secret_by_secret_group_slug, request.user)

    netutils_filters = jinja2_convenience_function()
    for template_name in [
        encrypt_templates for encrypt_templates in netutils_filters if encrypt_templates.startswith("encrypt")
    ]:
        template_filter = netutils_filters.get(template_name)
        if template_filter is not None:
            jinja_env.filters[template_name] = template_filter

    try:
        template = jinja_env.from_string(config_postprocessing)
    except jinja_errors.TemplateAssertionError as error:
        return f"Jinja encountered an TemplateAssertionError: '{error}'; check the template for correctness"

    device_data = _get_device_agg_data(configs.device, request)

    try:
        return template.render(device_data)
    except jinja_errors.UndefinedError as error:
        raise RenderConfigToPushError(
            f"Jinja encountered and UndefinedError: {error}, check the template for missing variable definitions.\n"
        ) from error
    except jinja_errors.TemplateSyntaxError as error:  # Also catches subclass of TemplateAssertionError
        raise RenderConfigToPushError(
            f"Jinja encountered a SyntaxError at line number {error.lineno},"
            f"check the template for invalid Jinja syntax.\n"
        ) from error
    except jinja_errors.TemplateError as error:  # Catches all remaining Jinja errors
        raise RenderConfigToPushError(
            "Jinja encountered an unexpected TemplateError; check the template for correctness\n"
        ) from error


def get_config_postprocessing(configs: models.GoldenConfig, request: HttpRequest) -> str:
    """Renders final configuration  artifact from intended configuration.

    It chains multiple callables to transform an intended configuration into a configuration that can be pushed.
    Each callable should match the following signature:
    `my_callable_function(config_postprocessing: str, configs: models.GoldenConfig, request: HttpRequest)`

    Args:
        configs (models.GoldenConfig): Golden Config object per device, to retrieve device info, and related configs.
        request (HttpRequest): HTTP request for context.
    """
    if not ENABLE_POSTPROCESSING:
        return (
            "Generation of intended configurations postprocessing it is not enabled, check your plugin configuration."
        )

    config_postprocessing = configs.intended_config
    if not config_postprocessing:
        return (
            "No intended configuration is available. Before rendering the configuration with postprocessing, "
            "you need to generate the intended configuration."
        )

    # Available functions to create the final intended configuration, in string dotted format
    # The order is important because, if not changed by the `postprocessing_subscribed`, is going
    # to be used to process the intended configuration in this specific order
    default_postprocessing_callables = [
        "nautobot_golden_config.utilities.config_postprocessing.render_secrets",
    ]
    # The available methods can be extended by configuration settings from postprocessing_callables
    postprocessing_callables = default_postprocessing_callables + PLUGIN_CFG.get("postprocessing_callables", [])

    # Subscribed callables to post-process the intended configuration, in a specific order. With this option, you could
    # skip some default callables, such as `render_secrets` if not desired.
    # In the future, this could be taken from query parameters.
    postprocessing_subscribed = postprocessing_callables
    if PLUGIN_CFG.get("postprocessing_subscribed"):
        postprocessing_subscribed = PLUGIN_CFG["postprocessing_subscribed"]

    for func_name_subscribed in postprocessing_subscribed:
        if func_name_subscribed in postprocessing_callables:
            try:
                func = import_string(func_name_subscribed)
            except ImportError as error:
                msg = (
                    "There was an issue attempting to import a `postprocessing_callables` function of "
                    f"{func_name_subscribed}, this is expected with a local configuration issue and not related to"
                    " the Golden Configuration Plugin, please contact your system admin for further details.\n"
                )
                raise ValueError(msg + str(error)) from error
        else:
            raise ValueError(
                f"{func_name_subscribed} is not included in the available callables: {', '.join(postprocessing_callables)}"
            )
        try:
            config_postprocessing = func(config_postprocessing, configs, request)
        except RenderConfigToPushError as error:
            return f"Found an error rendering the configuration to push: {error}"

    return config_postprocessing
