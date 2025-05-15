"""Add the configuration compliance buttons to the Apps Navigation."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

items_operate = (
    NavMenuItem(
        link="plugins:nautobot_golden_config:goldenconfig_list",
        name="Config Overview",
        permissions=["nautobot_golden_config.view_goldenconfig"],
    ),
    NavMenuItem(
        link="plugins:nautobot_golden_config:configcompliance_list",
        name="Config Compliance",
        permissions=["nautobot_golden_config.view_configcompliance"],
    ),
    NavMenuItem(
        link="plugins:nautobot_golden_config:configcompliance_overview",
        name="Compliance Report",
        permissions=["nautobot_golden_config.view_configcompliance"],
    ),
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
    ),
)

items_setup = (
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
    ),
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
    ),
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
    ),
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
    ),
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
    ),
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
            NavMenuGroup(name="Manage", weight=100, items=items_operate),
            NavMenuGroup(name="Setup", weight=100, items=items_setup),
            NavMenuGroup(
                name="Tools",
                weight=300,
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_golden_config:generate_intended_config",
                        name="Generate Intended Config",
                        permissions=["dcim.view_device", "extras.view_gitrepository"],
                    ),
                ),
            ),
        ),
    ),
)
