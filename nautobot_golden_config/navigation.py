"""Menu items."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

items = (
    NavMenuItem(
        link="plugins:nautobot_golden_config:compliancefeature_list",
        name="Golden Config",
        permissions=["nautobot_golden_config.view_compliancefeature"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_golden_config:compliancefeature_add",
                permissions=["nautobot_golden_config.add_compliancefeature"],
            ),
        ),
    ),
)

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(NavMenuGroup(name="Golden Config", items=tuple(items)),),
    ),
)
