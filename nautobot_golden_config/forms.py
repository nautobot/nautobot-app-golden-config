"""Forms for Device Configuration Backup."""

from django import forms

import nautobot.extras.forms as extras_forms
import nautobot.utilities.forms as utilities_forms
from nautobot.dcim.models import Device, Platform, Region, Site, DeviceRole, DeviceType, Manufacturer, Rack, RackGroup
from nautobot.extras.models import Status
from nautobot.tenancy.models import Tenant, TenantGroup

from nautobot_golden_config import models


class GoldenConfigFilterForm(utilities_forms.BootstrapMixin, extras_forms.CustomFieldFilterForm):
    """Filter Form for GoldenConfig instances."""

    model = Device

    class Meta:
        """Meta definitions of searchable fields."""

    field_order = [
        "q",
        "tenant_group",
        "tenant",
        "region",
        "site",
        "rack_group_id",
        "rack_id",
        "role",
        "manufacturer",
        "platform",
        "device_status_id",
        "device_type_id",
        "device",
    ]
    q = forms.CharField(required=False, label="Search")
    tenant_group = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(), to_field_name="slug", required=False, null_option="None"
    )
    tenant = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        to_field_name="slug",
        required=False,
        null_option="None",
        query_params={"group": "$tenant_group"},
    )
    region = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(), to_field_name="slug", required=False
    )
    site = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(), to_field_name="slug", required=False, query_params={"region": "$region"}
    )
    rack_group_id = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=RackGroup.objects.all(), required=False, label="Rack group", query_params={"site": "$site"}
    )
    rack_id = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        label="Rack",
        null_option="None",
        query_params={
            "site": "$site",
            "group_id": "$rack_group_id",
        },
    )
    role = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=DeviceRole.objects.all(), to_field_name="slug", required=False
    )
    manufacturer = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Manufacturer.objects.all(), to_field_name="slug", required=False, label="Manufacturer"
    )
    device_type_id = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        label="Model",
        display_field="model",
        query_params={"manufacturer": "$manufacturer"},
    )
    platform = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="slug", required=False, null_option="None"
    )
    device = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, null_option="None", label="Device"
    )

    def __init__(self, *args, **kwargs):
        """Required for status to work."""
        super().__init__(*args, **kwargs)
        self.fields["device_status_id"] = utilities_forms.DynamicModelMultipleChoiceField(
            required=False,
            queryset=Status.objects.all(),
            query_params={"content_types": Device._meta.label_lower},
            display_field="label",
            label="Device Status",
            to_field_name="name",
        )
        self.order_fields(self.field_order)  # Reorder fields again


# ConfigCompliance


class ConfigComplianceFilterForm(GoldenConfigFilterForm):
    """Filter Form for ConfigCompliance instances."""

    model = models.ConfigCompliance


# ComplianceRule


class ComplianceRuleForm(
    utilities_forms.BootstrapMixin, extras_forms.CustomFieldModelForm, extras_forms.RelationshipModelForm
):
    """Filter Form for ComplianceRule instances."""

    platform = utilities_forms.DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for compliance rule."""

        model = models.ComplianceRule
        fields = (
            "platform",
            "feature",
            "description",
            "config_ordered",
            "match_config",
            "config_type",
        )


class ComplianceRuleFilterForm(utilities_forms.BootstrapMixin, extras_forms.CustomFieldFilterForm):
    """Form for ComplianceRule instances."""

    model = models.ComplianceRule
    platform = utilities_forms.DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), required=False)
    feature = utilities_forms.DynamicModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(), required=False
    )


class ComplianceRuleBulkEditForm(
    utilities_forms.BootstrapMixin, extras_forms.AddRemoveTagsForm, extras_forms.CustomFieldBulkEditForm
):
    """BulkEdit form for ComplianceRule instances."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ComplianceRule.objects.all(), widget=forms.MultipleHiddenInput)

    class Meta:
        """Boilerplate form Meta data for ComplianceRule."""

        nullable_fields = []


class ComplianceRuleCSVForm(extras_forms.CustomFieldModelCSVForm):
    """CSV Form for ComplianceRule instances."""

    class Meta:
        """Boilerplate form Meta data for ComplianceRule."""

        model = models.ComplianceRule
        fields = models.ComplianceRule.csv_headers


# ComplianceFeature


class ComplianceFeatureForm(
    utilities_forms.BootstrapMixin, extras_forms.CustomFieldModelForm, extras_forms.RelationshipModelForm
):
    """Filter Form for ComplianceFeature instances."""

    class Meta:
        """Boilerplate form Meta data for compliance feature."""

        model = models.ComplianceFeature
        fields = ("name", "slug", "description")


class ComplianceFeatureFilterForm(utilities_forms.BootstrapMixin, extras_forms.CustomFieldFilterForm):
    """Form for ComplianceFeature instances."""

    model = models.ComplianceFeature

    name = utilities_forms.DynamicModelChoiceField(queryset=models.ComplianceFeature.objects.all(), required=False)


class ComplianceFeatureBulkEditForm(
    utilities_forms.BootstrapMixin, extras_forms.AddRemoveTagsForm, extras_forms.CustomFieldBulkEditForm
):
    """BulkEdit form for ComplianceFeature instances."""

    pk = forms.ModelMultipleChoiceField(
        queryset=models.ComplianceFeature.objects.all(), widget=forms.MultipleHiddenInput
    )

    class Meta:
        """Boilerplate form Meta data for ComplianceFeature."""

        nullable_fields = []


class ComplianceFeatureCSVForm(extras_forms.CustomFieldModelCSVForm):
    """CSV Form for ComplianceFeature instances."""

    class Meta:
        """Boilerplate form Meta data for ComplianceFeature."""

        model = models.ComplianceFeature
        fields = models.ComplianceFeature.csv_headers


# ConfigRemove


class ConfigRemoveForm(
    utilities_forms.BootstrapMixin, extras_forms.CustomFieldModelForm, extras_forms.RelationshipModelForm
):
    """Filter Form for Line Removal instances."""

    platform = utilities_forms.DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for removal feature."""

        model = models.ConfigRemove
        fields = (
            "platform",
            "name",
            "description",
            "regex",
        )


class ConfigRemoveFeatureFilterForm(utilities_forms.BootstrapMixin, extras_forms.CustomFieldFilterForm):
    """Filter Form for Line Removal."""

    model = models.ConfigRemove

    platform = utilities_forms.DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), required=False)
    name = utilities_forms.DynamicModelChoiceField(queryset=models.ConfigRemove.objects.all(), required=False)


class ConfigRemoveBulkEditForm(
    utilities_forms.BootstrapMixin, extras_forms.AddRemoveTagsForm, extras_forms.CustomFieldBulkEditForm
):
    """BulkEdit form for ConfigRemove instances."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ConfigRemove.objects.all(), widget=forms.MultipleHiddenInput)

    class Meta:
        """Boilerplate form Meta data for ConfigRemove."""

        nullable_fields = []


class ConfigRemoveCSVForm(extras_forms.CustomFieldModelCSVForm):
    """CSV Form for ConfigRemove instances."""

    class Meta:
        """Boilerplate form Meta data for ConfigRemove."""

        model = models.ConfigRemove
        fields = models.ConfigRemove.csv_headers


# ConfigReplace


class ConfigReplaceForm(
    utilities_forms.BootstrapMixin, extras_forms.CustomFieldModelForm, extras_forms.RelationshipModelForm
):
    """Filter Form for Line Removal instances."""

    platform = utilities_forms.DynamicModelChoiceField(queryset=Platform.objects.all())

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


class ConfigReplaceFeatureFilterForm(utilities_forms.BootstrapMixin, extras_forms.CustomFieldFilterForm):
    """Filter Form for Line Replacement."""

    model = models.ConfigReplace

    platform = utilities_forms.DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), required=False)
    name = utilities_forms.DynamicModelChoiceField(queryset=models.ConfigReplace.objects.all(), required=False)


class ConfigReplaceCSVForm(extras_forms.CustomFieldModelCSVForm):
    """CSV Form for ConfigRemove instances."""

    class Meta:
        """Boilerplate form Meta data for ConfigRemove."""

        model = models.ConfigReplace
        fields = models.ConfigReplace.csv_headers


class ConfigReplaceBulkEditForm(
    utilities_forms.BootstrapMixin, extras_forms.AddRemoveTagsForm, extras_forms.CustomFieldBulkEditForm
):
    """BulkEdit form for ConfigReplace instances."""

    pk = forms.ModelMultipleChoiceField(queryset=models.ConfigReplace.objects.all(), widget=forms.MultipleHiddenInput)

    class Meta:
        """Boilerplate form Meta data for ConfigReplace."""

        nullable_fields = []


# GoldenConfigSetting


class GoldenConfigSettingFeatureForm(
    utilities_forms.BootstrapMixin, extras_forms.CustomFieldModelForm, extras_forms.RelationshipModelForm
):
    """Filter Form for GoldenConfigSettingFeatureForm instances."""

    class Meta:
        """Filter Form Meta Data for GoldenConfigSettingFeatureForm instances."""

        model = models.GoldenConfigSetting
        fields = (
            "backup_repository",
            "backup_path_template",
            "intended_repository",
            "intended_path_template",
            "jinja_repository",
            "jinja_path_template",
            "backup_test_connectivity",
            "scope",
            "sot_agg_query",
        )
