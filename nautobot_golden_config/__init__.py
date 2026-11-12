"""App declaration for nautobot_golden_config."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
import logging
from importlib import metadata

from django.conf import settings
from django.db.models.signals import post_migrate
from nautobot.apps import ConstanceConfigItem, NautobotAppConfig, nautobot_database_ready

__version__ = metadata.version(__name__)

logger = logging.getLogger(__name__)

# App-level settings that moved to per-`GoldenConfigSetting` fields of the same name.
DEPRECATED_ENABLE_SETTINGS = (
    "enable_backup",
    "enable_compliance",
    "enable_intended",
    "enable_sotagg",
    "enable_postprocessing",
    "enable_plan",
    "enable_deploy",
)


class GoldenConfig(NautobotAppConfig):
    """App configuration for the nautobot_golden_config app."""

    name = "nautobot_golden_config"
    verbose_name = "Golden Configuration"
    version = __version__
    author = "Network to Code, LLC"
    author_email = "opensource@networktocode.com"
    description = "Nautobot Apps that embraces NetDevOps and automates configuration backups, performs configuration compliance, generates intended configurations, and has config remediation and deployment features. Includes native Git integration and gives users the flexibility to mix and match the supported features."
    base_url = "golden-config"
    docs_view_name = "plugins:nautobot_golden_config:docs"
    default_settings = {
        "default_deploy_status": "Not Approved",
        "postprocessing_callables": [],
        "postprocessing_subscribed": [],
        "per_feature_bar_width": 0.3,
        "per_feature_width": 13,
        "per_feature_height": 4,
        "get_custom_compliance": None,
        # This is an experimental and undocumented setting that will change in the future!!
        # Use at your own risk!!!!!
        "_manual_dynamic_group_mgmt": False,
        "jinja_env": {
            "undefined": "jinja2.StrictUndefined",
            "trim_blocks": True,
            "lstrip_blocks": False,
        },
    }
    constance_config = {
        "DEFAULT_FRAMEWORK": ConstanceConfigItem(
            default={"all": "napalm"},
            help_text="The network library you prefer for by default for your dispatcher methods.",
            field_type="optional_json_field",
        ),
        "GET_CONFIG_FRAMEWORK": ConstanceConfigItem(
            default={},
            help_text="The network library you prefer for making backups.",
            field_type="optional_json_field",
        ),
        "MERGE_CONFIG_FRAMEWORK": ConstanceConfigItem(
            default={},
            help_text="The network library you prefer for pushing configs via a merge.",
            field_type="optional_json_field",
        ),
        "REPLACE_CONFIG_FRAMEWORK": ConstanceConfigItem(
            default={},
            help_text="The network library you prefer for pushing configs via a merge.",
            field_type="optional_json_field",
        ),
    }

    def ready(self):
        """Register custom signals."""
        from nautobot_golden_config.models import ConfigCompliance  # pylint: disable=import-outside-toplevel

        # pylint: disable=import-outside-toplevel
        from .signals import (
            config_compliance_platform_cleanup,
            post_migrate_create_job_button,
            post_migrate_create_statuses,
        )

        nautobot_database_ready.connect(post_migrate_create_statuses, sender=self)
        nautobot_database_ready.connect(post_migrate_create_job_button, sender=self)

        super().ready()
        self._warn_deprecated_enable_settings()
        post_migrate.connect(config_compliance_platform_cleanup, sender=ConfigCompliance)

    def _warn_deprecated_enable_settings(self):
        """Log a warning when `PLUGINS_CONFIG` still carries the removed app-level `enable_*` settings."""
        configured = sorted(set(DEPRECATED_ENABLE_SETTINGS) & set(settings.PLUGINS_CONFIG.get(self.name, {})))
        if configured:
            logger.warning(
                "The `nautobot_golden_config` settings %s are deprecated and no longer read at runtime. Their values "
                "are copied onto each existing Golden Config Setting by the upgrade migration; once it has run, "
                "manage them on the Golden Config Setting and remove them from `PLUGINS_CONFIG`.",
                ", ".join(f"`{name}`" for name in configured),
            )


config = GoldenConfig  # pylint:disable=invalid-name
