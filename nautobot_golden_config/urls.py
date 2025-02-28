"""Django urlpatterns declaration for nautobot_golden_config app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

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
    path("generate-intended-config/", views.GenerateIntendedConfigView.as_view(), name="generate_intended_config"),
    path("docs/", RedirectView.as_view(url=static("nautobot_golden_config/docs/index.html")), name="docs"),
]

urlpatterns += router.urls
