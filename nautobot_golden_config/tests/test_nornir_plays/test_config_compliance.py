"""Unit tests for nautobot_golden_config nornir compliance."""

import unittest
import json
from unittest.mock import patch, Mock, MagicMock
from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.nornir_plays.config_compliance import get_rules, get_config_element


class ConfigComplianceTest(unittest.TestCase):
    """Test Nornir Compliance Task."""

    @patch("nautobot_golden_config.nornir_plays.config_compliance.ComplianceRule", autospec=True)
    def test_get_rules(self, mock_compliance_rule):
        """Test proper return when Features are returned."""
        features = {"config_ordered": "test_ordered", "match_config": "aaa\nsnmp\n"}
        mock_obj = Mock(**features)
        mock_obj.name = "test_name"
        mock_obj.platform = Mock(slug="test_slug")
        mock_compliance_rule.objects.all.return_value = [mock_obj]
        features = get_rules()
        mock_compliance_rule.objects.all.assert_called_once()
        self.assertEqual(
            features, {"test_slug": [{"obj": mock_obj, "ordered": "test_ordered", "section": ["aaa", "snmp"]}]}
        )

    def test_get_config_element_match_config_present(self):
        """Test proper return when Config JSON is returned with match_config"""
        mock_config = json.dumps({"key1": "value1", "key2": "value2", "key3": "value3"})
        mock_obj = MagicMock(name="Device")
        mock_obj.platform = Mock(slug="test_slug")
        mock_rule = MagicMock(name="ComplianceRule")
        mock_rule["obj"].match_config = "key1"
        mock_rule["obj"].config_ordered = True
        mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_JSON
        return_config = json.dumps(get_config_element(mock_rule, mock_config, mock_obj, None))
        self.assertEqual(return_config, json.dumps({"key1": "value1"}))

    def test_get_config_element_match_config_absent(self):
        """Test proper return when Config JSON is returned without match_config"""
        mock_config = json.dumps({"key1": "value1", "key2": "value2", "key3": "value3"})
        mock_obj = MagicMock(name="Device")
        mock_obj.platform = Mock(slug="test_slug")
        mock_rule = MagicMock(name="ComplianceRule")
        mock_rule["obj"].match_config = ""
        mock_rule["obj"].config_ordered = True
        mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_JSON
        return_config = json.dumps(get_config_element(mock_rule, mock_config, mock_obj, None))
        self.assertEqual(return_config, mock_config)
