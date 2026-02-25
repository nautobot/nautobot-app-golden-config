"""Django views for Nautobot Golden Configuration."""  # pylint: disable=too-many-lines

import json
import logging
from datetime import datetime

import yaml
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Exists, ExpressionWrapper, F, FloatField, Max, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.timezone import make_aware
from django.views.generic import TemplateView, View
from django_pivot.pivot import pivot
from django_tables2 import RequestConfig
from nautobot.apps import views
from nautobot.apps.ui import (
    EChartsPanel,
    EChartsThemeColors,
    EChartsTypeChoices,
    queryset_to_nested_dict_keys_as_series,
)
from nautobot.core.views.mixins import PERMISSIONS_ACTION_MAP, ObjectDataComplianceViewMixin
from nautobot.dcim.models import Device
from nautobot.dcim.views import DeviceUIViewSet
from nautobot.extras.models import Job, JobResult
from rest_framework.decorators import action
from rest_framework.response import Response

from nautobot_golden_config import details, filters, forms, models, tables
from nautobot_golden_config.api import serializers
from nautobot_golden_config.utilities import constant
from nautobot_golden_config.utilities.config_postprocessing import get_config_postprocessing
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import add_message, calculate_aggr_percentage, get_device_to_settings_map

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
    ObjectDataComplianceViewMixin,  # TODO: Import from views after nautobot release
):
    """Views for the GoldenConfig model."""

    bulk_update_form_class = forms.GoldenConfigBulkEditForm
    table_class = tables.GoldenConfigTable
    filterset_class = filters.GoldenConfigFilterSet
    filterset_form_class = forms.GoldenConfigFilterForm
    queryset = models.GoldenConfig.objects.all()
    serializer_class = serializers.GoldenConfigSerializer
    action_buttons = ("export",)
    object_detail_content = details.golden_config

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

    def _get_device_context(self, instance):
        return {
            "Backup Config": reverse(
                "plugins:nautobot_golden_config:goldenconfig_backup", kwargs={"pk": instance.device.pk}
            ),
            "Intended Config": reverse(
                "plugins:nautobot_golden_config:goldenconfig_intended", kwargs={"pk": instance.device.pk}
            ),
            "Compliance Config": reverse(
                "plugins:nautobot_golden_config:goldenconfig_compliance", kwargs={"pk": instance.device.pk}
            ),
        }

    def get_extra_context(self, request, instance=None):
        """Get extra context data."""
        context = super().get_extra_context(request, instance)
        if self.action == "retrieve":
            context["device_object"] = self._get_device_context(instance)
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
        if request.GET.get("config_plan_id"):
            self.config_details = models.ConfigPlan.objects.get(id=request.GET.get("config_plan_id"))
        else:
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
    object_detail_content = details.config_compliance
    queryset_report_for_table = (
        models.ConfigCompliance.objects.values("rule__feature__slug")
        .annotate(
            count=Count("rule__feature__slug"),
            compliant=Count("rule__feature__slug", filter=Q(compliance=True)),
            non_compliant=Count("rule__feature__slug", filter=~Q(compliance=True)),
            comp_percent=ExpressionWrapper(100 * F("compliant") / F("count"), output_field=FloatField()),
        )
        .order_by("-comp_percent")
    )
    queryset_report_for_chart = models.ConfigCompliance.objects.annotate(
        count=Count("rule__feature__slug"),
        compliant=Count("rule__feature__slug", filter=Q(compliance=True)),
        non_compliant=Count("rule__feature__slug", filter=~Q(compliance=True)),
        comp_percent=ExpressionWrapper(100 * F("compliant") / F("count"), output_field=FloatField()),
    ).order_by("-comp_percent")

    def __init__(self, *args, **kwargs):
        """Used to set default variables on ConfigComplianceUIViewSet."""
        super().__init__(*args, **kwargs)
        self.pk_list = None
        self.report_context = None
        self.store_table = None  # Used to store the table for bulk delete. No longer required in Nautobot 2.3.11

    def get_extra_context(self, request, instance=None):
        """A ConfigCompliance helper function to warn if the Job is not enabled to run."""
        context = super().get_extra_context(request, instance)
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
        # Super because alter_queryset() calls get_queryset(), which is what calls queryset.restrict()
        self.queryset = super().alter_queryset(request)
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
            context["compliance_filter"] = "compliant"
            context["compliance_details"] = compliance_details.filter(compliance=True)
        elif request.GET.get("compliance") == "non-compliant":
            context["compliance_filter"] = "non-compliant"
            context["compliance_details"] = compliance_details.filter(compliance=False)

        context["active_tab"] = request.GET.get("tab")
        context["device"] = device
        context["object"] = device
        context["object_detail_content"] = DeviceUIViewSet.object_detail_content
        context["verbose_name"] = "Device"

        return render(request, "nautobot_golden_config/configcompliance_devicetab.html", context)

    @action(detail=False, methods=["get"], custom_view_base_action="view")
    def overview(self, request, *args, **kwargs):  # pylint: disable=too-many-locals
        """Custom action to show the visual report of the compliance stats."""
        # Basic Setup
        context = {}
        theme = request.COOKIES["theme"] if "theme" in request.COOKIES else "light"
        if theme not in ["light", "dark"]:
            theme = "light"
        filter_params = self.get_filter_params(request)

        # Table Setup
        filterset = self.filterset_class(request.GET, self.queryset_report_for_table)
        table = tables.ConfigComplianceGlobalFeatureTable(filterset.qs, user=request.user)
        paginate = {
            "paginator_class": views.EnhancedPaginator,
            "per_page": views.get_paginate_count(request),
        }
        RequestConfig(request, paginate).configure(table)

        context["filterset"] = filterset
        context["table"] = table
        context["filter_form"] = self.filterset_form_class
        context["action_buttons"] = ("export",)
        context["filter"] = self.filterset_class

        # Bar Chart Setup
        feature_qs = self.filterset_class(request.GET, self.queryset_report_for_chart).qs
        chart_data = queryset_to_nested_dict_keys_as_series(
            feature_qs,
            record_key="rule__feature__slug",  # becomes the x-axis
            value_keys=["compliant", "non_compliant"],  # becomes the series names
        )
        bar_chart_panel = EChartsPanel(
            label="Compliance Overview",
            weight=100,
            chart_kwargs={
                "chart_type": EChartsTypeChoices.BAR,
                "header": "Compliance per Feature",
                "description": "This shows the compliance status for each feature.",
                "theme_colors": EChartsThemeColors.LIGHTER_GREEN_RED_COLORS,
                "data": chart_data,
            },
        )
        context["bar_chart_panel"] = [bar_chart_panel]

        # Pie Charts Setup
        main_qs = models.ConfigCompliance.objects

        device_aggr, feature_aggr = {}, {}
        if self.filterset_class is not None:
            device_aggr = (
                self.filterset_class(filter_params, main_qs)
                .qs.values("device")
                .annotate(compliant=Count("device", filter=Q(compliance=False)))
                .aggregate(total=Count("device", distinct=True), compliants=Count("compliant", filter=Q(compliant=0)))
            )

            feature_aggr = self.filterset_class(filter_params, main_qs).qs.aggregate(
                total=Count("rule"), compliants=Count("rule", filter=Q(compliance=True))
            )
        device_aggr = calculate_aggr_percentage(device_aggr)
        feature_aggr = calculate_aggr_percentage(feature_aggr)

        pie_device_panel = EChartsPanel(
            label="Device Compliance Overview",
            weight=100,
            chart_kwargs={
                "chart_type": EChartsTypeChoices.PIE,
                "header": "Compliant vs Non-Compliant Devices",
                "description": "This shows the compliance status on a device level.",
                "theme_colors": EChartsThemeColors.LIGHTER_GREEN_RED_COLORS,
                "data": {
                    "Device Compliance": {
                        "Compliant": device_aggr["compliants"],
                        "Non-Compliant": device_aggr["non_compliants"],
                    }
                },
            },
        )
        context["pie_device_panel"] = [pie_device_panel]

        pie_feature_panel = EChartsPanel(
            label="Feature Compliance Overview",
            weight=100,
            chart_kwargs={
                "chart_type": EChartsTypeChoices.PIE,
                "header": "Compliant vs Non-Compliant Features",
                "description": "This shows the compliance status on a feature level.",
                "theme_colors": EChartsThemeColors.LIGHTER_GREEN_RED_COLORS,
                "data": {
                    "Feature Compliance": {
                        "Compliant": feature_aggr["compliants"],
                        "Non-Compliant": feature_aggr["non_compliants"],
                    }
                },
            },
        )
        context["pie_feature_panel"] = [pie_feature_panel]

        return Response(context)


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
    object_detail_content = details.compliance_feature

    def get_extra_context(self, request, instance=None):
        """A ComplianceFeature helper function to warn if the Job is not enabled to run."""
        add_message([["ComplianceJob", constant.ENABLE_COMPLIANCE]], request)
        return super().get_extra_context(request, instance)


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
    object_detail_content = details.compliance_rule

    def get_extra_context(self, request, instance=None):
        """A ComplianceRule helper function to warn if the Job is not enabled to run."""
        add_message([["ComplianceJob", constant.ENABLE_COMPLIANCE]], request)
        return super().get_extra_context(request, instance)


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
    object_detail_content = details.golden_config_setting
    extra_buttons = ("clone",)

    def get_extra_context(self, request, instance=None):
        """A GoldenConfig helper function to warn if the Job is not enabled to run."""
        context = super().get_extra_context(request, instance)
        if self.action == "retrieve":
            dg = getattr(instance, "dynamic_group", None)
            context["dg_data"] = {"Dynamic Group": dg, "Filter Query Logic": dg.filter, "Scope of Devices": dg}

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
        return context


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
    object_detail_content = details.config_remove

    def get_extra_context(self, request, instance=None):
        """A ConfigRemove helper function to warn if the Job is not enabled to run."""
        add_message([["BackupJob", constant.ENABLE_BACKUP]], request)
        return super().get_extra_context(request, instance)


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
    object_detail_content = details.config_replace

    def get_extra_context(self, request, instance=None):
        """A ConfigReplace helper function to warn if the Job is not enabled to run."""
        add_message([["BackupJob", constant.ENABLE_BACKUP]], request)
        return super().get_extra_context(request, instance)


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
    object_detail_content = details.config_remediation

    def get_extra_context(self, request, instance=None):
        """A RemediationSetting helper function to warn if the Job is not enabled to run."""
        add_message([["ComplianceJob", constant.ENABLE_COMPLIANCE]], request)
        return super().get_extra_context(request, instance)


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
    object_detail_content = details.config_plan

    def alter_queryset(self, request):
        """Build actual runtime queryset to automatically remove `Completed` by default."""
        if "Completed" not in request.GET.getlist("status"):
            return self.queryset.exclude(status__name="Completed")
        return self.queryset

    def get_extra_context(self, request, instance=None):
        """A ConfigPlan helper function to warn if the Job is not enabled to run."""
        context = super().get_extra_context(request, instance)
        jobs = []
        jobs.append(["GenerateConfigPlans", constant.ENABLE_PLAN])
        jobs.append(["DeployConfigPlans", constant.ENABLE_DEPLOY])
        jobs.append(["DeployConfigPlanJobButtonReceiver", constant.ENABLE_DEPLOY])
        add_message(jobs, request)
        return context


class ConfigPlanBulkDeploy(views.ObjectPermissionRequiredMixin, View):
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


class ConfigComplianceHashUIViewSet(views.NautobotUIViewSet):
    """View for configuration hashes with bulk operations."""

    filterset_class = filters.ConfigComplianceHashFilterSet
    filterset_form_class = forms.ConfigComplianceHashFilterForm
    table_class = tables.ConfigComplianceHashTable
    serializer_class = serializers.ConfigComplianceHashSerializer

    action_buttons = []

    # Base queryset of individual ConfigComplianceHash objects
    # Show actual config hashes where there's a corresponding non-compliant ConfigCompliance record
    queryset = (
        models.ConfigComplianceHash.objects.filter(config_type="actual")
        .select_related("device", "rule__feature")
        .filter(
            Exists(
                models.ConfigCompliance.objects.filter(
                    device=OuterRef("device"), rule=OuterRef("rule"), compliance=False
                )
            )
        )
        .distinct()
    )

    def __init__(self, *args, **kwargs):
        """Used to set default variables on ConfigComplianceHashUIViewSet."""
        super().__init__(*args, **kwargs)
        self.pk_list = None

    def get_extra_context(self, request, instance=None, **kwargs):
        """Add extra context for the template."""
        context = super().get_extra_context(request, instance, **kwargs)  # pylint: disable=no-member
        context.update(
            {
                "title": "Configuration Hashes",
                "compliance": constant.ENABLE_COMPLIANCE,
            }
        )
        return context

    def _get_pk_list_for_bulk_destroy(self, request):
        """Extract primary key list based on request parameters."""
        model = self.queryset.model

        if request.POST.get("_all"):
            filter_params = self.get_filter_params(request)
            if not filter_params:
                hash_objects = model.objects.only("pk").all().values_list("pk", flat=True)
            elif self.filterset_class is None:
                raise NotImplementedError("filterset_class must be defined to use _all")
            else:
                hash_objects = self.filterset_class(filter_params, model.objects.only("pk")).qs
            return list(hash_objects.values_list("pk", flat=True))

        return request.POST.getlist("pk")

    def _perform_hash_deletion(self, request):
        """Perform the actual deletion of hash records."""
        if not self.pk_list:
            messages.error(request, "No items selected for deletion.")
            return redirect(self.get_return_url(request))

        # Get the selected ConfigComplianceHash records
        selected_hashes = models.ConfigComplianceHash.objects.filter(pk__in=self.pk_list)

        if not selected_hashes.exists():
            messages.error(request, "Selected items not found.")
            return redirect(self.get_return_url(request))

        # Extract device/rule combinations from selected hashes
        device_rule_combinations = set()
        for hash_record in selected_hashes:
            device_rule_combinations.add((hash_record.device_id, hash_record.rule_id))

        # Delete both actual and intended hashes for the same device/rule combinations
        # Use Q objects to filter by device/rule combinations more reliably
        q_objects = Q()
        for device_id, rule_id in device_rule_combinations:
            q_objects |= Q(device_id=device_id, rule_id=rule_id)

        deleted_count, _ = models.ConfigComplianceHash.objects.filter(q_objects).delete()

        messages.success(
            request,
            f"Successfully deleted {deleted_count} configuration hash records "
            f"(both actual and intended) for {len(device_rule_combinations)} device/rule combinations.",
        )

        return redirect(self.get_return_url(request))

    def perform_bulk_destroy(self, request, **kwargs):
        """Override bulk destroy to delete both actual and intended hashes for the same device/rule combinations."""
        self.pk_list = self._get_pk_list_for_bulk_destroy(request)

        form_class = self.get_form_class(**kwargs)
        data = {}

        if "_confirm" in request.POST:
            form = form_class(request.POST)
            if form.is_valid():
                return self._perform_hash_deletion(request)
            return self.form_invalid(form)

        # Show confirmation page
        table = self.table_class(self.queryset.filter(pk__in=self.pk_list), orderable=False)

        if not table.rows:
            messages.warning(
                request,
                f"No {self.queryset.model._meta.verbose_name_plural} were selected for deletion.",
            )
            return redirect(self.get_return_url(request))

        if not request.POST.get("_all"):
            data.update({"table": table, "total_objs_to_delete": len(table.rows)})
        else:
            data.update({"table": None, "delete_all": True, "total_objs_to_delete": len(table.rows)})

        return Response(data)


class ConfigHashGroupingUIViewSet(views.NautobotUIViewSet):
    """View for configuration hash grouping report."""

    filterset_class = filters.ConfigHashGroupingFilterSet
    filterset_form_class = forms.ConfigHashGroupingFilterForm
    table_class = tables.ConfigHashGroupingTable
    serializer_class = serializers.ConfigHashGroupingSerializer

    # Disable add and import actions since this is a read-only report
    action_buttons = []
    template_name = "nautobot_golden_config/confighashgrouping_list.html"

    queryset = (
        models.ConfigHashGrouping.objects.annotate(
            device_count=Count(
                "hash_records__device",
                distinct=True,
                filter=Q(
                    hash_records__config_type="actual",
                    hash_records__device__configcompliance__rule=F("rule"),
                    hash_records__device__configcompliance__compliance=False,
                ),
            ),
            feature_id=F("rule__feature__id"),
            feature_name=F("rule__feature__name"),
            feature_slug=F("rule__feature__slug"),
        )
        .filter(device_count__gt=1)
        .order_by("-device_count", "rule__feature__name")
    )

    def __init__(self, *args, **kwargs):
        """Used to set default variables on ConfigHashGroupingUIViewSet."""
        super().__init__(*args, **kwargs)
        self.pk_list = None

    def get_extra_context(self, request, instance=None, **kwargs):
        """Add extra context for the template."""
        context = super().get_extra_context(request, instance, **kwargs)  # pylint: disable=no-member
        context.update(
            {
                "title": "Configuration Hash Grouping Report - Multiple Devices",
                "compliance": constant.ENABLE_COMPLIANCE,
            }
        )
        return context

    def perform_bulk_destroy(self, request, **kwargs):  # pylint: disable=too-many-locals
        """Override bulk destroy to cascade delete related ConfigComplianceHash records for each group's rule."""
        model = self.queryset.model

        # Handle the primary key collection like the existing ConfigCompliance bulk delete
        if request.POST.get("_all"):
            filter_params = self.get_filter_params(request)
            if not filter_params:
                hash_group_objects = model.objects.only("pk").all().values_list("pk", flat=True)
            elif self.filterset_class is None:
                raise NotImplementedError("filterset_class must be defined to use _all")
            else:
                hash_group_objects = self.filterset_class(filter_params, model.objects.only("pk")).qs
            self.pk_list = list(hash_group_objects.values_list("pk", flat=True))
        elif "_confirm" not in request.POST:
            # Initial selection - get the pk list from the form
            self.pk_list = request.POST.getlist("pk")
        else:
            # Get the pk list from the form
            self.pk_list = request.POST.getlist("pk")

        form_class = self.get_form_class(**kwargs)
        data = {}

        if "_confirm" in request.POST:
            form = form_class(request.POST)
            if form.is_valid():
                # Perform the actual deletion with cascade
                if not self.pk_list:
                    messages.error(request, "No hash groups selected for deletion.")
                    return redirect(self.get_return_url(request))

                try:
                    # Get the selected groups before deletion - only fetch what we need
                    selected_groups = model.objects.filter(pk__in=self.pk_list)
                    group_count = selected_groups.count()

                    # Get all ConfigComplianceHash records that reference any of the selected groups
                    # This single query replaces the loop that was doing individual queries per group
                    related_hash_records = models.ConfigComplianceHash.objects.filter(
                        config_group__in=selected_groups
                    ).select_related("device", "rule")

                    # Collect device/rule combinations for the success message
                    # Use values() to get distinct combinations efficiently
                    device_rule_combinations = set(related_hash_records.values_list("device_id", "rule_id"))

                    # Count hash records that will be deleted before deletion
                    hash_records_count = related_hash_records.count()

                    # Delete all related ConfigComplianceHash records in one operation
                    # This handles both actual and intended records since we're deleting by device/rule combinations
                    related_hash_records.delete()

                    # Now delete the hash groups themselves
                    selected_groups.delete()

                    messages.success(
                        request,
                        f"Successfully deleted {group_count} configuration hash group{'' if group_count == 1 else 's'} "
                        f"and {hash_records_count} related hash record{'' if hash_records_count == 1 else 's'} "
                        f"for {len(device_rule_combinations)} device/rule combination{'' if len(device_rule_combinations) == 1 else 's'}.",
                    )

                except ObjectDoesNotExist as e:
                    messages.error(request, f"Error during deletion: {str(e)}")

                return redirect(self.get_return_url(request))

        # Show confirmation page - include feature name data for display
        selected_hash_groups = (
            model.objects.filter(pk__in=self.pk_list)
            .select_related("rule__feature")
            .annotate(
                feature_name=F("rule__feature__name"),
                feature_id=F("rule__feature__id"),
            )
        )
        table = tables.ConfigHashGroupingTable(selected_hash_groups)

        if not request.POST.get("_all"):
            data.update({"table": table, "total_objs_to_delete": len(table.rows)})
        else:
            data.update({"table": None, "delete_all": True, "total_objs_to_delete": len(table.rows)})

        return Response(data)


class RemediateHashGroupView(PermissionRequiredMixin, View):
    """View to remediate a hash group by running GenerateConfigPlans job."""

    permission_required = ["extras.run_job"]

    def get(self, request):
        """Handle GET request to run the remediation job."""
        feature_id = request.GET.get("feature_id")
        config_hash = request.GET.get("config_hash")

        if not feature_id or not config_hash:
            messages.error(request, "Missing feature_id or config_hash parameters.")
            return redirect("plugins:nautobot_golden_config:configcompliance_hash_grouping")

        try:
            feature = models.ComplianceFeature.objects.get(pk=feature_id)

            # Get the config group for this feature and hash
            try:
                config_group = models.ConfigHashGrouping.objects.get(
                    rule__feature_id=feature_id, config_hash=config_hash
                )
            except models.ConfigHashGrouping.DoesNotExist:
                messages.warning(request, "Configuration group not found for this feature and hash")
                return redirect("plugins:nautobot_golden_config:configcompliance_hash_grouping")

            # Get all devices in this hash group
            devices_in_group = (
                models.ConfigComplianceHash.objects.filter(
                    config_group=config_group,
                    config_type="actual",
                    device__configcompliance__rule__feature_id=feature_id,
                    device__configcompliance__compliance=False,
                )
                .values_list("device_id", flat=True)
                .distinct()
            )

            if not devices_in_group:
                messages.warning(request, "No devices found in hash group for this feature")
                return redirect("plugins:nautobot_golden_config:configcompliance_hash_grouping")

            device_ids = list(devices_in_group)

            if not device_ids:
                messages.warning(request, "No devices found for this hash group.")
                return redirect("plugins:nautobot_golden_config:configcompliance_hash_grouping")

            # Get the GenerateConfigPlans job
            job = Job.objects.get(name="Generate Config Plans")

            # Enqueue the job
            job_result = JobResult.enqueue_job(
                job,
                request.user,
                plan_type="remediation",
                feature=[feature.pk],
                device=list(devices_in_group),
            )

            messages.success(request, f"Remediation job started for {len(device_ids)} devices.")
            return redirect(job_result.get_absolute_url())

        except (Job.DoesNotExist, ValueError, TypeError, RuntimeError) as e:
            messages.error(request, f"Error starting remediation job: {str(e)}")
            return redirect("plugins:nautobot_golden_config:configcompliance_hash_grouping")

    def post(self, request):  # pylint: disable=too-many-return-statements
        """Handle POST request for AJAX modal job execution."""
        feature_id = request.POST.get("feature_id")
        config_hash = request.POST.get("config_hash")
        get_devices_only = request.POST.get("get_devices_only")

        if not feature_id or not config_hash:
            return JsonResponse({"error": "Missing feature_id or config_hash parameters."}, status=400)

        try:
            feature = models.ComplianceFeature.objects.get(pk=feature_id)

            # Get the config group for this feature and hash
            try:
                config_group = models.ConfigHashGrouping.objects.get(
                    rule__feature_id=feature_id, config_hash=config_hash
                )
            except models.ConfigHashGrouping.DoesNotExist:
                return JsonResponse({"error": "Configuration group not found for this feature and hash"}, status=404)

            # Get all devices in this hash group
            devices_in_group = (
                models.ConfigComplianceHash.objects.filter(
                    config_group=config_group,
                    config_type="actual",
                    device__configcompliance__rule__feature_id=feature_id,
                    device__configcompliance__compliance=False,
                )
                .values_list("device_id", flat=True)
                .distinct()
            )

            if not devices_in_group:
                return JsonResponse({"error": "No devices found in hash group for this feature"}, status=404)

            device_ids = list(devices_in_group)

            if not device_ids:
                return JsonResponse({"error": "No devices found for this hash group."}, status=404)

            # If only requesting device IDs, return them without starting a job
            if get_devices_only == "true":
                return JsonResponse({"device_ids": device_ids})

            # Get the GenerateConfigPlans job
            job = Job.objects.get(name="Generate Config Plans")

            # Enqueue the job
            job_result = JobResult.enqueue_job(
                job,
                request.user,
                plan_type="remediation",
                feature=[feature.pk],
                device=device_ids,
            )

            return JsonResponse({"job_result": {"id": str(job_result.pk), "url": job_result.get_absolute_url()}})

        except (Job.DoesNotExist, ValueError, TypeError, RuntimeError) as e:
            return JsonResponse({"error": f"Error starting remediation job: {str(e)}"}, status=500)
        except models.ComplianceFeature.DoesNotExist:
            return JsonResponse({"error": f"Feature with ID {feature_id} not found"}, status=404)
