from prometheus_client import Gauge

number_of_devices_metric = Gauge(
    "nautobot_gc_devices_total", "Amount of devices GC functions ran on", ["use_case"], multiprocess_mode="max"
)
