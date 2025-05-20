"""Unit tests for nautobot_golden_config nornir hier-config compliance."""

import hashlib
import json
import unittest
from unittest.mock import MagicMock, Mock, patch

import yaml
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.nornir_plays.config_compliance import process_nested_compliance_rule_hier_config


class TestProcessNestedComplianceRuleHierConfig(unittest.TestCase):
    """Tests for the process_nested_compliance_rule_hier_config function."""

    def setUp(self):
        """Set up common test components."""
        self.mock_obj = MagicMock()
        self.mock_obj.name = "test-device"
        self.mock_obj.platform.network_driver_mappings = {"hier_config": "ios"}

        self.mock_logger = MagicMock()

        # Sample configs
        self.backup_cfg = """
interface GigabitEthernet0/1
 description LAN
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 description WAN
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
router ospf 1
 network 192.168.1.0 0.0.0.255 area 0
 network 10.0.0.0 0.0.0.255 area 0
!
"""

        self.intended_cfg = """
interface GigabitEthernet0/1
 description LAN
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 description WAN
 ip address 10.0.0.1 255.255.255.0
 shutdown
!
router ospf 1
 network 192.168.1.0 0.0.0.255 area 0
 network 10.0.0.0 0.0.0.255 area 0
 network 172.16.0.0 0.0.0.255 area 0
!
"""

        # Valid match config for testing
        self.valid_match_config = """
- lineage:
    - startswith: interface
  add_children: true

- lineage:
    - startswith: router ospf
  add_children: true
"""

        # Invalid match configs
        self.string_match_config = "interface GigabitEthernet"
        self.list_of_strings_config = """
- interface GigabitEthernet
- router ospf
"""

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config.Host")
    def test_valid_config(self, mock_hier_config_host):
        """Test with valid hierarchical configuration rule."""
        # Setup mock objects
        mock_rule = {
            "obj": Mock(config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI, match_config=self.valid_match_config)
        }

        # Setup mock for hier_config.Host instance
        mock_host = mock_hier_config_host.return_value
        mock_host._hconfig_tags = {"tag1": "val1"}

        # Setup running config mock
        mock_running_config = Mock()
        mock_running_config.all_children_sorted_by_tags.return_value = [
            Mock(cisco_style_text=lambda: "interface GigabitEthernet0/1"),
            Mock(cisco_style_text=lambda: " ip address 192.168.1.1 255.255.255.0"),
        ]
        mock_host.running_config = mock_running_config

        # Setup generated config mock
        mock_generated_config = Mock()
        mock_generated_config.all_children_sorted_by_tags.return_value = [
            Mock(cisco_style_text=lambda: "interface GigabitEthernet0/1"),
            Mock(cisco_style_text=lambda: " ip address 192.168.1.1 255.255.255.0"),
        ]
        mock_host.generated_config = mock_generated_config

        # Call the function
        running_text, intended_text = process_nested_compliance_rule_hier_config(
            rule=mock_rule,
            backup_cfg=self.backup_cfg,
            intended_cfg=self.intended_cfg,
            obj=self.mock_obj,
            logger=self.mock_logger,
        )

        # Assert the function calls and returns
        mock_hier_config_host.assert_called_once_with(hostname="test-device", os="ios")
        mock_host.load_running_config.assert_called_once_with(self.backup_cfg)
        mock_host.load_generated_config.assert_called_once_with(self.intended_cfg)
        mock_host.load_tags.assert_called_once()
        mock_running_config.add_tags.assert_called_once_with(mock_host._hconfig_tags)
        mock_generated_config.add_tags.assert_called_once_with(mock_host._hconfig_tags)

        # Check outputs
        self.assertEqual(running_text, "interface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0")
        self.assertEqual(intended_text, "interface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0")

    def test_non_cli_rule_type(self):
        """Test with non-CLI rule type (should raise exception)."""
        mock_rule = {
            "obj": Mock(config_type=ComplianceRuleConfigTypeChoice.TYPE_JSON, match_config=self.valid_match_config)
        }

        with self.assertRaises(NornirNautobotException) as context:
            process_nested_compliance_rule_hier_config(
                rule=mock_rule,
                backup_cfg=self.backup_cfg,
                intended_cfg=self.intended_cfg,
                obj=self.mock_obj,
                logger=self.mock_logger,
            )

        self.assertIn("E3008", str(context.exception))
        self.mock_logger.error.assert_called_once()

    @patch("nautobot_golden_config.nornir_plays.config_compliance.yaml.safe_load")
    def test_yaml_parsing_exception(self, mock_yaml_load):
        """Test with YAML parsing exception."""
        mock_rule = {
            "obj": Mock(config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI, match_config=self.valid_match_config)
        }

        # Mock YAML parsing exception
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

        with self.assertRaises(Exception):
            process_nested_compliance_rule_hier_config(
                rule=mock_rule,
                backup_cfg=self.backup_cfg,
                intended_cfg=self.intended_cfg,
                obj=self.mock_obj,
                logger=self.mock_logger,
            )

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config.Host")
    def test_end_to_end_integration(self, mock_hier_config_host):
        """Test the entire function with realistic data to verify tagging and filtering logic."""
        # Setup mock rule with valid YAML
        mock_rule = {
            "obj": Mock(config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI, match_config=self.valid_match_config)
        }

        # Expected parsed YAML
        expected_parsed_yaml = yaml.safe_load(self.valid_match_config)

        # Calculate expected tag names
        expected_tag_names = set()
        for lineage in expected_parsed_yaml:
            tag_name = hashlib.sha1(json.dumps(lineage, sort_keys=True).encode()).hexdigest()
            expected_tag_names.add(tag_name)

        # Setup mock for hier_config.Host instance
        mock_host = mock_hier_config_host.return_value
        mock_host._hconfig_tags = {"tag1": "val1"}

        # Running config children
        mock_running_children = [
            Mock(cisco_style_text=lambda: "interface GigabitEthernet0/1"),
            Mock(cisco_style_text=lambda: " description LAN"),
            Mock(cisco_style_text=lambda: " ip address 192.168.1.1 255.255.255.0"),
        ]
        mock_host.running_config.all_children_sorted_by_tags.return_value = mock_running_children

        # Intended config children
        mock_intended_children = [
            Mock(cisco_style_text=lambda: "interface GigabitEthernet0/1"),
            Mock(cisco_style_text=lambda: " description LAN Modified"),
            Mock(cisco_style_text=lambda: " ip address 192.168.1.1 255.255.255.0"),
        ]
        mock_host.generated_config.all_children_sorted_by_tags.return_value = mock_intended_children

        # Call the function
        running_text, intended_text = process_nested_compliance_rule_hier_config(
            rule=mock_rule,
            backup_cfg=self.backup_cfg,
            intended_cfg=self.intended_cfg,
            obj=self.mock_obj,
            logger=self.mock_logger,
        )

        # Verify the expected function calls
        mock_host.load_tags.assert_called_once()
        mock_host.running_config.add_tags.assert_called_once()
        mock_host.generated_config.add_tags.assert_called_once()

        # Check host.running_config.all_children_sorted_by_tags was called with expected tag names
        args, kwargs = mock_host.running_config.all_children_sorted_by_tags.call_args
        self.assertEqual(len(args[0]), len(expected_tag_names))

        # Check outputs
        expected_running = "interface GigabitEthernet0/1\n description LAN\n ip address 192.168.1.1 255.255.255.0"
        expected_intended = (
            "interface GigabitEthernet0/1\n description LAN Modified\n ip address 192.168.1.1 255.255.255.0"
        )

        self.assertEqual(running_text, expected_running)
        self.assertEqual(intended_text, expected_intended)
