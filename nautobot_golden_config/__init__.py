"""App declaration for nautobot_golden_config."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotGoldenConfigConfig(NautobotAppConfig):
    """App configuration for the nautobot_golden_config app."""

    name = "nautobot_golden_config"
    verbose_name = "Golden Config"
    version = __version__
    author = "Network to Code, LLC"
    description = "An app for configuration on nautobot."
    base_url = "golden-config"
    required_settings = []
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_golden_config:docs"
    searchable_models = ["compliancefeature"]


config = NautobotGoldenConfigConfig  # pylint:disable=invalid-name
