"""Object Detail components for golden config."""

from django.utils.html import format_html
from nautobot.apps import ui
from nautobot.core.templatetags import helpers  # core-import-update


def get_model_instances(m2m_object):
    """Return a unordered bullet list of model instances from a m2m object."""
    if m2m_object.count() == 0:
        return None
    ul_elements = []
    for obj in m2m_object.all():
        ul_elements.append(f"<li>{helpers.hyperlinked_object(obj)}</li>")
    return format_html(f"<ul>{''.join(ul_elements)}</ul>")


def hyperlinked_field_with_icon(url, title, icon_class="mdi mdi-text-box-check-outline"):
    """Render a redirect link with custom icon."""
    return format_html('<a href="{}"><i class="{}" title="{}"></i></a>', url, icon_class, title)


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

golden_config_setting = ui.ObjectDetailContent(
    panels=(
        ui.ObjectFieldsPanel(
            label="General Settings",
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            fields=("weight", "description"),
        ),
        ui.KeyValueTablePanel(
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            context_data_key="dg_data",
            label="Device Scope Details",
            value_transforms={
                "Filter Query Logic": [lambda v: helpers.render_json(v, pretty_print=True)],
                "Scope of Devices": [lambda v: helpers.hyperlinked_field(v.members.count(), v.get_group_members_url())],
            },
        ),
        ui.ObjectFieldsPanel(
            label="Backup Configuration",
            section=ui.SectionChoices.RIGHT_HALF,
            weight=100,
            fields=("backup_repository", "backup_path_template", "backup_test_connectivity"),
            value_transforms={
                "backup_path_template": [helpers.pre_tag],
            },
        ),
        ui.ObjectFieldsPanel(
            label="Intended Configuration",
            section=ui.SectionChoices.RIGHT_HALF,
            weight=200,
            fields=("intended_repository", "intended_path_template"),
            value_transforms={
                "intended_path_template": [helpers.pre_tag],
            },
        ),
        ui.ObjectFieldsPanel(
            label="Templates Configuration",
            section=ui.SectionChoices.RIGHT_HALF,
            weight=300,
            fields=("jinja_repository", "jinja_path_template", "sot_agg_query"),
            value_transforms={
                "jinja_path_template": [helpers.pre_tag],
            },
        ),
    )
)

golden_config = ui.ObjectDetailContent(
    panels=(
        ui.KeyValueTablePanel(
            section=ui.SectionChoices.RIGHT_HALF,
            weight=100,
            label="Configuration Links",
            context_data_key="device_object",
            value_transforms={
                "Backup Config": [
                    lambda v: hyperlinked_field_with_icon(v, title="Backup Configuration"),
                ],
                "Intended Config": [
                    lambda v: hyperlinked_field_with_icon(v, title="Intended Configuration"),
                ],
                "Compliance Config": [
                    lambda v: hyperlinked_field_with_icon(v, title="Compliance"),
                ],
            },
        ),
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            fields=("device",),
        ),
        ui.ObjectFieldsPanel(
            label="Backup Configuration",
            section=ui.SectionChoices.LEFT_HALF,
            weight=200,
            fields=("backup_last_attempt_date", "backup_last_success_date"),
        ),
        ui.ObjectFieldsPanel(
            label="Intended Configuration",
            section=ui.SectionChoices.LEFT_HALF,
            weight=300,
            fields=("intended_last_attempt_date", "intended_last_success_date"),
        ),
        ui.ObjectFieldsPanel(
            label="Compliance Details",
            section=ui.SectionChoices.LEFT_HALF,
            weight=400,
            fields=("compliance_last_attempt_date", "compliance_last_success_date"),
        ),
    ),
)

config_plan = ui.ObjectDetailContent(
    panels=(
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.LEFT_HALF,
            label="Config Plan Details",
            weight=100,
            fields=(
                "device",
                "status",
                "created",
                "plan_type",
                "feature",
                "plan_result",
            ),
            value_transforms={
                "feature": [get_model_instances, helpers.placeholder],
            },
        ),
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.RIGHT_HALF,
            label="Config Deployment Details",
            weight=100,
            fields=(
                "change_control_id",
                "change_control_url",
                "deploy_result",
            ),
            value_transforms={
                "deploy_result": [lambda v: helpers.hyperlinked_field(getattr(v, "status", v))],
            },
        ),
        ui.Panel(
            label="Postprocessed Config Set",
            weight=100,
            section=ui.SectionChoices.RIGHT_HALF,
            body_content_template_path="nautobot_golden_config/configplan_postprocessing.html",
        ),
        ui.ObjectTextPanel(
            weight=200,
            label="Config Set",
            section=ui.SectionChoices.FULL_WIDTH,
            object_field="config_set",
            render_as=ui.TextPanel.RenderOptions.CODE,
            render_placeholder=True,
        ),
    ),
)


config_compliance = ui.ObjectDetailContent(
    panels=(
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.LEFT_HALF,
            weight=100,
            fields=("device", "rule", "compliance"),
        ),
        ui.ObjectFieldsPanel(
            section=ui.SectionChoices.RIGHT_HALF,
            weight=100,
            fields=("actual", "intended", "remediation", "missing", "extra"),
            value_transforms={
                "actual": [helpers.pre_tag],
                "intended": [helpers.pre_tag],
                "remediation": [helpers.pre_tag],
                "missing": [helpers.pre_tag],
                "extra": [helpers.pre_tag],
            },
        ),
    ),
)
