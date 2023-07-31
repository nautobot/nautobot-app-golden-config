"""Add the configuration compliance buttons to the Plugins Navigation."""

from nautobot.core.apps import NavMenuGroup, NavMenuItem, NavMenuTab
from nautobot_golden_config.utilities.constant import ENABLE_COMPLIANCE, ENABLE_BACKUP

items = [
    NavMenuItem(
        link="plugins:nautobot_golden_config:goldenconfig_list",
        name="Home",
        permissions=["nautobot_golden_config.view_goldenconfig"],
    )
]

if ENABLE_COMPLIANCE:
    items.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configcompliance_list",
            name="Configuration Compliance",
            permissions=["nautobot_golden_config.view_configcompliance"],
        )
    )
    items.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configcompliance_report",
            name="Compliance Report",
            permissions=["nautobot_golden_config.view_configcompliance"],
        )
    )
    items.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:compliancerule_list",
            name="Compliance Rules",
            permissions=["nautobot_golden_config.view_compliancerule"],
        )
    )
    items.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:compliancefeature_list",
            name="Compliance Features",
            permissions=["nautobot_golden_config.view_compliancefeature"],
        )
    )

if ENABLE_BACKUP:
    items.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configremove_list",
            name="Config Removals",
            permissions=["nautobot_golden_config.view_configremove"],
        )
    )
    items.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configreplace_list",
            name="Config Replacements",
            permissions=["nautobot_golden_config.view_configreplace"],
        )
    )


items.append(
    NavMenuItem(
        link="plugins:nautobot_golden_config:goldenconfigsetting_list",
        name="Settings",
        permissions=["nautobot_golden_config.view_goldenconfigsetting"],
    ),
)


menu_items = (
    NavMenuTab(
        name="Golden Config",
        weight=1000,
        groups=(NavMenuGroup(name="Golden Config", weight=100, items=tuple(items)),),
    ),
)
