"""Django urlpatterns declaration for nautobot_golden_config app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter


from nautobot_golden_config import views


router = NautobotUIViewSetRouter()

router.register("compliancefeature", views.ComplianceFeatureUIViewSet)


urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("nautobot_golden_config/docs/index.html")), name="docs"),
]

urlpatterns += router.urls
