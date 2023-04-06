"""Plugin declaration for nautobot_golden_config."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)

from nautobot.extras.plugins import PluginConfig


class GoldenConfig(PluginConfig):
    """Plugin configuration for the nautobot_golden_config plugin."""

    name = "nautobot_golden_config"
    verbose_name = "Golden Configuration"
    version = __version__
    author = "Network to Code, LLC"
    author_email = "opensource@networktocode.com"
    description = "Nautobot Apps that embraces NetDevOps and automates configuration backups, performs configuration compliance, and generates intended configurations. Includes native Git integration and gives users the flexibility to mix and match the supported features."
    base_url = "golden-config"
    min_version = "1.4.0"
    max_version = "1.99"
    default_settings = {
        "enable_backup": True,
        "enable_compliance": True,
        "enable_intended": True,
        "enable_sotagg": True,
        "enable_postprocessing": False,
        "postprocessing_callables": [],
        "postprocessing_subscribed": [],
        "per_feature_bar_width": 0.3,
        "per_feature_width": 13,
        "per_feature_height": 4,
        "get_custom_compliance": None,
    }

    def ready(self):
        super().ready()
        from . import models
        from . import signals

        if not models.GoldenConfig.objects.count():
            try:
                gc_setting = models.GoldenConfigSetting.objects.first()
            except models.GoldenConfigSetting.DoesNotExist:
                return  # TODO: Log a message
            dynamic_group = gc_setting.dynamic_group
            if dynamic_group:
                for device in dynamic_group.members.all():
                    models.GoldenConfig.objects.create(device=device)


config = GoldenConfig  # pylint:disable=invalid-name
