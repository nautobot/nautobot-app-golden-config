"""Filters for UI and API Views."""

import django_filters
from django.db.models import Q

from nautobot.core.filters import BaseFilterSet, MultiValueDateTimeFilter, TagFilter, TreeNodeMultipleChoiceFilter
from nautobot.dcim.models import Device, DeviceType, Manufacturer, Platform, Rack, RackGroup, Location
from nautobot.dcim.filters import DeviceFilterSet
from nautobot.extras.filters import NaturalKeyOrPKMultipleChoiceFilter, NautobotFilterSet, StatusFilter
from nautobot.extras.models import JobResult, Role, Status
from nautobot.tenancy.models import Tenant, TenantGroup

from nautobot_golden_config import models


# TODO: 2.0: DeviceFilterSet has bugs in regards to Location in 2.0.0-rc.2
class GoldenConfigDeviceFilterSet(DeviceFilterSet):  # pylint: disable=too-many-ancestors
    """Filter capabilities that extend the standard DeviceFilterSet."""

    @staticmethod
    def _get_filter_lookup_dict(existing_filter):
        """Extend method to account for isnull on datetime types."""
        # Choose the lookup expression map based on the filter type
        lookup_map = DeviceFilterSet._get_filter_lookup_dict(existing_filter)
        if isinstance(existing_filter, MultiValueDateTimeFilter):
            lookup_map.update({"isnull": "isnull"})
        return lookup_map

    class Meta(DeviceFilterSet.Meta):
        """Update the Meta class, but only for fields."""

        fields = DeviceFilterSet.Meta.fields + [
            "goldenconfig__backup_config",
            "goldenconfig__backup_last_attempt_date",
            "goldenconfig__backup_last_success_date",
            "goldenconfig__intended_config",
            "goldenconfig__intended_last_attempt_date",
            "goldenconfig__intended_last_success_date",
            "goldenconfig__compliance_config",
            "goldenconfig__compliance_last_attempt_date",
            "goldenconfig__compliance_last_success_date",
        ]


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

    q = django_filters.CharFilter(
        method="search",
        label="Search",
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
        label="Location (ID)",
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
        queryset=Role.objects.all(),  # TODO: 2.0: How does change to Role model affect this?
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

    def search(self, queryset, name, value):  # pylint: disable=unused-argument
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
        fields = [
            "id",
            "backup_config",
            "backup_last_attempt_date",
            "backup_last_success_date",
            "intended_config",
            "intended_last_attempt_date",
            "intended_last_success_date",
            "compliance_config",
            "compliance_last_attempt_date",
            "compliance_last_success_date",
        ]


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
        fields = ["id", "compliance", "actual", "intended", "missing", "extra", "ordered", "compliance_int", "rule"]


class ComplianceFeatureFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for compliance feature."""

        model = models.ComplianceFeature
        fields = ["id", "name", "slug", "description"]


class ComplianceRuleFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="platform",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(feature__name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for compliance rule."""

        model = models.ComplianceRule
        fields = ["feature", "id"]


class ConfigRemoveFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="platform",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for Config Remove."""

        model = models.ConfigRemove
        fields = ["id", "name"]


class ConfigReplaceFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    platform = NaturalKeyOrPKMultipleChoiceFilter(
        field_name="platform",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for Config Replace."""

        model = models.ConfigReplace
        fields = ["id", "name"]


class GoldenConfigSettingFilterSet(NautobotFilterSet):
    """Inherits Base Class NautobotFilterSet."""

    class Meta:
        """Boilerplate filter Meta data for Config Remove."""

        model = models.GoldenConfigSetting
        fields = ["id", "name", "slug", "weight", "backup_repository", "intended_repository", "jinja_repository"]


class RemediationSettingFilterSet(BaseFilterSet):
    """Inherits Base Class CustomFieldModelFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
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
    remediation_type = django_filters.ModelMultipleChoiceFilter(
        field_name="remediation_type",
        queryset=models.RemediationSetting.objects.all(),
        to_field_name="remediation_type",
        label="Remediation Type",
    )

    def search(self, queryset, name, value):  # pylint: disable=unused-argument
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(platform__name__icontains=value) | Q(remediation_type__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for Remediation Setting."""

        model = models.RemediationSetting
        fields = ["id", "platform", "remediation_type"]


class ConfigPlanFilterSet(BaseFilterSet):
    """Inherits Base Class BaseFilterSet."""

    q = django_filters.CharFilter(
        method="search",
        label="Search",
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
    job_result_id = django_filters.ModelMultipleChoiceFilter(
        queryset=JobResult.objects.filter(config_plan__isnull=False).distinct(),
        label="JobResult ID",
    )
    change_control_id = django_filters.CharFilter(
        field_name="change_control_id",
        lookup_expr="exact",
    )
    status_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Status.objects.all(),
        label="Status ID",
    )
    status = django_filters.ModelMultipleChoiceFilter(
        field_name="status__name",
        queryset=Status.objects.all(),
        to_field_name="name",
        label="Status",
    )
    tag = TagFilter()

    def search(self, queryset, name, value):  # pylint: disable=unused-argument
        """Perform the filtered search."""
        if not value.strip():
            return queryset
        qs_filter = Q(device__name__icontains=value) | Q(change_control_id__icontains=value)
        return queryset.filter(qs_filter)

    class Meta:
        """Boilerplate filter Meta data for Config Plan."""

        model = models.ConfigPlan
        fields = ["id", "device", "created", "plan_type", "feature", "change_control_id", "status"]
