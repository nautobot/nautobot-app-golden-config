"""Forms for Device Configuration Backup."""
# pylint: disable=too-many-ancestors

import json

from django import forms

import nautobot.core.forms as core_forms
from nautobot.dcim.models import Device, Platform, Location, DeviceType, Manufacturer, Rack, RackGroup
from nautobot.extras.forms import NautobotFilterForm, NautobotBulkEditForm, NautobotModelForm
from nautobot.extras.models import Status, GitRepository, DynamicGroup, Role
from nautobot.tenancy.models import Tenant, TenantGroup
import nautobot.utilities.forms as utilities_forms

from nautobot_golden_config import models
from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice, ConfigPlanTypeChoice, RemediationTypeChoice

# ConfigCompliance


class ConfigComplianceFilterForm(NautobotFilterForm):
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
        "device_type_id",
        "device_id",
    ]

    q = forms.CharField(required=False, label="Search")
    tenant_group_id = core_forms.DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(), to_field_name="id", required=False, label="Tenant group ID"
    )
    tenant_group = core_forms.DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        to_field_name="name",
        required=False,
        label="Tenant group name",
        null_option="None",
    )
    tenant = core_forms.DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        to_field_name="name",
        required=False,
        null_option="None",
        query_params={"group": "$tenant_group"},
    )
    location_id = core_forms.DynamicModelMultipleChoiceField(
        # Not limiting to query_params={"content_type": "dcim.device" to allow parent locations to be included
        # i.e. include all sites in a Region, even though Region can't be assigned to a Device
        queryset=Location.objects.all(),
        to_field_name="id",
        required=False,
        label="Location ID",
    )
    location = core_forms.DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(), to_field_name="name", required=False, label="Location name"
    )
    rack_group_id = core_forms.DynamicModelMultipleChoiceField(
        queryset=RackGroup.objects.all(),
        to_field_name="id",
        required=False,
        label="Rack group ID",
        query_params={"location": "$location"},
    )
    rack_group = core_forms.DynamicModelMultipleChoiceField(
        queryset=RackGroup.objects.all(),
        to_field_name="name",
        required=False,
        label="Rack group name",
        query_params={"location": "$location"},
    )
    rack_id = core_forms.DynamicModelMultipleChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        label="Rack",
        null_option="None",
        query_params={
            "location": "$location",
            "group_id": "$rack_group_id",
        },
    )
    role = core_forms.DynamicModelMultipleChoiceField(
        queryset=Role.objects.all(),
        to_field_name="name",
        required=False,  # TODO: Test with change to Role model
    )
    manufacturer = core_forms.DynamicModelMultipleChoiceField(
        queryset=Manufacturer.objects.all(), to_field_name="name", required=False, label="Manufacturer"
    )
    device_type_id = core_forms.DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        label="Model",
        display_field="model",
        query_params={"manufacturer": "$manufacturer"},
    )

    platform = core_forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="name", required=False, null_option="None"
    )
    device_id = core_forms.DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, null_option="None", label="Device"
    )

    def __init__(self, *args, **kwargs):
        """Required for status to work."""
        super().__init__(*args, **kwargs)
        self.fields["device_status"] = core_forms.DynamicModelMultipleChoiceField(
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

    platform = core_forms.DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for compliance rule."""

        model = models.ComplianceRule
        fields = (
            "platform",
            "feature",
            "description",
            "config_ordered",
            "config_type",
            "match_config",
            "custom_compliance",
            "config_remediation",
        )


class ComplianceRuleFilterForm(NautobotFilterForm):
    """Form for ComplianceRule instances."""

    model = models.ComplianceRule

    q = forms.CharField(required=False, label="Search")
    platform = core_forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="name", required=False, null_option="None"
    )

    feature = core_forms.DynamicModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(), required=False
    )


class ComplianceRuleBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ComplianceRule instances."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ComplianceRule.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(max_length=200, required=False)
    config_type = forms.ChoiceField(
        required=False,
        choices=utilities_forms.add_blank_choice(ComplianceRuleConfigTypeChoice),
    )
    config_ordered = forms.NullBooleanField(required=False, widget=utilities_forms.BulkEditNullBooleanSelect())
    custom_compliance = forms.NullBooleanField(required=False, widget=utilities_forms.BulkEditNullBooleanSelect())
    config_remediation = forms.NullBooleanField(required=False, widget=utilities_forms.BulkEditNullBooleanSelect())

    class Meta:
        """Boilerplate form Meta data for ComplianceRule."""

        nullable_fields = []


# ComplianceFeature


class ComplianceFeatureForm(NautobotModelForm):
    """Filter Form for ComplianceFeature instances."""

    slug = core_forms.fields.SlugField()  # TODO: Remove slugs

    class Meta:
        """Boilerplate form Meta data for compliance feature."""

        model = models.ComplianceFeature
        fields = ("name", "slug", "description")


class ComplianceFeatureFilterForm(NautobotFilterForm):
    """Form for ComplianceFeature instances."""

    model = models.ComplianceFeature
    q = forms.CharField(required=False, label="Search")
    name = core_forms.DynamicModelChoiceField(queryset=models.ComplianceFeature.objects.all(), required=False)


class ComplianceFeatureBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ComplianceFeature instances."""

    pk = forms.ModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(), widget=forms.MultipleHiddenInput
    )
    description = forms.CharField(max_length=200, required=False)

    class Meta:
        """Boilerplate form Meta data for ComplianceFeature."""

        nullable_fields = []


# ConfigRemove


class ConfigRemoveForm(NautobotModelForm):
    """Filter Form for Line Removal instances."""

    platform = core_forms.DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for removal feature."""

        model = models.ConfigRemove
        fields = (
            "platform",
            "name",
            "description",
            "regex",
        )


class ConfigRemoveFilterForm(NautobotFilterForm):
    """Filter Form for Line Removal."""

    model = models.ConfigRemove
    platform = core_forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="name", required=False, null_option="None"
    )
    name = core_forms.DynamicModelChoiceField(
        queryset=models.ConfigRemove.objects.all(), to_field_name="name", required=False
    )


class ConfigRemoveBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ConfigRemove instances."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ConfigRemove.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(max_length=200, required=False)

    class Meta:
        """Boilerplate form Meta data for ConfigRemove."""

        nullable_fields = []


# ConfigReplace


class ConfigReplaceForm(NautobotModelForm):
    """Filter Form for Line Removal instances."""

    platform = core_forms.DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for removal feature."""

        model = models.ConfigReplace
        fields = (
            "platform",
            "name",
            "description",
            "regex",
            "replace",
        )


class ConfigReplaceFilterForm(NautobotFilterForm):
    """Filter Form for Line Replacement."""

    model = models.ConfigReplace

    platform = core_forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="name", required=False, null_option="None"
    )
    name = core_forms.DynamicModelChoiceField(
        queryset=models.ConfigReplace.objects.all(), to_field_name="name", required=False
    )


class ConfigReplaceBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for ConfigReplace instances."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ConfigReplace.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(max_length=200, required=False)

    class Meta:
        """Boilerplate form Meta data for ConfigReplace."""

        nullable_fields = []


# GoldenConfigSetting


class GoldenConfigSettingForm(NautobotModelForm):
    """Filter Form for GoldenConfigSettingForm instances."""

    slug = core_forms.fields.SlugField()  # TODO: Remove slugs
    dynamic_group = core_forms.DynamicModelChoiceField(queryset=DynamicGroup.objects.all(), required=False)

    class Meta:
        """Filter Form Meta Data for GoldenConfigSettingForm instances."""

        model = models.GoldenConfigSetting
        fields = (
            "name",
            "slug",
            "weight",
            "description",
            "backup_repository",
            "backup_path_template",
            "intended_repository",
            "intended_path_template",
            "jinja_repository",
            "jinja_path_template",
            "backup_test_connectivity",
            "dynamic_group",
            "sot_agg_query",
            "tags",
        )


class GoldenConfigSettingFilterForm(NautobotFilterForm):
    """Form for GoldenConfigSetting instances."""

    model = models.GoldenConfigSetting

    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False)
    weight = forms.IntegerField(required=False)
    backup_repository = forms.ModelChoiceField(
        queryset=GitRepository.objects.filter(provided_contents__contains="nautobot_golden_config.backupconfigs"),
        required=False,
    )
    intended_repository = forms.ModelChoiceField(
        queryset=GitRepository.objects.filter(provided_contents__contains="nautobot_golden_config.intendedconfigs"),
        required=False,
    )
    jinja_repository = forms.ModelChoiceField(
        queryset=GitRepository.objects.filter(provided_contents__contains="nautobot_golden_config.jinjatemplate"),
        required=False,
    )


class GoldenConfigSettingBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for GoldenConfigSetting instances."""

    pk = forms.ModelMultipleChoiceField(
        queryset=models.GoldenConfigSetting.objects.all(), widget=forms.MultipleHiddenInput
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
        fields = (
            "platform",
            "remediation_type",
            "remediation_options",
        )


class RemediationSettingFilterForm(NautobotFilterForm):
    """Filter Form for Remediation Settings."""

    model = models.RemediationSetting
    q = forms.CharField(required=False, label="Search")
    platform = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), required=False, display_field="name", to_field_name="name"
    )
    remediation_type = forms.ChoiceField(
        choices=add_blank_choice(RemediationTypeChoice), required=False, label="Remediation Type"
    )


class RemediationSettingCSVForm(extras_forms.CustomFieldModelCSVForm):
    """CSV Form for RemediationSetting instances."""

    class Meta:
        """Boilerplate form Meta data for RemediationSetting."""

        model = models.RemediationSetting
        fields = models.RemediationSetting.csv_headers


class RemediationSettingBulkEditForm(NautobotBulkEditForm):
    """BulkEdit form for RemediationSetting instances."""

    pk = forms.ModelMultipleChoiceField(
        queryset=models.RemediationSetting.objects.all(), widget=forms.MultipleHiddenInput
    )
    remediation_type = forms.ChoiceField(choices=RemediationTypeChoice, label="Remediation Type")

    class Meta:
        """Boilerplate form Meta data for RemediationSetting."""

        nullable_fields = []


# ConfigPlan


class ConfigPlanForm(NautobotModelForm):
    """Form for ConfigPlan instances."""

    plan_type = forms.ChoiceField(choices=add_blank_choice(ConfigPlanTypeChoice), required=True, label="Plan Type")
    change_control_id = forms.CharField(required=False, label="Change Control ID")
    change_control_url = forms.URLField(required=False, label="Change Control URL")

    feature = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(),
        display_field="name",
        required=False,
        help_text="Note: Selecting no features will generate plans for all applicable features.",
    )
    commands = forms.CharField(
        widget=forms.Textarea,
        help_text=(
            "Enter your configuration template here representing CLI configuration.<br>"
            'You may use Jinja2 templating. Example: <code>{% if "foo" in bar %}foo{% endif %}</code><br>'
            "You can also reference the device object with <code>obj</code>.<br>"
            "For example: <code>hostname {{ obj.name }}</code> or <code>ip address {{ obj.primary_ip4.host }}</code>"
        ),
        required=True,
    )

    tenant_group = utilities_forms.DynamicModelMultipleChoiceField(queryset=TenantGroup.objects.all(), required=False)
    tenant = utilities_forms.DynamicModelMultipleChoiceField(queryset=Tenant.objects.all(), required=False)
    # Requires https://github.com/nautobot/nautobot-plugin-golden-config/issues/430
    # location = utilities_forms.DynamicModelMultipleChoiceField(queryset=Location.objects.all(), required=False)
    region = utilities_forms.DynamicModelMultipleChoiceField(queryset=Region.objects.all(), required=False)
    site = utilities_forms.DynamicModelMultipleChoiceField(queryset=Site.objects.all(), required=False)
    rack_group = utilities_forms.DynamicModelMultipleChoiceField(queryset=RackGroup.objects.all(), required=False)
    rack = utilities_forms.DynamicModelMultipleChoiceField(queryset=Rack.objects.all(), required=False)
    role = utilities_forms.DynamicModelMultipleChoiceField(queryset=DeviceRole.objects.all(), required=False)
    manufacturer = utilities_forms.DynamicModelMultipleChoiceField(queryset=Manufacturer.objects.all(), required=False)
    platform = utilities_forms.DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), required=False)
    device_type = utilities_forms.DynamicModelMultipleChoiceField(queryset=DeviceType.objects.all(), required=False)
    device = utilities_forms.DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False)
    tag = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(), query_params={"content_types": "dcim.device"}, required=False
    )
    status = utilities_forms.DynamicModelMultipleChoiceField(
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
        fields = (
            "plan_type",
            "change_control_id",
            "feature",
            "commands",
            "tenant",
            # "location", Requires https://github.com/nautobot/nautobot-plugin-golden-config/issues/430
            "region",
            "site",
            "rack_group",
            "rack",
            "role",
            "manufacturer",
            "platform",
            "device_type",
            "device",
            "tag",
            "status",
        )


class ConfigPlanUpdateForm(NautobotModelForm):
    """Form for ConfigPlan instances."""

    change_control_id = forms.CharField(required=False, label="Change Control ID")
    change_control_url = forms.URLField(required=False, label="Change Control URL")
    status = utilities_forms.DynamicModelChoiceField(
        queryset=Status.objects.all(),
        query_params={"content_types": models.ConfigPlan._meta.label_lower},
        required=False,
    )
    tag = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(), query_params={"content_types": "dcim.device"}, required=False
    )

    class Meta:
        """Boilerplate form Meta data for ConfigPlan."""

        model = models.ConfigPlan
        fields = (
            "change_control_id",
            "change_control_url",
            "tag",
            "status",
        )


class ConfigPlanFilterForm(NautobotFilterForm):
    """Filter Form for ConfigPlan."""

    model = models.ConfigPlan

    q = forms.CharField(required=False, label="Search")
    device_id = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, null_option="None", label="Device"
    )
    created__lte = forms.DateTimeField(label="Created Before", required=False, widget=utilities_forms.DatePicker())
    created__gte = forms.DateTimeField(label="Created After", required=False, widget=utilities_forms.DatePicker())
    plan_type = forms.ChoiceField(
        choices=utilities_forms.add_blank_choice(ConfigPlanTypeChoice), required=False, widget=forms.Select(), label="Plan Type"
    )
    feature = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(),
        required=False,
        null_option="None",
        label="Feature",
        to_field_name="name",
    )
    change_control_id = forms.CharField(required=False, label="Change Control ID")
    job_result_id = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=JobResult.objects.all(),
        query_params={"nautobot_golden_config_config_plan_null": True},
        label="Job Result",
        required=False,
        display_field="id",
    )
    status = utilities_forms.DynamicModelMultipleChoiceField(
        required=False,
        queryset=Status.objects.all(),
        query_params={"content_types": models.ConfigPlan._meta.label_lower},
        display_field="label",
        label="Status",
        to_field_name="name",
    )
    tag = utilities_forms.TagFilterField(model)


class ConfigPlanBulkEditForm(core_forms.TagsBulkEditFormMixin, NautobotBulkEditForm):
    """BulkEdit form for ConfigPlan instances."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ConfigPlan.objects.all(), widget=forms.MultipleHiddenInput)
    status = utilities_forms.DynamicModelChoiceField(
        queryset=Status.objects.all(),
        query_params={"content_types": models.ConfigPlan._meta.label_lower},
        required=False,
    )
    change_control_id = forms.CharField(required=False, label="Change Control ID")
    change_control_url = forms.URLField(required=False, label="Change Control URL")

    class Meta:
        """Boilerplate form Meta data for ConfigPlan."""

        nullable_fields = [
            "change_control_id",
            "change_control_url",
            "tags",
        ]
