"""Filtering for nautobot_golden_config."""

from nautobot.apps.filters import NameSearchFilterSet, NautobotFilterSet

from nautobot_golden_config import models


class ComplianceFeatureFilterSet(NameSearchFilterSet, NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for ComplianceFeature."""

    class Meta:
        """Meta attributes for filter."""

        model = models.ComplianceFeature

        # add any fields from the model that you would like to filter your searches by using those
        fields = "__all__"
