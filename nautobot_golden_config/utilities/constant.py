"""Storage of data that will not change throughout the life cycle of application."""
from django.conf import settings

PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_golden_config"]

ENABLE_INTENDED = PLUGIN_CFG["enable_intended"]
ENABLE_COMPLIANCE = PLUGIN_CFG["enable_compliance"]
ENABLE_BACKUP = PLUGIN_CFG["enable_backup"]
ENABLE_SOTAGG = PLUGIN_CFG["enable_sotagg"]
ENABLE_PLAN = PLUGIN_CFG["enable_plan"]
ENABLE_DEPLOY = PLUGIN_CFG["enable_deploy"]
ENABLE_POSTPROCESSING = PLUGIN_CFG["enable_postprocessing"]
DEFAULT_DEPLOY_STATUS = PLUGIN_CFG["default_deploy_status"]

CONFIG_FEATURES = {
    "intended": ENABLE_INTENDED,
    "compliance": ENABLE_COMPLIANCE,
    "backup": ENABLE_BACKUP,
    "sotagg": ENABLE_SOTAGG,
    "postprocessing": ENABLE_POSTPROCESSING,
}
