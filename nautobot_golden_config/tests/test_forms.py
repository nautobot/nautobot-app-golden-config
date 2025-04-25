"""Test compliancefeature forms."""

from django.test import TestCase

from nautobot_golden_config import forms


class ComplianceFeatureTest(TestCase):
    """Test ComplianceFeature forms."""

    def test_specifying_all_fields_success(self):
        form = forms.ComplianceFeatureForm(
            data={
                "name": "Development",
                "description": "Development Testing",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = forms.ComplianceFeatureForm(
            data={
                "name": "Development",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_compliancefeature_is_required(self):
        form = forms.ComplianceFeatureForm(data={"description": "Development Testing"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])
