"""Add the configuration compliance buttons to the Plugins Navigation."""

from nautobot.extras.plugins import PluginMenuItem, PluginMenuButton
from nautobot.utilities.choices import ButtonColorChoices
from .utilities.constant import ENABLE_COMPLIANCE


plugin_items = [
    PluginMenuItem(
        link="plugins:nautobot_golden_config:home",
        link_text="Home",
        permissions=["nautobot_golden_config.view_configstatus"],
    )
]

if ENABLE_COMPLIANCE:
    plugin_items.append(
        PluginMenuItem(
            link="plugins:nautobot_golden_config:config_report",
            link_text="Configuration Compliance",
            permissions=["nautobot_golden_config.view_configcompliance"],
        )
    )
    plugin_items.append(
        PluginMenuItem(
            link="plugins:nautobot_golden_config:compliancefeature_list",
            link_text="Compliance Rules",
            permissions=["nautobot_golden_config.view_compliancefeature"],
            buttons=(
                PluginMenuButton(
                    link="plugins:nautobot_golden_config:compliancefeature_add",
                    title="Compliance Rules",
                    icon_class="mdi mdi-plus-thick",
                    color=ButtonColorChoices.GREEN,
                    permissions=["nautobot_golden_config.add_compliancefeature"],
                ),
            ),
        )
    )

menu_items = tuple(plugin_items)
