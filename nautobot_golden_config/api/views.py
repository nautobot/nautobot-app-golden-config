"""View for Golden Config APIs."""
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.permissions import AllowAny
from nautobot.extras.api.views import CustomFieldModelViewSet
from nautobot.dcim.models import Device

from nautobot_golden_config.api import serializers
from nautobot_golden_config import models
from nautobot_golden_config import filters
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import get_device_to_settings_map


class GoldenConfigRootView(APIRootView):
    """Golden Config API root view."""

    def get_view_name(self):
        """Golden Config API root view boilerplate."""
        return "Golden Config"


class SOTAggDeviceDetailView(APIView):
    """Detail REST API view showing graphql, with a potential "transformer" of data on a specific device."""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Get method serialize for a dictionary to json response."""
        device = Device.objects.get(pk=kwargs["pk"])
        settings = get_device_to_settings_map(queryset=Device.objects.filter(pk=device.pk))[device.id]
        status_code, data = graph_ql_query(request, device, settings.sot_agg_query.query)
        data = json.loads(json.dumps(data))
        return Response(serializers.GraphQLSerializer(data=data).initial_data, status=status_code)


class ComplianceRuleViewSet(CustomFieldModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ComplianceRule objects."""

    queryset = models.ComplianceRule.objects.all()
    serializer_class = serializers.ComplianceRuleSerializer
    filterset_class = filters.ComplianceRuleFilterSet


class ComplianceFeatureViewSet(CustomFieldModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ComplianceFeature objects."""

    queryset = models.ComplianceFeature.objects.all()
    serializer_class = serializers.ComplianceFeatureSerializer
    filterset_class = filters.ComplianceFeatureFilterSet


class ConfigComplianceViewSet(CustomFieldModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ConfigCompliance objects."""

    queryset = models.ConfigCompliance.objects.all()
    serializer_class = serializers.ConfigComplianceSerializer
    filterset_class = filters.ConfigComplianceFilterSet


class GoldenConfigViewSet(CustomFieldModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with GoldenConfig objects."""

    queryset = models.GoldenConfig.objects.all()
    serializer_class = serializers.GoldenConfigSerializer
    filterset_class = filters.GoldenConfigFilterSet


class GoldenConfigSettingViewSet(CustomFieldModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with GoldenConfigSetting objects."""

    queryset = models.GoldenConfigSetting.objects.all()
    serializer_class = serializers.GoldenConfigSettingSerializer
    filterset_class = filters.GoldenConfigSettingFilterSet


class ConfigRemoveViewSet(CustomFieldModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ConfigRemove objects."""

    queryset = models.ConfigRemove.objects.all()
    serializer_class = serializers.ConfigRemoveSerializer
    filterset_class = filters.ConfigRemoveFilterSet


class ConfigReplaceViewSet(CustomFieldModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ConfigReplace objects."""

    queryset = models.ConfigReplace.objects.all()
    serializer_class = serializers.ConfigReplaceSerializer
    filterset_class = filters.ConfigReplaceFilterSet
