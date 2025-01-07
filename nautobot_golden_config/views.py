"""Views for nautobot_golden_config."""

from nautobot.apps.views import NautobotUIViewSet

from nautobot_golden_config import filters, forms, models, tables
from nautobot_golden_config.api import serializers


class ComplianceFeatureUIViewSet(NautobotUIViewSet):
    """ViewSet for ComplianceFeature views."""

    bulk_update_form_class = forms.ComplianceFeatureBulkEditForm
    filterset_class = filters.ComplianceFeatureFilterSet
    filterset_form_class = forms.ComplianceFeatureFilterForm
    form_class = forms.ComplianceFeatureForm
    lookup_field = "pk"
    queryset = models.ComplianceFeature.objects.all()
    serializer_class = serializers.ComplianceFeatureSerializer
    table_class = tables.ComplianceFeatureTable
