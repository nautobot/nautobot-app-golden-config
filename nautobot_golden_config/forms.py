"""Forms for Device Configuration Backup."""
# pylint: disable=too-many-ancestors

from django import forms

import nautobot.core.forms as core_forms
from nautobot.dcim.models import Device, Platform, Location, DeviceType, Manufacturer, Rack, RackGroup
from nautobot.extras.forms import NautobotFilterForm, NautobotBulkEditForm, NautobotModelForm
from nautobot.extras.models import Status, GitRepository, DynamicGroup, Role
from nautobot.tenancy.models import Tenant, TenantGroup

from nautobot_golden_config import models

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
