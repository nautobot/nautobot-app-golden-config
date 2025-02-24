"""API views for nautobot_golden_config."""

import datetime
import difflib
import logging
from pathlib import Path

from django.conf import settings as nautobot_settings
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from jinja2.exceptions import TemplateError, TemplateSyntaxError
from nautobot.apps.api import NautobotModelViewSet, NotesViewSetMixin
from nautobot.apps.utils import render_jinja2
from nautobot.core.api.views import (
    BulkDestroyModelMixin,
    BulkUpdateModelMixin,
    ModelViewSetMixin,
    NautobotAPIVersionMixin,
)
from nautobot.dcim.models import Device
from nautobot.extras.datasources.git import ensure_git_repository
from nautobot.extras.models import GitRepository, GraphQLQuery
from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nornir import InitNornir
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher
from packaging import version
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.viewsets import GenericViewSet

from nautobot_golden_config import filters, models
from nautobot_golden_config.api import serializers
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import dispatch_params, get_django_env


class GoldenConfigRootView(APIRootView):
    """Golden Config API root view."""

    def get_view_name(self):
        """Golden Config API root view boilerplate."""
        return "Golden Config"


class SOTAggDeviceDetailView(NautobotAPIVersionMixin, GenericAPIView):
    """Detail REST API view showing graphql, with a potential "transformer" of data on a specific device."""

    name = "SOTAgg Device View"
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.GraphQLSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="graphql_query_id",
                required=False,
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """Get GraphQL data for a Device."""
        device = get_object_or_404(Device.objects.restrict(request.user, "view"), pk=kwargs["pk"])

        graphql_query = None
        graphql_query_id_param = request.query_params.get("graphql_query_id")
        if graphql_query_id_param:
            try:
                graphql_query = GraphQLQuery.objects.get(pk=graphql_query_id_param)
            except GraphQLQuery.DoesNotExist as exc:
                raise ValidationError(f"GraphQLQuery with id '{graphql_query_id_param}' not found") from exc
        settings = models.GoldenConfigSetting.objects.get_for_device(device)

        if graphql_query is None:
            if settings.sot_agg_query is not None:
                graphql_query = settings.sot_agg_query
            else:
                raise ValidationError("Golden Config settings sot_agg_query not set")

        if "device_id" not in graphql_query.variables:
            raise ValidationError("The selected GraphQL query is missing a 'device_id' variable")

        status_code, graphql_data = graph_ql_query(request, device, graphql_query.query)
        if status_code == status.HTTP_200_OK:
            return Response(
                data=graphql_data,
                status=status.HTTP_200_OK,
            )

        raise ValidationError("Unable to generate the GraphQL data for this device")


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

    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]


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

    def _get_diff(self, device, intended_config):
        """Generate a unified diff between the provided config and the intended config stored on the Device's GoldenConfig.intended_config."""
        diff = None
        try:
            golden_config = device.goldenconfig
            if golden_config.intended_last_success_date is not None:
                prior_intended_config = golden_config.intended_config
                diff = "".join(
                    difflib.unified_diff(
                        prior_intended_config.splitlines(keepends=True),
                        intended_config.splitlines(keepends=True),
                        fromfile="prior intended config",
                        tofile="rendered config",
                    )
                )
        except models.GoldenConfig.DoesNotExist:
            pass

        return diff

    def _get_object(self, request, model, query_param):
        """Get the requested model instance, restricted to requesting user."""
        pk = request.query_params.get(query_param)
        if not pk:
            raise GenerateIntendedConfigException(f"Parameter {query_param} is required")
        try:
            return model.objects.restrict(request.user, "view").get(pk=pk)
        except model.DoesNotExist as exc:
            raise GenerateIntendedConfigException(f"{model.__name__} with id '{pk}' not found") from exc

    def _get_jinja_template_path(self, settings, device, git_repository, base_path=None):
        """Get the Jinja template path for the device in the provided git repository."""
        try:
            rendered_path = render_jinja2(template_code=settings.jinja_path_template, context={"obj": device})
        except (TemplateSyntaxError, TemplateError) as exc:
            raise GenerateIntendedConfigException("Error rendering Jinja path template") from exc
        if base_path is None:
            filesystem_path = Path(git_repository.filesystem_path) / rendered_path
        else:
            filesystem_path = Path(base_path) / rendered_path
        if not filesystem_path.is_file():
            msg = f"Jinja template {rendered_path} not found in git repository {git_repository}"
            raise GenerateIntendedConfigException(msg)
        return filesystem_path

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="branch",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="device_id",
                required=True,
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="graphql_query_id",
                required=False,
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):  # pylint: disable=too-many-locals, too-many-branches
        """Generate intended configuration for a Device."""
        device = self._get_object(request, Device, "device_id")
        branch_param = request.query_params.get("branch")
        if branch_param and version.parse(nautobot_settings.VERSION) < version.parse("2.4.2"):
            raise GenerateIntendedConfigException("Branch support requires Nautobot v2.4.2 or later")
        graphql_query = None
        graphql_query_id_param = request.query_params.get("graphql_query_id")
        if graphql_query_id_param:
            try:
                graphql_query = GraphQLQuery.objects.get(pk=graphql_query_id_param)
            except GraphQLQuery.DoesNotExist as exc:
                raise GenerateIntendedConfigException(
                    f"GraphQLQuery with id '{graphql_query_id_param}' not found"
                ) from exc
        settings = models.GoldenConfigSetting.objects.get_for_device(device)
        if not settings:
            raise GenerateIntendedConfigException("No Golden Config settings found for this device")
        if not settings.jinja_repository:
            raise GenerateIntendedConfigException("Golden Config settings jinja_repository not set")

        if graphql_query is None:
            if settings.sot_agg_query is not None:
                graphql_query = settings.sot_agg_query
            else:
                raise GenerateIntendedConfigException("Golden Config settings sot_agg_query not set")

        if "device_id" not in graphql_query.variables:
            raise GenerateIntendedConfigException("The selected GraphQL query is missing a 'device_id' variable")

        try:
            git_repository = settings.jinja_repository
            ensure_git_repository(git_repository)
        except Exception as exc:
            raise GenerateIntendedConfigException("Error trying to sync git repository") from exc

        status_code, graphql_data = graph_ql_query(request, device, graphql_query.query)
        if status_code == status.HTTP_200_OK:
            try:
                if branch_param:
                    with git_repository.clone_to_directory_context(branch=branch_param, depth=1) as git_repo_path:
                        filesystem_path = self._get_jinja_template_path(
                            settings, device, git_repository, base_path=git_repo_path
                        )
                        intended_config = self._render_config_nornir_serial(
                            device=device,
                            jinja_template=filesystem_path.name,
                            jinja_root_path=filesystem_path.parent,
                            graphql_data=graphql_data,
                        )
                else:
                    filesystem_path = self._get_jinja_template_path(settings, device, git_repository)
                    intended_config = self._render_config_nornir_serial(
                        device=device,
                        jinja_template=filesystem_path.name,
                        jinja_root_path=filesystem_path.parent,
                        graphql_data=graphql_data,
                    )
            except Exception as exc:
                raise GenerateIntendedConfigException(f"Error rendering Jinja template: {exc}") from exc

            diff = self._get_diff(device, intended_config)

            return Response(
                data={
                    "intended_config": intended_config,
                    "intended_config_lines": intended_config.split("\n"),
                    "graphql_data": graphql_data,
                    "diff": diff,
                    "diff_lines": diff.split("\n") if diff else [],
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


@extend_schema(exclude=True)
class GitRepositoryBranchesView(NautobotAPIVersionMixin, RetrieveAPIView):
    """API view for extras.GitRepository with branches."""

    name = "Git Repository with Branches"
    permission_classes = [IsAuthenticated]
    queryset = GitRepository.objects.all()
    serializer_class = serializers.GitRepositoryWithBranchesSerializer

    def get_queryset(self):
        """Override the original get_queryset to apply permissions."""
        queryset = super().get_queryset()
        return queryset.restrict(self.request.user, "view")
