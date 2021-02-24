"""API for Custom Jobs ."""

from django.urls import path

from . import views

app_name = "nautobot_golden_config"
urlpatterns = [
    path(
        "sotagg/<str:device_name>/",
        views.SOTAggDeviceDetailView.as_view(),
        name="device_detail",
    ),
]
