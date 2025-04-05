"""Unit tests for nautobot_golden_config nornir compliance."""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.nornir_plays.config_compliance import get_config_element, get_rules


class ConfigComplianceTest(unittest.TestCase):
    """Test Nornir Compliance Task."""

    def setUp(self):
        """Set up common mock objects for tests."""
        self.mock_config = json.dumps({"key1": "value1", "key2": "value2", "key3": "value3"})
        self.mock_obj = MagicMock(name="Device")
        self.mock_obj.platform = Mock(network_driver="test_driver")
        self.mock_rule = MagicMock(name="ComplianceRule")
        self.mock_logger = MagicMock(name="Logger")

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
        """Test proper return when Config JSON is returned with match_config."""
        self.mock_rule["obj"].match_config = "key1"
        self.mock_rule["obj"].config_ordered = True
        self.mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_JSON
        return_config = json.dumps(get_config_element(self.mock_rule, self.mock_config, self.mock_obj, None))
        self.assertEqual(return_config, json.dumps({"key1": "value1"}))

    def test_get_config_element_match_config_absent(self):
        """Test proper return when Config JSON is returned without match_config."""
        self.mock_rule["obj"].match_config = ""
        self.mock_rule["obj"].config_ordered = True
        self.mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_JSON
        return_config = json.dumps(get_config_element(self.mock_rule, self.mock_config, self.mock_obj, None))
        self.assertEqual(return_config, self.mock_config)

    def test_get_config_element_match_config_present_jdiff(self):
        """Test proper return when Config JSONV2 is returned with match_config."""
        self.mock_rule["obj"].match_config = "key1"
        self.mock_rule["obj"].config_ordered = True
        self.mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_JSONV2
        return_config = json.dumps(get_config_element(self.mock_rule, self.mock_config, self.mock_obj, None))
        self.assertEqual(return_config, json.dumps({"key1": "value1"}))

    def test_get_config_element_match_config_absent_jdiff(self):
        """Test proper return when Config JSONV2 is returned without match_config."""
        self.mock_rule["obj"].match_config = ""
        self.mock_rule["obj"].config_ordered = True
        self.mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_JSONV2
        return_config = json.dumps(get_config_element(self.mock_rule, self.mock_config, self.mock_obj, None))
        self.assertEqual(return_config, self.mock_config)

    def test_get_config_element_wrong_config_xml(self):
        """Test proper exception when improper xml config used."""
        self.mock_rule["obj"].match_config = ""
        self.mock_rule["obj"].config_ordered = True
        self.mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_XML
        with self.assertRaises(NornirNautobotException) as context:
            json.dumps(get_config_element(self.mock_rule, self.mock_config, self.mock_obj, self.mock_logger))
        self.assertEqual(str(context.exception), "`E3002:` Unable to interpret configuration as XML.")

    def test_get_config_element_wrong_config_json(self):
        """Test proper exception when improper json config used."""
        self.mock_config = "aaa\nsnmp\n"
        self.mock_rule["obj"].match_config = ""
        self.mock_rule["obj"].config_ordered = True
        self.mock_rule["obj"].config_type = ComplianceRuleConfigTypeChoice.TYPE_JSON
        with self.assertRaises(NornirNautobotException) as context:
            json.dumps(get_config_element(self.mock_rule, self.mock_config, self.mock_obj, self.mock_logger))
        self.assertEqual(str(context.exception), "`E3002:` Unable to interpret configuration as JSON.")
