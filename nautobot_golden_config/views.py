"""Django views for Nautobot Golden Configuration."""  # pylint: disable=too-many-lines
import base64
import difflib
import io
import json
import logging
import urllib
from datetime import datetime, timezone

import matplotlib.pyplot as plt
import numpy as np
import yaml
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, ExpressionWrapper, F, FloatField, Max, ProtectedError, Q
from django.forms import ModelMultipleChoiceField, MultipleHiddenInput
from django.shortcuts import redirect, render
from django.utils.module_loading import import_string
from django.views.generic import View
from django_pivot.pivot import pivot
from nautobot.core.views import generic
from nautobot.core.views.viewsets import NautobotUIViewSet
from nautobot.dcim.forms import DeviceFilterForm
from nautobot.dcim.models import Device
from nautobot.extras.jobs import run_job
from nautobot.extras.models import Job, JobResult
from nautobot.extras.utils import get_job_content_type
from nautobot.utilities.error_handlers import handle_protectederror
from nautobot.utilities.forms import ConfirmationForm
from nautobot.utilities.utils import copy_safe_request, csv_format
from nautobot.utilities.views import ContentTypePermissionRequiredMixin, ObjectPermissionRequiredMixin

from nautobot_golden_config import filters, forms, models, tables
from nautobot_golden_config.api import serializers
from nautobot_golden_config.utilities import constant
from nautobot_golden_config.utilities.config_postprocessing import get_config_postprocessing
from nautobot_golden_config.utilities.graphql import graph_ql_query
from nautobot_golden_config.utilities.helper import add_message, get_device_to_settings_map

LOGGER = logging.getLogger(__name__)

GREEN = "#D5E8D4"  # TODO: 2.0: change all to ColorChoices.COLOR_GREEN
RED = "#F8CECC"

#
# GoldenConfig
#


class GoldenConfigListView(generic.ObjectListView):
    """View for displaying the configuration management status for backup, intended, diff, and SoT Agg."""

    table = tables.GoldenConfigTable
    filterset = filters.GoldenConfigDeviceFilterSet
    filterset_form = DeviceFilterForm
    queryset = Device.objects.all()
    template_name = "nautobot_golden_config/goldenconfig_list.html"
    action_buttons = ("export",)

    def extra_context(self):
        """Boilerplace code to modify data before returning."""
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="ComplianceJob").first()
        add_message([[job, self.request, constant.ENABLE_COMPLIANCE]])
        return constant.CONFIG_FEATURES

    def alter_queryset(self, request):
        """Build actual runtime queryset as the build time queryset provides no information."""
        qs = Device.objects.none()
        for obj in models.GoldenConfigSetting.objects.all():
            qs = qs | obj.get_queryset().distinct()

        return self.queryset.filter(id__in=qs).annotate(
            backup_config=F("goldenconfig__backup_config"),
            intended_config=F("goldenconfig__intended_config"),
            compliance_config=F("goldenconfig__compliance_config"),
            backup_last_success_date=F("goldenconfig__backup_last_success_date"),
            intended_last_success_date=F("goldenconfig__intended_last_success_date"),
            compliance_last_success_date=F("goldenconfig__compliance_last_success_date"),
            backup_last_attempt_date=F("goldenconfig__backup_last_attempt_date"),
            intended_last_attempt_date=F("goldenconfig__intended_last_attempt_date"),
            compliance_last_attempt_date=F("goldenconfig__compliance_last_attempt_date"),
        )

    @property
    def dynamic_group_queryset(self):
        """Return queryset of DynamicGroups associated with all GoldenConfigSettings."""
        golden_config_device_queryset = Device.objects.none()
        for setting in models.GoldenConfigSetting.objects.all():
            golden_config_device_queryset = golden_config_device_queryset | setting.dynamic_group.members
        return golden_config_device_queryset & self.queryset.distinct()

    def queryset_to_csv(self):
        """Override nautobot default to account for using Device model for GoldenConfig data."""
        golden_config_devices_in_scope = self.dynamic_group_queryset
        csv_headers = models.GoldenConfig.csv_headers.copy()
        # Exclude GoldenConfig entries no longer in scope
        golden_config_entries_in_scope = models.GoldenConfig.objects.filter(device__in=golden_config_devices_in_scope)
        golden_config_entries_as_csv = [csv_format(entry.to_csv()) for entry in golden_config_entries_in_scope]
        # Account for devices in scope without GoldenConfig entries
        commas = "," * (len(csv_headers) - 1)
        devices_in_scope_without_golden_config_entries_as_csv = [
            f"{device.name}{commas}" for device in golden_config_devices_in_scope.filter(goldenconfig__isnull=True)
        ]
        csv_data = (
            [",".join(csv_headers)]
            + golden_config_entries_as_csv
            + devices_in_scope_without_golden_config_entries_as_csv
        )

        return "\n".join(csv_data)


class GoldenConfigBulkDeleteView(generic.BulkDeleteView):
    """Standard view for bulk deletion of data."""

    queryset = Device.objects.all()
    table = tables.GoldenConfigTable
    filterset = filters.GoldenConfigDeviceFilterSet

    def post(self, request, **kwargs):
        """Delete instances based on post request data."""
        # This is a deviation from standard Nautobot, since the objectlistview is shown on devices, but
        # displays elements from GoldenConfig model. We have to override attempting to delete from the Device model.

        model = self.queryset.model

        pk_list = request.POST.getlist("pk")

        form_cls = self.get_form()

        if "_confirm" in request.POST:
            form = form_cls(request.POST)
            if form.is_valid():
                LOGGER.debug("Form validation was successful")

                # Delete objects
                queryset = models.GoldenConfig.objects.filter(pk__in=pk_list)
                try:
                    deleted_count = queryset.delete()[1][models.GoldenConfig._meta.label]
                except ProtectedError as error:
                    LOGGER.info("Caught ProtectedError while attempting to delete objects")
                    handle_protectederror(queryset, request, error)
                    return redirect(self.get_return_url(request))

                msg = f"Deleted {deleted_count} {models.GoldenConfig._meta.verbose_name_plural}"
                LOGGER.info(msg)
                messages.success(request, msg)
                return redirect(self.get_return_url(request))

            LOGGER.debug("Form validation failed")

        else:
            # From the list of Device IDs, get the GoldenConfig IDs
            obj_to_del = [
                item[0] for item in models.GoldenConfig.objects.filter(device__pk__in=pk_list).values_list("id")
            ]

            form = form_cls(
                initial={
                    "pk": obj_to_del,
                    "return_url": self.get_return_url(request),
                }
            )
        # Levarge a custom table just for deleting
        table = tables.DeleteGoldenConfigTable(models.GoldenConfig.objects.filter(pk__in=obj_to_del), orderable=False)
        if not table.rows:
            messages.warning(
                request,
                f"No {model._meta.verbose_name_plural} were selected for deletion.",
            )
            return redirect(self.get_return_url(request))

        context = {
            "form": form,
            "obj_type_plural": model._meta.verbose_name_plural,
            "table": table,
            "return_url": self.get_return_url(request),
        }
        return render(request, self.template_name, context)

    def get_form(self):
        """Override standard form."""

        class BulkDeleteForm(ConfirmationForm):
            """Local class override."""

            pk = ModelMultipleChoiceField(queryset=models.GoldenConfig.objects.all(), widget=MultipleHiddenInput)

        if self.form:
            return self.form

        return BulkDeleteForm


#
# ConfigCompliance
#


class ConfigComplianceListView(generic.ObjectListView):
    """Django View for visualizing the compliance report."""

    action_buttons = ("export",)
    filterset = filters.ConfigComplianceFilterSet
    filterset_form = forms.ConfigComplianceFilterForm
    queryset = models.ConfigCompliance.objects.all().order_by("device__name")
    template_name = "nautobot_golden_config/compliance_report.html"
    table = tables.ConfigComplianceTable

    def alter_queryset(self, request):
        """Build actual runtime queryset as the build time queryset provides no information."""
        return pivot(
            self.queryset,
            ["device", "device__name"],
            "rule__feature__slug",
            "compliance_int",
            aggregation=Max,
        )

    def extra_context(self):
        """Boilerplate code to modify before returning data."""
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="ComplianceJob").first()
        add_message([[job, self.request, constant.ENABLE_COMPLIANCE]])
        return {"compliance": constant.ENABLE_COMPLIANCE}

    def queryset_to_csv(self):
        """Export queryset of objects as comma-separated value (CSV)."""

        def convert_to_str(val):
            if val is None:
                return "N/A"
            if bool(val) is False:
                return "non-compliant"
            if bool(val) is True:
                return "compliant"
            raise ValueError(f"Expecting one of 'N/A', 0, or 1, got {val}")

        csv_data = []
        headers = sorted(list(models.ComplianceFeature.objects.values_list("slug", flat=True).distinct()))
        csv_data.append(",".join(list(["Device name"] + headers)))
        for obj in self.alter_queryset(None):
            # From all of the unique fields, obtain the columns, using list comprehension, add values per column,
            # as some fields may not exist for every device.
            row = [obj.get("device__name")] + [convert_to_str(obj.get(header)) for header in headers]
            csv_data.append(csv_format(row))
        return "\n".join(csv_data)


class ConfigComplianceView(generic.ObjectView):
    """View for a device's specific configuration compliance feature."""

    queryset = models.ConfigCompliance.objects.all()

    def get_extra_context(self, request, instance):
        """A Add extra data to detail view for Nautobot."""
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="ComplianceJob").first()
        add_message([[job, request, constant.ENABLE_COMPLIANCE]])
        return {}


class ConfigComplianceBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more OnboardingTasks."""

    queryset = models.ConfigCompliance.objects.all()
    table = tables.ConfigComplianceDeleteTable
    filterset = filters.ConfigComplianceFilterSet

    def post(self, request, **kwargs):
        """Delete instances based on post request data."""
        # This is a deviation from standard Nautobot. Since the config compliance is pivot'd, the actual
        # pk is based on the device, this crux of the change is to get all actual config changes based on
        # the incoming device pk's.
        model = self.queryset.model

        # Are we deleting *all* objects in the queryset or just a selected subset?
        if request.POST.get("_all"):
            if self.filterset is not None:
                pk_list = [obj.pk for obj in self.filterset(request.GET, model.objects.only("pk")).qs]
            else:
                pk_list = model.objects.values_list("pk", flat=True)
            # When selecting *all* the resulting request args are ConfigCompliance object PKs
            obj_to_del = [item[0] for item in self.queryset.filter(pk__in=pk_list).values_list("id")]
        else:
            pk_list = request.POST.getlist("pk")
            # When selecting individual rows the resulting request args are Device object PKs
            obj_to_del = [item[0] for item in self.queryset.filter(device__pk__in=pk_list).values_list("id")]

        form_cls = self.get_form()

        if "_confirm" in request.POST:
            form = form_cls(request.POST)
            if form.is_valid():
                LOGGER.debug("Form validation was successful")

                # Delete objects
                queryset = self.queryset.filter(pk__in=pk_list)
                try:
                    deleted_count = queryset.delete()[1][model._meta.label]
                except ProtectedError as error:
                    LOGGER.info("Caught ProtectedError while attempting to delete objects")
                    handle_protectederror(queryset, request, error)
                    return redirect(self.get_return_url(request))

                msg = f"Deleted {deleted_count} {model._meta.verbose_name_plural}"
                LOGGER.info(msg)
                messages.success(request, msg)
                return redirect(self.get_return_url(request))

            LOGGER.debug("Form validation failed")

        else:
            form = form_cls(
                initial={
                    "pk": obj_to_del,
                    "return_url": self.get_return_url(request),
                }
            )

        # Retrieve objects being deleted
        table = self.table(self.queryset.filter(pk__in=obj_to_del), orderable=False)
        if not table.rows:
            messages.warning(
                request,
                f"No {model._meta.verbose_name_plural} were selected for deletion.",
            )
            return redirect(self.get_return_url(request))

        context = {
            "form": form,
            "obj_type_plural": model._meta.verbose_name_plural,
            "table": table,
            "return_url": self.get_return_url(request),
        }
        context.update(self.extra_context())
        return render(request, self.template_name, context)


class ConfigComplianceDeleteView(generic.ObjectDeleteView):
    """View for deleting compliance rules."""

    queryset = models.ConfigCompliance.objects.all()


# ConfigCompliance Non-Standards


class ConfigComplianceDeviceView(ContentTypePermissionRequiredMixin, generic.View):
    """View for individual device detailed information."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for device report."""
        return "nautobot_golden_config.view_configcompliance"

    def get(self, request, pk):  # pylint: disable=invalid-name
        """Read request into a view of a single device."""
        device = Device.objects.get(pk=pk)
        compliance_details = models.ConfigCompliance.objects.filter(device=device)

        config_details = {"compliance_details": compliance_details, "device": device}

        return render(
            request,
            "nautobot_golden_config/compliance_device_report.html",
            config_details,
        )


class ComplianceDeviceFilteredReport(ContentTypePermissionRequiredMixin, generic.View):
    """View for the single device detailed information."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for filtered report."""
        return "nautobot_golden_config.view_configcompliance"

    def get(self, request, pk, compliance):  # pylint: disable=invalid-name
        """Read request into a view of a single device."""
        device = Device.objects.get(pk=pk)
        compliance_details = models.ConfigCompliance.objects.filter(device=device)

        if compliance == "compliant":
            compliance_details = compliance_details.filter(compliance=True)
        else:
            compliance_details = compliance_details.filter(compliance=False)

        config_details = {"compliance_details": compliance_details, "device": device}
        return render(
            request,
            "nautobot_golden_config/compliance_device_report.html",
            config_details,
        )


class ConfigComplianceDetails(ContentTypePermissionRequiredMixin, generic.View):
    """View for the single configuration or diff of a single."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for config details."""
        return "nautobot_golden_config.view_goldenconfig"

    def get(
        self, request, pk, config_type
    ):  # pylint: disable=invalid-name,too-many-branches,too-many-locals,too-many-statements
        """Read request into a view of a single device."""

        def diff_structured_data(backup_data, intended_data):
            """Utility function to provide `Unix Diff` between two JSON snippets."""
            backup_yaml = yaml.safe_dump(json.loads(backup_data))
            intend_yaml = yaml.safe_dump(json.loads(intended_data))

            for line in difflib.unified_diff(backup_yaml.splitlines(), intend_yaml.splitlines(), lineterm=""):
                yield line

        device = Device.objects.get(pk=pk)
        config_details = models.GoldenConfig.objects.filter(device=device).first()
        if not config_details and config_type == "json_compliance":
            # Create the GoldenConfig object for the device only for JSON compliance.
            config_details = models.GoldenConfig.objects.create(device=device)
        structure_format = "json"

        if config_type == "sotagg":
            if request.GET.get("format") in ["json", "yaml"]:
                structure_format = request.GET.get("format")

            settings = get_device_to_settings_map(queryset=Device.objects.filter(pk=device.pk))
            if device.id in settings:
                sot_agg_query_setting = settings[device.id].sot_agg_query
                if sot_agg_query_setting is not None:
                    _, output = graph_ql_query(request, device, sot_agg_query_setting.query)
                else:
                    output = {"Error": "No saved `GraphQL Query` query was configured in the `Golden Config Setting`"}
            else:
                raise ObjectDoesNotExist(f"{device.name} does not map to a Golden Config Setting.")

            if structure_format == "yaml":
                output = yaml.dump(json.loads(json.dumps(output)), default_flow_style=False)
            else:
                output = json.dumps(output, indent=4)
        elif not config_details:
            output = ""
        elif config_type == "backup":
            output = config_details.backup_config
        elif config_type == "intended":
            output = config_details.intended_config
        elif config_type == "postprocessing":
            output = get_config_postprocessing(config_details, request)
        # Compliance type is broken up into JSON(json_compliance) and CLI(compliance) compliance.
        elif "compliance" in config_type:
            if config_type == "compliance":
                # This section covers the steps to run regular CLI compliance which is a diff of 2 files (backup and intended).
                diff_type = "File"
                output = config_details.compliance_config
                if config_details.backup_last_success_date:
                    backup_date = str(config_details.backup_last_success_date.strftime("%b %d %Y"))
                else:
                    backup_date = datetime.now().strftime("%b %d %Y")
                if config_details.intended_last_success_date:
                    intended_date = str(config_details.intended_last_success_date.strftime("%b %d %Y"))
                else:
                    intended_date = datetime.now().strftime("%b %d %Y")
            elif config_type == "json_compliance":
                # The JSON compliance runs differently then CLI, it grabs all configcompliance objects for
                # a given device and merges them, sorts them, and diffs them.
                diff_type = "JSON"
                # Get all compliance objects for a device.
                compliance_objects = models.ConfigCompliance.objects.filter(device=device.id)
                actual = {}
                intended = {}
                # Set a starting time that will be older than all last updated objects in compliance objects.
                most_recent_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
                # Loop through config compliance objects and merge the data into one dataset.
                for obj in compliance_objects:
                    actual[obj.rule.feature.slug] = obj.actual
                    intended[obj.rule.feature.slug] = obj.intended
                    # Update most_recent_time each time the compliance objects time is more recent then previous.
                    if obj.last_updated > most_recent_time:
                        most_recent_time = obj.last_updated
                config_details.compliance_last_attempt_date = most_recent_time
                config_details.compliance_last_success_date = most_recent_time
                # Generate the diff between both JSON objects and sort keys for accurate diff.
                config_details.compliance_config = "\n".join(
                    diff_structured_data(json.dumps(actual, sort_keys=True), json.dumps(intended, sort_keys=True))
                )
                config_details.save()
                output = config_details.compliance_config
                backup_date = intended_date = str(most_recent_time.strftime("%b %d %Y"))
            if output == "":
                # This is used if all config snippets are in compliance and no diff exist.
                output = f"--- Backup {diff_type} - " + backup_date + f"\n+++ Intended {diff_type} - " + intended_date
            else:
                first_occurence = output.index("@@")
                second_occurence = output.index("@@", first_occurence)
                # This is logic to match diff2html's expected input.
                output = (
                    f"--- Backup {diff_type} - "
                    + backup_date
                    + f"\n+++ Intended {diff_type} - "
                    + intended_date
                    + "\n"
                    + output[first_occurence:second_occurence]
                    + "@@"
                    + output[second_occurence + 2 :]  # noqa: E203
                )

        template_name = "nautobot_golden_config/configcompliance_details.html"
        if request.GET.get("modal") == "true":
            template_name = "nautobot_golden_config/configcompliance_detailsmodal.html"

        return render(
            request,
            template_name,
            {
                "output": output,
                "device_name": device.name,
                "config_type": config_type,
                "format": structure_format,
                "device": device,
                "include_file": "extras/inc/json_format.html",
            },
        )


class ConfigComplianceOverviewOverviewHelper(ContentTypePermissionRequiredMixin, generic.View):
    """Customized overview view reports aggregation and filterset."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for global report."""
        return "nautobot_golden_config.view_configcompliance"

    @staticmethod
    def plot_visual(aggr):
        """Plot aggregation visual."""
        labels = "Compliant", "Non-Compliant"
        # Only Compliants and Non-Compliants values are used to create the diagram
        # if either of them are True (not 0), create the diagram
        if any((aggr["compliants"], aggr["non_compliants"])):
            sizes = [aggr["compliants"], aggr["non_compliants"]]
            explode = (0, 0.1)  # only "explode" the 2nd slice (i.e. 'Hogs')
            # colors used for visuals ('compliant','non_compliant')
            fig1, ax1 = plt.subplots()
            logging.debug(fig1)
            ax1.pie(
                sizes,
                explode=explode,
                labels=labels,
                autopct="%1.1f%%",
                colors=[GREEN, RED],
                shadow=True,
                startangle=90,
            )
            ax1.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
            plt.title("Compliance", y=-0.1)
            fig = plt.gcf()
            # convert graph into string buffer and then we convert 64 bit code into image
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)
            string = base64.b64encode(buf.read())
            plt_visual = urllib.parse.quote(string)
            return plt_visual
        return None

    @staticmethod
    def plot_barchart_visual(qs):  # pylint: disable=too-many-locals
        """Construct report visual from queryset."""
        labels = [item["rule__feature__slug"] for item in qs]

        compliant = [item["compliant"] for item in qs]
        non_compliant = [item["non_compliant"] for item in qs]

        label_locations = np.arange(len(labels))  # the label locations

        per_feature_bar_width = constant.PLUGIN_CFG["per_feature_bar_width"]
        per_feature_width = constant.PLUGIN_CFG["per_feature_width"]
        per_feature_height = constant.PLUGIN_CFG["per_feature_height"]

        width = per_feature_bar_width  # the width of the bars

        fig, axis = plt.subplots(figsize=(per_feature_width, per_feature_height))
        rects1 = axis.bar(label_locations - width / 2, compliant, width, label="Compliant", color=GREEN)
        rects2 = axis.bar(label_locations + width / 2, non_compliant, width, label="Non Compliant", color=RED)

        # Add some text for labels, title and custom x-axis tick labels, etc.
        axis.set_ylabel("Compliance")
        axis.set_title("Compliance per Feature")
        axis.set_xticks(label_locations)
        axis.set_xticklabels(labels, rotation=45)
        axis.margins(0.2, 0.2)
        axis.legend()

        def autolabel(rects):
            """Attach a text label above each bar in *rects*, displaying its height."""
            for rect in rects:
                height = rect.get_height()
                axis.annotate(
                    f"{height}",
                    xy=(rect.get_x() + rect.get_width() / 2, 0.5),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    rotation=90,
                )

        autolabel(rects1)
        autolabel(rects2)

        # convert graph into dtring buffer and then we convert 64 bit code into image
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        string = base64.b64encode(buf.read())
        bar_chart = urllib.parse.quote(string)
        return bar_chart

    @staticmethod
    def calculate_aggr_percentage(aggr):
        """Calculate percentage of compliance given aggregation fields.

        Returns:
            aggr: same aggr dict given as parameter with two new keys
                - comp_percents
                - non_compliants
        """
        aggr["non_compliants"] = aggr["total"] - aggr["compliants"]
        try:
            aggr["comp_percents"] = round(aggr["compliants"] / aggr["total"] * 100, 2)
        except ZeroDivisionError:
            aggr["comp_percents"] = 0
        return aggr


class ConfigComplianceOverview(generic.ObjectListView):
    """View for executive report on configuration compliance."""

    action_buttons = ("export",)
    filterset = filters.ConfigComplianceFilterSet
    filterset_form = forms.ConfigComplianceFilterForm
    table = tables.ConfigComplianceGlobalFeatureTable
    template_name = "nautobot_golden_config/compliance_overview_report.html"
    kind = "Features"
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

    # extra content dict to be returned by self.extra_context() method
    extra_content = {}

    def setup(self, request, *args, **kwargs):
        """Using request object to perform filtering based on query params."""
        super().setup(request, *args, **kwargs)
        device_aggr, feature_aggr = self.get_global_aggr(request)
        feature_qs = self.filterset(request.GET, self.queryset).qs
        self.extra_content = {
            "bar_chart": ConfigComplianceOverviewOverviewHelper.plot_barchart_visual(feature_qs),
            "device_aggr": device_aggr,
            "device_visual": ConfigComplianceOverviewOverviewHelper.plot_visual(device_aggr),
            "feature_aggr": feature_aggr,
            "feature_visual": ConfigComplianceOverviewOverviewHelper.plot_visual(feature_aggr),
        }

    def get_global_aggr(self, request):
        """Get device and feature global reports.

        Returns:
            device_aggr: device global report dict
            feature_aggr: feature global report dict
        """
        main_qs = models.ConfigCompliance.objects

        device_aggr, feature_aggr = {}, {}
        if self.filterset is not None:
            device_aggr = (
                self.filterset(request.GET, main_qs)
                .qs.values("device")
                .annotate(compliant=Count("device", filter=Q(compliance=False)))
                .aggregate(total=Count("device", distinct=True), compliants=Count("compliant", filter=Q(compliant=0)))
            )
            feature_aggr = self.filterset(request.GET, main_qs).qs.aggregate(
                total=Count("rule"), compliants=Count("rule", filter=Q(compliance=True))
            )

        return (
            ConfigComplianceOverviewOverviewHelper.calculate_aggr_percentage(device_aggr),
            ConfigComplianceOverviewOverviewHelper.calculate_aggr_percentage(feature_aggr),
        )

    def extra_context(self):
        """Extra content method on."""
        # add global aggregations to extra context.
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="ComplianceJob").first()
        add_message([[job, self.request, constant.ENABLE_COMPLIANCE]])
        return self.extra_content

    def queryset_to_csv(self):
        """Export queryset of objects as comma-separated value (CSV)."""
        csv_data = []

        csv_data.append(",".join(["Type", "Total", "Compliant", "Non-Compliant", "Compliance"]))
        csv_data.append(
            ",".join(
                ["Devices"]
                + [
                    f"{str(val)} %" if key == "comp_percents" else str(val)
                    for key, val in self.extra_content["device_aggr"].items()
                ]
            )
        )
        csv_data.append(
            ",".join(
                ["Features"]
                + [
                    f"{str(val)} %" if key == "comp_percents" else str(val)
                    for key, val in self.extra_content["feature_aggr"].items()
                ]
            )
        )
        csv_data.append(",".join([]))

        qs = self.queryset.values("rule__feature__name", "count", "compliant", "non_compliant", "comp_percent")
        csv_data.append(",".join(["Total" if item == "count" else item.capitalize() for item in qs[0].keys()]))
        for obj in qs:
            csv_data.append(
                ",".join([f"{str(val)} %" if key == "comp_percent" else str(val) for key, val in obj.items()])
            )

        return "\n".join(csv_data)


class ComplianceFeatureUIViewSet(NautobotUIViewSet):
    """Views for the ComplianceFeature model."""

    bulk_create_form_class = forms.ComplianceFeatureCSVForm
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
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="ComplianceJob").first()
        add_message([[job, request, constant.ENABLE_COMPLIANCE]])
        return {}


class ComplianceRuleUIViewSet(NautobotUIViewSet):
    """Views for the ComplianceRule model."""

    bulk_create_form_class = forms.ComplianceRuleCSVForm
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
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="ComplianceJob").first()
        add_message([[job, request, constant.ENABLE_COMPLIANCE]])
        return {}


class GoldenConfigSettingUIViewSet(NautobotUIViewSet):
    """Views for the GoldenConfigSetting model."""

    bulk_create_form_class = forms.GoldenConfigSettingCSVForm
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
        jobs.append(
            [
                Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="BackupJob").first(),
                request,
                constant.ENABLE_BACKUP,
            ]
        )
        jobs.append(
            [
                Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="IntendedJob").first(),
                request,
                constant.ENABLE_INTENDED,
            ]
        )
        jobs.append(
            [
                Job.objects.filter(
                    module_name="nautobot_golden_config.jobs", job_class_name="DeployConfigPlans"
                ).first(),
                request,
                constant.ENABLE_DEPLOY,
            ]
        )
        jobs.append(
            [
                Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="ComplianceJob").first(),
                request,
                constant.ENABLE_COMPLIANCE,
            ]
        )
        jobs.append(
            [
                Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="AllGoldenConfig").first(),
                request,
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
                Job.objects.filter(
                    module_name="nautobot_golden_config.jobs", job_class_name="AllDevicesGoldenConfig"
                ).first(),
                request,
                [
                    constant.ENABLE_BACKUP,
                    constant.ENABLE_COMPLIANCE,
                    constant.ENABLE_DEPLOY,
                    constant.ENABLE_INTENDED,
                    constant.ENABLE_SOTAGG,
                ],
            ]
        )
        add_message(jobs)
        return {}


class ConfigRemoveUIViewSet(NautobotUIViewSet):
    """Views for the ConfigRemove model."""

    bulk_create_form_class = forms.ConfigRemoveCSVForm
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
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="BackupJob").first()
        add_message([[job, request, constant.ENABLE_BACKUP]])
        return {}


class ConfigReplaceUIViewSet(NautobotUIViewSet):
    """Views for the ConfigReplace model."""

    bulk_create_form_class = forms.ConfigReplaceCSVForm
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
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="BackupJob").first()
        add_message([[job, request, constant.ENABLE_BACKUP]])
        return {}


class RemediationSettingUIViewSet(NautobotUIViewSet):
    """Views for the RemediationSetting model."""

    bulk_create_form_class = forms.RemediationSettingCSVForm
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
        job = Job.objects.filter(module_name="nautobot_golden_config.jobs", job_class_name="ComplianceJob").first()
        add_message([[job, request, constant.ENABLE_COMPLIANCE]])
        return {}


class ConfigPlanUIViewSet(NautobotUIViewSet):
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

    def get_form_class(self, **kwargs):
        """Helper function to get form_class for different views."""
        if self.action == "update":
            return forms.ConfigPlanUpdateForm
        return super().get_form_class(**kwargs)

    def get_extra_context(self, request, instance=None):
        """A ConfigPlan helper function to warn if the Job is not enabled to run."""
        jobs = []
        jobs.append(
            [
                Job.objects.filter(
                    module_name="nautobot_golden_config.jobs", job_class_name="GenerateConfigPlans"
                ).first(),
                request,
                constant.ENABLE_PLAN,
            ]
        )
        jobs.append(
            [
                Job.objects.filter(
                    module_name="nautobot_golden_config.jobs", job_class_name="DeployConfigPlans"
                ).first(),
                request,
                constant.ENABLE_DEPLOY,
            ]
        )
        jobs.append(
            [
                Job.objects.filter(
                    module_name="nautobot_golden_config.jobs", job_class_name="DeployConfigPlanJobButtonReceiver"
                ).first(),
                request,
                constant.ENABLE_DEPLOY,
            ]
        )
        add_message(jobs)
        return {}


class ConfigPlanBulkDeploy(ObjectPermissionRequiredMixin, View):
    """View to run the Config Plan Deploy Job."""

    queryset = models.ConfigPlan.objects.all()

    def get_required_permission(self):
        """Permissions required for the view."""
        return "extras.run_job"

    def post(self, request):
        """Enqueue the job and redirect to the job results page."""
        config_plan_pks = request.POST.getlist("pk")
        if not config_plan_pks:
            messages.warning(request, "No Config Plans selected for deployment.")
            return redirect("plugins:nautobot_golden_config:configplan_list")

        job_data = {"config_plan": config_plan_pks}

        result = JobResult.enqueue_job(
            func=run_job,
            name=import_string("nautobot_golden_config.jobs.DeployConfigPlans").class_path,
            obj_type=get_job_content_type(),
            user=request.user,
            data=job_data,
            request=copy_safe_request(request),
            commit=request.POST.get("commit", False),
        )

        return redirect(result.get_absolute_url())
