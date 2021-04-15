"""API for Custom Jobs ."""

from django.urls import path
from rest_framework import routers

from . import views

app_name = "nautobot_golden_config"

router = routers.DefaultRouter()
router.register("line_remove", views.BackupConfigLineRemovalViewSet)
router.register("line_replace", views.BackupConfigLineReplaceViewSet)
urlpatterns = router.urls
urlpatterns.append(path(
        "sotagg/<str:device_name>/",
        views.SOTAggDeviceDetailView.as_view(),
        name="device_detail",
    ))
