"""Utility functions for working with mathplotlib."""

import base64
import io
import logging
import urllib

import matplotlib.pyplot as plt
import numpy as np
from django.db.models import Count, Q
from nautobot.core.choices import ColorChoices

from nautobot_golden_config.utilities import constant

GREEN = "#" + ColorChoices.COLOR_GREEN
RED = "#" + ColorChoices.COLOR_RED


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


def get_global_aggr(queryset, filterset, filter_params):
    """Get device and feature global reports.

    Returns:
        device_aggr: device global report dict
        feature_aggr: feature global report dict
    """
    device_aggr, feature_aggr = {}, {}
    if filterset is not None:
        device_aggr = (
            filterset(filter_params, queryset)
            .qs.values("device")
            .annotate(compliant=Count("device", filter=Q(compliance=False)))
            .aggregate(total=Count("device", distinct=True), compliants=Count("compliant", filter=Q(compliant=0)))
        )

        feature_aggr = filterset(filter_params, queryset).qs.aggregate(
            total=Count("rule"), compliants=Count("rule", filter=Q(compliance=True))
        )

    return (
        calculate_aggr_percentage(device_aggr),
        calculate_aggr_percentage(feature_aggr),
    )
