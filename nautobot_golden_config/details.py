"""Object Detail components for golden config."""

from nautobot.apps import ui
from nautobot.core.templatetags import helpers

compliance_feature = ui.ObjectDetailContent(
    panels=(
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            fields="__all__",
        ),
    ),
)

compliance_rule = ui.ObjectDetailContent(
    panels=(
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            fields="__all__",
            value_transforms={
                "match_config": [helpers.pre_tag],
            },
        ),
    ),
)

config_remove = ui.ObjectDetailContent(
    panels=(
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            fields="__all__",
            value_transforms={
                "regex": [helpers.pre_tag],
            },
        ),
    ),
)

config_replace = ui.ObjectDetailContent(
    panels=(
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            fields="__all__",
            value_transforms={
                "regex": [helpers.pre_tag],
                "replace": [helpers.pre_tag],
            },
        ),
    ),
)

config_remediation = ui.ObjectDetailContent(
    panels=(
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            fields="__all__",
            value_transforms={
                "remediation_options": [helpers.render_json],
            },
        ),
    ),
)
