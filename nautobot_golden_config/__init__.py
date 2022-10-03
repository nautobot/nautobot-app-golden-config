"""Plugin declaration for nautobot_golden_config."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)

from nautobot.core.signals import nautobot_database_ready
from nautobot.extras.plugins import PluginConfig

from nautobot_golden_config.signals import dynamic_group_validation_callback


class GoldenConfig(PluginConfig):
    """Plugin configuration for the nautobot_golden_config plugin."""

    name = "nautobot_golden_config"
    verbose_name = "Golden Configuration"
    version = __version__
    author = "Network to Code, LLC"
    author_email = "opensource@networktocode.com"
    description = "A plugin for managing Golden Configurations."
    base_url = "golden-config"
    min_version = "1.4.0"
    max_version = "1.99"
    default_settings = {
        "enable_backup": True,
        "enable_compliance": True,
        "enable_intended": True,
        "enable_sotagg": True,
        "per_feature_bar_width": 0.3,
        "per_feature_width": 13,
        "per_feature_height": 4,
        "get_custom_compliance": None,
    }

    def ready(self):
        """Callback when this plugin is loaded."""
        super().ready()
        # Run DynamicGroup validation to ensure an invalid scope was not used to create
        # a DynamicGroup in the v1.2.0 migration.
        nautobot_database_ready.connect(dynamic_group_validation_callback, sender=self)


config = GoldenConfig  # pylint:disable=invalid-name
