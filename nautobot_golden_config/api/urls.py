"""Django API urlpatterns declaration for nautobot_golden_config app."""

from django.urls import path
from nautobot.apps.api import OrderedDefaultRouter

from nautobot_golden_config.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.APIRootView = views.GoldenConfigRootView
router.register("compliance-feature", views.ComplianceFeatureViewSet)
router.register("compliance-rule", views.ComplianceRuleViewSet)
router.register("config-compliance", views.ConfigComplianceViewSet)
router.register("golden-config", views.GoldenConfigViewSet)
router.register("golden-config-settings", views.GoldenConfigSettingViewSet)
router.register("config-remove", views.ConfigRemoveViewSet)
router.register("config-replace", views.ConfigReplaceViewSet)
router.register("remediation-setting", views.RemediationSettingViewSet)
router.register("config-postprocessing", views.ConfigToPushViewSet)
router.register("config-plan", views.ConfigPlanViewSet)

urlpatterns = [
    path(
        "sotagg/<uuid:pk>/",
        views.SOTAggDeviceDetailView.as_view(),
        name="device_detail",
    ),
    path(
        "generate-intended-config/",
        views.GenerateIntendedConfigView.as_view(),
        name="generate_intended_config",
    ),
    path(
        "git-repository-branches/<pk>/",
        views.GitRepositoryBranchesView.as_view(),
        name="git_repository_branches",
    ),
]
app_name = "nautobot_golden_config-api"
urlpatterns += router.urls
