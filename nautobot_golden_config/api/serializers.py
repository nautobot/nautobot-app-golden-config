"""API serializers for nautobot_golden_config."""

# pylint: disable=too-many-ancestors
from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin
from nautobot.apps.utils import GitRepo
from nautobot.dcim.api.serializers import DeviceSerializer
from nautobot.dcim.models import Device
from nautobot.extras.api.serializers import GitRepositorySerializer
from nautobot.extras.datasources.git import ensure_git_repository, get_repo_from_url_to_path_and_from_branch
from nautobot.extras.models import GitRepository
from rest_framework import serializers

from nautobot_golden_config import models
from nautobot_golden_config.utilities.config_postprocessing import get_config_postprocessing


class GraphQLSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for a GraphQL object."""

    data = serializers.JSONField(read_only=True)


class ComplianceFeatureSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """ComplianceFeature Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.ComplianceFeature
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []


class ComplianceRuleSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for ComplianceRule object."""

    class Meta:
        """Set Meta Data for ComplianceRule, will serialize all fields."""

        model = models.ComplianceRule
        fields = "__all__"


class ConfigComplianceSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for ConfigCompliance object."""

    class Meta:
        """Set Meta Data for ConfigCompliance, will serialize fields."""

        model = models.ConfigCompliance
        fields = "__all__"


class GoldenConfigSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for GoldenConfig object."""

    class Meta:
        """Set Meta Data for GoldenConfig, will serialize all fields."""

        model = models.GoldenConfig
        fields = "__all__"


class GoldenConfigSettingSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for GoldenConfigSetting object."""

    class Meta:
        """Set Meta Data for GoldenConfigSetting, will serialize all fields."""

        model = models.GoldenConfigSetting
        fields = "__all__"


class ConfigRemoveSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for ConfigRemove object."""

    class Meta:
        """Set Meta Data for ConfigRemove, will serialize all fields."""

        model = models.ConfigRemove
        fields = "__all__"


class ConfigReplaceSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for ConfigReplace object."""

    class Meta:
        """Set Meta Data for ConfigReplace, will serialize all fields."""

        model = models.ConfigReplace
        fields = "__all__"


class ConfigToPushSerializer(DeviceSerializer):  # pylint: disable=nb-sub-class-name
    """Serializer for ConfigToPush view."""

    config = serializers.SerializerMethodField()

    class Meta(DeviceSerializer.Meta):
        """Extend the Device serializer with the configuration after postprocessing."""

        fields = "__all__"
        model = Device

    def get_config(self, obj):
        """Provide the intended configuration ready after postprocessing to the config field."""
        request = self.context.get("request")
        config_details = models.GoldenConfig.objects.get(device=obj)
        return get_config_postprocessing(config_details, request)


class RemediationSettingSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for RemediationSetting object."""

    class Meta:
        """Set Meta Data for RemediationSetting, will serialize all fields."""

        model = models.RemediationSetting
        fields = "__all__"


class ConfigPlanSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):
    """Serializer for ConfigPlan object."""

    class Meta:
        """Set Meta Data for ConfigPlan, will serialize all fields."""

        model = models.ConfigPlan
        fields = "__all__"
        read_only_fields = ["device", "plan_type", "feature", "config_set"]


class GenerateIntendedConfigSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for GenerateIntendedConfigView."""

    intended_config = serializers.CharField(read_only=True)
    intended_config_lines = serializers.ListField(read_only=True, child=serializers.CharField())
    graphql_data = serializers.JSONField(read_only=True)
    diff = serializers.CharField(read_only=True)
    diff_lines = serializers.ListField(read_only=True, child=serializers.CharField())


class GitRepositoryWithBranchesSerializer(GitRepositorySerializer):  # pylint: disable=nb-sub-class-name
    """Serializer for extras.GitRepository with remote branches field."""

    remote_branches = serializers.SerializerMethodField()

    def get_remote_branches(self, obj):
        """Return a list of branches for the GitRepository."""
        ensure_git_repository(obj)
        from_url, to_path, _ = get_repo_from_url_to_path_and_from_branch(obj)
        repo_helper = GitRepo(to_path, from_url)
        repo_helper.repo.remotes.origin.fetch()
        return [
            ref.name[7:]  # removeprefix("origin/")
            for ref in repo_helper.repo.remotes.origin.refs
            if ref.name != "origin/HEAD"
        ]

    class Meta:  # noqa: D106  # undocumented-public-nested-class
        model = GitRepository
        fields = "__all__"
