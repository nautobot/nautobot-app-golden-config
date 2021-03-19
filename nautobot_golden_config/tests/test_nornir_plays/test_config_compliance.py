"""Unit tests for nautobot_golden_config nornir compliance.

(c) 2020-2021 Network To Code
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
  http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import unittest
from unittest.mock import patch, Mock
from nautobot_golden_config.nornir_plays.config_compliance import get_features


class ConfigComplianceTest(unittest.TestCase):
    """Test Nornir Compliance Task."""

    @patch("nautobot_golden_config.nornir_plays.config_compliance.ComplianceFeature", autospec=True)
    def test_get_features(self, mock_compliance_feature):
        """Test proper return when Features are returned."""
        features = {
            "config_ordered": "test_ordered",
            "match_config": "aaa\nsnmp\n"
        }
        mock_obj = Mock(**features)
        mock_obj.name = "test_name"
        mock_obj.platform = Mock(slug="test_slug")
        mock_compliance_feature.objects.all.return_value = [mock_obj]
        features = get_features()
        mock_compliance_feature.objects.all.assert_called_once()
        self.assertEqual(features, {"test_slug": [{'name': 'test_name', 'ordered': 'test_ordered', 'section': ['aaa', 'snmp']}]})
