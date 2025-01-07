"""Test ComplianceFeature."""

from django.test import TestCase

from nautobot_golden_config import models


class TestComplianceFeature(TestCase):
    """Test ComplianceFeature."""

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
