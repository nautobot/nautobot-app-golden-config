"""App declaration for nautobot_golden_config."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotGoldenConfigConfig(NautobotAppConfig):
    """App configuration for the nautobot_golden_config app."""

    name = "nautobot_golden_config"
    verbose_name = "Golden Configuration"
    version = __version__
    author = "Network to Code, LLC"
    description = "An app for configuration on nautobot."
    base_url = "golden-config"
    default_settings = {
        "enable_backup": True,
        "enable_compliance": True,
        "enable_intended": True,
        "enable_sotagg": True,
        "enable_postprocessing": False,
        "enable_plan": True,
        "enable_deploy": True,
        "default_deploy_status": "Not Approved",
        "postprocessing_callables": [],
        "postprocessing_subscribed": [],
        "per_feature_bar_width": 0.3,
        "per_feature_width": 13,
        "per_feature_height": 4,
        "get_custom_compliance": None,
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
            post_migrate_create_statuses,
            post_migrate_create_job_button,
        )

        nautobot_database_ready.connect(post_migrate_create_statuses, sender=self)
        nautobot_database_ready.connect(post_migrate_create_job_button, sender=self)

        super().ready()
        post_migrate.connect(config_compliance_platform_cleanup, sender=ConfigCompliance)


config = GoldenConfig  # pylint:disable=invalid-name
