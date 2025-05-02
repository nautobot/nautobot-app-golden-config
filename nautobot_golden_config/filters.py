"""Filtering for nautobot_golden_config."""

import django_filters
from nautobot.apps.filters import (
    MultiValueDateTimeFilter,
    NaturalKeyOrPKMultipleChoiceFilter,
    NautobotFilterSet,
    SearchFilter,
    StatusFilter,
    TreeNodeMultipleChoiceFilter,
)
from nautobot.dcim.models import Device, DeviceType, Location, Manufacturer, Platform, Rack, RackGroup
from nautobot.extras.models import JobResult, Role, Status
from nautobot.tenancy.models import Tenant, TenantGroup

from nautobot_golden_config import models


class GoldenConfigFilterSet(NautobotFilterSet):
    """Filter capabilities for GoldenConfig instances."""

    @staticmethod
    def _get_filter_lookup_dict(existing_filter):
        """Extend method to account for isnull on datetime types."""
        # Choose the lookup expression map based on the filter type
        lookup_map = NautobotFilterSet._get_filter_lookup_dict(existing_filter)
        if isinstance(existing_filter, MultiValueDateTimeFilter):
            lookup_map.update({"isnull": "isnull"})
        return lookup_map

    q = SearchFilter(
        filter_predicates={
            "device__name": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
        },
    )
    tenant_group_id = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="device__tenant__tenant_group",
        to_field_name="id",
        label="Tenant Group (ID)",
    )
    tenant_group = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="device__tenant__tenant_group",
        to_field_name="name",
        label="Tenant Group (name)",
    )
    tenant = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="device__tenant",
        to_field_name="name",
        label="Tenant (name or ID)",
    )
    location_id = TreeNodeMultipleChoiceFilter(
        # Not limiting to content_type=dcim.device to allow parent locations to be included
        # i.e. include all Sites in a Region, even though Region can't be assigned to a Device
        queryset=Location.objects.all(),
        field_name="device__location",
        to_field_name="id",
        label="Location (ID)",
    )
    location = TreeNodeMultipleChoiceFilter(
        # Not limiting to content_type=dcim.device to allow parent locations to be included
        # i.e. include all sites in a Region, even though Region can't be assigned to a Device
        queryset=Location.objects.all(),
        field_name="device__location",
        to_field_name="name",
        label="Location (name)",
    )
    rack_group_id = TreeNodeMultipleChoiceFilter(
        queryset=RackGroup.objects.all(),
        field_name="device__rack__rack_group",
        to_field_name="id",
        label="Rack group (ID)",
    )
    rack_group = TreeNodeMultipleChoiceFilter(
        queryset=RackGroup.objects.all(),
        field_name="device__rack__rack_group",
        to_field_name="name",
        label="Rack group (name)",
    )
    rack = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__rack",
        queryset=Rack.objects.all(),
        to_field_name="name",
        label="Rack (name or ID)",
    )
    role = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__role",
        queryset=Role.objects.filter(content_types__model="device"),
        to_field_name="name",
        label="Role (name or ID)",
    )
    manufacturer = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__device_type__manufacturer",
        queryset=Manufacturer.objects.all(),
        to_field_name="name",
        label="Manufacturer (name or ID)",
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__platform",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )
    device_status = StatusFilter(
        field_name="device__status",
        queryset=Status.objects.all(),
        label="Device Status",
    )
    device_type = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__device_type",
        queryset=DeviceType.objects.all(),
        to_field_name="model",
        label="DeviceType (model or ID)",
    )
    device = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device",
        queryset=Device.objects.all(),
        to_field_name="name",
        label="Device (name or ID)",
    )

    class Meta:
        """Meta class attributes for GoldenConfigFilter."""

        model = models.GoldenConfig
        distinct = True
        fields = "__all__"


class ConfigComplianceFilterSet(GoldenConfigFilterSet):  # pylint: disable=too-many-ancestors
    """Filter capabilities for ConfigCompliance instances."""

    feature_id = django_filters.ModelMultipleChoiceFilter(
        field_name="rule__feature",
        queryset=models.ComplianceFeature.objects.all(),
        label="ComplianceFeature (ID)",
    )
    feature = django_filters.ModelMultipleChoiceFilter(
        field_name="rule__feature__slug",
        queryset=models.ComplianceFeature.objects.all(),
        to_field_name="slug",
        label="ComplianceFeature (slug)",
    )

    class Meta:
        """Meta class attributes for ConfigComplianceFilter."""

        model = models.ConfigCompliance
        fields = "__all__"


class ComplianceFeatureFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = SearchFilter(
        filter_predicates={
            "name": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
        },
    )

    class Meta:
        """Boilerplate filter Meta data for compliance feature."""

        model = models.ComplianceFeature
        fields = "__all__"


class ComplianceRuleFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = SearchFilter(
        filter_predicates={
            "feature__name": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
        },
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="platform",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )

    class Meta:
        """Boilerplate filter Meta data for compliance rule."""

        model = models.ComplianceRule
        fields = "__all__"


class ConfigRemoveFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = SearchFilter(
        filter_predicates={
            "name": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
        },
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="platform",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )

    class Meta:
        """Boilerplate filter Meta data for Config Remove."""

        model = models.ConfigRemove
        fields = "__all__"


class ConfigReplaceFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = SearchFilter(
        filter_predicates={
            "name": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
        },
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="platform",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )

    class Meta:
        """Boilerplate filter Meta data for Config Replace."""

        model = models.ConfigReplace
        fields = "__all__"


class GoldenConfigSettingFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    device_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(),
        label="Device (ID)",
        method="filter_device_id",
    )

    def filter_device_id(self, queryset, name, value):  # pylint: disable=unused-argument
        """Filter by Device ID."""
        if not value:
            return queryset
        golden_config_setting_ids = []
        for instance in value:
            if isinstance(instance, Device):
                device = instance
            else:
                device = Device.objects.get(id=instance)
            golden_config_setting = models.GoldenConfigSetting.objects.get_for_device(device)
            if golden_config_setting is not None:
                golden_config_setting_ids.append(golden_config_setting.id)
        return queryset.filter(id__in=golden_config_setting_ids)

    class Meta:
        """Boilerplate filter Meta data for Config Remove."""

        model = models.GoldenConfigSetting
        fields = "__all__"


class RemediationSettingFilterSet(NautobotFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    q = SearchFilter(
        filter_predicates={
            "platform__name": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
            "remediation_type": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
        },
    )
    platform = django_filters.ModelMultipleChoiceFilter(
        field_name="platform__name",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform Name",
    )
    platform_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Platform.objects.all(),
        label="Platform ID",
    )

    class Meta:
        """Boilerplate filter Meta data for Remediation Setting."""

        model = models.RemediationSetting
        fields = "__all__"


class ConfigPlanFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = SearchFilter(
        filter_predicates={
            "device__name": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
            "change_control_id": {
                "lookup_expr": "icontains",
                "preprocessor": str,
            },
        },
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(),
        label="Device ID",
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name="device__name",
        queryset=Device.objects.all(),
        to_field_name="name",
        label="Device Name",
    )
    feature_id = django_filters.ModelMultipleChoiceFilter(
        field_name="feature__id",
        queryset=models.ComplianceFeature.objects.all(),
        to_field_name="id",
        label="Feature ID",
    )
    feature = django_filters.ModelMultipleChoiceFilter(
        field_name="feature__name",
        queryset=models.ComplianceFeature.objects.all(),
        to_field_name="name",
        label="Feature Name",
    )
    plan_result_id = django_filters.ModelMultipleChoiceFilter(
        queryset=JobResult.objects.filter(config_plan__isnull=False).distinct(),
        label="Plan JobResult ID",
        to_field_name="id",
    )
    tenant_group_id = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="device__tenant__tenant_group",
        to_field_name="id",
        label="Tenant Group (ID)",
    )
    tenant_group = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="device__tenant__tenant_group",
        to_field_name="name",
        label="Tenant Group (name)",
    )
    tenant = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="device__tenant",
        to_field_name="name",
        label="Tenant (name or ID)",
    )
    manufacturer = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__device_type__manufacturer",
        queryset=Manufacturer.objects.all(),
        to_field_name="name",
        label="Manufacturer (name or ID)",
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__platform",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )
    location_id = TreeNodeMultipleChoiceFilter(
        # Not limiting to content_type=dcim.device to allow parent locations to be included
        # i.e. include all Sites in a Region, even though Region can't be assigned to a Device
        queryset=Location.objects.all(),
        field_name="device__location",
        to_field_name="id",
        label="Location (ID)",
    )
    location = TreeNodeMultipleChoiceFilter(
        # Not limiting to content_type=dcim.device to allow parent locations to be included
        # i.e. include all sites in a Region, even though Region can't be assigned to a Device
        queryset=Location.objects.all(),
        field_name="device__location",
        to_field_name="name",
        label="Location (name)",
    )
    deploy_result_id = django_filters.ModelMultipleChoiceFilter(
        queryset=JobResult.objects.filter(config_plan__isnull=False).distinct(),
        label="Deploy JobResult ID",
        to_field_name="id",
    )
    change_control_id = django_filters.CharFilter(
        field_name="change_control_id",
        lookup_expr="exact",
    )
    rack_group_id = TreeNodeMultipleChoiceFilter(
        queryset=RackGroup.objects.all(),
        field_name="device__rack__rack_group",
        to_field_name="id",
        label="Rack group (ID)",
    )
    rack_group = TreeNodeMultipleChoiceFilter(
        queryset=RackGroup.objects.all(),
        field_name="device__rack__rack_group",
        to_field_name="name",
        label="Rack group (name)",
    )
    rack = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__rack",
        queryset=Rack.objects.all(),
        to_field_name="name",
        label="Rack (name or ID)",
    )
    role = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="device__role",
        queryset=Role.objects.filter(content_types__model="device"),
        to_field_name="name",
        label="Role (name or ID)",
    )
    status_id = django_filters.ModelMultipleChoiceFilter(
        # field_name="status__id",
        queryset=Status.objects.all(),
        label="Status ID",
    )
    status = django_filters.ModelMultipleChoiceFilter(
        field_name="status__name",
        queryset=Status.objects.all(),
        to_field_name="name",
        label="Status",
    )

    class Meta:
        """Boilerplate filter Meta data for Config Plan."""

        model = models.ConfigPlan
        fields = "__all__"
