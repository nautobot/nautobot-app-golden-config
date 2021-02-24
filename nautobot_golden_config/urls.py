"""Django urlpatterns declaration for config compliance plugin."""
from django.urls import path

from . import views

app_name = "nautobot_golden_config"

urlpatterns = [
    path("home/", views.Home.as_view(), name="home"),
    path("home/delete/", views.HomeBulkDeleteView.as_view(), name="home_bulk_delete"),
    path("report/", views.ComplianceReport.as_view(), name="config_report"),
    path("report/<str:device_name>", views.ComplianceDeviceReport.as_view(), name="device_report"),
    path(
        "report/<str:device_name>/<str:compliance>/",
        views.ComplianceDeviceFilteredReport.as_view(),
        name="device_filter_report",
    ),
    path("report/delete/", views.ComplianceBulkDeleteView.as_view(), name="compliance_bulk_delete"),
    path("overview-report/", views.ComplianceOverviewReport.as_view(), name="compliance_overview_report"),
    path("config-details/<str:device_name>/<str:config_type>/", views.ConfigDetails.as_view(), name="config_details"),
    path("compliance-features/", views.ComplianceFeatureView.as_view(), name="compliancefeature_list"),
    path("compliance-features/add/", views.ComplianceFeatureEditView.as_view(), name="compliancefeature_add"),
    path(
        "compliance-features/delete/",
        views.ComplianceFeatureBulkDeleteView.as_view(),
        name="compliancefeature_bulk_delete",
    ),
    path(
        "compliance-features/<uuid:pk>/edit/", views.ComplianceFeatureEditView.as_view(), name="compliancefeature_edit"
    ),
    path(
        "compliance-features/<uuid:pk>/delete/",
        views.ComplianceFeatureDeleteView.as_view(),
        name="compliancefeature_delete",
    ),
    path("settings/<uuid:pk>/edit/", views.GoldenConfigSettingsEditView.as_view(), name="goldenconfigsettings_edit"),
]
