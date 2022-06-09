"""View for Golden Config APIs."""
import json
import logging

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated

from nautobot.extras.api.views import CustomFieldModelViewSet
from nautobot.dcim.models import Device
from nautobot.dcim.api.serializers import DeviceSerializer

from nautobot_golden_config.api import serializers, renderers
from nautobot_golden_config import models
from nautobot_golden_config import filters
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import get_device_to_settings_map
from nautobot_golden_config.nornir_plays.config_intended import config_intended

LOGGER = logging.getLogger(__name__)


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


class CandidateConfigDetailView(GenericAPIView):
    """Detail REST API view showing configuration to push to appliances, with secrets rendered."""

    permission_classes = [IsAuthenticated]
    queryset = Device.objects.values_list("name", "serial")
    filter_fields = ("serial", "name")

    @extend_schema(methods=["get"], responses={200: DeviceSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """Get method serialize for a dictionary to json response that gets configuration candidate."""
        serial = request.query_params.get("serial")
        name = request.query_params.get("name")
        if serial and name:
            obj = Device.objects.filter(name=name, serial=serial).first()
            if not obj:
                LOGGER.error("There is no device with name: %s and serial: %s", name, serial)
                raise NotFound(f"There is no device with name {name} and serial {serial}")
        elif serial:
            try:
                obj = Device.objects.get(serial=serial)
            except Device.DoesNotExist:
                LOGGER.error("There is no device with serial number: %s", serial)
                raise NotFound(f"There is no device with serial number {serial}") from Device.DoesNotExist
        elif name:
            try:
                obj = Device.objects.get(name=name)
            except Device.DoesNotExist:
                LOGGER.error("There is no device with name: %s", name)
                raise NotFound(f"There is no device with name {name}") from Device.DoesNotExist
        else:
            LOGGER.error("No device name or serial number in input.")
            raise NotFound("No device name or serial number in input.")

        data = {"device": obj, "debug": True}
        config = []
        # TODO: add proper logger, not None - Issue: https://gitlab.ddt.gov.net/nautobot/nautobot-plugin-golden-config/-/issues/5
        try:
            config = config_intended(
                request,
                None,
                data,
                False,
            )
        except Exception as config_exception:
            LOGGER.error("Candidate configuration not rendered %s.", config_exception)
            raise NotFound((f"Candidate configuration not rendered. {config_exception}")) from config_exception

        # We are using "Accept" to render raw configuration with secrets
        # Ex. api/plugins/golden-config/config-candidate/?serial=123456789 -H "Accept: text/plain"
        # It can be used by appliances to provision a configuration with a simple `copy` command to this API call.
        if request.accepted_media_type == "text/plain":
            response = renderers.PlainTextRenderer().render(str(config[obj.name][0]))
            # Render the plain text http response, not the standard django rest api response
            return HttpResponse(response)

        # config returned object is an AggregatedResult of the form:
        # AggregatedResult (RENDER CONFIG): {'Dev-Name': MultiResult: [Result: "RENDER CONFIG", MultiResult: [Result: "GENERATE CONFIG", MultiResult: [Result: "generate_config", Result: "template_file"]]]}
        # It includes a list of multiresults one for each executed nornir task
        response = [{"name": obj.name, "serial": obj.serial, "config": str(config[obj.name][0])}]
        return Response(response)
