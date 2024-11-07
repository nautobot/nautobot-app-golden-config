"""View for Golden Config APIs."""

import datetime
import json
import logging
from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import make_aware
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
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
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nornir import InitNornir
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from nautobot_golden_config import filters, models
from nautobot_golden_config.api import serializers
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import dispatch_params, get_device_to_settings_map, get_django_env


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


def _nornir_task_inject_graphql_data(task, graphql_data, **kwargs):
    """Inject the GraphQL data into the Nornir task host data and then run nornir_nautobot.plugins.tasks.dispatcher.dispatcher subtask.

    This is a small stub of the logic in nautobot_golden_config.nornir_plays.config_intended.run_template.
    """
    task.host.data.update(graphql_data)
    generated_config = task.run(task=dispatcher, name="GENERATE CONFIG", **kwargs)
    return generated_config


class GenerateIntendedConfigView(NautobotAPIVersionMixin, GenericAPIView):
    """API view for generating the intended config for a Device."""

    name = "Generate Intended Config for Device"
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.GenerateIntendedConfigSerializer

    def _get_object(self, request, model, query_param):
        """Get the requested model instance, restricted to requesting user."""
        pk = request.query_params.get(query_param)
        if not pk:
            raise GenerateIntendedConfigException(f"Parameter {query_param} is required")
        try:
            return model.objects.restrict(request.user, "view").get(pk=pk)
        except model.DoesNotExist as exc:
            raise GenerateIntendedConfigException(f"{model.__name__} with id '{pk}' not found") from exc

    def _get_jinja_template_path(self, settings, device, git_repository):
        """Get the Jinja template path for the device in the provided git repository."""
        try:
            rendered_path = render_jinja2(template_code=settings.jinja_path_template, context={"obj": device})
        except (TemplateSyntaxError, TemplateError) as exc:
            raise GenerateIntendedConfigException("Error rendering Jinja path template") from exc
        filesystem_path = Path(git_repository.filesystem_path) / rendered_path
        if not filesystem_path.is_file():
            msg = f"Jinja template {filesystem_path} not found in git repository {git_repository}"
            raise GenerateIntendedConfigException(msg)
        return filesystem_path

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="device_id",
                required=True,
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """Generate intended configuration for a Device."""
        device = self._get_object(request, Device, "device_id")
        settings = models.GoldenConfigSetting.objects.get_for_device(device)
        if not settings:
            raise GenerateIntendedConfigException("No Golden Config settings found for this device")
        if not settings.sot_agg_query:
            raise GenerateIntendedConfigException("Golden Config settings sot_agg_query not set")
        if not settings.jinja_repository:
            raise GenerateIntendedConfigException("Golden Config settings jinja_repository not set")

        try:
            git_repository = settings.jinja_repository
            ensure_git_repository(git_repository)
        except Exception as exc:
            raise GenerateIntendedConfigException("Error trying to sync git repository") from exc

        filesystem_path = self._get_jinja_template_path(settings, device, git_repository)

        status_code, context = graph_ql_query(request, device, settings.sot_agg_query.query)
        if status_code == status.HTTP_200_OK:
            try:
                intended_config = self._render_config_nornir_serial(
                    device=device,
                    jinja_template=filesystem_path.name,
                    jinja_root_path=filesystem_path.parent,
                    graphql_data=context,
                )
            except Exception as exc:
                raise GenerateIntendedConfigException(f"Error rendering Jinja template: {exc}") from exc
            return Response(
                data={
                    "intended_config": intended_config,
                    "intended_config_lines": intended_config.split("\n"),
                },
                status=status.HTTP_200_OK,
            )

        raise GenerateIntendedConfigException("Unable to generate the intended config for this device")

    def _render_config_nornir_serial(self, device, jinja_template, jinja_root_path, graphql_data):
        """Render the Jinja template for the device using Nornir serial runner.

        This is a small stub of the logic in nornir_plays.config_intended.config_intended.
        """
        jinja_env = get_django_env()
        with InitNornir(
            runner={"plugin": "serial"},
            logging={"enabled": False},
            inventory={
                "plugin": "nautobot-inventory",
                "options": {
                    "credentials_class": NORNIR_SETTINGS.get("credentials"),
                    "params": NORNIR_SETTINGS.get("inventory_params"),
                    "queryset": Device.objects.filter(pk=device.pk),
                    "defaults": {"now": make_aware(datetime.datetime.now())},
                },
            },
        ) as nornir_obj:
            results = nornir_obj.run(
                task=_nornir_task_inject_graphql_data,
                name="REST API GENERATE CONFIG",
                graphql_data=graphql_data,
                obj=device,  # Used by the nornir tasks for logging to the logger below
                logger=logging.getLogger(
                    dispatcher.__module__
                ),  # The nornir tasks are built for logging to a JobResult, pass a standard logger here
                jinja_template=jinja_template,
                jinja_root_path=jinja_root_path,
                output_file_location="/dev/null",  # The nornir task outputs the templated config to a file, but this API doesn't need it
                jinja_filters=jinja_env.filters,
                jinja_env=jinja_env,
                **dispatch_params(
                    "generate_config", device.platform.network_driver, logging.getLogger(dispatch_params.__module__)
                ),
            )
            if results[device.name].failed:
                if results[device.name].exception:  # pylint: disable=no-else-raise
                    raise results[device.name].exception
                else:
                    raise GenerateIntendedConfigException(
                        f"Error generating intended config for {device.name}: {results[device.name].result}"
                    )
            else:
                return results[device.name][1][1][0].result["config"]
