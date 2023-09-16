"""Add the configuration compliance buttons to the Plugins Navigation."""

from nautobot.core.apps import NavMenuGroup, NavMenuItem, NavMenuTab, NavMenuAddButton
from nautobot_golden_config.utilities.constant import ENABLE_COMPLIANCE, ENABLE_BACKUP, ENABLE_PLAN

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
            buttons=(
                NavMenuAddButton(
                    link="plugins:nautobot_golden_config:compliancerule_add",
                    permissions=["nautobot_golden_config.add_compliancerule"],
                ),
            ),
        )
    )

if ENABLE_COMPLIANCE:
    items_setup.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:compliancefeature_list",
            name="Compliance Features",
            permissions=["nautobot_golden_config.view_compliancefeature"],
            buttons=(
                NavMenuAddButton(
                    link="plugins:nautobot_golden_config:compliancefeature_add",
                    permissions=["nautobot_golden_config.add_compliancefeature"],
                ),
            ),
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

if ENABLE_PLAN:
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
            buttons=(
                NavMenuAddButton(
                    link="plugins:nautobot_golden_config:configremove_add",
                    permissions=["nautobot_golden_config.add_configremove"],
                ),
            ),
        )
    )

if ENABLE_BACKUP:
    items_setup.append(
        NavMenuItem(
            link="plugins:nautobot_golden_config:configreplace_list",
            name="Config Replacements",
            permissions=["nautobot_golden_config.view_configreplace"],
            buttons=(
                NavMenuAddButton(
                    link="plugins:nautobot_golden_config:configreplace_add",
                    permissions=["nautobot_golden_config.add_configreplace"],
                ),
            ),
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
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_golden_config:goldenconfigsetting_add",
                permissions=["nautobot_golden_config.change_goldenconfigsetting"],
            ),
        ),
    ),
)


menu_items = (
    NavMenuTab(
        name="Golden Config",
        weight=1000,
        groups=(
            NavMenuGroup(name="Manage", weight=100, items=tuple(items_operate)),
            NavMenuGroup(name="Setup", weight=100, items=tuple(items_setup)),
        ),
    ),
)
