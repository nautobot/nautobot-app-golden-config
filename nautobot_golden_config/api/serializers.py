"""REST API serializer capabilities for graphql plugin."""
# pylint: disable=too-many-ancestors
from rest_framework import serializers

from nautobot.extras.api.customfields import CustomFieldModelSerializer
from nautobot.extras.api.serializers import TaggedObjectSerializer
from nautobot.core.api.serializers import BaseModelSerializer

from nautobot_golden_config import models


class GraphQLSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for a GraphQL object."""

    data = serializers.JSONField()


class ComplianceFeatureSerializer(TaggedObjectSerializer, CustomFieldModelSerializer):
    """Serializer for ComplianceFeature object."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:nautobot_golden_config-api:compliancefeature-detail"
    )

    class Meta:
        """Set Meta Data for ComplianceFeature, will serialize all fields."""

        model = models.ComplianceFeature
        fields = "__all__"


class ComplianceRuleSerializer(BaseModelSerializer):
    """Serializer for ComplianceRule object."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_golden_config-api:compliancerule-detail")

    class Meta:
        """Set Meta Data for ComplianceRule, will serialize all fields."""

        model = models.ComplianceRule
        fields = "__all__"


class ConfigComplianceSerializer(TaggedObjectSerializer, CustomFieldModelSerializer):
    """Serializer for ConfigCompliance object."""

    class Meta:
        """Set Meta Data for ConfigCompliance, will serialize device and rule fields."""

        model = models.ConfigCompliance
        fields = (
            "id",
            "device",
            "rule",
            "actual",
            "intended",
            "ordered",
        )


class GoldenConfigSerializer(TaggedObjectSerializer, CustomFieldModelSerializer):
    """Serializer for GoldenConfig object."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_golden_config-api:goldenconfig-detail")

    class Meta:
        """Set Meta Data for GoldenConfig, will serialize all fields."""

        model = models.GoldenConfig
        fields = "__all__"


class GoldenConfigSettingSerializer(TaggedObjectSerializer, CustomFieldModelSerializer):
    """Serializer for GoldenConfigSetting object."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:nautobot_golden_config-api:goldenconfigsetting-detail"
    )

    class Meta:
        """Set Meta Data for GoldenConfigSetting, will serialize all fields."""

        model = models.GoldenConfigSetting
        fields = "__all__"


class ConfigRemoveSerializer(TaggedObjectSerializer, CustomFieldModelSerializer):
    """Serializer for ConfigRemove object."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_golden_config-api:configremove-detail")

    class Meta:
        """Set Meta Data for ConfigRemove, will serialize all fields."""

        model = models.ConfigRemove
        fields = "__all__"


class ConfigReplaceSerializer(TaggedObjectSerializer, CustomFieldModelSerializer):
    """Serializer for ConfigReplace object."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_golden_config-api:configreplace-detail")

    class Meta:
        """Set Meta Data for ConfigReplace, will serialize all fields."""

        model = models.ConfigReplace
        fields = "__all__"
