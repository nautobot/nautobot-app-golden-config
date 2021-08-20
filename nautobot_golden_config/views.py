"""Django views for Nautobot Golden Configuration."""
from datetime import datetime

import base64
import io
import json
import logging
import urllib
import yaml
import difflib

import matplotlib.pyplot as plt
import numpy as np

from django.contrib import messages
from django.db.models import F, Q, Max
from django.db.models import Count, FloatField, ExpressionWrapper, ProtectedError
from django.shortcuts import render, redirect
from django_pivot.pivot import pivot

from nautobot.dcim.models import Device
from nautobot.core.views import generic
from nautobot.utilities.utils import csv_format
from nautobot.utilities.error_handlers import handle_protectederror
from nautobot.utilities.views import ContentTypePermissionRequiredMixin

from nautobot_golden_config import filters, forms, models, tables

from nautobot_golden_config.utilities.constant import PLUGIN_CFG, ENABLE_COMPLIANCE, CONFIG_FEATURES
from nautobot_golden_config.utilities.graphql import graph_ql_query

from nautobot_golden_config.choices import ComplianceRuleTypeChoice

LOGGER = logging.getLogger(__name__)

GREEN = "#D5E8D4"
RED = "#F8CECC"

#
# GoldenConfig
#


class GoldenConfigListView(generic.ObjectListView):
    """View for displaying the configuration management status for backup, intended, diff, and SoT Agg."""

    table = tables.GoldenConfigTable
    filterset = filters.GoldenConfigFilter
    filterset_form = forms.GoldenConfigFilterForm
    queryset = models.GoldenConfigSetting.objects.first().get_queryset()

    template_name = "nautobot_golden_config/goldenconfig_list.html"

    def extra_context(self):
        """Boilerplace code to modify data before returning."""
        return CONFIG_FEATURES

    def alter_queryset(self, request):
        """Build actual runtime queryset as the build time queryset provides no information."""
        return models.GoldenConfigSetting.objects.first().get_queryset()


class GoldenConfigBulkDeleteView(generic.BulkDeleteView):
    """Standard view for bulk deletion of data."""

    queryset = models.GoldenConfig.objects.all()
    table = tables.GoldenConfigTable
    filterset = filters.GoldenConfigFilter


#
# ConfigCompliance
#


class ConfigComplianceListView(generic.ObjectListView):
    """Django View for visualizing the compliance report."""

    filterset = filters.ConfigComplianceFilter
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
        return {"compliance": ENABLE_COMPLIANCE}

    def queryset_to_csv(self):
        """Export queryset of objects as comma-separated value (CSV)."""

        def conver_to_str(val):
            if val is False:  # pylint: disable=no-else-return
                return "non-compliant"
            elif val is True:
                return "compliant"
            return "N/A"

        csv_data = []
        headers = sorted(list(models.ConfigCompliance.objects.values_list("feature", flat=True).distinct()))
        csv_data.append(",".join(list(["Device name"] + headers)))
        for obj in self.alter_queryset(None).values():
            # From all of the unique fields, obtain the columns, using list comprehension, add values per column,
            # as some fields may not exist for every device.
            row = [Device.objects.get(id=obj["device_id"]).name] + [
                conver_to_str(obj.get(header)) for header in headers
            ]
            csv_data.append(csv_format(row))
        return "\n".join(csv_data)


class ConfigComplianceView(generic.ObjectView):
    """View for a device's specific configuration compliance feature."""

    queryset = models.ConfigCompliance.objects.all()

    def get_extra_context(self, request, instance):
        """Add extra data to detail view for Nautobot."""
        return {}


class ConfigComplianceBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more OnboardingTasks."""

    queryset = models.ConfigCompliance.objects.all()
    table = tables.ConfigComplianceDeleteTable
    filterset = filters.ConfigComplianceFilter

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
        else:
            pk_list = request.POST.getlist("pk")

        form_cls = self.get_form()

        # The difference between nautobot core is the creation and usage of obj_to_del
        obj_to_del = [item[0] for item in self.queryset.filter(device__pk__in=pk_list).values_list("id")]
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

                msg = "Deleted {} {}".format(deleted_count, model._meta.verbose_name_plural)
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
                "No {} were selected for deletion.".format(model._meta.verbose_name_plural),
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

    def get(self, request, pk, config_type):  # pylint: disable=invalid-name,too-many-branches
        """Read request into a view of a single device."""

        def diff_structured_data(b, i):
            """Utility function to provide `Unix Diff` between two files."""
            bk = yaml.safe_dump(json.loads(b))
            intend = yaml.safe_dump(json.loads(i))

            for line in difflib.unified_diff(bk.splitlines(), intend.splitlines(), lineterm=""):
                yield line

        device = Device.objects.get(pk=pk)
        config_details = models.GoldenConfig.objects.filter(device=device).first()
        structure_format = "json"
        if not config_details:
            output = ""
        elif config_type == "backup":
            output = config_details.backup_config
        elif config_type == "intended":
            output = config_details.intended_config
        elif config_type == "compliance":
            is_type_json = models.ConfigCompliance.objects.filter(device=device.id).first().rule.config_type
            print(is_type_json)
            if is_type_json == 'json':
                print("Do new logic for JSON types.")
                objs = models.ConfigCompliance.objects.filter(device=device.id)
                actual = {}
                intended = {}
                for obj in objs:
                    actual[obj.rule.feature.slug] = obj.actual
                    intended[obj.rule.feature.slug] = obj.intended

                temp_backup = json.dumps(actual, sort_keys=True)
                temp_intended = json.dumps(intended, sort_keys=True)

                config_details.compliance_config = "\n".join(diff_structured_data(temp_backup, temp_intended))
                print(f"######## actual = {actual}")
                print(f"######## intended = {intended}")
                # Do the json dumps stuff
                # Need to build the backup_config and intended_config by looping through all current configcompiance objects for the device provided.
                # Then need to run it through json dumps and sort the keys and pass the diff back in yaml.
                output = config_details.compliance_config
                print(f"###########output = {output}")
                first_occurence = output.index("@@")
                second_occurence = output.index("@@", first_occurence)
                output = (
                    "--- Backup File - "
                    + 'backup on the fly'
                    + "\n+++ Intended File - "
                    + 'intended on the fly'
                    + "\n"
                    + output[first_occurence:second_occurence]
                    + "@@"
                    + output[second_occurence + 2 :]
                )
            else:
                output = config_details.compliance_config
                if config_details.backup_last_success_date:
                    backup_date = str(config_details.backup_last_success_date.strftime("%b %d %Y"))
                else:
                    backup_date = datetime.now().strftime("%b %d %Y")
                if config_details.intended_last_success_date:
                    intended_date = str(config_details.intended_last_success_date.strftime("%b %d %Y"))
                else:
                    intended_date = datetime.now().strftime("%b %d %Y")
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

            global_settings = models.GoldenConfigSetting.objects.first()
            _, output = graph_ql_query(request, device, global_settings.sot_agg_query)

            if structure_format == "yaml":
                output = yaml.dump(json.loads(json.dumps(output)), default_flow_style=False)
            else:
                output = json.dumps(output, indent=4)

        template_name = "nautobot_golden_config/configcompliancedetails.html"
        if request.GET.get("modal") == "true":
            template_name = "nautobot_golden_config/configcompliancedetails_modal.html"

        return render(
            request,
            template_name,
            {
                "output": output,
                "device_name": device.name,
                "config_type": config_type,
                "format": structure_format,
                "device": device,
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
        labels = [item["rule__feature__slug"] for item in qs]

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


class ConfigComplianceOverview(generic.ObjectListView):
    """View for executive report on configuration compliance."""

    filterset = filters.ConfigComplianceFilter
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

        qs = self.queryset.values("rule", "count", "compliant", "non_compliant", "comp_percent")
        csv_data.append(",".join(["Total" if item == "count" else item.capitalize() for item in qs[0].keys()]))
        for obj in qs:
            csv_data.append(
                ",".join([f"{str(val)} %" if key == "comp_percent" else str(val) for key, val in obj.items()])
            )

        return "\n".join(csv_data)


#
# ComplianceFeature
#


class ComplianceFeatureListView(generic.ObjectListView):
    """View for managing the config compliance rule definition."""

    table = tables.ComplianceFeatureTable
    filterset = filters.ComplianceFeatureFilter
    filterset_form = forms.ComplianceFeatureFilterForm
    queryset = models.ComplianceFeature.objects.all()
    # TODO: Get import working
    action_buttons = ("add", "export")


class ComplianceFeatureView(generic.ObjectView):
    """View for single ComplianceFeature instance."""

    queryset = models.ComplianceFeature.objects.all()

    def get_extra_context(self, request, instance):
        """Add extra data to detail view for Nautobot."""
        return {}


class ComplianceFeatureBulkImportView(generic.BulkImportView):
    """View for bulk import of ComplianceFeature."""

    queryset = models.ComplianceFeature.objects.all()
    model_form = forms.ComplianceFeatureCSVForm
    table = tables.ComplianceFeatureTable


class ComplianceFeatureEditView(generic.ObjectEditView):
    """View for managing compliance rules."""

    queryset = models.ComplianceFeature.objects.all()
    model_form = forms.ComplianceFeatureForm


class ComplianceFeatureDeleteView(generic.ObjectDeleteView):
    """View for deleting compliance rules."""

    queryset = models.ComplianceFeature.objects.all()


class ComplianceFeatureBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting compliance rules."""

    queryset = models.ComplianceFeature.objects.all()
    table = tables.ComplianceFeatureTable


class ComplianceFeatureBulkEditView(generic.BulkEditView):
    """View for bulk deleting ComplianceFeature instance."""

    queryset = models.ComplianceFeature.objects.all()
    filterset = filters.ComplianceFeatureFilter
    table = tables.ComplianceFeatureTable
    form = forms.ComplianceFeatureBulkEditForm


#
# ComplianceRule
#


class ComplianceRuleListView(generic.ObjectListView):
    """View for managing the config compliance rule definition."""

    table = tables.ComplianceRuleTable
    filterset = filters.ComplianceRuleFilter
    filterset_form = forms.ComplianceRuleFilterForm
    queryset = models.ComplianceRule.objects.all()
    # TODO: Get import working
    action_buttons = ("add", "export")


class ComplianceRuleView(generic.ObjectView):
    """View for single ComplianceRule instance."""

    queryset = models.ComplianceRule.objects.all()

    def get_extra_context(self, request, instance):
        """Add extra data to detail view for Nautobot."""
        return {}


class ComplianceRuleBulkImportView(generic.BulkImportView):
    """View for bulk import of ComplianceRule."""

    queryset = models.ComplianceRule.objects.all()
    model_form = forms.ComplianceRuleCSVForm
    table = tables.ComplianceRuleTable


class ComplianceRuleEditView(generic.ObjectEditView):
    """View for managing compliance rules."""

    queryset = models.ComplianceRule.objects.all()
    model_form = forms.ComplianceRuleForm


class ComplianceRuleDeleteView(generic.ObjectDeleteView):
    """View for deleting compliance rules."""

    queryset = models.ComplianceRule.objects.all()


class ComplianceRuleBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting compliance rules."""

    queryset = models.ComplianceRule.objects.all()
    table = tables.ComplianceRuleTable


class ComplianceRuleBulkEditView(generic.BulkEditView):
    """View for bulk deleting ComplianceRule instance."""

    queryset = models.ComplianceRule.objects.all()
    filterset = filters.ComplianceRuleFilter
    table = tables.ComplianceRuleTable
    form = forms.ComplianceRuleBulkEditForm


#
# GoldenConfigSetting
#


class GoldenConfigSettingView(generic.ObjectView):
    """View for the only GoldenConfigSetting instance."""

    queryset = models.GoldenConfigSetting.objects.all()

    def get(self, request, *args, **kwargs):
        """Override the get parameter to get the first instance to enforce singleton pattern."""
        instance = self.queryset.first()

        return render(
            request,
            self.get_template_name(),
            {
                "object": instance,
                **self.get_extra_context(request, instance),
            },
        )

    def get_extra_context(self, request, instance):
        """Add extra data to detail view for Nautobot."""
        return {}


class GoldenConfigSettingEditView(generic.ObjectEditView):
    """View for editing the Global configurations."""

    queryset = models.GoldenConfigSetting.objects.all()
    model_form = forms.GoldenConfigSettingFeatureForm
    default_return_url = "plugins:nautobot_golden_config:goldenconfigsetting"

    def get_object(self, kwargs):
        """Override method to get first object to enforce the singleton pattern."""
        return self.queryset.first()


#
# ConfigRemove
#


class ConfigRemoveListView(generic.ObjectListView):
    """View to display the current Line Removals."""

    queryset = models.ConfigRemove.objects.all()
    table = tables.ConfigRemoveTable
    filterset = filters.ConfigRemoveFilter
    filterset_form = forms.ConfigRemoveFeatureFilterForm


class ConfigRemoveView(generic.ObjectView):
    """View for single ConfigRemove instance."""

    queryset = models.ConfigRemove.objects.all()

    def get_extra_context(self, request, instance):
        """Add extra data to detail view for Nautobot."""
        return {}


class ConfigRemoveBulkImportView(generic.BulkImportView):
    """View for bulk import of ConfigRemove."""

    queryset = models.ConfigRemove.objects.all()
    model_form = forms.ConfigRemoveCSVForm
    table = tables.ConfigRemoveTable


class ConfigRemoveBulkEditView(generic.BulkEditView):
    """View for bulk deleting ConfigRemove instances."""

    queryset = models.ConfigRemove.objects.all()
    filterset = filters.ConfigRemoveFilter
    table = tables.ConfigRemoveTable
    form = forms.ConfigRemoveBulkEditForm


class ConfigRemoveEditView(generic.ObjectEditView):
    """View for editing the current Line Removals."""

    queryset = models.ConfigRemove.objects.all()
    model_form = forms.ConfigRemoveForm


class ConfigRemoveDeleteView(generic.ObjectDeleteView):
    """View for deleting a ConfigRemove instance."""

    queryset = models.ConfigRemove.objects.all()


class ConfigRemoveBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting Line Removals."""

    queryset = models.ConfigRemove.objects.all()
    table = tables.ConfigRemoveTable


#
# ConfigReplace
#


class ConfigReplaceListView(generic.ObjectListView):
    """View for displaying the current Line Replacements."""

    queryset = models.ConfigReplace.objects.all()
    table = tables.ConfigReplaceTable
    filterset = filters.ConfigReplaceFilter
    filterset_form = forms.ConfigReplaceFeatureFilterForm


class ConfigReplaceView(generic.ObjectView):
    """View for single ConfigReplace instance."""

    queryset = models.ConfigReplace.objects.all()

    def get_extra_context(self, request, instance):
        """Add extra data to detail view for Nautobot."""
        return {}


class ConfigReplaceEditView(generic.ObjectEditView):
    """View for editing the current Line Replacements."""

    queryset = models.ConfigReplace.objects.all()
    model_form = forms.ConfigReplaceForm


class ConfigReplaceBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting Line Replacements."""

    queryset = models.ConfigReplace.objects.all()
    table = tables.ConfigReplaceTable


class ConfigReplaceBulkImportView(generic.BulkImportView):
    """View for bulk import of ConfigReplace."""

    queryset = models.ConfigReplace.objects.all()
    model_form = forms.ConfigReplaceCSVForm
    table = tables.ConfigReplaceTable


class ConfigReplaceDeleteView(generic.ObjectDeleteView):
    """View for deleting a ConfigReplace instance."""

    queryset = models.ConfigReplace.objects.all()


class ConfigReplaceBulkEditView(generic.BulkEditView):
    """View for bulk deleting ConfigReplace instances."""

    queryset = models.ConfigReplace.objects.all()
    filterset = filters.ConfigReplaceFilter
    table = tables.ConfigReplaceTable
    form = forms.ConfigReplaceBulkEditForm
