"""Django views for Nautobot Golden Configuration."""

import base64
import io
import json
import logging
import urllib
import yaml

import matplotlib.pyplot as plt
import numpy as np

from django.contrib import messages
from django.db.models import F, Q
from django.db.models import Subquery, OuterRef, Count, FloatField, ExpressionWrapper, ProtectedError
from django.shortcuts import render, redirect

from nautobot.dcim.models import Device
from nautobot.core.views import generic
from nautobot.utilities.utils import csv_format
from nautobot.utilities.error_handlers import handle_protectederror
from nautobot.utilities.views import ContentTypePermissionRequiredMixin

from .filters import ComplianceFeatureFilter, ConfigComplianceFilter, GoldenConfigurationFilter
from .forms import (
    ComplianceFeatureForm,
    ComplianceFeatureFilterForm,
    ConfigComplianceFilterForm,
    GoldenConfigSettingsFeatureForm,
    GoldenConfigurationFilterForm,
)
from .models import ComplianceFeature, ConfigCompliance, GoldenConfigSettings, GoldenConfiguration
from .tables import (
    ComplianceFeatureTable,
    ConfigComplianceGlobalFeatureTable,
    ConfigComplianceTable,
    ConfigComplianceDeleteTable,
    GoldenConfigurationTable,
)
from .utilities.constant import PLUGIN_CFG, ENABLE_COMPLIANCE, CONFIG_FEATURES
from .utilities.helper import get_allowed_os_from_nested
from .utilities.graphql import graph_ql_query

LOGGER = logging.getLogger(__name__)

GREEN = "#D5E8D4"
RED = "#F8CECC"


class Home(generic.ObjectListView):
    """View for displaying the configuration management status for backup, intended, diff, and SoT Agg."""

    table = GoldenConfigurationTable
    filterset = GoldenConfigurationFilter
    filterset_form = GoldenConfigurationFilterForm
    queryset = GoldenConfiguration.objects.filter(**get_allowed_os_from_nested()).order_by("device__name")
    template_name = "nautobot_golden_config/home.html"

    def extra_context(self):
        """Boilerplace code to modify data before returning."""
        return CONFIG_FEATURES


class HomeBulkDeleteView(generic.BulkDeleteView):
    """Standard view for bulk deletion of data."""

    queryset = GoldenConfiguration.objects.filter(**get_allowed_os_from_nested()).order_by("device__name")
    table = GoldenConfigurationTable
    filterset = GoldenConfigurationFilter


class ConfigDetails(ContentTypePermissionRequiredMixin, generic.View):
    """View for the single configuration or diff of a single."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for config details."""
        return "nautobot_golden_config.view_goldenconfiguration"

    def get(self, request, device_name, config_type):
        """Read request into a view of a single device."""
        device = Device.objects.get(name=device_name)
        config_details = GoldenConfiguration.objects.filter(device=device).first()
        structure_format = "json"
        if config_type == "backup":
            output = config_details.backup_config
        elif config_type == "intended":
            output = config_details.intended_config
        elif config_type == "compliance":
            output = config_details.compliance_config
            backup_date = str(config_details.backup_last_success_date.strftime("%b %d %Y"))
            intended_date = str(config_details.intended_last_success_date.strftime("%b %d %Y"))
            first_occurence = output.index("@@")
            second_occurence = output.index("@@", first_occurence)
            # This is logic to match diff2html's expected input.
            output = (
                "--- Backup File - "
                + backup_date
                + "\n+++ Intended File - "
                + intended_date
                + "\n"
                + output[first_occurence:second_occurence]
                + "@@"
                + output[second_occurence + 2 :]
            )
        elif config_type == "sotagg":
            if request.GET.get("format") in ["json", "yaml"]:
                structure_format = request.GET.get("format")

            global_settings = GoldenConfigSettings.objects.get(id="aaaaaaaa-0000-0000-0000-000000000001")
            _, output = graph_ql_query(request, device, global_settings.sot_agg_query)

            if structure_format == "yaml":
                output = yaml.dump(output, default_flow_style=False)
            else:
                output = json.dumps(output, indent=4)

        template_name = "nautobot_golden_config/config_details.html"
        if request.GET.get("modal") == "true":
            template_name = "nautobot_golden_config/config_details_modal.html"

        return render(
            request,
            template_name,
            {"output": output, "device_name": device_name, "config_type": config_type, "format": structure_format},
        )


class ComplianceReport(generic.ObjectListView):
    """Django View for visualizing the compliance report."""

    filterset = ConfigComplianceFilter
    filterset_form = ConfigComplianceFilterForm
    queryset = ConfigCompliance.objects.filter(**get_allowed_os_from_nested())
    template_name = "nautobot_golden_config/compliance_report.html"
    table = ConfigComplianceTable

    def extra_context(self):
        """Boilerplate code to modify before returning data."""
        return {"compliance": ENABLE_COMPLIANCE}

    def alter_queryset(self, request):
        """Build actual runtime queryset as the build time queryset provides no information."""
        # Current implementation of for feature in ConfigCompliance.objects.values_list(), to always show all
        # features, however this may or may not be desirable in the future. To modify, change to
        # self.queryset.values_list()
        return (
            self.queryset.annotate(
                **{
                    feature: Subquery(
                        self.queryset.filter(device=OuterRef("device_id"), feature=feature).values("compliance")
                    )
                    for feature in ConfigCompliance.objects.values_list("feature", flat=True)
                    .distinct()
                    .order_by("feature")
                }
            )
            .distinct(*list(ConfigCompliance.objects.values_list("feature", flat=True).distinct()) + ["device__name"])
            .order_by("device__name")
        )

    def queryset_to_csv(self):
        """Export queryset of objects as comma-separated value (CSV)."""

        def conver_to_str(val):
            if val is False:  # pylint: disable=no-else-return
                return "non-compliant"
            elif val is True:
                return "compliant"
            return "N/A"

        csv_data = []
        headers = sorted(list(ConfigCompliance.objects.values_list("feature", flat=True).distinct()))
        csv_data.append(",".join(list(["Device name"] + headers)))
        for obj in self.alter_queryset(None).values():
            # From all of the unique fields, obtain the columns, using list comprehension, add values per column,
            # as some fields may not exist for every device.
            row = [Device.objects.get(id=obj["device_id"]).name] + [
                conver_to_str(obj.get(header)) for header in headers
            ]
            csv_data.append(csv_format(row))
        return "\n".join(csv_data)


class ComplianceBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more OnboardingTasks."""

    queryset = ConfigCompliance.objects.filter(**get_allowed_os_from_nested()).order_by("device__name")
    default_return_url = "plugins:nautobot_golden_config:config_report"
    table = ConfigComplianceDeleteTable
    filterset = ConfigComplianceFilter

    def post(self, request, **kwargs):
        """Delete instances based on post request data."""
        model = self.queryset.model

        # Are we deleting *all* objects in the queryset or just a selected subset?
        if request.POST.get("_all"):
            if self.filterset is not None:
                pk_list = [obj.pk for obj in self.filterset(request.GET, model.objects.only("pk")).qs]
            else:
                pk_list = model.objects.values_list("pk", flat=True)
        else:
            pk_list = request.POST.getlist("pk")

        form_cls = self.get_form()

        obj_to_del = [item[0] for item in ConfigCompliance.objects.filter(pk__in=pk_list).values_list("device")]
        if "_confirm" in request.POST:
            form = form_cls(request.POST)
            if form.is_valid():
                LOGGER.debug("Form validation was successful")

                # Delete objects
                queryset = ConfigCompliance.objects.filter(device__in=obj_to_del)
                try:
                    deleted_count = queryset.delete()[1][model._meta.label]
                except ProtectedError as error:
                    LOGGER.info("Caught ProtectedError while attempting to delete objects")
                    handle_protectederror(queryset, request, error)
                    return redirect(self.get_return_url(request))

                msg = "Deleted {} {}".format(deleted_count, model._meta.verbose_name_plural)
                LOGGER.info(msg)
                messages.success(request, msg)
                return redirect(self.get_return_url(request))

            LOGGER.debug("Form validation failed")

        else:
            form = form_cls(initial={"pk": pk_list, "return_url": self.get_return_url(request)})

        table = self.table(ConfigCompliance.objects.filter(device__in=obj_to_del), orderable=False)
        if not table.rows:
            messages.warning(request, "No {} were selected for deletion.".format(model._meta.verbose_name_plural))
            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "obj_type_plural": model._meta.verbose_name_plural,
                "table": table,
                "return_url": self.get_return_url(request),
            },
        )


class ComplianceDeviceReport(ContentTypePermissionRequiredMixin, generic.View):
    """View for the single device detailed information."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for device report."""
        return "nautobot_golden_config.view_configcompliance"

    def get(self, request, device_name):
        """Read request into a view of a single device."""
        device = Device.objects.get(name=device_name)
        compliance_details = (
            ConfigCompliance.objects.filter(device=device).filter(**get_allowed_os_from_nested()).order_by("feature")
        )
        config_details = {"compliance_details": compliance_details, "device_name": device_name}

        return render(
            request,
            "nautobot_golden_config/device_report.html",
            config_details,
        )


class ComplianceDeviceFilteredReport(ContentTypePermissionRequiredMixin, generic.View):
    """View for the single device detailed information."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for filtered report."""
        return "nautobot_golden_config.view_configcompliance"

    def get(self, request, device_name, compliance):
        """Read request into a view of a single device."""
        device = Device.objects.get(name=device_name)
        if compliance == "compliant":
            compliance_details = (
                ConfigCompliance.objects.filter(device=device)
                .filter(**get_allowed_os_from_nested())
                .order_by("feature")
            )
            compliance_details = compliance_details.filter(compliance=True)
        else:
            compliance_details = (
                ConfigCompliance.objects.filter(device=device)
                .filter(**get_allowed_os_from_nested())
                .order_by("feature")
            )
            compliance_details = compliance_details.filter(compliance=False)

        config_details = {"compliance_details": compliance_details, "device_name": device_name}

        return render(
            request,
            "nautobot_golden_config/device_report.html",
            config_details,
        )


class GlobalReportHelper(ContentTypePermissionRequiredMixin, generic.View):
    """Customized overview view reports aggregation and filterset."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for global report."""
        return "nautobot_golden_config.view_configcompliance"

    @staticmethod
    def plot_visual(aggr):
        """Plot aggregation visual."""
        labels = "Compliant", "Non-Compliant"
        if aggr["compliants"] is not None:
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
        labels = [item["feature"] for item in qs]

        compliant = [item["compliant"] for item in qs]
        non_compliant = [item["non_compliant"] for item in qs]

        label_locations = np.arange(len(labels))  # the label locations

        per_feature_bar_width = PLUGIN_CFG["per_feature_bar_width"]
        per_feature_width = PLUGIN_CFG["per_feature_width"]
        per_feature_height = PLUGIN_CFG["per_feature_height"]

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
                    "{}".format(height),
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


class ComplianceOverviewReport(generic.ObjectListView):
    """View for executive report on configuration compliance."""

    filterset = ConfigComplianceFilter
    filterset_form = ConfigComplianceFilterForm
    table = ConfigComplianceGlobalFeatureTable
    template_name = "nautobot_golden_config/overview_report.html"
    kind = "Features"
    queryset = (
        ConfigCompliance.objects.values("feature")
        .filter(**get_allowed_os_from_nested())
        .annotate(
            count=Count("feature"),
            compliant=Count("feature", filter=Q(compliance=True)),
            non_compliant=Count("feature", filter=~Q(compliance=True)),
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
            "bar_chart": GlobalReportHelper.plot_barchart_visual(feature_qs),
            "device_aggr": device_aggr,
            "device_visual": GlobalReportHelper.plot_visual(device_aggr),
            "feature_aggr": feature_aggr,
            "feature_visual": GlobalReportHelper.plot_visual(feature_aggr),
        }

    def get_global_aggr(self, request):
        """Get device and feature global reports.

        Returns:
            device_aggr: device global report dict
            feature_aggr: feature global report dict
        """
        main_qs = ConfigCompliance.objects.filter(**get_allowed_os_from_nested())

        device_aggr, feature_aggr = {}, {}
        if self.filterset is not None:
            device_aggr = (
                self.filterset(request.GET, main_qs)
                .qs.values("device")
                .annotate(compliant=Count("device", filter=Q(compliance=False)))
                .aggregate(total=Count("device", distinct=True), compliants=Count("compliant", filter=Q(compliant=0)))
            )
            feature_aggr = self.filterset(request.GET, main_qs).qs.aggregate(
                total=Count("feature"), compliants=Count("feature", filter=Q(compliance=True))
            )

        return (
            GlobalReportHelper.calculate_aggr_percentage(device_aggr),
            GlobalReportHelper.calculate_aggr_percentage(feature_aggr),
        )

    def extra_context(self):
        """Extra content method on."""
        # add global aggregations to extra context.

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

        qs = self.queryset.values("feature", "count", "compliant", "non_compliant", "comp_percent")
        csv_data.append(",".join(["Total" if item == "count" else item.capitalize() for item in qs[0].keys()]))
        for obj in qs:
            csv_data.append(
                ",".join([f"{str(val)} %" if key == "comp_percent" else str(val) for key, val in obj.items()])
            )

        return "\n".join(csv_data)


class ComplianceFeatureView(generic.ObjectListView):
    """View for managing the config compliance feature definition."""

    table = ComplianceFeatureTable
    filterset = ComplianceFeatureFilter
    filterset_form = ComplianceFeatureFilterForm
    queryset = ComplianceFeature.objects.all().order_by("platform", "name")
    template_name = "nautobot_golden_config/compliance_features.html"


class ComplianceFeatureEditView(generic.ObjectEditView):
    """View for managing compliance features."""

    queryset = ComplianceFeature.objects.all()
    model_form = ComplianceFeatureForm


class ComplianceFeatureDeleteView(generic.ObjectDeleteView):
    """View for deleting compliance features."""

    queryset = ComplianceFeature.objects.all()


class ComplianceFeatureBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting compliance features."""

    queryset = ComplianceFeature.objects.all()
    table = ComplianceFeatureTable


class GoldenConfigSettingsEditView(generic.ObjectEditView):
    """View for editing the Global configurations."""

    queryset = GoldenConfigSettings.objects.filter(id="aaaaaaaa-0000-0000-0000-000000000001")
    model_form = GoldenConfigSettingsFeatureForm
