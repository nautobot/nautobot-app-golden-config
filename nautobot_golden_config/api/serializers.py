"""REST API serializer capabilities for graphql plugin."""
# pylint: disable=too-many-ancestors
from rest_framework import serializers

from nautobot.extras.api.customfields import CustomFieldModelSerializer
from nautobot.extras.api.serializers import TaggedObjectSerializer
from nautobot.extras.api.nested_serializers import NestedDynamicGroupSerializer
from nautobot.dcim.api.serializers import DeviceSerializer
from nautobot.dcim.models import Device

from nautobot_golden_config import models
from nautobot_golden_config.utilities.config_postprocessing import get_config_postprocessing


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


class ComplianceRuleSerializer(TaggedObjectSerializer, CustomFieldModelSerializer):
    """Serializer for ComplianceRule object."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_golden_config-api:compliancerule-detail")

    class Meta:
        """Set Meta Data for ComplianceRule, will serialize all fields."""

        model = models.ComplianceRule
        fields = "__all__"


class ConfigComplianceSerializer(TaggedObjectSerializer, CustomFieldModelSerializer):
    """Serializer for ConfigCompliance object."""

    class Meta:
        """Set Meta Data for ConfigCompliance, will serialize fields."""

        model = models.ConfigCompliance
        fields = "__all__"


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
    scope = serializers.JSONField(required=False)
    dynamic_group = NestedDynamicGroupSerializer(required=False)

    class Meta:
        """Set Meta Data for GoldenConfigSetting, will serialize all fields."""

        model = models.GoldenConfigSetting
        fields = "__all__"

    def validate(self, data):
        """Validate scope & dynamic_group are not both submitted."""
        if data.get("scope") and data.get("dynamic_group"):
            raise serializers.ValidationError(
                "Payload can only contain `scope` or `dynamic_group`, but both were provided."
            )
        return data

    def create(self, validated_data):
        """Overload to handle ability to post scope instead of dynamic_group."""
        if not validated_data.get("scope"):
            return models.GoldenConfigSetting.objects.create(**validated_data)

        # The scope setter is not called on use of Model.objects.create method.
        # The model must first be created in memory without the scope, then
        # assign the scope which will call the scope setter. Finally .save()
        # and return.
        scope = validated_data.pop("scope")
        setting = models.GoldenConfigSetting(**validated_data)
        setting.scope = scope

        # Using .save() over .validated_save() as validation is done prior to .create() being called
        setting.save()
        return setting


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


class ConfigToPushSerializer(DeviceSerializer):
    """Serializer for ConfigToPush view."""

    config = serializers.SerializerMethodField()

    class Meta(DeviceSerializer):
        """Extend the Device serializer with the configuration after postprocessing."""

        fields = DeviceSerializer.Meta.fields + ["config"]
        model = Device

    def get_config(self, obj):
        """Provide the intended configuration ready after postprocessing to the config field."""
        request = self.context.get("request")

        config_details = models.GoldenConfig.objects.get(device=obj)
        return get_config_postprocessing(config_details, request)
