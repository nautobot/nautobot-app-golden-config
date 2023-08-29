"""Nautobot Golden Config plugin application level metrics ."""
from django.conf import settings
from django.db.models import Count, F, Q
from nautobot.dcim.models import Device
from prometheus_client.core import GaugeMetricFamily

from nautobot_golden_config.models import ComplianceFeature, ComplianceRule, ConfigCompliance, GoldenConfig

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("nautobot_golden_config", {})


def metric_gc_functions():
    """Calculate the successful vs the failed GC jobs for backups, intended & compliance.

    Yields:
        GaugeMetricFamily: Prometheus Metrics
    """
    backup_gauges = GaugeMetricFamily("nautobot_gc_backup_total", "Nautobot Golden Config Backups", labels=["status"])

    successful_backups = GoldenConfig.objects.filter(backup_last_attempt_date=F("backup_last_success_date")).count()
    attempted_backups = GoldenConfig.objects.filter(backup_last_attempt_date__isnull=False).count()

    backup_gauges.add_metric(labels=["success"], value=successful_backups)
    backup_gauges.add_metric(labels=["failure"], value=attempted_backups - successful_backups)

    yield backup_gauges

    intended_gauges = GaugeMetricFamily(
        "nautobot_gc_intended_total", "Nautobot Golden Config Intended", labels=["status"]
    )

    successful_intended = GoldenConfig.objects.filter(
        intended_last_attempt_date=F("intended_last_success_date")
    ).count()
    attempted_intended = GoldenConfig.objects.filter(intended_last_attempt_date__isnull=False).count()

    intended_gauges.add_metric(labels=["success"], value=successful_intended)
    intended_gauges.add_metric(labels=["failure"], value=attempted_intended - successful_intended)

    yield intended_gauges

    compliance_gauges = GaugeMetricFamily(
        "nautobot_gc_compliance_total", "Nautobot Golden Config Compliance", labels=["status"]
    )

    successful_compliance = GoldenConfig.objects.filter(
        compliance_last_attempt_date=F("compliance_last_success_date")
    ).count()
    attempted_compliance = GoldenConfig.objects.filter(compliance_last_attempt_date__isnull=False).count()

    compliance_gauges.add_metric(labels=["success"], value=successful_compliance)
    compliance_gauges.add_metric(labels=["failure"], value=attempted_compliance - successful_compliance)

    yield compliance_gauges


def metric_devices_per_feature():
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


def metric_compliance_devices():
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

    counters = {item["rule__feature__slug"]: {"compliant": 0, "non_compliant": 0} for item in queryset}

    for feature in queryset:
        counters[feature["rule__feature__slug"]]["compliant"] += feature["compliant"]
        counters[feature["rule__feature__slug"]]["non_compliant"] += feature["non_compliant"]

    for feature, counter_value in counters.items():
        compliance_gauge.add_metric(labels=[feature, "true"], value=counter_value["compliant"])
        compliance_gauge.add_metric(labels=[feature, "false"], value=counter_value["non_compliant"])

    yield compliance_gauge


metrics = [metric_gc_functions, metric_devices_per_feature, metric_compliance_devices]
