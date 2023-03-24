"""Nautobot Golden Config plugin application level metrics ."""
from datetime import datetime, timedelta

from django.conf import settings
from prometheus_client import Gauge
from django.db.models import Count, Q
from prometheus_client.core import GaugeMetricFamily
from nautobot.dcim.models import Device
from nautobot_golden_config.models import GoldenConfig, ComplianceFeature, ComplianceRule, ConfigCompliance

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("nautobot_golden_config", {})

number_of_devices_metric = Gauge(
    "nautobot_gc_devices_total", "Amount of devices GC functions ran on", ["use_case"], multiprocess_mode="max"
)


def metric_gc_jobs():
    """Calculate the successful vs the failed GC jobs for backups, intended & compliance.

    Yields:
        GaugeMetricFamily: Prometheus Metrics
    """
    backup_gauges = GaugeMetricFamily(
        "nautobot_gc_backup_total", "Nautobot Golden Config Backups", labels=["seconds", "status"]
    )
    time_delta_to_include = PLUGIN_SETTINGS.get("metrics", {}).get("time_delta", timedelta(days=1))
    start_inclusion_date = datetime.now() - time_delta_to_include

    successful_backups = GoldenConfig.objects.filter(backup_last_success_date__gte=start_inclusion_date)
    attempted_backups = GoldenConfig.objects.filter(backup_last_attempt_date__gte=start_inclusion_date)

    backup_gauges.add_metric(
        labels=[str(int(time_delta_to_include.total_seconds())), "success"],
        value=successful_backups.count(),
    )
    backup_gauges.add_metric(
        labels=[str(int(time_delta_to_include.total_seconds())), "failure"],
        value=attempted_backups.count() - successful_backups.count(),
    )

    yield backup_gauges

    intended_gauges = GaugeMetricFamily(
        "nautobot_gc_intended_total", "Nautobot Golden Config Intended", labels=["seconds", "status"]
    )

    successful_intended = GoldenConfig.objects.filter(intended_last_success_date__gte=start_inclusion_date)
    attempted_intended = GoldenConfig.objects.filter(intended_last_attempt_date__gte=start_inclusion_date)

    intended_gauges.add_metric(
        labels=[str(int(time_delta_to_include.total_seconds())), "success"],
        value=successful_intended.count(),
    )
    intended_gauges.add_metric(
        labels=[str(int(time_delta_to_include.total_seconds())), "failure"],
        value=attempted_intended.count() - successful_intended.count(),
    )

    yield intended_gauges

    compliance_gauges = GaugeMetricFamily(
        "nautobot_gc_compliance_total", "Nautobot Golden Config Compliance", labels=["seconds", "status"]
    )

    successful_compliance = GoldenConfig.objects.filter(compliance_last_success_date__gte=start_inclusion_date)
    attempted_compliance = GoldenConfig.objects.filter(compliance_last_attempt_date__gte=start_inclusion_date)

    compliance_gauges.add_metric(
        labels=[str(int(time_delta_to_include.total_seconds())), "success"],
        value=successful_compliance.count(),
    )

    compliance_gauges.add_metric(
        labels=[str(int(time_delta_to_include.total_seconds())), "failure"],
        value=attempted_compliance.count() - successful_compliance.count(),
    )

    yield compliance_gauges


def metric_golden_config():
    """Calculate number of devices configured for GC Compliance feature.

    Yields:
        GaugeMetricFamily: Prometheus Metrics
    """
    features = ComplianceFeature.objects.all()

    devices_gauge = GaugeMetricFamily(
        "nautobot_gc_devices_per_feature", "Nautobot Golden Config Devices per feature", labels=["device"]
    )

    for feature in features:
        rules_per_feature = ComplianceRule.objects.filter(feature=feature)
        if rules_per_feature:
            devices_gauge.add_metric(
                labels=[feature.name], value=Device.objects.filter(platform=rules_per_feature.first().platform).count()
            )
        else:
            devices_gauge.add_metric(labels=[feature.name], value=0)

    yield devices_gauge


def metric_compliance():
    """Calculate Compliant & Non-Compliant total number of devices per feature.

    Yields:
        GaugeMetricFamily: Prometheus Metrics
    """
    compliance_gauge = GaugeMetricFamily(
        "nautobot_gc_compliant_devices_by_feature_total",
        "Nautobot Golden Config Compliance",
        labels=["feature", "compliant"],
    )
    queryset = ConfigCompliance.objects.values("rule__feature__slug").annotate(
        compliant=Count("rule__feature__slug", filter=Q(compliance=True)),
        non_compliant=Count("rule__feature__slug", filter=~Q(compliance=True)),
    )

    for feature in queryset:
        compliance_gauge.add_metric(labels=[feature["rule__feature__slug"], "true"], value=feature["compliant"])
        compliance_gauge.add_metric(labels=[feature["rule__feature__slug"], "false"], value=feature["non_compliant"])

    yield compliance_gauge


metrics = [metric_gc_jobs, metric_golden_config, metric_compliance]
