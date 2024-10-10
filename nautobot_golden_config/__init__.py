"""App declaration for nautobot_golden_config."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from django.db.models.signals import post_migrate
from nautobot.apps import ConstanceConfigItem, NautobotAppConfig
from nautobot.core.signals import nautobot_database_ready

__version__ = metadata.version(__name__)


class GoldenConfig(NautobotAppConfig):
    """App configuration for the nautobot_golden_config app."""

    name = "nautobot_golden_config"
    verbose_name = "Golden Configuration"
    version = __version__
    author = "Network to Code, LLC"
    author_email = "opensource@networktocode.com"
    description = "Nautobot Apps that embraces NetDevOps and automates configuration backups, performs configuration compliance, generates intended configurations, and has config remediation and deployment features. Includes native Git integration and gives users the flexibility to mix and match the supported features."
    base_url = "golden-config"
    required_settings = []
    min_version = "2.0.0"
    max_version = "2.9999"
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_golden_config:docs"


config = GoldenConfig  # pylint:disable=invalid-name
