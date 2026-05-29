"""Test forms for nautobot_golden_config."""

from django.test import TestCase
from nautobot.dcim.models import Platform

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.forms import ComplianceRuleForm
from nautobot_golden_config.models import ComplianceFeature


class ComplianceRuleFormTestCase(TestCase):
    """Test ComplianceRuleForm."""

    form_class = ComplianceRuleForm

    @classmethod
    def setUpTestData(cls):
        """Setup test data."""
        cls.platform = Platform.objects.create(name="Platform 1")
        cls.feature = ComplianceFeature.objects.create(name="Feature 1", slug="feature-1")

    def test_valid_form_data(self):
        """Test valid form data."""
        data = {
            "feature": self.feature,
            "platform": self.platform,
            "config_type": ComplianceRuleConfigTypeChoice.TYPE_CLI,
            "config_ordered": True,
            "match_config": "config 1",
        }
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        saved_obj = form.save()
        self.assertEqual(saved_obj.feature, self.feature)
        self.assertEqual(saved_obj.platform, self.platform)
        self.assertEqual(saved_obj.config_type, ComplianceRuleConfigTypeChoice.TYPE_CLI)
        self.assertEqual(saved_obj.config_ordered, True)
        self.assertEqual(saved_obj.match_config, "config 1")

    def test_match_config_leading_space(self):
        """Test that leading spaces are preserved in match config."""
        data = {
            "feature": self.feature,
            "platform": self.platform,
            "config_type": ComplianceRuleConfigTypeChoice.TYPE_CLI,
            "config_ordered": True,
            "match_config": " config 1",
        }
        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())
        saved_obj = form.save()
        self.assertEqual(saved_obj.match_config, " config 1")
