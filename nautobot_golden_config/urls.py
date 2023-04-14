"""Django urlpatterns declaration for config compliance plugin."""
from django.urls import path

from nautobot.extras.views import ObjectChangeLogView, ObjectNotesView
from nautobot.core.views.routers import NautobotUIViewSetRouter
from nautobot_golden_config import views, models

app_name = "nautobot_golden_config"

router = NautobotUIViewSetRouter()
router.register("compliance-feature", views.ComplianceFeatureUIViewSet)
router.register("compliance-rule", views.ComplianceRuleUIViewSet)
router.register("golden-config-setting", views.GoldenConfigSettingUIViewSet)
router.register("config-remove", views.ConfigRemoveUIViewSet)
router.register("config-replace", views.ConfigReplaceUIViewSet)

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
    path(
        "compliance-rule/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="compliancerule_changelog",
        kwargs={"model": models.ComplianceRule},
    ),
    path(
        "compliance-feature/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="compliancefeature_changelog",
        kwargs={"model": models.ComplianceFeature},
    ),
    path(
        "golden-config-setting/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="goldenconfigsetting_changelog",
        kwargs={"model": models.GoldenConfigSetting},
    ),
    path(
        "config-remove/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="configremove_changelog",
        kwargs={"model": models.ConfigRemove},
    ),
    path(
        "config-replace/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="configreplace_changelog",
        kwargs={"model": models.ConfigReplace},
    ),
    path(
        "compliance-rule/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="compliancerule_notes",
        kwargs={"model": models.ComplianceRule},
    ),
    path(
        "compliance-feature/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="compliancefeature_notes",
        kwargs={"model": models.ComplianceFeature},
    ),
    path(
        "golden-config-setting/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="goldenconfigsetting_notes",
        kwargs={"model": models.GoldenConfigSetting},
    ),
    path(
        "config-remove/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="configremove_notes",
        kwargs={"model": models.ConfigRemove},
    ),
    path(
        "config-replace/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="configreplace_notes",
        kwargs={"model": models.ConfigReplace},
    ),
] + router.urls

print([i for i in urlpatterns])