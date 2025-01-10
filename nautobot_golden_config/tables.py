"""Django Tables2 classes for golden_config app."""

from django.utils.html import format_html
from django_tables2 import Column, LinkColumn, TemplateColumn
from django_tables2.utils import A
from nautobot.apps.tables import BaseTable, BooleanColumn, TagColumn, ToggleColumn
from nautobot.extras.tables import StatusTableMixin

from nautobot_golden_config import models
from nautobot_golden_config.utilities.constant import CONFIG_FEATURES, ENABLE_BACKUP, ENABLE_COMPLIANCE, ENABLE_INTENDED

ALL_ACTIONS = """
{% if backup == True %}
    {% if record.config_type == 'json' %}
        <i class="mdi mdi-circle-small"></i>
    {% else %}
        {% if record.backup_config %}
            <a value="{% url 'plugins:nautobot_golden_config:goldenconfig_backup' pk=record.device.pk %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:goldenconfig_backup' pk=record.device.pk %}?modal=true">
                <i class="mdi mdi-file-document-outline" title="Backup Configuration"></i>
            </a>
        {% else %}
            <i class="mdi mdi-circle-small"></i>
        {% endif %}
    {% endif %}
{% endif %}
{% if intended == True %}
    {% if record.config_type == 'json' %}
        <i class="mdi mdi-circle-small"></i>
    {% else %}
        {% if record.intended_config %}
            <a value="{% url 'plugins:nautobot_golden_config:goldenconfig_intended' pk=record.device.pk %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:goldenconfig_intended' pk=record.device.pk %}?modal=true">
                <i class="mdi mdi-text-box-check-outline" title="Intended Configuration"></i>
            </a>
        {% else %}
            <i class="mdi mdi-circle-small"></i>
        {% endif %}
    {% endif %}
{% endif %}
{% if postprocessing == True %}
    {% if record.intended_config %}
        <a value="{% url 'plugins:nautobot_golden_config:goldenconfig_postprocessing' pk=record.device.pk %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:goldenconfig_postprocessing' pk=record.device.pk %}?modal=true">
            <i class="mdi mdi-text-box-check" title="Configuration after Postprocessing"></i>
        </a>
    {% else %}
        <i class="mdi mdi-circle-small"></i>
    {% endif %}
{% endif %}
{% if compliance == True %}
    {% if record.intended_config and record.backup_config %}
        <a value="{% url 'plugins:nautobot_golden_config:goldenconfig_compliance' pk=record.device.pk %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:goldenconfig_compliance' pk=record.device.pk %}?modal=true">
            <i class="mdi mdi-file-compare" title="Compliance Details"></i>
        </a>
    {% else %}
        <i class="mdi mdi-circle-small"></i>
    {% endif %}
{% endif %}
{% if sotagg == True %}
    <a value="{% url 'plugins:nautobot_golden_config:goldenconfig_sotagg' pk=record.device.pk %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:goldenconfig_sotagg' pk=record.device.pk %}?modal=true">
        <i class="mdi mdi-code-json" title="SOT Aggregate Data"></i>
    </a>
    {% if record.config_type == 'json' %}
        <i class="mdi mdi-circle-small"></i>
    {% else %}
        <a href="{% url 'extras:job_run_by_class_path' class_path='nautobot_golden_config.jobs.AllGoldenConfig' %}?device={{ record.device.pk }}">
            <span class="text-primary">
                <i class="mdi mdi-play-circle" title="Execute All Golden Config Jobs"></i>
            </span>
        </a>
    {% endif %}
{% endif %}
"""

CONFIG_SET_BUTTON = """
<a href="#" class="openBtn" data-toggle="modal" data-target="#codeModal-{{ record.pk }}">
    <i class="mdi mdi-file-document-outline"></i>
</a>

<div class="modal" id="codeModal-{{ record.pk }}">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <!-- Modal Header -->
            <div class="modal-header">
                <h3 class="modal-title">Config Set - {{ record.device }}</h3>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>

            <!-- Modal body -->
            <div class="modal-body">
                <span id="config_set_{{ record.pk }}"><pre>{{ record.config_set }}</pre></span>
                <span class="config_hover_button">
                    <button type="button" class="btn btn-inline btn-default hover_copy_button" data-clipboard-action='copy' data-clipboard-target="#config_set_{{ record.pk }}">
                        <span class="mdi mdi-content-copy"></span>
                    </button>
                </span>
            </div>

            <!-- Modal footer -->
            <div class="modal-footer">
                <button id="close" type="button" class="btn btn-default" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>"""

MATCH_CONFIG = """{{ record.match_config|linebreaksbr }}"""


def actual_fields():
    """Convienance function to conditionally toggle columns."""
    active_fields = ["pk", "name"]
    if ENABLE_BACKUP:
        active_fields.append("backup_last_success_date")
    if ENABLE_INTENDED:
        active_fields.append("intended_last_success_date")
    if ENABLE_COMPLIANCE:
        active_fields.append("compliance_last_success_date")
    active_fields.append("actions")
    return tuple(active_fields)


#
# Columns
#


class PercentageColumn(Column):
    """Column used to display percentage."""

    def render(self, value):
        """Render percentage value."""
        return f"{value} %"


class ComplianceColumn(Column):
    """Column used to display config compliance status (True/False/None)."""

    def render(self, value):
        """Render an entry in this column."""
        if value == 1:  # pylint: disable=no-else-return
            return format_html('<span class="text-success"><i class="mdi mdi-check-bold"></i></span>')
        elif value == 0:
            return format_html('<span class="text-danger"><i class="mdi mdi-close-thick"></i></span>')
        else:  # value is None
            return format_html('<span class="mdi mdi-minus"></span>')


#
# Tables
#


# ConfigCompliance
class ConfigComplianceTable(BaseTable):
    """Table for rendering a listing of Device entries and their associated ConfigCompliance record status."""

    pk = ToggleColumn(accessor=A("device"))
    device = TemplateColumn(
        template_code="""<a href="{% url 'plugins:nautobot_golden_config:configcompliance_devicetab' pk=record.device %}?tab=nautobot_golden_config:1"><strong>{{ record.device__name }}</strong></a> """
    )

    def __init__(self, *args, **kwargs):
        """Override default values to dynamically add columns."""
        # Used ConfigCompliance.objects on purpose, vs queryset (set in args[0]), as there were issues with that as
        # well as not as expected from user standpoint (e.g. not always the same values on columns depending on
        # filtering)
        features = list(
            models.ConfigCompliance.objects.order_by("rule__feature__slug")
            .values_list("rule__feature__slug", flat=True)
            .distinct()
        )
        # Nautobot's BaseTable.configurable_columns() only recognizes columns in self.base_columns,
        # so override the class's base_columns to include our additional columns as configurable.
        # Note: The correct way to modify django_tables2 columns at init is to use the extra_columns kwarg but Nautobot doesn't support that.
        for feature in features:
            self.base_columns[feature] = ComplianceColumn(verbose_name=feature)  # pylint: disable=no-member
        compliance_columns = [
            column_name
            for column_name, column in self.base_columns.items()  # pylint: disable=no-member
            if isinstance(column, ComplianceColumn)
        ]
        removed_features = set(compliance_columns) - set(features)
        for column_name in removed_features:
            del self.base_columns[column_name]  # pylint: disable=no-member
        super().__init__(*args, **kwargs)

    class Meta(BaseTable.Meta):
        """Metaclass attributes of ConfigComplianceTable."""

        model = models.ConfigCompliance
        fields = (
            "pk",
            "device",
        )
        # All other fields (ConfigCompliance names) are constructed dynamically at instantiation time - see views.py


class ConfigComplianceGlobalFeatureTable(BaseTable):  # pylint: disable=nb-sub-class-name
    """Table for feature compliance report."""

    name = Column(accessor="rule__feature__slug", verbose_name="Feature")
    count = Column(accessor="count", verbose_name="Total")
    compliant = Column(accessor="compliant", verbose_name="Compliant")
    non_compliant = Column(accessor="non_compliant", verbose_name="Non-Compliant")
    comp_percent = PercentageColumn(accessor="comp_percent", verbose_name="Compliance (%)")

    class Meta(BaseTable.Meta):
        """Metaclass attributes of ConfigComplianceGlobalFeatureTable."""

        model = models.ConfigCompliance
        fields = ["name", "count", "compliant", "non_compliant", "comp_percent"]
        default_columns = [
            "name",
            "count",
            "compliant",
            "non_compliant",
            "comp_percent",
        ]


class ConfigComplianceDeleteTable(BaseTable):  # pylint: disable=nb-sub-class-name
    """Table for device compliance report."""

    feature = Column(accessor="rule__feature__name", verbose_name="Feature")

    class Meta(BaseTable.Meta):
        """Metaclass attributes of ConfigComplianceDeleteTable."""

        device = Column(accessor="device__name", verbose_name="Device Name")
        model = models.ConfigCompliance
        fields = ("device", "feature")


class DeleteGoldenConfigTable(BaseTable):  # pylint: disable=nb-sub-class-name
    """
    Table used in bulk delete confirmation.

    This is required since there model is different when deleting the record compared to when viewing the records initially via Device.
    """

    pk = ToggleColumn()

    def __init__(self, *args, **kwargs):
        """Remove all fields from showing except device ."""
        super().__init__(*args, **kwargs)
        for feature in list(self.base_columns.keys()):  # pylint: disable=no-member
            if feature not in ["pk", "device"]:
                self.base_columns.pop(feature)  # pylint: disable=no-member
                self.sequence.remove(feature)

    class Meta(BaseTable.Meta):
        """Meta for class DeleteGoldenConfigTable."""

        model = models.GoldenConfig


# GoldenConfig


class GoldenConfigTable(BaseTable):
    """Table to display Config Management Status."""

    pk = ToggleColumn()
    name = LinkColumn(
        "plugins:nautobot_golden_config:goldenconfig",
        args=[A("pk")],
        text=lambda record: record.device.name,
        verbose_name="Device",
    )

    if ENABLE_BACKUP:
        backup_last_success_date = Column(
            verbose_name="Backup Status", empty_values=(), order_by="backup_last_success_date"
        )
    if ENABLE_INTENDED:
        intended_last_success_date = Column(
            verbose_name="Intended Status",
            empty_values=(),
            order_by="intended_last_success_date",
        )
    if ENABLE_COMPLIANCE:
        compliance_last_success_date = Column(
            verbose_name="Compliance Status",
            empty_values=(),
            order_by="compliance_last_success_date",
        )

    actions = TemplateColumn(
        template_code=ALL_ACTIONS, verbose_name="Actions", extra_context=CONFIG_FEATURES, orderable=False
    )

    def _render_last_success_date(self, record, column, value):
        """Abstract method to get last success per row record."""
        last_success_date = getattr(record, f"{value}_last_success_date", None)
        last_attempt_date = getattr(record, f"{value}_last_attempt_date", None)
        if not last_success_date or not last_attempt_date:
            column.attrs = {"td": {"style": "color:black"}}
            return "--"
        if not last_success_date and not last_attempt_date:
            column.attrs = {"td": {"style": "color:black"}}
            return "--"
        if last_success_date and last_attempt_date == last_success_date:
            column.attrs = {"td": {"style": "color:green"}}
            return last_success_date
        column.attrs = {"td": {"style": "color:red"}}
        return last_success_date

    def render_backup_last_success_date(self, record, column):
        """Pull back backup last success per row record."""
        return self._render_last_success_date(record, column, "backup")

    def render_intended_last_success_date(self, record, column):
        """Pull back intended last success per row record."""
        return self._render_last_success_date(record, column, "intended")

    def render_compliance_last_success_date(self, record, column):
        """Pull back compliance last success per row record."""
        return self._render_last_success_date(record, column, "compliance")

    class Meta(BaseTable.Meta):
        """Meta for class GoldenConfigTable."""

        model = models.GoldenConfig
        fields = actual_fields()


# ComplianceFeature


class ComplianceFeatureTable(BaseTable):
    """Table to display Compliance Features."""

    pk = ToggleColumn()
    name = LinkColumn("plugins:nautobot_golden_config:compliancefeature", args=[A("pk")])

    class Meta(BaseTable.Meta):
        """Table to display Compliance Features Meta Data."""

        model = models.ComplianceFeature
        fields = ("pk", "name", "slug", "description")
        default_columns = ("pk", "name", "slug", "description")


# ComplianceRule


class ComplianceRuleTable(BaseTable):
    """Table to display Compliance Rules."""

    pk = ToggleColumn()
    feature = LinkColumn("plugins:nautobot_golden_config:compliancerule", args=[A("pk")])
    match_config = TemplateColumn(template_code=MATCH_CONFIG)
    config_ordered = BooleanColumn()
    custom_compliance = BooleanColumn()
    config_remediation = BooleanColumn()

    class Meta(BaseTable.Meta):
        """Table to display Compliance Rules Meta Data."""

        model = models.ComplianceRule
        fields = (
            "pk",
            "feature",
            "platform",
            "description",
            "config_ordered",
            "match_config",
            "config_type",
            "custom_compliance",
            "config_remediation",
        )
        default_columns = (
            "pk",
            "feature",
            "platform",
            "description",
            "config_ordered",
            "match_config",
            "config_type",
            "custom_compliance",
            "config_remediation",
        )


# ConfigRemove


class ConfigRemoveTable(BaseTable):
    """Table to display Compliance Rules."""

    pk = ToggleColumn()
    name = LinkColumn("plugins:nautobot_golden_config:configremove", args=[A("pk")])

    class Meta(BaseTable.Meta):
        """Table to display Compliance Rules Meta Data."""

        model = models.ConfigRemove
        fields = ("pk", "name", "platform", "description", "regex")
        default_columns = ("pk", "name", "platform", "description", "regex")


# ConfigReplace


class ConfigReplaceTable(BaseTable):
    """Table to display Compliance Rules."""

    pk = ToggleColumn()
    name = LinkColumn("plugins:nautobot_golden_config:configreplace", args=[A("pk")])

    class Meta(BaseTable.Meta):
        """Table to display Compliance Rules Meta Data."""

        model = models.ConfigReplace
        fields = ("pk", "name", "platform", "description", "regex", "replace")
        default_columns = ("pk", "name", "platform", "description", "regex", "replace")


class GoldenConfigSettingTable(BaseTable):
    # pylint: disable=R0903
    """Table for list view."""

    pk = ToggleColumn()
    name = Column(order_by=("_name",), linkify=True)
    jinja_repository = Column(
        verbose_name="Jinja Repository",
        empty_values=(),
    )
    intended_repository = Column(
        verbose_name="Intended Repository",
        empty_values=(),
    )
    backup_repository = Column(
        verbose_name="Backup Repository",
        empty_values=(),
    )

    def _render_capability(self, record, column, record_attribute):  # pylint: disable=unused-argument
        if getattr(record, record_attribute, None):
            return format_html('<span class="text-success"><i class="mdi mdi-check-bold"></i></span>')
        return format_html('<span class="text-danger"><i class="mdi mdi-close-thick"></i></span>')

    def render_backup_repository(self, record, column):
        """Render backup repository boolean value."""
        return self._render_capability(record=record, column=column, record_attribute="backup_repository")

    def render_intended_repository(self, record, column):
        """Render intended repository boolean value."""
        return self._render_capability(record=record, column=column, record_attribute="intended_repository")

    def render_jinja_repository(self, record, column):
        """Render jinja repository boolean value."""
        return self._render_capability(record=record, column=column, record_attribute="jinja_repository")

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.GoldenConfigSetting
        fields = (
            "pk",
            "name",
            "weight",
            "description",
            "backup_repository",
            "intended_repository",
            "jinja_repository",
        )


class RemediationSettingTable(BaseTable):
    """Table to display RemediationSetting Rules."""

    pk = ToggleColumn()
    platform = LinkColumn("plugins:nautobot_golden_config:remediationsetting", args=[A("pk")])

    class Meta(BaseTable.Meta):
        """Table to display RemediationSetting Meta Data."""

        model = models.RemediationSetting
        fields = ("pk", "platform", "remediation_type")
        default_columns = ("pk", "platform", "remediation_type")


# ConfigPlan


class ConfigPlanTable(StatusTableMixin, BaseTable):
    """Table to display Config Plans."""

    pk = ToggleColumn()
    device = LinkColumn("plugins:nautobot_golden_config:configplan", args=[A("pk")])
    plan_result = TemplateColumn(
        template_code="""<a href="{% url 'extras:jobresult' pk=record.plan_result.pk %}"><i class="mdi mdi-clipboard-text-play-outline"></i></a>"""
    )
    deploy_result = TemplateColumn(
        template_code="""
        {% if record.deploy_result %}
            <a href="{% url 'extras:jobresult' pk=record.deploy_result.pk %}"><i class="mdi mdi-clipboard-text-play-outline"></i></a>
        {% else %}
            &mdash;
        {% endif %}
        """
    )
    config_set = TemplateColumn(template_code=CONFIG_SET_BUTTON, verbose_name="Config Set", orderable=False)
    tags = TagColumn(url_name="plugins:nautobot_golden_config:configplan_list")

    class Meta(BaseTable.Meta):
        """Table to display Config Plans Meta Data."""

        model = models.ConfigPlan
        fields = (
            "pk",
            "device",
            "created",
            "plan_type",
            "feature",
            "change_control_id",
            "change_control_url",
            "plan_result",
            "deploy_result",
            "config_set",
            "status",
            "tags",
        )
        default_columns = (
            "pk",
            "device",
            "created",
            "plan_type",
            "feature",
            "change_control_id",
            "change_control_url",
            "plan_result",
            "deploy_result",
            "config_set",
            "status",
        )
