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
    path("settings/", views.GoldenConfigSettingsView.as_view(), name="goldenconfigsettings"),
    path("settings/<uuid:pk>/edit/", views.GoldenConfigSettingsEditView.as_view(), name="goldenconfigsettings_edit"),
    path("line-removal/", views.BackupConfigLineRemovalView.as_view(), name="backuplineremoval"),
    path("line-removal/add/", views.BackupConfigLineRemovalEditView.as_view(), name="backuplineremoval_add"),
    path(
        "line-removal/<str:name>/edit/", views.BackupConfigLineRemovalEditView.as_view(), name="backuplineremoval_edit"
    ),
    path(
        "line-removal/delete/",
        views.BackupConfigLineRemovalBulkDeleteView.as_view(),
        name="backuplineremoval_bulk_delete",
    ),
    path("line-replace/", views.BackupConfigLineReplaceView.as_view(), name="backuplinereplace"),
    path("line-replace/add/", views.BackupConfigLineReplaceEditView.as_view(), name="backuplinereplace_add"),
    path(
        "line-replace/<str:name>/edit/", views.BackupConfigLineReplaceEditView.as_view(), name="backuplinereplace_edit"
    ),
    path(
        "line-replace/delete/",
        views.BackupConfigLineReplaceBulkDeleteView.as_view(),
        name="backuplinereplace_bulk_delete",
    ),
]
