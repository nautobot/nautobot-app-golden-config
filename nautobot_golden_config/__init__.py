"""Plugin declaration for nautobot_golden_config."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

__version__ = metadata.version(__name__)

from nautobot.extras.plugins import NautobotAppConfig


class NautobotGoldenConfigConfig(NautobotAppConfig):
    """Plugin configuration for the nautobot_golden_config plugin."""

    name = "nautobot_golden_config"
    verbose_name = "Golden Config"
    version = __version__
    author = "Network to Code, LLC"
    description = "A plugin for configuration on nautobot."
    base_url = "golden-config"
    required_settings = []
    min_version = "1.4.0"
    max_version = "1.9999"
    default_settings = {}
    caching_config = {}


config = NautobotGoldenConfigConfig  # pylint:disable=invalid-name
