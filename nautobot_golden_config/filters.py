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


class ComplianceFeatureFilterSet(NameSearchFilterSet, NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for ComplianceFeature."""

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

        # add any fields from the model that you would like to filter your searches by using those
        fields = "__all__"
