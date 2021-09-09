"""Django Tables2 classes for golden_config plugin."""
import copy

from django.utils.html import format_html
from django_tables2 import Column, LinkColumn, TemplateColumn
from django_tables2.utils import A

from nautobot.dcim.models import Device
from nautobot.utilities.tables import (
    BaseTable,
    ToggleColumn,
)
from nautobot_golden_config import models
from nautobot_golden_config.utilities.constant import ENABLE_BACKUP, ENABLE_COMPLIANCE, ENABLE_INTENDED, CONFIG_FEATURES


ALL_ACTIONS = """
{% if backup == True %}
    {% if record.configcompliance_set.first.rule.config_type == 'json' %}
        <i class="mdi mdi-circle-small"></i>
    {% else %}
        {% if record.goldenconfig_set.first.backup_config %}
            <a value="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='backup' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='backup' %}?modal=true">
                <i class="mdi mdi-file-document-outline" title="Backup Configuration"></i>
            </a>
        {% else %}
            <i class="mdi mdi-circle-small"></i>
        {% endif %}
    {% endif %}
{% endif %}
{% if intended == True %}
    {% if record.configcompliance_set.first.rule.config_type == 'json' %}
        <i class="mdi mdi-circle-small"></i>
    {% else %}
        {% if record.goldenconfig_set.first.intended_config %}
            <a value="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='intended' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='intended' %}?modal=true">
                <i class="mdi mdi-text-box-check-outline" title="Intended Configuration"></i>
            </a>
        {% else %}
            <i class="mdi mdi-circle-small"></i>
        {% endif %}
    {% endif %}
{% endif %}
{% if compliance == True %}
    {% if record.configcompliance_set.first.rule.config_type == 'json' %}
            <a value="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='json_compliance' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='json_compliance' %}?modal=true">
                <i class="mdi mdi-file-compare" title="Compliance Details JSON"></i>
            </a>
    {% else %}
        {% if record.goldenconfig_set.first.compliance_config %}
            <a value="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='compliance' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='compliance' %}?modal=true">
                <i class="mdi mdi-file-compare" title="Compliance Details"></i>
            </a>
        {% else %}
            <i class="mdi mdi-circle-small"></i>
        {% endif %}
    {% endif %}
{% endif %}
{% if sotagg == True %}
    <a value="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='sotagg' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:configcompliance_details' pk=record.pk config_type='sotagg' %}?modal=true">
        <i class="mdi mdi-code-json" title="SOT Aggregate Data"></i>
    </a>
    {% if record.configcompliance_set.first.rule.config_type == 'json' %}
        <i class="mdi mdi-circle-small"></i>
    {% else %}
        <a href="{% url 'extras:job' class_path='plugins/nautobot_golden_config.jobs/AllGoldenConfig' %}?device={{ record.pk }}"
            <span class="text-primary">
                <i class="mdi mdi-play-circle" title="Execute All Golden Config Jobs"></i>
            </span>
        </a>
    {% endif %}
{% endif %}
"""

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
        template_code="""<a href="{% url 'plugins:nautobot_golden_config:configcompliance_devicedetail' pk=record.device  %}" <strong>{{ record.device__name }}</strong></a> """
    )

    def __init__(self, *args, **kwargs):
        """Override default values to dynamically add columns."""
        # Used ConfigCompliance.objects on purpose, vs queryset (set in args[0]), as there were issues with that as
        # well as not as expected from user standpoint (e.g. not always the same values on columns depending on
        # filtering)
        features = list(
            models.ConfigCompliance.objects.order_by("rule__feature__name")
            .values_list("rule__feature__name", flat=True)
            .distinct()
        )
        extra_columns = [(feature, ComplianceColumn(verbose_name=feature)) for feature in features]
        kwargs["extra_columns"] = extra_columns
        # Nautobot's BaseTable.configurable_columns() only recognizes columns in self.base_columns,
        # so override the class's base_columns to include our additional columns as configurable.
        self.base_columns = copy.deepcopy(self.base_columns)
        for feature, column in extra_columns:
            self.base_columns[feature] = column
        super().__init__(*args, **kwargs)

    class Meta(BaseTable.Meta):
        """Metaclass attributes of ConfigComplianceTable."""

        model = models.ConfigCompliance
        fields = (
            "pk",
            "device",
        )
        # All other fields (ConfigCompliance names) are constructed dynamically at instantiation time - see views.py


class ConfigComplianceGlobalFeatureTable(BaseTable):
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


class ConfigComplianceDeleteTable(BaseTable):
    """Table for device compliance report."""

    feature = Column(accessor="rule__feature__name", verbose_name="Feature")

    class Meta(BaseTable.Meta):
        """Metaclass attributes of ConfigComplianceDeleteTable."""

        device = Column(accessor="device__name", verbose_name="Device Name")
        compliance = Column(accessor="compliance", verbose_name="Compliance")
        model = models.ConfigCompliance
        fields = ("device", "feature", "compliance")


# GoldenConfig


class GoldenConfigTable(BaseTable):
    """Table to display Config Management Status."""

    pk = ToggleColumn()
    name = TemplateColumn(
        template_code="""<a href="{% url 'dcim:device' pk=record.pk %}">{{ record.name }}</a>""",
        verbose_name="Device",
    )

    if ENABLE_BACKUP:
        backup_last_success_date = Column(verbose_name="Backup Status", empty_values=())
    if ENABLE_INTENDED:
        intended_last_success_date = Column(verbose_name="Intended Status", empty_values=())
    if ENABLE_COMPLIANCE:
        compliance_last_success_date = Column(verbose_name="Compliance Status", empty_values=())

    actions = TemplateColumn(
        template_code=ALL_ACTIONS, verbose_name="Actions", extra_context=CONFIG_FEATURES, orderable=False
    )

    def _render_last_success_date(self, record, column, value):  # pylint: disable=no-self-use
        """Abstract method to get last success per row record."""
        entry = record.goldenconfig_set.first()
        last_success_date = getattr(entry, f"{value}_last_success_date", None)
        last_attempt_date = getattr(entry, f"{value}_last_attempt_date", None)
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

    def render_backup_last_success_date(self, record, column):  # pylint: disable=no-self-use
        """Pull back backup last success per row record."""
        return self._render_last_success_date(record, column, "backup")

    def render_intended_last_success_date(self, record, column):  # pylint: disable=no-self-use
        """Pull back intended last success per row record."""
        return self._render_last_success_date(record, column, "intended")

    def render_compliance_last_success_date(self, record, column):  # pylint: disable=no-self-use
        """Pull back compliance last success per row record."""
        return self._render_last_success_date(record, column, "compliance")

    class Meta(BaseTable.Meta):
        """Meta for class GoldenConfigTable."""

        model = Device
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

    class Meta(BaseTable.Meta):
        """Table to display Compliance Rules Meta Data."""

        model = models.ComplianceRule
        fields = ("pk", "feature", "platform", "description", "config_ordered", "match_config", "config_type")
        default_columns = ("pk", "feature", "platform", "description", "config_ordered", "match_config", "config_type")


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
