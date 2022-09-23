"""API for Custom Jobs ."""

from django.urls import path
from nautobot.core.api import OrderedDefaultRouter

from nautobot_golden_config.api import views

router = OrderedDefaultRouter()
router.APIRootView = views.GoldenConfigRootView
router.register("compliance-feature", views.ComplianceFeatureViewSet)
router.register("compliance-rule", views.ComplianceRuleViewSet)
router.register("config-compliance", views.ConfigComplianceViewSet)
router.register("golden-config", views.GoldenConfigViewSet)
router.register("golden-config-settings", views.GoldenConfigSettingViewSet)
router.register("config-remove", views.ConfigRemoveViewSet)
router.register("config-replace", views.ConfigReplaceViewSet)
router.register("config-postprocessing", views.ConfigToPushViewSet)
urlpatterns = router.urls
urlpatterns.append(
    path(
        "sotagg/<uuid:pk>/",
        views.SOTAggDeviceDetailView.as_view(),
        name="device_detail",
    )
)
