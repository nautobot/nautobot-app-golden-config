"""Django urlpatterns declaration for config compliance plugin."""
from django.urls import path

from nautobot.extras.views import ObjectChangeLogView
from nautobot_golden_config import views, models

app_name = "nautobot_golden_config"

urlpatterns = [
    path("golden/", views.GoldenConfigListView.as_view(), name="goldenconfig_list"),
    path("golden/delete/", views.GoldenConfigBulkDeleteView.as_view(), name="goldenconfig_bulk_delete"),
    path("config-compliance/", views.ConfigComplianceListView.as_view(), name="configcompliance_list"),
    path("config-compliance/delete/", views.ConfigComplianceBulkDeleteView.as_view(), name="compliance_bulk_delete"),
    path("config-compliance/overview/", views.ConfigComplianceOverview.as_view(), name="configcompliance_report"),
    path("config-compliance/<uuid:pk>", views.ConfigComplianceView.as_view(), name="configcompliance"),
    path(
        "config-compliance/devicedetail/<uuid:pk>",
        views.ConfigComplianceDeviceView.as_view(),
        name="configcompliance_devicedetail",
    ),
    path(
        "config-compliance/<uuid:pk>/delete/",
        views.ConfigComplianceDeleteView.as_view(),
        name="configcompliance_delete",
    ),
    path(
        "config-compliance/details/<uuid:pk>/<str:config_type>/",
        views.ConfigComplianceDetails.as_view(),
        name="configcompliance_details",
    ),
    path(
        "config-compliance/filtered/<uuid:pk>/<str:compliance>/",
        views.ComplianceDeviceFilteredReport.as_view(),
        name="configcompliance_filter_report",
    ),
    path(
        "config-compliance/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="configcompliance_changelog",
        kwargs={"model": models.ConfigCompliance},
    ),
    path("compliance-rule/", views.ComplianceRuleListView.as_view(), name="compliancerule_list"),
    path("compliance-rule/add/", views.ComplianceRuleEditView.as_view(), name="compliancerule_add"),
    path(
        "compliance-rule/import/",
        views.ComplianceRuleBulkImportView.as_view(),
        name="compliancerule_import",
    ),
    path(
        "compliance-rule/delete/",
        views.ComplianceRuleBulkDeleteView.as_view(),
        name="compliancerule_bulk_delete",
    ),
    path("compliance-rule/<uuid:pk>/", views.ComplianceRuleView.as_view(), name="compliancerule"),
    path("compliance-rule/edit/", views.ConfigReplaceBulkEditView.as_view(), name="compliancerule_bulk_edit"),
    path("compliance-rule/<uuid:pk>/edit/", views.ComplianceRuleEditView.as_view(), name="compliancerule_edit"),
    path(
        "compliance-rule/<uuid:pk>/delete/",
        views.ComplianceRuleDeleteView.as_view(),
        name="compliancerule_delete",
    ),
    path(
        "compliance-rule/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="compliancerule_changelog",
        kwargs={"model": models.ComplianceRule},
    ),
    path("compliance-feature/", views.ComplianceFeatureListView.as_view(), name="compliancefeature_list"),
    path("compliance-feature/add/", views.ComplianceFeatureEditView.as_view(), name="compliancefeature_add"),
    path(
        "compliance-feature/delete/",
        views.ComplianceFeatureBulkDeleteView.as_view(),
        name="compliancefeature_bulk_delete",
    ),
    path("compliance-feature/<uuid:pk>/", views.ComplianceFeatureView.as_view(), name="compliancefeature"),
    path("compliance-feature/edit/", views.ComplianceFeatureBulkEditView.as_view(), name="compliancefeature_bulk_edit"),
    path(
        "compliance-feature/<uuid:pk>/edit/", views.ComplianceFeatureEditView.as_view(), name="compliancefeature_edit"
    ),
    path(
        "compliance-feature/<uuid:pk>/delete/",
        views.ComplianceFeatureDeleteView.as_view(),
        name="compliancefeature_delete",
    ),
    path(
        "compliance-feature/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="compliancefeature_changelog",
        kwargs={"model": models.ComplianceFeature},
    ),
    path("setting/", views.GoldenConfigSettingListView.as_view(), name="goldenconfigsetting_list"),
    path("setting/add/", views.GoldenConfigSettingCreateView.as_view(), name="goldenconfigsetting_add"),
    path("setting/delete/", views.GoldenConfigSettingBulkDeleteView.as_view(), name="goldenconfigsetting_bulk_delete"),
    path(
        "setting/<slug:slug>/delete/", views.GoldenConfigSettingDeleteView.as_view(), name="goldenconfigsetting_delete"
    ),
    path("setting/<slug:slug>/edit/", views.GoldenConfigSettingEditView.as_view(), name="goldenconfigsetting_edit"),
    path(
        "setting/<slug:slug>/changelog/",
        ObjectChangeLogView.as_view(),
        name="goldenconfigsetting_changelog",
        kwargs={"model": models.GoldenConfigSetting},
    ),
    path("setting/<slug:slug>/", views.GoldenConfigSettingView.as_view(), name="goldenconfigsetting"),
    path("config-remove/", views.ConfigRemoveListView.as_view(), name="configremove_list"),
    path("config-remove/add/", views.ConfigRemoveEditView.as_view(), name="configremove_add"),
    path(
        "config-remove/import/",
        views.ConfigRemoveBulkImportView.as_view(),
        name="configremove_import",
    ),
    path(
        "config-remove/edit/",
        views.ConfigRemoveBulkEditView.as_view(),
        name="configremove_bulk_edit",
    ),
    path(
        "config-remove/delete/",
        views.ConfigRemoveBulkDeleteView.as_view(),
        name="configremove_bulk_delete",
    ),
    path(
        "config-remove/<uuid:pk>/delete/",
        views.ConfigRemoveDeleteView.as_view(),
        name="configremove_delete",
    ),
    path("config-remove/<uuid:pk>/", views.ConfigRemoveView.as_view(), name="configremove"),
    path(
        "config-remove/<uuid:pk>/edit/",
        views.ConfigRemoveEditView.as_view(),
        name="configremove_edit",
    ),
    path(
        "config-remove/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="configremove_changelog",
        kwargs={"model": models.ConfigRemove},
    ),
    path("config-replace/", views.ConfigReplaceListView.as_view(), name="configreplace_list"),
    path("config-replace/add/", views.ConfigReplaceEditView.as_view(), name="configreplace_add"),
    path("config-replace/import/", views.ConfigReplaceBulkImportView.as_view(), name="configreplace_import"),
    path("config-replace/edit/", views.ConfigReplaceBulkEditView.as_view(), name="configreplace_bulk_edit"),
    path(
        "config-replace/delete/",
        views.ConfigReplaceBulkDeleteView.as_view(),
        name="configreplace_bulk_delete",
    ),
    path("config-replace/<uuid:pk>/", views.ConfigReplaceView.as_view(), name="configreplace"),
    path("config-replace/<uuid:pk>/edit/", views.ConfigReplaceEditView.as_view(), name="configreplace_edit"),
    path(
        "config-replace/<uuid:pk>/delete/",
        views.ConfigReplaceDeleteView.as_view(),
        name="configreplace_delete",
    ),
    path(
        "config-replace/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="configreplace_changelog",
        kwargs={"model": models.ConfigReplace},
    ),
]
