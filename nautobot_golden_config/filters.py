"""Filter for Device Configuration Backup."""

import django_filters

from django.db.models import Q

from nautobot.dcim.models import Device, Platform, Region, Site, DeviceRole, DeviceType, Manufacturer, RackGroup, Rack
from nautobot.extras.models import Status
from nautobot.extras.filters import CreatedUpdatedFilterSet, StatusFilter, CustomFieldModelFilterSet
from nautobot.tenancy.models import Tenant, TenantGroup
from nautobot.utilities.filters import TreeNodeMultipleChoiceFilter

from nautobot_golden_config import models


class GoldenConfigFilter(CreatedUpdatedFilterSet):
    """Filter capabilities for GoldenConfig instances."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    tenant_group_id = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="tenant__group",
        lookup_expr="in",
        label="Tenant Group (ID)",
    )
    tenant_group = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="tenant__group",
        to_field_name="slug",
        lookup_expr="in",
        label="Tenant Group (slug)",
    )
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="tenant_id",
        label="Tenant (ID)",
    )
    tenant = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="tenant__slug",
        to_field_name="slug",
        label="Tenant (slug)",
    )
    region_id = TreeNodeMultipleChoiceFilter(
        queryset=Region.objects.all(),
        field_name="site__region",
        lookup_expr="in",
        label="Region (ID)",
    )
    region = TreeNodeMultipleChoiceFilter(
        queryset=Region.objects.all(),
        field_name="site__region",
        lookup_expr="in",
        to_field_name="slug",
        label="Region (slug)",
    )
    site_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Site.objects.all(),
        label="Site (ID)",
    )
    site = django_filters.ModelMultipleChoiceFilter(
        field_name="site__slug",
        queryset=Site.objects.all(),
        to_field_name="slug",
        label="Site name (slug)",
    )
    rack_group_id = TreeNodeMultipleChoiceFilter(
        queryset=RackGroup.objects.all(),
        field_name="rack__group",
        lookup_expr="in",
        label="Rack group (ID)",
    )
    rack_id = django_filters.ModelMultipleChoiceFilter(
        field_name="rack",
        queryset=Rack.objects.all(),
        label="Rack (ID)",
    )
    role_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device_role_id",
        queryset=DeviceRole.objects.all(),
        label="Role (ID)",
    )
    role = django_filters.ModelMultipleChoiceFilter(
        field_name="device_role__slug",
        queryset=DeviceRole.objects.all(),
        to_field_name="slug",
        label="Role (slug)",
    )
    manufacturer_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device_type__manufacturer",
        queryset=Manufacturer.objects.all(),
        label="Manufacturer (ID)",
    )
    manufacturer = django_filters.ModelMultipleChoiceFilter(
        field_name="device_type__manufacturer__slug",
        queryset=Manufacturer.objects.all(),
        to_field_name="slug",
        label="Manufacturer (slug)",
    )
    platform_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Platform.objects.all(),
        label="Platform (ID)",
    )
    platform = django_filters.ModelMultipleChoiceFilter(
        field_name="platform__slug",
        queryset=Platform.objects.all(),
        to_field_name="slug",
        label="Platform (slug)",
    )
    device_status_id = StatusFilter(
        field_name="status",
        queryset=Status.objects.all(),
        label="Device Status",
    )
    device_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device_type_id",
        queryset=DeviceType.objects.all(),
        label="Device type (ID)",
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device",
        queryset=Device.objects.all(),
        label="Device (ID)",
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name="name",
        queryset=Device.objects.all(),
        label="Device Name",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument,no-self-use
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        # Chose only device, can be convinced more should be included
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Meta class attributes for GoldenConfig."""

        model = Device
        distinct = True
        fields = [
            "q",
            "tenant_group_id",
            "tenant_group",
            "tenant_id",
            "tenant",
            "region_id",
            "region",
            "site_id",
            "site",
            "rack_group_id",
            "rack_id",
            "role_id",
            "role",
            "manufacturer_id",
            "manufacturer",
            "platform_id",
            "platform",
            "device_status_id",
            "device_type_id",
            "device_id",
            "device",
        ]


class ConfigComplianceFilter(CreatedUpdatedFilterSet):
    """Filter capabilities for ConfigCompliance instances."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    tenant_group_id = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="device__tenant__group",
        lookup_expr="in",
        label="Tenant Group (ID)",
    )
    tenant_group = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="device__tenant__group",
        to_field_name="slug",
        lookup_expr="in",
        label="Tenant Group (slug)",
    )
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="device__tenant_id",
        label="Tenant (ID)",
    )
    tenant = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="device__tenant__slug",
        to_field_name="slug",
        label="Tenant (slug)",
    )
    region_id = TreeNodeMultipleChoiceFilter(
        queryset=Region.objects.all(),
        field_name="device__site__region",
        lookup_expr="in",
        label="Region (ID)",
    )
    region = TreeNodeMultipleChoiceFilter(
        queryset=Region.objects.all(),
        field_name="device__site__region",
        lookup_expr="in",
        to_field_name="slug",
        label="Region (slug)",
    )
    site_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Site.objects.all(),
        label="Site (ID)",
    )
    site = django_filters.ModelMultipleChoiceFilter(
        field_name="device__site__slug",
        queryset=Site.objects.all(),
        to_field_name="slug",
        label="Site name (slug)",
    )
    rack_group_id = TreeNodeMultipleChoiceFilter(
        queryset=RackGroup.objects.all(),
        field_name="device__rack__group",
        lookup_expr="in",
        label="Rack group (ID)",
    )
    rack_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device__rack",
        queryset=Rack.objects.all(),
        label="Rack (ID)",
    )
    role_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device__device_role_id",
        queryset=DeviceRole.objects.all(),
        label="Role (ID)",
    )
    role = django_filters.ModelMultipleChoiceFilter(
        field_name="device__device_role__slug",
        queryset=DeviceRole.objects.all(),
        to_field_name="slug",
        label="Role (slug)",
    )
    manufacturer_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device__device_type__manufacturer",
        queryset=Manufacturer.objects.all(),
        label="Manufacturer (ID)",
    )
    manufacturer = django_filters.ModelMultipleChoiceFilter(
        field_name="device__device_type__manufacturer__slug",
        queryset=Manufacturer.objects.all(),
        to_field_name="slug",
        label="Manufacturer (slug)",
    )
    platform_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Platform.objects.all(),
        label="Platform (ID)",
    )
    platform = django_filters.ModelMultipleChoiceFilter(
        field_name="device__platform__slug",
        queryset=Platform.objects.all(),
        to_field_name="slug",
        label="Platform (slug)",
    )
    device_status_id = StatusFilter(
        field_name="device__status",
        queryset=Status.objects.all(),
        label="Device Status",
    )
    device_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device__device_type_id",
        queryset=DeviceType.objects.all(),
        label="Device type (ID)",
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(),
        label="Device Name",
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name="device__name",
        queryset=Device.objects.all(),
        label="Device Name",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument,no-self-use
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        # Chose only device, can be convinced more should be included
        qs_filter = Q(device__name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Meta class attributes for ConfigComplianceFilter."""

        model = models.ConfigCompliance
        distinct = True
        fields = [
            "q",
            "tenant_group_id",
            "tenant_group",
            "tenant_id",
            "tenant",
            "region_id",
            "region",
            "site_id",
            "site",
            "rack_group_id",
            "rack_id",
            "role_id",
            "role",
            "manufacturer_id",
            "manufacturer",
            "platform_id",
            "platform",
            "device_status_id",
            "device_type_id",
            "device_id",
            "device",
        ]


class ComplianceFeatureFilter(CustomFieldModelFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )

    class Meta:
        """Boilerplate filter Meta data for compliance feature."""

        model = models.ComplianceFeature
        fields = ["q", "name"]


class ComplianceRuleFilter(CustomFieldModelFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    class Meta:
        """Boilerplate filter Meta data for compliance rule."""

        model = models.ComplianceRule
        fields = ["platform", "feature"]


class ConfigRemoveFilter(CustomFieldModelFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    class Meta:
        """Boilerplate filter Meta data for Config Remove."""

        model = models.ConfigRemove
        fields = ["platform", "name"]


class ConfigReplaceFilter(CustomFieldModelFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    class Meta:
        """Boilerplate filter Meta data for Config Remove."""

        model = models.ConfigReplace
        fields = ["platform", "name"]
