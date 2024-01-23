"""Unit tests for nautobot_golden_config nornir compliance."""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.nornir_plays.config_compliance import get_config_element, get_rules
from nautobot_golden_config.tests.conftest import create_device, create_feature_rule_cli


class ConfigComplianceJsonTest(unittest.TestCase):
    """Test Nornir Compliance Task."""

    @patch("nautobot_golden_config.nornir_plays.config_compliance.ComplianceRule", autospec=True)
    def test_get_rules(self, mock_compliance_rule):
        """Test proper return when Features are returned."""
        features = {"config_ordered": "test_ordered", "match_config": "aaa\nsnmp\n"}
        mock_obj = Mock(**features)
        mock_obj.name = "test_name"
        mock_obj.platform = Mock(network_driver="test_driver")
        mock_compliance_rule.objects.all.return_value = [mock_obj]
        features = get_rules()
        mock_compliance_rule.objects.all.assert_called_once()
        self.assertEqual(
            features, {"test_driver": [{"obj": mock_obj, "ordered": "test_ordered", "section": ["aaa", "snmp"]}]}
        )

    def test_get_config_element_match_config_present(self):
        """Test proper return when Config JSON is returned with match_config"""
        mock_config = json.dumps({"key1": "value1", "key2": "value2", "key3": "value3"})
        mock_obj = MagicMock(name="Device")
        mock_obj.platform = Mock(network_driver="test_driver")
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
        mock_obj.platform = Mock(network_driver="test_driver")
        mock_rule = MagicMock(name="ComplianceRule")
        mock_rule["obj"].match_config = ""
        mock_rule["obj"].config_ordered = True
        mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_JSON
        return_config = json.dumps(get_config_element(mock_rule, mock_config, mock_obj, None))
        self.assertEqual(return_config, mock_config)


class ConfigComplianceCliTest(unittest.TestCase):
    """Test Nornir Compliance Task."""

    def setUp(self):
        """Setup test."""

        self.device = create_device(name="config_plan_utility_test")
        self.feature_rule = create_feature_rule_cli(self.device)
        self.feature_rule.match_config = "aaa\nsnmp\n"
        self.feature_rule.save()

    def test_get_config_element_match_config_present(self):
        """Test proper return when Config CLI is returned with match_config"""
        mock_config = "router bgp 123\naaa 123\n  with a child line"
        features = {"ordered": False, "obj": self.feature_rule, "section": ["aaa", "snmp"]}
        return_config = get_config_element(features, mock_config, self.device, None)
        self.assertEqual(return_config, "aaa 123\n  with a child line")

    def test_get_config_element_match_nonduplicate_line_broken(self):
        """Test proper return when Config CLI is returned with match_config"""
        mock_config = "aaa 123\n  with a child line\naccess-list 93 remark abcd\naccess-list 93 deny any any\n"
        features = {"ordered": False, "obj": self.feature_rule, "section": ["aaa", "snmp"]}
        return_config = get_config_element(features, mock_config, self.device, None)
        self.assertEqual(return_config, "aaa 123\n  with a child line")

    def test_get_config_element_match_duplicate_line_broken(self):
        """Test proper return when Config CLI is returned with match_config"""
        mock_config = "aaa 123\n  with a child line\naccess-list 93 remark abcd\naccess-list 93 deny any any\naccess-list 93 remark abcd\n"
        features = {"ordered": False, "obj": self.feature_rule, "section": ["aaa", "snmp"]}
        return_config = get_config_element(features, mock_config, self.device, None)
        self.assertEqual(return_config, "aaa 123\n  with a child line")
