"""Unit tests for nautobot_golden_config nornir compliance."""

import unittest
from unittest.mock import patch, Mock
from nautobot_golden_config.nornir_plays.config_compliance import get_rules


class ConfigComplianceTest(unittest.TestCase):
    """Test Nornir Compliance Task."""

    @patch("nautobot_golden_config.nornir_plays.config_compliance.ComplianceRule", autospec=True)
    def test_get_rules(self, mock_compliance_rule):
        """Test proper return when Features are returned."""
        features = {"config_ordered": "test_ordered", "match_config": "aaa\nsnmp\n"}
        mock_obj = Mock(**features)
        mock_obj.name = "test_name"
        mock_obj.platform = Mock(slug="test_slug")
        mock_compliance_rule.objects.filter.return_value = [mock_obj]
        features = get_rules()
        mock_compliance_rule.objects.filter.assert_called_once()
        self.assertEqual(
            features, {"test_slug": [{"obj": mock_obj, "ordered": "test_ordered", "section": ["aaa", "snmp"]}]}
        )
