"""Unit tests for nautobot_golden_config nornir compliance."""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch

import yaml
from nornir_nautobot.exceptions import NornirNautobotException

from nautobot_golden_config.choices import ComplianceRuleConfigTypeChoice
from nautobot_golden_config.nornir_plays.config_compliance import (
    get_config_element,
    get_rules,
    process_nested_compliance_rule_hier_config,
)


class ConfigComplianceTest(unittest.TestCase):
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


class ProcessNestedComplianceRuleHierConfigTest(unittest.TestCase):
    """Test Hierarchical Configuration Compliance Function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.mock_obj = Mock()
        self.mock_obj.platform.network_driver_mappings = {"hier_config": "cisco_ios"}

        # Sample configuration data
        self.backup_cfg = """
interface GigabitEthernet0/1
 description WAN_INTERFACE
 ip address 192.168.1.1 255.255.255.0
 mtu 1500
 no shutdown
!
interface GigabitEthernet0/2
 description LAN_INTERFACE
 ip address 10.0.0.1 255.255.255.0
 mtu 9000
 no shutdown
!
router bgp 65001
 neighbor 10.1.1.1 remote-as 65002
 neighbor 10.1.1.1 description PEER_A
 neighbor 10.1.1.2 remote-as 65003
 neighbor 10.1.1.2 description PEER_B
!
"""

        self.intended_cfg = """
interface GigabitEthernet0/1
 description WAN_INTERFACE
 ip address 192.168.1.1 255.255.255.0
 mtu 1500
 no shutdown
!
interface GigabitEthernet0/2
 description LAN_INTERFACE
 ip address 10.0.0.1 255.255.255.0
 mtu 1500
 no shutdown
!
router bgp 65001
 neighbor 10.1.1.1 remote-as 65002
 neighbor 10.1.1.1 description PEER_A
 neighbor 10.1.1.2 remote-as 65003
 neighbor 10.1.1.2 description PEER_B
!
"""

    def test_non_cli_config_type_raises_exception(self):
        """Test that non-CLI config types raise an exception."""
        mock_rule = {"obj": Mock(config_type=ComplianceRuleConfigTypeChoice.TYPE_JSON, match_config="test")}

        with self.assertRaises(NornirNautobotException) as context:
            process_nested_compliance_rule_hier_config(
                mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
            )

        self.assertIn("Hier config compliance rules are only supported for CLI config types", str(context.exception))
        self.mock_logger.error.assert_called_once()

    def test_unsupported_platform_raises_exception(self):
        """Test that unsupported platforms raise an exception."""
        mock_rule = {"obj": Mock(config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI, match_config="test")}

        # Mock an unsupported platform
        self.mock_obj.platform.network_driver_mappings = {"hier_config": "unsupported_platform"}

        with patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING", {}):
            with self.assertRaises(NornirNautobotException) as context:
                process_nested_compliance_rule_hier_config(
                    mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
                )

        self.assertIn("Unsupported platform for hier_config v3", str(context.exception))
        self.mock_logger.error.assert_called_once()

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.TypeAdapter")
    def test_hier_config_syntax_success(self, mock_type_adapter, mock_platform_mapping, mock_hier_config):
        """Test successful processing with hier_config syntax (# hier_config)."""
        mock_platform_mapping.get.return_value = "cisco_ios"
        mock_running_config = Mock()
        mock_generated_config = Mock()
        mock_hier_config.get_hconfig.side_effect = [mock_running_config, mock_generated_config]

        # Mock tag rule
        mock_tag_rule = Mock()
        mock_tag_rule.match_rules = ["interface"]
        mock_tag_rule.apply_tags = frozenset(["test_tag"])
        mock_type_adapter_instance = Mock()
        mock_type_adapter_instance.validate_python.return_value = (mock_tag_rule,)
        mock_type_adapter.return_value = mock_type_adapter_instance

        # Mock config children
        mock_child = Mock()
        mock_child.cisco_style_text.return_value = "interface GigabitEthernet0/1"
        mock_running_config.get_children_deep.return_value = [mock_child]
        mock_generated_config.get_children_deep.return_value = [mock_child]
        mock_running_config.all_children_sorted_by_tags.return_value = [mock_child]
        mock_generated_config.all_children_sorted_by_tags.return_value = [mock_child]

        mock_rule = {
            "obj": Mock(
                config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
                match_config="# hier_config\n- match_rules:\n  - startswith: interface",
            )
        }

        running_text, intended_text = process_nested_compliance_rule_hier_config(
            mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
        )

        # Verify results
        self.assertEqual(running_text, "interface GigabitEthernet0/1")
        self.assertEqual(intended_text, "interface GigabitEthernet0/1")
        mock_hier_config.get_hconfig.assert_called()
        mock_type_adapter_instance.validate_python.assert_called_once()

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.yaml.safe_load")
    def test_invalid_yaml_raises_exception(self, mock_yaml_load, mock_platform_mapping, mock_hier_config):
        """Test that invalid YAML in compliance rule raises an exception."""
        mock_platform_mapping.get.return_value = "cisco_ios"

        # Mock YAML parsing to raise an exception
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML syntax")
        mock_rule = {
            "obj": Mock(
                config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
                match_config="# hier_config\ninvalid: yaml: content: [",
            )
        }
        with self.assertRaises(NornirNautobotException) as context:
            process_nested_compliance_rule_hier_config(
                mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
            )
        self.assertIn("Invalid YAML in match_config", str(context.exception))
        self.mock_logger.error.assert_called_once()

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.TypeAdapter")
    def test_multiple_rules(self, mock_type_adapter, mock_platform_mapping, mock_hier_config):
        """Test processing with multiple match configs in a single compliance rule."""
        mock_platform_mapping.get.return_value = "cisco_ios"
        mock_running_config = Mock()
        mock_generated_config = Mock()
        mock_hier_config.get_hconfig.side_effect = [mock_running_config, mock_generated_config]

        # Mock tag rules
        mock_tag_rule1 = Mock()
        mock_tag_rule1.match_rules = ["interface"]
        mock_tag_rule1.apply_tags = frozenset(["interface_tag"])
        mock_tag_rule2 = Mock()
        mock_tag_rule2.match_rules = ["router bgp"]
        mock_tag_rule2.apply_tags = frozenset(["bgp_tag"])
        mock_type_adapter_instance = Mock()
        mock_type_adapter_instance.validate_python.return_value = (mock_tag_rule1, mock_tag_rule2)
        mock_type_adapter.return_value = mock_type_adapter_instance

        # Mock config children
        mock_interface_child = Mock()
        mock_interface_child.cisco_style_text.return_value = "interface GigabitEthernet0/1"
        mock_bgp_child = Mock()
        mock_bgp_child.cisco_style_text.return_value = "router bgp 65001"
        mock_running_config.get_children_deep.return_value = [mock_interface_child, mock_bgp_child]
        mock_generated_config.get_children_deep.return_value = [mock_interface_child, mock_bgp_child]
        mock_running_config.all_children_sorted_by_tags.return_value = [mock_interface_child, mock_bgp_child]
        mock_generated_config.all_children_sorted_by_tags.return_value = [mock_interface_child, mock_bgp_child]

        mock_rule = {
            "obj": Mock(
                config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
                match_config="""# hier_config
- match_rules:
  - startswith: interface
- match_rules:
  - startswith: router bgp""",
            )
        }

        running_text, intended_text = process_nested_compliance_rule_hier_config(
            mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
        )
        expected_text = "interface GigabitEthernet0/1\nrouter bgp 65001"
        self.assertEqual(running_text, expected_text)
        self.assertEqual(intended_text, expected_text)
        mock_type_adapter_instance.validate_python.assert_called_once()

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.TypeAdapter")
    def test_empty_filtered_config_with_interface_fallback(
        self, mock_type_adapter, mock_platform_mapping, mock_hier_config
    ):
        """Test processing when intended config is empty but running config has interfaces (fallback behavior)."""
        # Setup mocks
        mock_platform_mapping.get.return_value = "cisco_ios"
        mock_running_config = Mock()
        mock_generated_config = Mock()
        mock_hier_config.get_hconfig.side_effect = [mock_running_config, mock_generated_config]
        # Mock tag rule via TypeAdapter
        mock_tag_rule = Mock()
        mock_tag_rule.match_rules = ["flow exporter"]
        mock_tag_rule.apply_tags = frozenset(["test_tag"])
        mock_type_adapter_instance = Mock()
        mock_type_adapter_instance.validate_python.return_value = (mock_tag_rule,)
        mock_type_adapter.return_value = mock_type_adapter_instance

        # Mock running config with interface and flow exporter
        mock_interface_child = Mock()
        mock_interface_child.cisco_style_text.return_value = "interface GigabitEthernet0/1"
        mock_interface_child.real_indent_level = 0

        mock_flow_child = Mock()
        mock_flow_child.cisco_style_text.return_value = "flow exporter 192.0.0.1"
        mock_flow_child.real_indent_level = 0

        # Only the flow exporter should match the tag rule
        mock_running_config.get_children_deep.return_value = [mock_flow_child]
        # Fallback second call coverage
        mock_running_config.all_children_sorted_by_tags.side_effect = [
            [mock_flow_child],
            [mock_interface_child, mock_flow_child],
        ]

        # Generated config has no matching elements (empty intended config)
        mock_generated_config.get_children_deep.return_value = []
        mock_generated_config.all_children_sorted_by_tags.return_value = []

        mock_rule = {
            "obj": Mock(
                config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
                match_config="# hier_config\n- match_rules:\n  - startswith: flow exporter",
            )
        }

        running_text, intended_text = process_nested_compliance_rule_hier_config(
            mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
        )

        # Running text should have the flow exporter
        self.assertEqual(running_text, "flow exporter 192.0.0.1")
        # Intended text should fallback to interface lines from running config
        self.assertEqual(intended_text, "interface GigabitEthernet0/1")

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.TypeAdapter")
    def test_empty_filtered_config_no_interfaces(self, mock_type_adapter, mock_platform_mapping, mock_hier_config):
        """Test processing when both configs are empty and no interfaces are available for fallback."""
        # Setup mocks
        mock_platform_mapping.get.return_value = "cisco_ios"
        mock_running_config = Mock()
        mock_generated_config = Mock()
        mock_hier_config.get_hconfig.side_effect = [mock_running_config, mock_generated_config]

        # Mock tag rule
        mock_tag_rule = Mock()
        mock_tag_rule.match_rules = ["nonexistent"]
        mock_tag_rule.apply_tags = frozenset(["test_tag"])
        mock_type_adapter_instance = Mock()
        mock_type_adapter_instance.validate_python.return_value = (mock_tag_rule,)
        mock_type_adapter.return_value = mock_type_adapter_instance

        # Mock empty results for both configs
        mock_running_config.get_children_deep.return_value = []
        mock_generated_config.get_children_deep.return_value = []
        mock_running_config.all_children_sorted_by_tags.return_value = []
        mock_generated_config.all_children_sorted_by_tags.return_value = []

        mock_rule = {
            "obj": Mock(
                config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
                match_config="# hier_config\n- match_rules:\n  - startswith: nonexistent",
            )
        }

        running_text, intended_text = process_nested_compliance_rule_hier_config(
            mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
        )

        # Should return empty strings when no matches and no interfaces for fallback
        self.assertEqual(running_text, "")
        self.assertEqual(intended_text, "")

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.TypeAdapter")
    def test_interface_fallback_only_top_level_interfaces(
        self, mock_type_adapter, mock_platform_mapping, mock_hier_config
    ):
        """Test that fallback only includes top-level interface lines."""
        # Setup mocks
        mock_platform_mapping.get.return_value = "cisco_ios"
        mock_running_config = Mock()
        mock_generated_config = Mock()
        mock_hier_config.get_hconfig.side_effect = [mock_running_config, mock_generated_config]

        # Mock tag rule
        mock_tag_rule = Mock()
        mock_tag_rule.match_rules = ["router bgp"]
        mock_tag_rule.apply_tags = frozenset(["test_tag"])
        mock_type_adapter_instance = Mock()
        mock_type_adapter_instance.validate_python.return_value = (mock_tag_rule,)
        mock_type_adapter.return_value = mock_type_adapter_instance

        # Mock children with different indent levels
        mock_interface_child = Mock()
        mock_interface_child.cisco_style_text.return_value = "interface GigabitEthernet0/1"
        mock_interface_child.real_indent_level = 0
        mock_sub_interface_child = Mock()
        mock_sub_interface_child.cisco_style_text.return_value = "interface GigabitEthernet0/1.100"
        mock_sub_interface_child.real_indent_level = 1
        mock_other_child = Mock()
        mock_other_child.cisco_style_text.return_value = "hostname router1"
        mock_other_child.real_indent_level = 0
        mock_bgp_child = Mock()
        mock_bgp_child.cisco_style_text.return_value = "router bgp 65001"
        mock_running_config.get_children_deep.return_value = [mock_bgp_child]
        mock_running_config.all_children_sorted_by_tags.side_effect = [
            [mock_bgp_child],
            [mock_interface_child, mock_sub_interface_child, mock_other_child, mock_bgp_child],
        ]
        # Generated config is empty
        mock_generated_config.get_children_deep.return_value = []
        mock_generated_config.all_children_sorted_by_tags.return_value = []
        mock_rule = {
            "obj": Mock(
                config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
                match_config="# hier_config\n- match_rules:\n  - startswith: router bgp",
            )
        }
        running_text, intended_text = process_nested_compliance_rule_hier_config(
            mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
        )

        # Running text should have the BGP config
        self.assertEqual(running_text, "router bgp 65001")
        # Intended text should only have top-level interface (not sub-interface or hostname)
        self.assertEqual(intended_text, "interface GigabitEthernet0/1")

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.TypeAdapter")
    def test_multiple_interface_fallback(self, mock_type_adapter, mock_platform_mapping, mock_hier_config):
        """Test fallback behavior with multiple top-level interfaces."""
        # Setup mocks
        mock_platform_mapping.get.return_value = "cisco_ios"
        mock_running_config = Mock()
        mock_generated_config = Mock()
        mock_hier_config.get_hconfig.side_effect = [mock_running_config, mock_generated_config]

        # Mock tag rule
        mock_tag_rule = Mock()
        mock_tag_rule.match_rules = ["snmp-server"]
        mock_tag_rule.apply_tags = frozenset(["test_tag"])
        mock_type_adapter_instance = Mock()
        mock_type_adapter_instance.validate_python.return_value = (mock_tag_rule,)
        mock_type_adapter.return_value = mock_type_adapter_instance
        mock_interface1 = Mock()
        mock_interface1.cisco_style_text.return_value = "interface GigabitEthernet0/1"
        mock_interface1.real_indent_level = 0
        mock_interface2 = Mock()
        mock_interface2.cisco_style_text.return_value = "interface GigabitEthernet0/2"
        mock_interface2.real_indent_level = 0
        mock_snmp_child = Mock()
        mock_snmp_child.cisco_style_text.return_value = "snmp-server community public"

        # Running config has SNMP
        mock_running_config.get_children_deep.return_value = [mock_snmp_child]

        # Mock the second call to all_children_sorted_by_tags for interface fallback
        mock_running_config.all_children_sorted_by_tags.side_effect = [
            [mock_snmp_child],
            [mock_interface1, mock_interface2, mock_snmp_child],
        ]

        # Generated config is empty
        mock_generated_config.get_children_deep.return_value = []
        mock_generated_config.all_children_sorted_by_tags.return_value = []
        mock_rule = {
            "obj": Mock(
                config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
                match_config="# hier_config\n- match_rules:\n  - startswith: snmp-server",
            )
        }
        running_text, intended_text = process_nested_compliance_rule_hier_config(
            mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
        )

        # Running text should have the SNMP config
        self.assertEqual(running_text, "snmp-server community public")
        # Intended text should have both interfaces
        self.assertEqual(intended_text, "interface GigabitEthernet0/1\ninterface GigabitEthernet0/2")

    @patch("nautobot_golden_config.nornir_plays.config_compliance.hier_config")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.HCONFIG_PLATFORM_V2_TO_V3_MAPPING")
    @patch("nautobot_golden_config.nornir_plays.config_compliance.TypeAdapter")
    def test_tag_application_to_configs(self, mock_type_adapter, mock_platform_mapping, mock_hier_config):
        """Test that tags are properly applied to both running and generated configs in unified syntax."""
        mock_platform_mapping.get.return_value = "cisco_ios"
        mock_running_config = Mock()
        mock_generated_config = Mock()
        mock_hier_config.get_hconfig.side_effect = [mock_running_config, mock_generated_config]

        # Mock tag rule
        mock_tag_rule = Mock()
        mock_tag_rule.match_rules = ["interface"]
        mock_tag_rule.apply_tags = frozenset(["interface_tag"])
        mock_type_adapter_instance = Mock()
        mock_type_adapter_instance.validate_python.return_value = (mock_tag_rule,)
        mock_type_adapter.return_value = mock_type_adapter_instance

        # Mock config children
        mock_child = Mock()
        mock_child.cisco_style_text.return_value = "interface GigabitEthernet0/1"
        mock_running_config.get_children_deep.return_value = [mock_child]
        mock_generated_config.get_children_deep.return_value = [mock_child]
        mock_running_config.all_children_sorted_by_tags.return_value = [mock_child]
        mock_generated_config.all_children_sorted_by_tags.return_value = [mock_child]

        mock_rule = {
            "obj": Mock(
                config_type=ComplianceRuleConfigTypeChoice.TYPE_CLI,
                match_config="# hier_config\n- match_rules:\n  - startswith: interface",
            )
        }

        process_nested_compliance_rule_hier_config(
            mock_rule, self.backup_cfg, self.intended_cfg, self.mock_obj, self.mock_logger
        )

        # Verify tags were added to children from both configs
        self.assertEqual(mock_child.tags_add.call_count, 2)
        mock_child.tags_add.assert_called_with(frozenset(["interface_tag"]))
