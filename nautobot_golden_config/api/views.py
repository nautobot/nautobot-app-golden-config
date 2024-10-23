"""View for Golden Config APIs."""

import json
from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from jinja2.exceptions import TemplateError, TemplateSyntaxError
from nautobot.apps.utils import render_jinja2
from nautobot.core.api.views import (
    BulkDestroyModelMixin,
    BulkUpdateModelMixin,
    ModelViewSetMixin,
    NautobotAPIVersionMixin,
)
from nautobot.dcim.models import Device
from nautobot.extras.api.views import NautobotModelViewSet, NotesViewSetMixin
from nautobot.extras.datasources.git import ensure_git_repository
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from nautobot_golden_config import filters, models
from nautobot_golden_config.api import serializers
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


class ComplianceRuleViewSet(NautobotModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ComplianceRule objects."""

    queryset = models.ComplianceRule.objects.all()
    serializer_class = serializers.ComplianceRuleSerializer
    filterset_class = filters.ComplianceRuleFilterSet


class ComplianceFeatureViewSet(NautobotModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ComplianceFeature objects."""

    queryset = models.ComplianceFeature.objects.all()
    serializer_class = serializers.ComplianceFeatureSerializer
    filterset_class = filters.ComplianceFeatureFilterSet


class ConfigComplianceViewSet(NautobotModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ConfigCompliance objects."""

    queryset = models.ConfigCompliance.objects.all()
    serializer_class = serializers.ConfigComplianceSerializer
    filterset_class = filters.ConfigComplianceFilterSet


class GoldenConfigViewSet(NautobotModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with GoldenConfig objects."""

    queryset = models.GoldenConfig.objects.all()
    serializer_class = serializers.GoldenConfigSerializer
    filterset_class = filters.GoldenConfigFilterSet


class GoldenConfigSettingViewSet(NautobotModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with GoldenConfigSetting objects."""

    queryset = models.GoldenConfigSetting.objects.all()
    serializer_class = serializers.GoldenConfigSettingSerializer
    filterset_class = filters.GoldenConfigSettingFilterSet


class ConfigRemoveViewSet(NautobotModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ConfigRemove objects."""

    queryset = models.ConfigRemove.objects.all()
    serializer_class = serializers.ConfigRemoveSerializer
    filterset_class = filters.ConfigRemoveFilterSet


class ConfigReplaceViewSet(NautobotModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ConfigReplace objects."""

    queryset = models.ConfigReplace.objects.all()
    serializer_class = serializers.ConfigReplaceSerializer
    filterset_class = filters.ConfigReplaceFilterSet


class ConfigPushPermissions(BasePermission):
    """Permissions class to validate access to Devices and GoldenConfig view."""

    def has_permission(self, request, view):
        """Method to validated permissions to API view."""
        return request.user.has_perm("nautobot_golden_config.view_goldenconfig")

    def has_object_permission(self, request, view, obj):
        """Validate user access to the object, taking into account constraints."""
        return request.user.has_perm("dcim.view_device", obj=obj)


class ConfigToPushViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Detail REST API view showing configuration after postprocessing."""

    permission_classes = [IsAuthenticated & ConfigPushPermissions]
    queryset = Device.objects.all()
    serializer_class = serializers.ConfigToPushSerializer


class RemediationSettingViewSet(NautobotModelViewSet):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with RemediationSetting objects."""

    queryset = models.RemediationSetting.objects.all()
    serializer_class = serializers.RemediationSettingSerializer
    filterset_class = filters.RemediationSettingFilterSet


class ConfigPlanViewSet(
    NautobotAPIVersionMixin,
    NotesViewSetMixin,
    ModelViewSetMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    BulkUpdateModelMixin,
    BulkDestroyModelMixin,
    GenericViewSet,
):  # pylint:disable=too-many-ancestors
    """API viewset for interacting with ConfigPlan objects. Does not support POST to create objects."""

    queryset = models.ConfigPlan.objects.all()
    serializer_class = serializers.ConfigPlanSerializer
    filterset_class = filters.ConfigPlanFilterSet

    def get_serializer_context(self):
        """Gather all custom fields for the model. Copied from nautobot.extras.api.views.CustomFieldModelViewSet."""
        content_type = ContentType.objects.get_for_model(self.queryset.model)
        custom_fields = content_type.custom_fields.all()

        context = super().get_serializer_context()
        context.update(
            {
                "custom_fields": custom_fields,
            }
        )
        return context


class GenerateIntendedConfigException(APIException):
    """Exception for when the intended config cannot be generated."""

    status_code = 400
    default_detail = "Unable to generate the intended config for this device."
    default_code = "error"


class GenerateIntendedConfigView(RetrieveAPIView):
    """API view for generating the intended config for a Device."""

    queryset = Device.objects.all()
    name = "Generate Intended Config"

    def retrieve(self, request, *args, **kwargs):
        """Retrieve intended configuration for a Device."""
        device = self.get_object()
        settings = models.GoldenConfigSetting.objects.get_for_device(device)
        if not settings:
            raise GenerateIntendedConfigException("No Golden Config settings found for this device.")
        if not settings.jinja_repository:
            raise GenerateIntendedConfigException("Golden Config jinja template repository not found.")
        if not settings.sot_agg_query:
            raise GenerateIntendedConfigException("Golden Config GraphQL query not found.")

        try:
            ensure_git_repository(settings.jinja_repository)
        except Exception as exc:
            raise GenerateIntendedConfigException(f"Error trying to sync Jinja template repository: {exc}")
        filesystem_path = settings.get_jinja_template_path_for_device(device)
        if not Path(filesystem_path).is_file():
            raise GenerateIntendedConfigException("Jinja template not found for this device.")

        status_code, context = graph_ql_query(request, device, settings.sot_agg_query.query)
        if status_code == status.HTTP_200_OK:
            template_contents = Path(filesystem_path).read_text()
            try:
                intended_config = render_jinja2(template_code=template_contents, context=context)
            except (TemplateSyntaxError, TemplateError) as exc:
                raise GenerateIntendedConfigException(f"Error rendering Jinja template: {exc}")
            return Response(
                data={
                    "intended_config": intended_config,
                    "intended_config_lines": intended_config.split("\n"),
                },
                status=status.HTTP_200_OK,
            )

        raise GenerateIntendedConfigException("Unable to generate the intended config for this device.")
