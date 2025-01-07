"""API serializers for nautobot_golden_config."""

from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin

from nautobot_golden_config import models


class ComplianceFeatureSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """ComplianceFeature Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.ComplianceFeature
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
