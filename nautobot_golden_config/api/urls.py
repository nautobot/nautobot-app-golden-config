"""Django API urlpatterns declaration for nautobot_golden_config app."""

from django.urls import path
from nautobot.apps.api import OrderedDefaultRouter

from nautobot_golden_config.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("compliance-features", views.ComplianceFeatureViewSet)

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
