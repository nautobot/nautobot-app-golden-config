"""Forms for Device Configuration Backup."""
# pylint: disable=too-many-ancestors

import json

import django.forms as django_forms
from django.conf import settings
from nautobot.apps import forms
from nautobot.dcim.models import Device, DeviceType, Location, Manufacturer, Platform, Rack, RackGroup
from nautobot.extras.forms import NautobotBulkEditForm, NautobotFilterForm, NautobotModelForm
from nautobot.extras.models import DynamicGroup, GitRepository, GraphQLQuery, JobResult, Role, Status, Tag
from nautobot.tenancy.models import Tenant, TenantGroup
from packaging import version

from nautobot_golden_config import models
from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice, ConfigPlanTypeChoice, RemediationTypeChoice

# ConfigCompliance


class DeviceRelatedFilterForm(NautobotFilterForm):  # pylint: disable=nb-no-model-found
    """Base FilterForm for below FilterForms."""

    tenant_group_id = forms.DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(), to_field_name="id", required=False, label="Tenant group ID"
    )
    tenant_group = forms.DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        to_field_name="name",
        required=False,
        label="Tenant group name",
        null_option="None",
    )
    tenant = forms.DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        to_field_name="name",
        required=False,
        null_option="None",
        query_params={"group": "$tenant_group"},
    )
    location_id = forms.DynamicModelMultipleChoiceField(
        # Not limiting to query_params={"content_type": "dcim.device" to allow parent locations to be included
        # i.e. include all sites in a Region, even though Region can't be assigned to a Device
        queryset=Location.objects.all(),
        to_field_name="id",
        required=False,
        label="Location ID",
    )
    location = forms.DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(), to_field_name="name", required=False, label="Location name"
    )
    rack_group_id = forms.DynamicModelMultipleChoiceField(
        queryset=RackGroup.objects.all(),
        to_field_name="id",
        required=False,
        label="Rack group ID",
        query_params={"location": "$location"},
    )
    rack_group = forms.DynamicModelMultipleChoiceField(
        queryset=RackGroup.objects.all(),
        to_field_name="name",
        required=False,
        label="Rack group name",
        query_params={"location": "$location"},
    )
    rack_id = forms.DynamicModelMultipleChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        label="Rack",
        null_option="None",
        query_params={
            "location": "$location",
            "group_id": "$rack_group_id",
        },
    )
    role = forms.DynamicModelMultipleChoiceField(
        queryset=Role.objects.all(),
        to_field_name="name",
        required=False,
        query_params={"content_types": "dcim.device"},
    )
    manufacturer = forms.DynamicModelMultipleChoiceField(
        queryset=Manufacturer.objects.all(), to_field_name="name", required=False, label="Manufacturer"
    )
    device_type = forms.DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        label="Model",
        display_field="model",
        query_params={"manufacturer": "$manufacturer"},
    )
    platform = forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="name", required=False, null_option="None"
    )
    device = forms.DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, null_option="None", label="Device", to_field_name="name"
    )


class GoldenConfigFilterForm(DeviceRelatedFilterForm):
    """Filter Form for GoldenConfig."""

    model = models.GoldenConfig
    field_order = [
        "q",
        "tenant_group",
        "tenant",
        "location_id",
        "location",
        "rack_group_id",
        "rack_group",
        "rack_id",
        "role",
        "manufacturer",
        "platform",
        "device_status",
        "device_type",
        "device",
    ]
    q = django_forms.CharField(required=False, label="Search")


class GoldenConfigBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for GoldenConfig instances."""

    pk = django_forms.ModelMultipleChoiceField(
        queryset=models.GoldenConfig.objects.all(), widget=django_forms.MultipleHiddenInput
    )
    # description = django_forms.CharField(max_length=200, required=False)

    class Meta:
        """Boilerplate form Meta data for GoldenConfig."""

        nullable_fields = []


class ConfigComplianceFilterForm(DeviceRelatedFilterForm):
    """Filter Form for ConfigCompliance instances."""

    model = models.ConfigCompliance
    # Set field order to be explicit
    field_order = [
        "q",
        "tenant_group",
        "tenant",
        "location_id",
        "location",
        "rack_group_id",
        "rack_group",
        "rack_id",
        "role",
        "manufacturer",
        "platform",
        "device_status",
        "device_type",
        "device",
    ]

    q = django_forms.CharField(required=False, label="Search")

    def __init__(self, *args, **kwargs):
        """Required for status to work."""
        super().__init__(*args, **kwargs)
        self.fields["device_status"] = forms.DynamicModelMultipleChoiceField(
            required=False,
            queryset=Status.objects.all(),
            query_params={"content_types": Device._meta.label_lower},
            display_field="label",
            label="Device Status",
            to_field_name="name",
        )
        self.order_fields(self.field_order)  # Reorder fields again


# ComplianceRule


class ComplianceRuleForm(NautobotModelForm):
    """Filter Form for ComplianceRule instances."""

    platform = forms.DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for compliance rule."""

        model = models.ComplianceRule
        fields = "__all__"


class ComplianceRuleFilterForm(NautobotFilterForm):
    """Form for ComplianceRule instances."""

    model = models.ComplianceRule

    q = django_forms.CharField(required=False, label="Search")
    platform = forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="name", required=False, null_option="None"
    )

    feature = forms.DynamicModelMultipleChoiceField(queryset=models.ComplianceFeature.objects.all(), required=False)


class ComplianceRuleBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ComplianceRule instances."""

    pk = django_forms.ModelMultipleChoiceField(
        queryset=models.ComplianceRule.objects.all(), widget=django_forms.MultipleHiddenInput
    )
    description = django_forms.CharField(max_length=200, required=False)
    config_type = django_forms.ChoiceField(
        required=False,
        choices=forms.add_blank_choice(ComplianceRuleConfigTypeChoice),
    )
    config_ordered = django_forms.NullBooleanField(required=False, widget=forms.BulkEditNullBooleanSelect())
    custom_compliance = django_forms.NullBooleanField(required=False, widget=forms.BulkEditNullBooleanSelect())
    config_remediation = django_forms.NullBooleanField(required=False, widget=forms.BulkEditNullBooleanSelect())

    class Meta:
        """Boilerplate form Meta data for ComplianceRule."""

        nullable_fields = []


# ComplianceFeature


class ComplianceFeatureForm(NautobotModelForm):
    """Filter Form for ComplianceFeature instances."""

    slug = forms.SlugField()  # TODO: 2.1: Change from slugs once django-pivot is figured out

    class Meta:
        """Boilerplate form Meta data for compliance feature."""

        model = models.ComplianceFeature
        fields = "__all__"


class ComplianceFeatureFilterForm(NautobotFilterForm):
    """Form for ComplianceFeature instances."""

    model = models.ComplianceFeature
    q = django_forms.CharField(required=False, label="Search")
    name = forms.DynamicModelChoiceField(queryset=models.ComplianceFeature.objects.all(), required=False)


class ComplianceFeatureBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ComplianceFeature instances."""

    pk = django_forms.ModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(), widget=django_forms.MultipleHiddenInput
    )
    description = django_forms.CharField(max_length=200, required=False)

    class Meta:
        """Boilerplate form Meta data for ComplianceFeature."""

        nullable_fields = []


# ConfigRemove


class ConfigRemoveForm(NautobotModelForm):
    """Filter Form for Line Removal instances."""

    platform = forms.DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for removal feature."""

        model = models.ConfigRemove
        fields = "__all__"


class ConfigRemoveFilterForm(NautobotFilterForm):
    """Filter Form for Line Removal."""

    model = models.ConfigRemove
    platform = forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="name", required=False, null_option="None"
    )
    name = forms.DynamicModelChoiceField(
        queryset=models.ConfigRemove.objects.all(), to_field_name="name", required=False
    )


class ConfigRemoveBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ConfigRemove instances."""

    pk = django_forms.ModelMultipleChoiceField(
        queryset=models.ConfigRemove.objects.all(), widget=django_forms.MultipleHiddenInput
    )
    description = django_forms.CharField(max_length=200, required=False)

    class Meta:
        """Boilerplate form Meta data for ConfigRemove."""

        nullable_fields = []


# ConfigReplace


class ConfigReplaceForm(NautobotModelForm):
    """Filter Form for Line Removal instances."""

    platform = forms.DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for removal feature."""

        model = models.ConfigReplace
        fields = "__all__"


class ConfigReplaceFilterForm(NautobotFilterForm):
    """Filter Form for Line Replacement."""

    model = models.ConfigReplace

    platform = forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="name", required=False, null_option="None"
    )
    name = forms.DynamicModelChoiceField(
        queryset=models.ConfigReplace.objects.all(), to_field_name="name", required=False
    )


class ConfigReplaceBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ConfigReplace instances."""

    pk = django_forms.ModelMultipleChoiceField(
        queryset=models.ConfigReplace.objects.all(), widget=django_forms.MultipleHiddenInput
    )
    description = django_forms.CharField(max_length=200, required=False)

    class Meta:
        """Boilerplate form Meta data for ConfigReplace."""

        nullable_fields = []


# GoldenConfigSetting


class GoldenConfigSettingForm(NautobotModelForm):
    """Filter Form for GoldenConfigSettingForm instances."""

    slug = forms.SlugField()
    dynamic_group = django_forms.ModelChoiceField(queryset=DynamicGroup.objects.all())

    class Meta:
        """Filter Form Meta Data for GoldenConfigSettingForm instances."""

        model = models.GoldenConfigSetting
        fields = "__all__"


class GoldenConfigSettingFilterForm(NautobotFilterForm):
    """Form for GoldenConfigSetting instances."""

    model = models.GoldenConfigSetting

    q = django_forms.CharField(required=False, label="Search")
    name = django_forms.CharField(required=False)
    weight = django_forms.IntegerField(required=False)
    backup_repository = django_forms.ModelChoiceField(
        queryset=GitRepository.objects.filter(provided_contents__contains="nautobot_golden_config.backupconfigs"),
        required=False,
    )
    intended_repository = django_forms.ModelChoiceField(
        queryset=GitRepository.objects.filter(provided_contents__contains="nautobot_golden_config.intendedconfigs"),
        required=False,
    )
    jinja_repository = django_forms.ModelChoiceField(
        queryset=GitRepository.objects.filter(provided_contents__contains="nautobot_golden_config.jinjatemplate"),
        required=False,
    )


class GoldenConfigSettingBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for GoldenConfigSetting instances."""

    pk = django_forms.ModelMultipleChoiceField(
        queryset=models.GoldenConfigSetting.objects.all(), widget=django_forms.MultipleHiddenInput
    )

    class Meta:
        """Boilerplate form Meta data for GoldenConfigSetting."""

        nullable_fields = []


# Remediation Setting
class RemediationSettingForm(NautobotModelForm):
    """Create/Update Form for Remediation Settings instances."""

    class Meta:
        """Boilerplate form Meta data for Remediation Settings."""

        model = models.RemediationSetting
        fields = "__all__"


class RemediationSettingFilterForm(NautobotFilterForm):
    """Filter Form for Remediation Settings."""

    model = models.RemediationSetting
    q = django_forms.CharField(required=False, label="Search")
    platform = forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), required=False, display_field="name", to_field_name="name"
    )
    remediation_type = django_forms.ChoiceField(
        choices=forms.add_blank_choice(RemediationTypeChoice),
        required=False,
        widget=django_forms.Select(),
        label="Remediation Type",
    )


class RemediationSettingBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for RemediationSetting instances."""

    pk = django_forms.ModelMultipleChoiceField(
        queryset=models.RemediationSetting.objects.all(), widget=django_forms.MultipleHiddenInput
    )
    remediation_type = django_forms.ChoiceField(choices=RemediationTypeChoice, label="Remediation Type")

    class Meta:
        """Boilerplate form Meta data for RemediationSetting."""

        nullable_fields = []


# ConfigPlan


class ConfigPlanForm(NautobotModelForm):
    """Form for ConfigPlan instances."""

    feature = forms.DynamicModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(),
        display_field="name",
        help_text="Note: Selecting no features will generate plans for all applicable features.",
    )
    commands = django_forms.CharField(
        widget=django_forms.Textarea,
        help_text=(
            "Enter your configuration template here representing CLI configuration.<br>"
            'You may use Jinja2 templating. Example: <code>{% if "foo" in bar %}foo{% endif %}</code><br>'
            "You can also reference the device object with <code>obj</code>.<br>"
            "For example: <code>hostname {{ obj.name }}</code> or <code>ip address {{ obj.primary_ip4.host }}</code>"
        ),
    )

    tenant_group = forms.DynamicModelMultipleChoiceField(queryset=TenantGroup.objects.all(), required=False)
    tenant = forms.DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(), required=False, query_params={"tenant_group": "$tenant_group"}
    )
    # Requires https://github.com/nautobot/nautobot-app-golden-config/issues/430
    location = forms.DynamicModelMultipleChoiceField(queryset=Location.objects.all(), required=False)
    rack_group = forms.DynamicModelMultipleChoiceField(
        queryset=RackGroup.objects.all(), required=False, query_params={"location": "$location"}
    )
    rack = forms.DynamicModelMultipleChoiceField(
        queryset=Rack.objects.all(), required=False, query_params={"rack_group": "$rack_group", "location": "$location"}
    )
    role = forms.DynamicModelMultipleChoiceField(
        queryset=Role.objects.all(), required=False, query_params={"content_types": "dcim.device"}
    )
    manufacturer = forms.DynamicModelMultipleChoiceField(queryset=Manufacturer.objects.all(), required=False)
    platform = forms.DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), required=False)
    device_type = forms.DynamicModelMultipleChoiceField(queryset=DeviceType.objects.all(), required=False)
    device = forms.DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False)
    tags = forms.DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(), query_params={"content_types": "dcim.device"}, required=False
    )
    status = forms.DynamicModelMultipleChoiceField(
        queryset=Status.objects.all(), query_params={"content_types": "dcim.device"}, required=False
    )

    def __init__(self, *args, **kwargs):
        """Method to get data from Python -> Django template -> JS  in support of toggle form fields."""
        super().__init__(*args, **kwargs)
        hide_form_data = [
            {
                "event_field": "id_plan_type",
                "values": [
                    {"name": "manual", "show": ["id_commands"], "hide": ["id_feature"]},
                    {"name": "missing", "show": ["id_feature"], "hide": ["id_commands"]},
                    {"name": "intended", "show": ["id_feature"], "hide": ["id_commands"]},
                    {"name": "remediation", "show": ["id_feature"], "hide": ["id_commands"]},
                    {"name": "", "show": [], "hide": ["id_commands", "id_feature"]},
                ],
            }
        ]
        # Example of how to use this `JSON.parse('{{ form.hide_form_data|safe }}')`
        self.hide_form_data = json.dumps(hide_form_data)

    class Meta:
        """Boilerplate form Meta data for ConfigPlan."""

        model = models.ConfigPlan
        fields = "__all__"


class ConfigPlanUpdateForm(NautobotModelForm):  # pylint: disable=nb-sub-class-name
    """Form for ConfigPlan instances."""

    status = forms.DynamicModelChoiceField(
        queryset=Status.objects.all(),
        query_params={"content_types": models.ConfigPlan._meta.label_lower},
    )
    tags = forms.DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(), query_params={"content_types": "dcim.device"}, required=False
    )

    class Meta:
        """Boilerplate form Meta data for ConfigPlan."""

        model = models.ConfigPlan
        fields = (  # pylint: disable=nb-use-fields-all
            "change_control_id",
            "change_control_url",
            "status",
            "tags",
        )


class ConfigPlanFilterForm(DeviceRelatedFilterForm):
    """Filter Form for ConfigPlan."""

    model = models.ConfigPlan

    q = django_forms.CharField(required=False, label="Search")
    # device_id = forms.DynamicModelMultipleChoiceField(
    #     queryset=Device.objects.all(), required=False, null_option="None", label="Device"
    # )
    created__lte = django_forms.DateTimeField(label="Created Before", required=False, widget=forms.DatePicker())
    created__gte = django_forms.DateTimeField(label="Created After", required=False, widget=forms.DatePicker())
    plan_type = django_forms.ChoiceField(
        choices=forms.add_blank_choice(ConfigPlanTypeChoice),
        required=False,
        widget=django_forms.Select(),
        label="Plan Type",
    )
    feature = forms.DynamicModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(),
        required=False,
        null_option="None",
        label="Feature",
        to_field_name="name",
    )
    change_control_id = django_forms.CharField(required=False, label="Change Control ID")
    plan_result_id = forms.DynamicModelMultipleChoiceField(
        queryset=JobResult.objects.all(),
        query_params={"job_model": "Generate Config Plans"},
        label="Plan Result",
        required=False,
        display_field="date_created",
    )
    deploy_result_id = forms.DynamicModelMultipleChoiceField(
        queryset=JobResult.objects.all(),
        query_params={"job_model": "Deploy Config Plans"},
        label="Deploy Result",
        required=False,
        display_field="date_created",
    )
    status = forms.DynamicModelMultipleChoiceField(
        required=False,
        queryset=Status.objects.all(),
        query_params={"content_types": models.ConfigPlan._meta.label_lower},
        display_field="label",
        label="Status",
        to_field_name="name",
    )
    tags = forms.TagFilterField(model)


class ConfigPlanBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ConfigPlan instances."""

    pk = django_forms.ModelMultipleChoiceField(
        queryset=models.ConfigPlan.objects.all(), widget=django_forms.MultipleHiddenInput
    )
    status = forms.DynamicModelChoiceField(
        queryset=Status.objects.all(),
        query_params={"content_types": models.ConfigPlan._meta.label_lower},
        required=False,
    )
    change_control_id = django_forms.CharField(required=False, label="Change Control ID")
    change_control_url = django_forms.URLField(required=False, label="Change Control URL")

    class Meta:
        """Boilerplate form Meta data for ConfigPlan."""

        nullable_fields = [
            "change_control_id",
            "change_control_url",
            "tags",
        ]


class GenerateIntendedConfigForm(django_forms.Form):
    """Form for generating intended configuration."""

    device = forms.DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        label="Device",
    )
    graphql_query = forms.DynamicModelChoiceField(
        queryset=GraphQLQuery.objects.all(),
        required=True,
        label="GraphQL Query",
        query_params={"nautobot_golden_config_graphql_query_variables": "device_id"},
    )
    git_repository_branch = django_forms.ChoiceField(widget=forms.StaticSelect2)

    def __init__(self, *args, **kwargs):
        """Conditionally hide the git_repository_branch field based on Nautobot version."""
        super().__init__(*args, **kwargs)
        if version.parse(settings.VERSION) < version.parse("2.4.2"):
            self.fields["git_repository_branch"].widget = django_forms.HiddenInput
