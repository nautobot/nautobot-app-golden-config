"""Django Tables2 classes for golden_config plugin."""
import copy

from django.utils.html import format_html
from django_tables2 import Column, TemplateColumn

from nautobot.utilities.tables import BaseTable, ToggleColumn

from .models import ConfigCompliance, ComplianceFeature, GoldenConfiguration
from .utilities.constant import ENABLE_BACKUP, ENABLE_COMPLIANCE, ENABLE_INTENDED, CONFIG_FEATURES


BACKUP_SUCCESS = """
{% if record.backup_last_success_date and record.backup_last_attempt_date == record.backup_last_success_date %}
    <span class="text-success" id="actions">
{% else %}
    <span class="text-danger" id="actions">
{% endif %}
{% if record.backup_last_success_date %}
        {{ record.backup_last_success_date|date:"SHORT_DATETIME_FORMAT" }}
{% else %}
    --
{% endif %}
        <span id=actiontext>{{ record.backup_last_attempt_date|date:"SHORT_DATETIME_FORMAT" }}</span>
    </span>
"""

INTENDED_SUCCESS = """
{% if record.intended_last_success_date and record.intended_last_attempt_date == record.intended_last_success_date %}
    <span class="text-success" id="actions">
{% else %}
    <span class="text-danger" id="actions">
{% endif %}
{% if record.intended_last_success_date %}
        {{ record.intended_last_success_date|date:"SHORT_DATETIME_FORMAT" }}
{% else %}
    --
{% endif %}
        <span id=actiontext>{{ record.intended_last_attempt_date|date:"SHORT_DATETIME_FORMAT" }}</span>
    </span>
"""


COMPLIANCE_SUCCESS = """
{% if record.compliance_last_success_date and record.compliance_last_attempt_date == record.compliance_last_success_date %}
    <span class="text-success" id="actions">
{% else %}
    <span class="text-danger" id="actions">
{% endif %}
{% if record.compliance_last_success_date %}
        {{ record.compliance_last_success_date|date:"SHORT_DATETIME_FORMAT" }}
{% else %}
    --
{% endif %}
        <span id=actiontext>{{ record.compliance_last_attempt_date|date:"SHORT_DATETIME_FORMAT" }}</span>
    </span>
"""

ALL_ACTIONS = """
{% if backup == True %}
    {% if record.backup_config %}
        <a value="{% url 'plugins:nautobot_golden_config:config_details' device_name=record.device config_type='backup' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:config_details' device_name=record.device config_type='backup' %}?modal=true"> 
            <i class="mdi mdi-file-document-outline"></i>
        </a>
    {% else %}
        <i class="mdi mdi-circle-small"></i>
    {% endif %}
{% endif %}
{% if intended == True %}
    {% if record.intended_config %}
        <a value="{% url 'plugins:nautobot_golden_config:config_details' device_name=record.device config_type='intended' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:config_details' device_name=record.device config_type='intended' %}?modal=true"> 
            <i class="mdi mdi-text-box-check-outline"></i>
        </a>
    {% else %}
        <i class="mdi mdi-circle-small"></i>
    {% endif %}
{% endif %}
{% if compliance == True %}
    {% if record.compliance_config %}
        <a value="{% url 'plugins:nautobot_golden_config:config_details' device_name=record.device config_type='compliance' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:config_details' device_name=record.device config_type='compliance' %}?modal=true"> 
            <i class="mdi mdi-file-compare"></i>
        </a>
    {% else %}
        <i class="mdi mdi-circle-small"></i>
    {% endif %}
{% endif %}
{% if sotagg == True %}
    <a value="{% url 'plugins:nautobot_golden_config:config_details' device_name=record.device config_type='sotagg' %}" class="openBtn" data-href="{% url 'plugins:nautobot_golden_config:config_details' device_name=record.device config_type='sotagg' %}?modal=true"> 
        <i class="mdi mdi-code-json"></i>
    </a>
    <a href="{% url 'extras:job' class_path='plugins/nautobot_golden_config.jobs/AllGoldenConfig' %}?device={{ record.device.pk }}"
        <span class="text-primary">
            <i class="mdi mdi-play-circle"></i>
        </span>
    </a>
{% endif %}
"""

COMPLIANCE_FEATURE_NAME = (
    """<a href="{% url 'plugins:nautobot_golden_config:compliancefeature_edit' pk=record.pk %}">{{ record.name }}</a>"""
)

MATCH_CONFIG = """{{ record.match_config|linebreaksbr }}"""


def actual_fields():
    """Convienance function to conditionally toggle columns."""
    active_fields = ["pk", "device__name"]
    if ENABLE_BACKUP:
        active_fields.append("backup_last_success_date")
    if ENABLE_INTENDED:
        active_fields.append("intended_last_success_date")
    if ENABLE_COMPLIANCE:
        active_fields.append("compliance_last_success_date")
    active_fields.append("actions")
    return tuple(active_fields)


class ComplianceColumn(Column):
    """Column used to display config compliance status (True/False/None)."""

    def render(self, value):
        """Render an entry in this column."""
        if value is True:  # pylint: disable=no-else-return
            return format_html('<span class="text-success"><i class="mdi mdi-check-bold"></i></span>')
        elif value is False:
            return format_html('<span class="text-danger"><i class="mdi mdi-close-thick"></i></span>')
        else:  # value is None
            return format_html('<span class="mdi mdi-minus"></span>')


class ConfigComplianceTable(BaseTable):
    """Table for rendering a listing of Device entries and their associated ConfigCompliance record status."""

    pk = ToggleColumn()
    device__name = TemplateColumn(
        template_code="""<a href="{% url 'plugins:nautobot_golden_config:device_report' device_name=record.device  %}" <strong>{{ record.device }}</strong></a> """
    )

    def __init__(self, *args, **kwargs):
        """Override default values to dynamically add columns."""
        # Used ConfigCompliance.objects on purpose, vs queryset (set in args[0]), as there were issues with that as
        # well as not as expected from user standpoint (e.g. not always the same values on columns depending on
        # filtering)
        features = list(ConfigCompliance.objects.order_by("feature").values_list("feature", flat=True).distinct())
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

        model = ConfigCompliance
        fields = (
            "pk",
            "device__name",
        )
        # All other fields (ConfigCompliance features) are constructed dynamically at instantiation time - see views.py


class PercentageColumn(Column):
    """Column used to display percentage."""

    def render(self, value):
        """Render percentage value."""
        return f"{value} %"


class ConfigComplianceGlobalFeatureTable(BaseTable):
    """Table for feature compliance report."""

    count = Column(accessor="count", verbose_name="Total")
    compliant = Column(accessor="compliant", verbose_name="Compliant")
    non_compliant = Column(accessor="non_compliant", verbose_name="Non-Compliant")
    comp_percent = PercentageColumn(accessor="comp_percent", verbose_name="Compliance (%)")
    feature = Column(accessor="feature", verbose_name="Feature")

    class Meta(BaseTable.Meta):
        """Metaclass attributes of ConfigComplianceGlobalFeatureTable."""

        model = ConfigCompliance
        fields = ["feature", "count", "compliant", "non_compliant", "comp_percent"]
        default_columns = [
            "feature",
            "count",
            "compliant",
            "non_compliant",
            "comp_percent",
        ]


class ConfigComplianceDeleteTable(BaseTable):
    """Table for device compliance report."""

    class Meta(BaseTable.Meta):
        """Metaclass attributes of ConfigComplianceDeleteTable."""

        feature = Column(accessor="feature", verbose_name="Feature")
        device__name = Column(accessor="device__name", verbose_name="Device Name")
        compliance = Column(accessor="compliance", verbose_name="Compliance")

        model = ConfigCompliance
        fields = ("device__name", "feature", "compliance")


class GoldenConfigurationTable(BaseTable):
    """Table to display Config Management Status."""

    pk = ToggleColumn()
    device__name = TemplateColumn(
        template_code="""<a href="{% url 'dcim:device' pk=record.device.pk %}">{{ record.device }}</a>""",
        verbose_name="Device",
    )
    if ENABLE_BACKUP:
        backup_last_success_date = TemplateColumn(verbose_name="Backup Status", template_code=BACKUP_SUCCESS)
    if ENABLE_INTENDED:
        intended_last_success_date = TemplateColumn(verbose_name="Intended Status", template_code=INTENDED_SUCCESS)
    if ENABLE_COMPLIANCE:
        compliance_last_success_date = TemplateColumn(
            verbose_name="Compliance Status", template_code=COMPLIANCE_SUCCESS
        )

    actions = TemplateColumn(
        template_code=ALL_ACTIONS, verbose_name="Actions", extra_context=CONFIG_FEATURES, orderable=False
    )

    class Meta(BaseTable.Meta):
        """Meta for class CircuitMaintenanceTable."""

        model = GoldenConfiguration
        fields = actual_fields()


class ComplianceFeatureTable(BaseTable):
    """Table to display Compliance Features."""

    pk = ToggleColumn()
    name = TemplateColumn(template_code=COMPLIANCE_FEATURE_NAME)
    match_config = TemplateColumn(template_code=MATCH_CONFIG)

    class Meta(BaseTable.Meta):
        """Table to display Compliance Features Meta Data."""

        model = ComplianceFeature
        fields = ("pk", "name", "slug", "platform", "description", "config_ordered", "match_config")
        default_columns = ("pk", "name", "slug", "platform", "description", "config_ordered", "match_config")
