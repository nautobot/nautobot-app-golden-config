"""Django urlpatterns declaration for config compliance app."""
from django.urls import path

from nautobot.core.views.routers import NautobotUIViewSetRouter
from nautobot_golden_config import views

app_name = "nautobot_golden_config"

router = NautobotUIViewSetRouter()
router.register("compliance-feature", views.ComplianceFeatureUIViewSet)
router.register("compliance-rule", views.ComplianceRuleUIViewSet)
router.register("golden-config-setting", views.GoldenConfigSettingUIViewSet)
router.register("config-remove", views.ConfigRemoveUIViewSet)
router.register("config-replace", views.ConfigReplaceUIViewSet)
router.register("remediation-setting", views.RemediationSettingUIViewSet)
router.register("config-plan", views.ConfigPlanUIViewSet)
router.register("config-compliance", views.ConfigComplianceUIViewSet)
router.register("golden-config", views.GoldenConfigUIViewSet)

urlpatterns = [
    path("config-compliance/overview/", views.ConfigComplianceOverview.as_view(), name="configcompliance_overview"),
    path("config-plan/bulk_deploy/", views.ConfigPlanBulkDeploy.as_view(), name="configplan_bulk-deploy"),
] + router.urls
