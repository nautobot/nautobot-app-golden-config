"""Test ComplianceFeature Filter."""

from django.test import TestCase

from nautobot_golden_config import filters, models
from nautobot_golden_config.tests import fixtures


class ComplianceFeatureFilterTestCase(TestCase):
    """ComplianceFeature Filter Test Case."""

    queryset = models.ComplianceFeature.objects.all()
    filterset = filters.ComplianceFeatureFilterSet

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
