"""Django urlpatterns declaration for config compliance plugin."""
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

urlpatterns = router.urls
