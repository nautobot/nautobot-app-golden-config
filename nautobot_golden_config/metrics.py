"""Nautobot Golden Config plugin application level metrics ."""
from datetime import datetime, timedelta

from django.conf import settings
from prometheus_client import Gauge
from prometheus_client.core import GaugeMetricFamily

from nautobot_golden_config.models import GoldenConfig

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("nautobot_golden_config", {})

number_of_devices_metric = Gauge(
    "nautobot_gc_devices_total", "Amount of devices GC functions ran on", ["use_case"], multiprocess_mode="max"
)


def metric_backup():
    backup_gauges = GaugeMetricFamily(
        "nautobot_gc_backup_total",
        "Nautobot Golden Config Backups",
        labels=["seconds", "status"]
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
        "nautobot_gc_intended_total",
        "Nautobot Golden Config Intended",
        labels=["seconds", "status"]
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


metrics = [metric_backup]
