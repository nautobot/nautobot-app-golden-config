"""Test ComplianceFeature."""

from nautobot.apps.testing import ModelTestCases

from nautobot_golden_config import models
from nautobot_golden_config.tests import fixtures


class TestComplianceFeature(ModelTestCases.BaseModelTestCase):
    """Test ComplianceFeature."""

    model = models.ComplianceFeature

    @classmethod
    def setUpTestData(cls):
        """Create test data for ComplianceFeature Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        fixtures.create_compliancefeature()

    def test_create_compliancefeature_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        compliancefeature = models.ComplianceFeature.objects.create(name="Development")
        self.assertEqual(compliancefeature.name, "Development")
        self.assertEqual(compliancefeature.description, "")
        self.assertEqual(str(compliancefeature), "Development")

    def test_create_compliancefeature_all_fields_success(self):
        """Create ComplianceFeature with all fields."""
        compliancefeature = models.ComplianceFeature.objects.create(name="Development", description="Development Test")
        self.assertEqual(compliancefeature.name, "Development")
        self.assertEqual(compliancefeature.description, "Development Test")
