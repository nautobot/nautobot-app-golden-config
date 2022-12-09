"""Filters for UI and API Views."""

import django_filters

from django.db.models import Q

from nautobot.dcim.models import Device, Platform, Region, Site, DeviceRole, DeviceType, Manufacturer, Rack, RackGroup
from nautobot.extras.models import Status
from nautobot.extras.filters import StatusFilter, CustomFieldModelFilterSet
from nautobot.tenancy.models import Tenant, TenantGroup
from nautobot.utilities.filters import TreeNodeMultipleChoiceFilter, BaseFilterSet, NameSlugSearchFilterSet

from nautobot_golden_config import models


class GenericPlatformFilterSet(CustomFieldModelFilterSet):
    """Generic method to reuse common FilterSet."""

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


class GoldenConfigFilterSet(CustomFieldModelFilterSet):
    """Filter capabilities for GoldenConfig instances."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    tenant_group_id = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="device__tenant__group",
        label="Tenant Group (ID)",
    )
    tenant_group = TreeNodeMultipleChoiceFilter(
        queryset=TenantGroup.objects.all(),
        field_name="device__tenant__group",
        to_field_name="slug",
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
        label="Region (ID)",
    )
    region = TreeNodeMultipleChoiceFilter(
        queryset=Region.objects.all(),
        field_name="device__site__region",
        to_field_name="slug",
        label="Region (slug)",
    )
    site_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device__site",
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
        label="Rack group (ID)",
    )
    rack_group = django_filters.ModelMultipleChoiceFilter(
        field_name="device__rack__group__slug",
        queryset=RackGroup.objects.all(),
        to_field_name="slug",
        label="Rack group (slug)",
    )
    rack_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device__rack",
        queryset=Rack.objects.all(),
        label="Rack (ID)",
    )
    rack = django_filters.ModelMultipleChoiceFilter(
        field_name="device__rack__name",
        queryset=Rack.objects.all(),
        to_field_name="name",
        label="Rack (name)",
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
        field_name="device__platform",
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
        field_name="device__status_id",
        queryset=Status.objects.all(),
        label="Device Status",
    )
    device_status = StatusFilter(
        field_name="device__status",
        queryset=Status.objects.all(),
        label="Device Status",
    )
    device_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name="device__device_type_id",
        queryset=DeviceType.objects.all(),
        label="Device type (ID)",
    )
    device_type = django_filters.ModelMultipleChoiceFilter(
        field_name="device__device_type__slug",
        queryset=DeviceType.objects.all(),
        to_field_name="slug",
        label="DeviceType (slug)",
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

    def search(self, queryset, name, value):  # pylint: disable=unused-argument,no-self-use
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        # Chose only device, can be convinced more should be included
        qs_filter = Q(device__name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Meta class attributes for GoldenConfigFilter."""

        model = models.GoldenConfig
        distinct = True
        fields = ["id"]


class ConfigComplianceFilterSet(GoldenConfigFilterSet):
    """Filter capabilities for ConfigCompliance instances."""

    class Meta:
        """Meta class attributes for ConfigComplianceFilter."""

        model = models.ConfigCompliance
        fields = ["id"]


class ComplianceFeatureFilterSet(CustomFieldModelFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument,no-self-use
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for compliance feature."""

        model = models.ComplianceFeature
        fields = ["id", "name", "slug"]


class ComplianceRuleFilterSet(GenericPlatformFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument,no-self-use
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(feature__name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for compliance rule."""

        model = models.ComplianceRule
        fields = ["feature", "id"]


class ConfigRemoveFilterSet(GenericPlatformFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument,no-self-use
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for Config Remove."""

        model = models.ConfigRemove
        fields = ["id", "name"]


class ConfigReplaceFilterSet(GenericPlatformFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument,no-self-use
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for Config Replace."""

        model = models.ConfigReplace
        fields = ["id", "name"]


class GoldenConfigSettingFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    """Inherits Base Class BaseFilterSet."""

    class Meta:
        """Boilerplate filter Meta data for Config Remove."""

        model = models.GoldenConfigSetting
        fields = ["id", "name", "slug", "weight", "backup_repository", "intended_repository", "jinja_repository"]
