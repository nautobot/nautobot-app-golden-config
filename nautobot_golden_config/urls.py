"""Django urlpatterns declaration for config compliance plugin."""
from django.urls import path

from nautobot.extras.views import ObjectChangeLogView
from . import views, models

app_name = "nautobot_golden_config"

urlpatterns = [
    path("golden/", views.GoldenConfigurationListView.as_view(), name="goldenconfiguration_list"),
    path("golden/delete/", views.GoldenConfigurationBulkDeleteView.as_view(), name="goldenconfiguration_bulk_delete"),
    path("config-compliance/", views.ConfigComplianceListView.as_view(), name="configcompliance_list"),
    path("config-compliance/delete/", views.ConfigComplianceBulkDeleteView.as_view(), name="compliance_bulk_delete"),
    path("config-compliance/overview/", views.ConfigComplianceOverview.as_view(), name="configcompliance_report"),
    path("config-compliance/<str:device_name>", views.ConfigComplianceView.as_view(), name="configcompliance"),
    path(
        "config-compliance/<str:device_name>/<str:config_type>/",
        views.ConfigComplianceDetails.as_view(),
        name="configcompliance_details",
    ),
    path(
        "config-compliance/filtered/<str:device_name>/<str:compliance>/",
        views.ComplianceDeviceFilteredReport.as_view(),
        name="configcompliance_filter_report",
    ),
    path("compliance-features/", views.ComplianceFeatureListView.as_view(), name="compliancefeature_list"),
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
    path("settings/", views.GoldenConfigSettingsListView.as_view(), name="goldenconfigsettings_list"),
    path("settings/view/", views.GoldenConfigSettingsView.as_view(), name="goldenconfigsettings"),
    path("settings/edit/", views.GoldenConfigSettingsEditView.as_view(), name="goldenconfigsettings_edit"),
    path(
        "settings/changelog/",
        ObjectChangeLogView.as_view(),
        name="goldenconfigsettings_changelog",
        kwargs={"model": models.GoldenConfigSettings},
    ),
    path("line-removal/", views.BackupConfigLineRemoveListView.as_view(), name="backupconfiglineremove_list"),
    path("line-removal/<uuid:pk>/", views.BackupConfigLineRemoveView.as_view(), name="backupconfiglineremove"),
    path("line-removal/add/", views.BackupConfigLineRemoveEditView.as_view(), name="backupconfiglineremove_add"),
    path(
        "line-removal/<uuid:pk>/edit/",
        views.BackupConfigLineRemoveEditView.as_view(),
        name="backupconfiglineremove_edit",
    ),
    path(
        "line-removal/delete/",
        views.BackupConfigLineRemoveBulkDeleteView.as_view(),
        name="backupconfiglineremove_bulk_delete",
    ),
    path("line-replace/", views.BackupConfigLineReplaceListView.as_view(), name="backuplinereplace_list"),
    path("line-replace/add/", views.BackupConfigLineReplaceEditView.as_view(), name="backuplinereplace_add"),
    path(
        "line-replace/<uuid:pk>/edit/", views.BackupConfigLineReplaceEditView.as_view(), name="backuplinereplace_edit"
    ),
    path(
        "line-replace/delete/",
        views.BackupConfigLineReplaceBulkDeleteView.as_view(),
        name="backuplinereplace_bulk_delete",
    ),
]
