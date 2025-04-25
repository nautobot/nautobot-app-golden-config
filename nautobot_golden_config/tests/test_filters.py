"""Test ComplianceFeature Filter."""

from nautobot.apps.testing import FilterTestCases

from nautobot_golden_config import filters, models
from nautobot_golden_config.tests import fixtures


class ComplianceFeatureFilterTestCase(FilterTestCases.FilterTestCase):
    """ComplianceFeature Filter Test Case."""

    queryset = models.ComplianceFeature.objects.all()
    filterset = filters.ComplianceFeatureFilterSet
    generic_filter_tests = (
        ("id",),
        ("created",),
        ("last_updated",),
        ("name",),
    )

    @classmethod
    def setUpTestData(cls):
        """Setup test data for ComplianceFeature Model."""
        fixtures.create_compliancefeature()

    def test_q_search_name(self):
        """Test using Q search with name of ComplianceFeature."""
        params = {"q": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for ComplianceFeature."""
        params = {"q": "test-five"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
