"""Django API urlpatterns declaration for nautobot_golden_config app."""

from nautobot.apps.api import OrderedDefaultRouter

from nautobot_golden_config.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("compliancefeature", views.ComplianceFeatureViewSet)

urlpatterns = router.urls
