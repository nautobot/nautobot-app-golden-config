"""Django views for Nautobot Golden Configuration."""  # pylint: disable=too-many-lines

import json
import logging
from datetime import datetime

import yaml
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, ExpressionWrapper, F, FloatField, Max, Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.timezone import make_aware
from django.views.generic import TemplateView, View
from django_pivot.pivot import pivot
from nautobot.apps import views
from nautobot.core.views import generic
from nautobot.core.views.mixins import PERMISSIONS_ACTION_MAP, ObjectPermissionRequiredMixin
from nautobot.dcim.models import Device
from nautobot.extras.models import Job, JobResult
from rest_framework.decorators import action
from rest_framework.response import Response

from nautobot_golden_config import filters, forms, models, tables
from nautobot_golden_config.api import serializers
from nautobot_golden_config.utilities import constant
from nautobot_golden_config.utilities.config_postprocessing import get_config_postprocessing
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import add_message, get_device_to_settings_map
from nautobot_golden_config.utilities.mat_plot import get_global_aggr, plot_barchart_visual, plot_visual

# TODO: Future #4512
PERMISSIONS_ACTION_MAP.update(
    {
        "backup": "view",
        "compliance": "view",
        "intended": "view",
        "sotagg": "view",
        "postprocessing": "view",
        "devicetab": "view",
    }
)
LOGGER = logging.getLogger(__name__)

#
# GoldenConfig
#


class GoldenConfigUIViewSet(  # pylint: disable=abstract-method
    views.ObjectDetailViewMixin,
    views.ObjectDestroyViewMixin,
    views.ObjectBulkDestroyViewMixin,
    views.ObjectListViewMixin,  # TODO: Changing the order of the mixins breaks things... why?
):
    """Views for the GoldenConfig model."""

    bulk_update_form_class = forms.GoldenConfigBulkEditForm
    table_class = tables.GoldenConfigTable
    filterset_class = filters.GoldenConfigFilterSet
    filterset_form_class = forms.GoldenConfigFilterForm
    queryset = models.GoldenConfig.objects.all()
    serializer_class = serializers.GoldenConfigSerializer
    action_buttons = ("export",)

    def __init__(self, *args, **kwargs):
        """Used to set default variables on GoldenConfigUIViewSet."""
        super().__init__(*args, **kwargs)
        self.device = None
        self.output = ""
        self.structured_format = None
        self.title_name = None
        self.is_modal = None
        self.config_details = None
        self.action_template_name = None

    def filter_queryset(self, queryset):
        """Add a warning message when GoldenConfig Table is out of sync."""
        queryset = super().filter_queryset(queryset)
        # Only adding a message when no filters are applied
        if self.filter_params:
            return queryset

        sync_job = Job.objects.get(
            module_name="nautobot_golden_config.jobs", job_class_name="SyncGoldenConfigWithDynamicGroups"
        )
        sync_job_url = f"<a href='{reverse('extras:job_run', kwargs={'pk': sync_job.pk})}'>{sync_job.name}</a>"
        out_of_sync_message = format_html(
            "The expected devices and actual devices here are not in sync. "
            f"Running the job {sync_job_url} will put it back in sync."
        )

        gc_dynamic_group_device_pks = models.GoldenConfig.get_dynamic_group_device_pks()
        gc_device_pks = models.GoldenConfig.get_golden_config_device_ids()
        if gc_dynamic_group_device_pks != gc_device_pks:
            messages.warning(self.request, message=out_of_sync_message)

        return queryset

    def get_extra_context(self, request, instance=None, **kwargs):
        """Get extra context data."""
        context = super().get_extra_context(request, instance)
        context["compliance"] = constant.ENABLE_COMPLIANCE
        context["backup"] = constant.ENABLE_BACKUP
        context["intended"] = constant.ENABLE_INTENDED
        jobs = []
        jobs.append(["BackupJob", constant.ENABLE_BACKUP])
        jobs.append(["IntendedJob", constant.ENABLE_INTENDED])
        jobs.append(["ComplianceJob", constant.ENABLE_COMPLIANCE])
        add_message(jobs, request)
        return context

    def _pre_helper(self, pk, request):
        self.device = Device.objects.get(pk=pk)
        self.config_details = models.GoldenConfig.objects.filter(device=self.device).first()
        self.action_template_name = "nautobot_golden_config/goldenconfig_details.html"
        self.structured_format = "json"
        self.is_modal = False
        if request.GET.get("modal") == "true":
            self.action_template_name = "nautobot_golden_config/goldenconfig_detailsmodal.html"
            self.is_modal = True

    def _post_render(self, request):
        context = {
            "output": self.output,
            "device": self.device,
            "device_name": self.device.name,
            "format": self.structured_format,
            "title_name": self.title_name,
            "is_modal": self.is_modal,
        }
        return render(request, self.action_template_name, context)

    @action(detail=True, methods=["get"])
    def backup(self, request, pk, *args, **kwargs):
        """Additional action to handle backup_config."""
        self._pre_helper(pk, request)
        self.output = self.config_details.backup_config
        self.structured_format = "cli"
        self.title_name = "Backup Configuration Details"
        return self._post_render(request)

    @action(detail=True, methods=["get"])
    def intended(self, request, pk, *args, **kwargs):
        """Additional action to handle intended_config."""
        self._pre_helper(pk, request)
        self.output = self.config_details.intended_config
        self.structured_format = "cli"
        self.title_name = "Intended Configuration Details"
        return self._post_render(request)

    @action(detail=True, methods=["get"])
    def postprocessing(self, request, pk, *args, **kwargs):
        """Additional action to handle postprocessing."""
        self._pre_helper(pk, request)
        self.output = get_config_postprocessing(self.config_details, request)
        self.structured_format = "cli"
        self.title_name = "Post Processing"
        return self._post_render(request)

    @action(detail=True, methods=["get"])
    def sotagg(self, request, pk, *args, **kwargs):
        """Additional action to handle sotagg."""
        self._pre_helper(pk, request)
        self.structured_format = "json"
        if request.GET.get("format") in ["json", "yaml"]:
            self.structured_format = request.GET.get("format")

        settings = get_device_to_settings_map(queryset=Device.objects.filter(pk=self.device.pk))
        if self.device.id in settings:
            sot_agg_query_setting = settings[self.device.id].sot_agg_query
            if sot_agg_query_setting is not None:
                _, self.output = graph_ql_query(request, self.device, sot_agg_query_setting.query)
            else:
                self.output = {"Error": "No saved `GraphQL Query` query was configured in the `Golden Config Setting`"}
        else:
            raise ObjectDoesNotExist(f"{self.device.name} does not map to a Golden Config Setting.")

        if self.structured_format == "yaml":
            self.output = yaml.dump(json.loads(json.dumps(self.output)), default_flow_style=False)
        else:
            self.output = json.dumps(self.output, indent=4)
        self.title_name = "Aggregate Data"
        return self._post_render(request)

    @action(detail=True, methods=["get"])
    def compliance(self, request, pk, *args, **kwargs):
        """Additional action to handle compliance."""
        self._pre_helper(pk, request)

        self.output = self.config_details.compliance_config
        if self.config_details.backup_last_success_date:
            backup_date = str(self.config_details.backup_last_success_date.strftime("%b %d %Y"))
        else:
            backup_date = make_aware(datetime.now()).strftime("%b %d %Y")
        if self.config_details.intended_last_success_date:
            intended_date = str(self.config_details.intended_last_success_date.strftime("%b %d %Y"))
        else:
            intended_date = make_aware(datetime.now()).strftime("%b %d %Y")

        diff_type = "File"
        self.structured_format = "diff"

        if self.output == "":
            # This is used if all config snippets are in compliance and no diff exist.
            self.output = f"--- Backup {diff_type} - " + backup_date + f"\n+++ Intended {diff_type} - " + intended_date
        else:
            first_occurence = self.output.index("@@")
            second_occurence = self.output.index("@@", first_occurence)
            # This is logic to match diff2html's expected input.
            self.output = (
                f"--- Backup {diff_type} - "
                + backup_date
                + f"\n+++ Intended {diff_type} - "
                + intended_date
                + "\n"
                + self.output[first_occurence:second_occurence]
                + "@@"
                + self.output[second_occurence + 2 :]  # noqa: E203
            )
        self.title_name = "Compliance Details"
        return self._post_render(request)


#
# ConfigCompliance
#


class ConfigComplianceUIViewSet(  # pylint: disable=abstract-method
    views.ObjectDetailViewMixin,
    views.ObjectDestroyViewMixin,
    views.ObjectBulkDestroyViewMixin,
    views.ObjectListViewMixin,
):
    """Views for the ConfigCompliance model."""

    filterset_class = filters.ConfigComplianceFilterSet
    filterset_form_class = forms.ConfigComplianceFilterForm
    queryset = models.ConfigCompliance.objects.all().order_by("device__name")
    serializer_class = serializers.ConfigComplianceSerializer
    table_class = tables.ConfigComplianceTable
    table_delete_class = tables.ConfigComplianceDeleteTable

    custom_action_permission_map = None
    action_buttons = ("export",)

    def __init__(self, *args, **kwargs):
        """Used to set default variables on ConfigComplianceUIViewSet."""
        super().__init__(*args, **kwargs)
        self.pk_list = None
        self.report_context = None
        self.store_table = None  # Used to store the table for bulk delete. No longer required in Nautobot 2.3.11

    def get_extra_context(self, request, instance=None, **kwargs):
        """A ConfigCompliance helper function to warn if the Job is not enabled to run."""
        context = super().get_extra_context(request, instance)
        if self.action == "overview":
            context = {**context, **self.report_context}
        # TODO Remove when dropping support for Nautobot < 2.3.11
        if self.action == "bulk_destroy":
            context["table"] = self.store_table

        context["compliance"] = constant.ENABLE_COMPLIANCE
        context["backup"] = constant.ENABLE_BACKUP
        context["intended"] = constant.ENABLE_INTENDED
        add_message([["ComplianceJob", constant.ENABLE_COMPLIANCE]], request)
        return context

    def alter_queryset(self, request):
        """Build actual runtime queryset as the build time queryset of table `pivoted`."""
        return pivot(
            self.queryset,
            ["device", "device__name"],
            "rule__feature__slug",
            "compliance_int",
            aggregation=Max,
        )

    def perform_bulk_destroy(self, request, **kwargs):
        """Overwrite perform_bulk_destroy to handle special use case in which the UI shows devices but want to delete ConfigCompliance objects."""
        model = self.queryset.model
        # Are we deleting *all* objects in the queryset or just a selected subset?
        if request.POST.get("_all"):
            filter_params = self.get_filter_params(request)
            if not filter_params:
                compliance_objects = model.objects.only("pk").all().values_list("pk", flat=True)
            elif self.filterset_class is None:
                raise NotImplementedError("filterset_class must be defined to use _all")
            else:
                compliance_objects = self.filterset_class(filter_params, model.objects.only("pk")).qs
            # When selecting *all* the resulting request args are ConfigCompliance object PKs
            self.pk_list = [item[0] for item in self.queryset.filter(pk__in=compliance_objects).values_list("id")]
        elif "_confirm" not in request.POST:
            # When it is not being confirmed, the pk's are the device objects.
            device_objects = request.POST.getlist("pk")
            self.pk_list = [item[0] for item in self.queryset.filter(device__pk__in=device_objects).values_list("id")]
        else:
            self.pk_list = request.POST.getlist("pk")

        form_class = self.get_form_class(**kwargs)
        data = {}
        if "_confirm" in request.POST:
            form = form_class(request.POST)
            if form.is_valid():
                return self.form_valid(form)
            return self.form_invalid(form)

        table = self.table_delete_class(self.queryset.filter(pk__in=self.pk_list), orderable=False)

        if not table.rows:
            messages.warning(
                request,
                f"No {self.queryset.model._meta.verbose_name_plural} were selected for deletion.",
            )
            return redirect(self.get_return_url(request))

        # TODO Remove when dropping support for Nautobot < 2.3.11
        self.store_table = table

        if not request.POST.get("_all"):
            data.update({"table": table, "total_objs_to_delete": len(table.rows)})
        else:
            data.update({"table": None, "delete_all": True, "total_objs_to_delete": len(table.rows)})
        return Response(data)

    @action(detail=True, methods=["get"])
    def devicetab(self, request, pk, *args, **kwargs):
        """Additional action to handle backup_config."""
        device = Device.objects.get(pk=pk)
        context = {}
        compliance_details = models.ConfigCompliance.objects.filter(device=device)
        context["compliance_details"] = compliance_details
        if request.GET.get("compliance") == "compliant":
            context["compliance_details"] = compliance_details.filter(compliance=True)
        elif request.GET.get("compliance") == "non-compliant":
            context["compliance_details"] = compliance_details.filter(compliance=False)

        context["active_tab"] = request.GET.get("tab")
        context["device"] = device
        context["object"] = device
        context["verbose_name"] = "Device"
        return render(request, "nautobot_golden_config/configcompliance_devicetab.html", context)


class ConfigComplianceOverview(generic.ObjectListView):
    """View for executive report on configuration compliance."""

    action_buttons = ("export",)
    filterset = filters.ConfigComplianceFilterSet
    filterset_form = forms.ConfigComplianceFilterForm
    table = tables.ConfigComplianceGlobalFeatureTable
    template_name = "nautobot_golden_config/configcompliance_overview.html"
    # kind = "Features"

    queryset = (
        models.ConfigCompliance.objects.values("rule__feature__slug")
        .annotate(
            count=Count("rule__feature__slug"),
            compliant=Count("rule__feature__slug", filter=Q(compliance=True)),
            non_compliant=Count("rule__feature__slug", filter=~Q(compliance=True)),
            comp_percent=ExpressionWrapper(100 * F("compliant") / F("count"), output_field=FloatField()),
        )
        .order_by("-comp_percent")
    )
    extra_content = {}

    # Once https://github.com/nautobot/nautobot/issues/4529 is addressed, can turn this on.
    # Permalink reference: https://github.com/nautobot/nautobot-app-golden-config/blob/017d5e1526fa9f642b9e02bfc7161f27d4948bef/nautobot_golden_config/views.py#L383
    # @action(detail=False, methods=["get"])
    # def overview(self, request, *args, **kwargs):
    def setup(self, request, *args, **kwargs):
        """Using request object to perform filtering based on query params."""
        super().setup(request, *args, **kwargs)
        filter_params = self.get_filter_params(request)
        main_qs = models.ConfigCompliance.objects
        device_aggr, feature_aggr = get_global_aggr(main_qs, self.filterset, filter_params)
        feature_qs = self.filterset(request.GET, self.queryset).qs
        self.extra_content = {
            "bar_chart": plot_barchart_visual(feature_qs),
            "device_aggr": device_aggr,
            "device_visual": plot_visual(device_aggr),
            "feature_aggr": feature_aggr,
            "feature_visual": plot_visual(feature_aggr),
            "compliance": constant.ENABLE_COMPLIANCE,
        }

    def extra_context(self):
        """Extra content method on."""
        # add global aggregations to extra context.
        return self.extra_content


class ComplianceFeatureUIViewSet(views.NautobotUIViewSet):
    """Views for the ComplianceFeature model."""

    bulk_update_form_class = forms.ComplianceFeatureBulkEditForm
    filterset_class = filters.ComplianceFeatureFilterSet
    filterset_form_class = forms.ComplianceFeatureFilterForm
    form_class = forms.ComplianceFeatureForm
    queryset = models.ComplianceFeature.objects.all()
    serializer_class = serializers.ComplianceFeatureSerializer
    table_class = tables.ComplianceFeatureTable
    lookup_field = "pk"

    def get_extra_context(self, request, instance=None):
        """A ComplianceFeature helper function to warn if the Job is not enabled to run."""
        add_message([["ComplianceJob", constant.ENABLE_COMPLIANCE]], request)
        return {}


class ComplianceRuleUIViewSet(views.NautobotUIViewSet):
    """Views for the ComplianceRule model."""

    bulk_update_form_class = forms.ComplianceRuleBulkEditForm
    filterset_class = filters.ComplianceRuleFilterSet
    filterset_form_class = forms.ComplianceRuleFilterForm
    form_class = forms.ComplianceRuleForm
    queryset = models.ComplianceRule.objects.all()
    serializer_class = serializers.ComplianceRuleSerializer
    table_class = tables.ComplianceRuleTable
    lookup_field = "pk"

    def get_extra_context(self, request, instance=None):
        """A ComplianceRule helper function to warn if the Job is not enabled to run."""
        add_message([["ComplianceJob", constant.ENABLE_COMPLIANCE]], request)
        return {}


class GoldenConfigSettingUIViewSet(views.NautobotUIViewSet):
    """Views for the GoldenConfigSetting model."""

    bulk_update_form_class = forms.GoldenConfigSettingBulkEditForm
    filterset_class = filters.GoldenConfigSettingFilterSet
    filterset_form_class = forms.GoldenConfigSettingFilterForm
    form_class = forms.GoldenConfigSettingForm
    queryset = models.GoldenConfigSetting.objects.all()
    serializer_class = serializers.GoldenConfigSettingSerializer
    table_class = tables.GoldenConfigSettingTable
    lookup_field = "pk"

    def get_extra_context(self, request, instance=None):
        """A GoldenConfig helper function to warn if the Job is not enabled to run."""
        jobs = []
        jobs.append(["BackupJob", constant.ENABLE_BACKUP])
        jobs.append(["IntendedJob", constant.ENABLE_INTENDED])
        jobs.append(["DeployConfigPlans", constant.ENABLE_DEPLOY])
        jobs.append(["ComplianceJob", constant.ENABLE_COMPLIANCE])
        jobs.append(
            [
                "AllGoldenConfig",
                [
                    constant.ENABLE_BACKUP,
                    constant.ENABLE_COMPLIANCE,
                    constant.ENABLE_DEPLOY,
                    constant.ENABLE_INTENDED,
                    constant.ENABLE_SOTAGG,
                ],
            ]
        )
        jobs.append(
            [
                "AllDevicesGoldenConfig",
                [
                    constant.ENABLE_BACKUP,
                    constant.ENABLE_COMPLIANCE,
                    constant.ENABLE_DEPLOY,
                    constant.ENABLE_INTENDED,
                    constant.ENABLE_SOTAGG,
                ],
            ]
        )
        add_message(jobs, request)
        return {}


class ConfigRemoveUIViewSet(views.NautobotUIViewSet):
    """Views for the ConfigRemove model."""

    bulk_update_form_class = forms.ConfigRemoveBulkEditForm
    filterset_class = filters.ConfigRemoveFilterSet
    filterset_form_class = forms.ConfigRemoveFilterForm
    form_class = forms.ConfigRemoveForm
    queryset = models.ConfigRemove.objects.all()
    serializer_class = serializers.ConfigRemoveSerializer
    table_class = tables.ConfigRemoveTable
    lookup_field = "pk"

    def get_extra_context(self, request, instance=None):
        """A ConfigRemove helper function to warn if the Job is not enabled to run."""
        add_message([["BackupJob", constant.ENABLE_BACKUP]], request)
        return {}


class ConfigReplaceUIViewSet(views.NautobotUIViewSet):
    """Views for the ConfigReplace model."""

    bulk_update_form_class = forms.ConfigReplaceBulkEditForm
    filterset_class = filters.ConfigReplaceFilterSet
    filterset_form_class = forms.ConfigReplaceFilterForm
    form_class = forms.ConfigReplaceForm
    queryset = models.ConfigReplace.objects.all()
    serializer_class = serializers.ConfigReplaceSerializer
    table_class = tables.ConfigReplaceTable
    lookup_field = "pk"

    def get_extra_context(self, request, instance=None):
        """A ConfigReplace helper function to warn if the Job is not enabled to run."""
        add_message([["BackupJob", constant.ENABLE_BACKUP]], request)
        return {}


class RemediationSettingUIViewSet(views.NautobotUIViewSet):
    """Views for the RemediationSetting model."""

    # bulk_create_form_class = forms.RemediationSettingCSVForm
    bulk_update_form_class = forms.RemediationSettingBulkEditForm
    filterset_class = filters.RemediationSettingFilterSet
    filterset_form_class = forms.RemediationSettingFilterForm
    form_class = forms.RemediationSettingForm
    queryset = models.RemediationSetting.objects.all()
    serializer_class = serializers.RemediationSettingSerializer
    table_class = tables.RemediationSettingTable
    lookup_field = "pk"

    def get_extra_context(self, request, instance=None):
        """A RemediationSetting helper function to warn if the Job is not enabled to run."""
        add_message([["ComplianceJob", constant.ENABLE_COMPLIANCE]], request)
        return {}


class ConfigPlanUIViewSet(views.NautobotUIViewSet):
    """Views for the ConfigPlan model."""

    bulk_update_form_class = forms.ConfigPlanBulkEditForm
    filterset_class = filters.ConfigPlanFilterSet
    filterset_form_class = forms.ConfigPlanFilterForm
    form_class = forms.ConfigPlanForm
    queryset = models.ConfigPlan.objects.all()
    serializer_class = serializers.ConfigPlanSerializer
    table_class = tables.ConfigPlanTable
    lookup_field = "pk"
    action_buttons = ("add",)
    update_form_class = forms.ConfigPlanUpdateForm

    def alter_queryset(self, request):
        """Build actual runtime queryset to automatically remove `Completed` by default."""
        if "Completed" not in request.GET.getlist("status"):
            return self.queryset.exclude(status__name="Completed")
        return self.queryset

    def get_extra_context(self, request, instance=None):
        """A ConfigPlan helper function to warn if the Job is not enabled to run."""
        jobs = []
        jobs.append(["GenerateConfigPlans", constant.ENABLE_PLAN])
        jobs.append(["DeployConfigPlans", constant.ENABLE_DEPLOY])
        jobs.append(["DeployConfigPlanJobButtonReceiver", constant.ENABLE_DEPLOY])
        add_message(jobs, request)
        return {}


class ConfigPlanBulkDeploy(ObjectPermissionRequiredMixin, View):
    """View to run the Config Plan Deploy Job."""

    queryset = models.ConfigPlan.objects.all()

    def get_required_permission(self):
        """Permissions required for the view."""
        return "extras.run_job"

    # Once https://github.com/nautobot/nautobot/issues/4529 is addressed, can turn this on.
    # Permalink reference: https://github.com/nautobot/nautobot-app-golden-config/blob/017d5e1526fa9f642b9e02bfc7161f27d4948bef/nautobot_golden_config/views.py#L609-L612
    # @action(detail=False, methods=["post"])
    # def bulk_deploy(self, request):
    def post(self, request):
        """Enqueue the job and redirect to the job results page."""
        config_plan_pks = request.POST.getlist("pk")
        if not config_plan_pks:
            messages.warning(request, "No Config Plans selected for deployment.")
            return redirect("plugins:nautobot_golden_config:configplan_list")

        job_data = {"config_plan": config_plan_pks}
        job = Job.objects.get(name="Generate Config Plans")

        job_result = JobResult.enqueue_job(
            job,
            request.user,
            data=job_data,
            **job.job_class.serialize_data(request),
        )
        return redirect(job_result.get_absolute_url())


class GenerateIntendedConfigView(PermissionRequiredMixin, TemplateView):
    """View to generate the intended configuration."""

    template_name = "nautobot_golden_config/generate_intended_config.html"
    permission_required = ["dcim.view_device", "extras.view_gitrepository"]

    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        context["form"] = forms.GenerateIntendedConfigForm()
        return context
