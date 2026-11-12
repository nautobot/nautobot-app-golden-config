"""Storage of data that will not change throughout the life cycle of application."""

from django.conf import settings
from django.utils.module_loading import import_string

PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_golden_config"]

DEFAULT_DEPLOY_STATUS = PLUGIN_CFG["default_deploy_status"]

JINJA_ENV = PLUGIN_CFG["jinja_env"]
if not JINJA_ENV.get("undefined"):
    raise ValueError("The `jinja_env` setting did not include the required key for `undefined`.")
if isinstance(JINJA_ENV["undefined"], str):
    JINJA_ENV["undefined"] = import_string(JINJA_ENV["undefined"])
