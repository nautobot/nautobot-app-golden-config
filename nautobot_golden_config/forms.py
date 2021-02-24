"""Forms for Device Configuration Backup."""

from django import forms
from django.db.models import Subquery

from nautobot.dcim.models import Device, Platform, Region, Site, DeviceRole, DeviceType, Manufacturer, Rack, RackGroup
from nautobot.extras.models import Status
from nautobot.extras.forms import CustomFieldFilterForm
from nautobot.tenancy.models import Tenant, TenantGroup
from nautobot.utilities.forms import BootstrapMixin, DynamicModelMultipleChoiceField, DynamicModelChoiceField

from .models import ConfigCompliance, ComplianceFeature, GoldenConfigSettings, GoldenConfiguration


class GoldenConfigurationFilterForm(BootstrapMixin, CustomFieldFilterForm):
    """Filter Form for GoldenConfiguration instances."""

    model = GoldenConfiguration

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
    tenant_group = DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(), to_field_name="slug", required=False, null_option="None"
    )
    tenant = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        to_field_name="slug",
        required=False,
        null_option="None",
        query_params={"group": "$tenant_group"},
    )
    region = DynamicModelMultipleChoiceField(queryset=Region.objects.all(), to_field_name="slug", required=False)
    site = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(), to_field_name="slug", required=False, query_params={"region": "$region"}
    )
    rack_group_id = DynamicModelMultipleChoiceField(
        queryset=RackGroup.objects.all(), required=False, label="Rack group", query_params={"site": "$site"}
    )
    rack_id = DynamicModelMultipleChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        label="Rack",
        null_option="None",
        query_params={
            "site": "$site",
            "group_id": "$rack_group_id",
        },
    )
    role = DynamicModelMultipleChoiceField(queryset=DeviceRole.objects.all(), to_field_name="slug", required=False)
    manufacturer = DynamicModelMultipleChoiceField(
        queryset=Manufacturer.objects.all(), to_field_name="slug", required=False, label="Manufacturer"
    )
    device_type_id = DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        label="Model",
        display_field="model",
        query_params={"manufacturer": "$manufacturer"},
    )
    platform = DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(), to_field_name="slug", required=False, null_option="None"
    )
    device = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, null_option="None", label="Device"
    )

    def __init__(self, *args, **kwargs):
        """Required for status to work."""
        super().__init__(*args, **kwargs)
        self.fields["device_status_id"] = DynamicModelMultipleChoiceField(
            required=False,
            queryset=Status.objects.all(),
            query_params={"content_types": Device._meta.label_lower},
            display_field="label",
            label="Device Status",
            to_field_name="name",
        )
        self.order_fields(self.field_order)  # Reorder fields again


class ConfigComplianceFilterForm(GoldenConfigurationFilterForm):
    """Filter Form for ConfigCompliance instances."""

    model = ConfigCompliance
    device = DynamicModelMultipleChoiceField(
        queryset=Device.objects.filter(id__in=Subquery(ConfigCompliance.objects.distinct("device").values("device"))),
        to_field_name="name",
        required=False,
        null_option="None",
    )


class ComplianceFeatureFilterForm(BootstrapMixin, forms.Form):
    """Form for ComplianceFeature instances."""

    model = ComplianceFeature
    platform = DynamicModelChoiceField(queryset=Platform.objects.all(), required=False)
    name = forms.CharField(required=False)


class ComplianceFeatureForm(BootstrapMixin, forms.ModelForm):
    """Filter Form for ComplianceFeature instances."""

    platform = DynamicModelChoiceField(queryset=Platform.objects.all())

    class Meta:
        """Boilerplate form Meta data for compliance feature."""

        model = ComplianceFeature
        fields = (
            "platform",
            "name",
            "description",
            "config_ordered",
            "match_config",
        )


class GoldenConfigSettingsFeatureForm(BootstrapMixin, forms.ModelForm):
    """Filter Form for GoldenConfigSettingsFeatureForm instances."""

    class Meta:
        """Filter Form Meta Data for GoldenConfigSettingsFeatureForm instances."""

        model = GoldenConfigSettings
        fields = (
            "backup_path_template",
            "intended_path_template",
            "jinja_path_template",
            "backup_test_connectivity",
            "shorten_sot_query",
            "sot_agg_query",
            "remove_lines",
            "substitute_lines",
        )
