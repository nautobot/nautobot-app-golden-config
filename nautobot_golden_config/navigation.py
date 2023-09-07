"""Add the configuration compliance buttons to the Plugins Navigation."""

from nautobot.core.apps import NavMenuGroup, NavMenuItem, NavMenuTab, NavMenuButton
from nautobot.utilities.choices import ButtonColorChoices
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
            buttons=(
                NavMenuButton(
                    link="plugins:nautobot_golden_config:compliancerule_add",
                    title="Compliance Rules",
                    icon_class="mdi mdi-plus-thick",
                    button_class=ButtonColorChoices.GREEN,
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
                NavMenuButton(
                    link="plugins:nautobot_golden_config:compliancefeature_add",
                    title="Compliance Features",
                    icon_class="mdi mdi-plus-thick",
                    button_class=ButtonColorChoices.GREEN,
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

items_operate.append(
    NavMenuItem(
        link="plugins:nautobot_golden_config:configplan_list",
        name="Config Plans",
        permissions=["nautobot_golden_config.view_configplan"],
        buttons=(
            NavMenuButton(
                link="plugins:nautobot_golden_config:configplan_add",
                title="Generate Config Plan",
                icon_class="mdi mdi-plus-thick",
                button_class=ButtonColorChoices.GREEN,
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
                NavMenuButton(
                    link="plugins:nautobot_golden_config:configremove_add",
                    title="Config Remove",
                    icon_class="mdi mdi-plus-thick",
                    button_class=ButtonColorChoices.GREEN,
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
                NavMenuButton(
                    link="plugins:nautobot_golden_config:configreplace_add",
                    title="Config Replace",
                    icon_class="mdi mdi-plus-thick",
                    button_class=ButtonColorChoices.GREEN,
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
                NavMenuButton(
                    link="plugins:nautobot_golden_config:remediationsetting_add",
                    title="Remediation Settings",
                    icon_class="mdi mdi-plus-thick",
                    button_class=ButtonColorChoices.GREEN,
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
            NavMenuButton(
                link="plugins:nautobot_golden_config:goldenconfigsetting_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                button_class=ButtonColorChoices.GREEN,
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
            (NavMenuGroup(name="Setup", weight=100, items=tuple(items_setup))),
        ),
    ),
)
