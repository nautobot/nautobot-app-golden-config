"""Unit tests for the nautobot_golden_config utilities config_plan."""
import unittest
from unittest.mock import Mock, patch

from nautobot_golden_config.utilities.config_plan import (
    generate_config_set_from_compliance_feature,
    generate_config_set_from_manual,
    config_plan_default_status,
)
from nautobot_golden_config.tests.conftest import create_device, create_feature_rule_cli, create_config_compliance


class ConfigPlanTest(unittest.TestCase):
    """Test Config Plan Utility."""

    def setUp(self):
        """Setup test."""
        mock_feature_compliance = Mock(
            return_value={
                "compliant": False,
                "ordered_compliant": False,
                "missing": "foo missing",
                "extra": "",
            }
        )
        self.patcher = patch("nautobot_golden_config.models.feature_compliance", mock_feature_compliance)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.device = create_device(name="config_plan_utility_test")
        self.feature_rule = create_feature_rule_cli(self.device)
        self.feature_rule.match_config = "foo"
        self.feature_rule.save()
        self.actual = "foo actual"
        self.missing = "foo missing"
        self.intended = "foo actual\nfoo missing"
        self.config_compliance = create_config_compliance(self.device, self.feature_rule, self.actual, self.intended)

    def test_generate_config_set_from_compliance_feature_intended(self):
        """Test generate_config_set_from_compliance_feature."""
        plan_type = "intended"
        config_set = generate_config_set_from_compliance_feature(self.device, plan_type, self.feature_rule.feature)
        self.assertEqual(config_set, self.intended)

    def test_generate_config_set_from_compliance_feature_missing(self):
        """Test generate_config_set_from_compliance_feature."""
        plan_type = "missing"
        config_set = generate_config_set_from_compliance_feature(self.device, plan_type, self.feature_rule.feature)
        self.assertEqual(config_set, self.missing)

    def test_generate_config_set_from_manual(self):
        """Test generate_config_set_from_manual."""
        commands = "hostname {{ obj.name }}"
        config_set = generate_config_set_from_manual(self.device, commands)
        self.assertEqual(config_set, "hostname config_plan_utility_test")

    def test_config_plan_default_status(self):
        """Test config_plan_default_status."""
        status = config_plan_default_status()
        self.assertEqual(status.name, "Not Approved")
        self.assertEqual(status.slug, "not-approved")
