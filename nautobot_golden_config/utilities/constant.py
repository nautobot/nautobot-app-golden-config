"""Storage of data that will not change throughout the life cycle of application."""
from django.conf import settings
from django.utils.module_loading import import_string

PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_golden_config"]

ENABLE_INTENDED = PLUGIN_CFG["enable_intended"]
ENABLE_COMPLIANCE = PLUGIN_CFG["enable_compliance"]
ENABLE_BACKUP = PLUGIN_CFG["enable_backup"]
ENABLE_SOTAGG = PLUGIN_CFG["enable_sotagg"]
ENABLE_PLAN = PLUGIN_CFG["enable_plan"]
ENABLE_DEPLOY = PLUGIN_CFG["enable_deploy"]
ENABLE_POSTPROCESSING = PLUGIN_CFG["enable_postprocessing"]

CONFIG_FEATURES = {
    "intended": ENABLE_INTENDED,
    "compliance": ENABLE_COMPLIANCE,
    "backup": ENABLE_BACKUP,
    "sotagg": ENABLE_SOTAGG,
    "postprocessing": ENABLE_POSTPROCESSING,
}

JINJA_ENV = PLUGIN_CFG["jinja_env"]
if not JINJA_ENV.get("undefined"):
    raise ValueError("The `jinja_env` setting did not include the required key for `undefined`.")
if isinstance(JINJA_ENV["undefined"], str):
    JINJA_ENV["undefined"] = import_string(JINJA_ENV["undefined"])
