"""Add the configuration compliance buttons to the Plugins Navigation."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

from nautobot_golden_config.utilities.constant import ENABLE_COMPLIANCE, ENABLE_BACKUP

items_operate = [
    NavMenuItem(
        link="plugins:nautobot_golden_config:goldenconfig_list",
        name="Config Overview",
        permissions=["nautobot_golden_config.view_goldenconfig"],
    )
]

items_setup = []

if ENABLE_COMPLIANCE:
    items_operate.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configcompliance_list",
            name="Config Compliance",
            permissions=["nautobot_golden_config.view_configcompliance"],
        )
    )

if ENABLE_COMPLIANCE:
    items_setup.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:compliancerule_list",
            name="Compliance Rules",
            permissions=["nautobot_golden_config.view_compliancerule"],
        )
    )

if ENABLE_COMPLIANCE:
    items_setup.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:compliancefeature_list",
            name="Compliance Features",
            permissions=["nautobot_golden_config.view_compliancefeature"],
        )
    )


if ENABLE_COMPLIANCE:
    items_operate.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configcompliance_report",
            name="Compliance Report",
            permissions=["nautobot_golden_config.view_configcompliance"],
        )
    )

items_operate.append(
    NavMenuItem(
        link="plugins:nautobot_golden_config:configplan_list",
        name="Config Plans",
        permissions=["nautobot_golden_config.view_configplan"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_golden_config:configplan_add",
                permissions=["nautobot_golden_config.add_configplan"],
            ),
        ),
    )
)

if ENABLE_BACKUP:
    items_setup.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configremove_list",
            name="Config Removals",
            permissions=["nautobot_golden_config.view_configremove"],
        )
    )

if ENABLE_BACKUP:
    items_setup.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configreplace_list",
            name="Config Replacements",
            permissions=["nautobot_golden_config.view_configreplace"],
        )
    )


if ENABLE_COMPLIANCE:
    items_setup.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:remediationsetting_list",
            name="Remediation Settings",
            permissions=["nautobot_golden_config.view_remediationsetting"],
            buttons=(
                NavMenuAddButton(
                    link="plugins:nautobot_golden_config:remediationsetting_add",
                    permissions=["nautobot_golden_config.add_remediationsetting"],
                ),
            ),
        )
    )

items_setup.append(
    NavMenuItem(
        link="plugins:nautobot_golden_config:goldenconfigsetting_list",
        name="Golden Config Settings",
        permissions=["nautobot_golden_config.view_goldenconfigsetting"],
    ),
)


menu_items = (
    NavMenuTab(
        name="Golden Config",
        weight=1000,
        groups=(
            NavMenuGroup(name="Manage", weight=100, items=tuple(items_operate)),
            (NavMenuGroup(name="Setup", weight=100, items=tuple(items_setup))),
        ),
    ),
)
