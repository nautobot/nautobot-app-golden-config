"""API views for nautobot_golden_config."""

from nautobot.apps.api import NautobotModelViewSet

from nautobot_golden_config import filters, models
from nautobot_golden_config.api import serializers


class ComplianceFeatureViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """ComplianceFeature viewset."""

    queryset = models.ComplianceFeature.objects.all()
    serializer_class = serializers.ComplianceFeatureSerializer
    filterset_class = filters.ComplianceFeatureFilterSet

    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]
