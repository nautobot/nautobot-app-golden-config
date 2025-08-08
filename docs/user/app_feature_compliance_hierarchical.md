# Hierarchical Configuration Compliance

!!! note
    This document provides instructions for hierarchical configuration compliance using the `hier_config` library. This is an advanced feature that provides sophisticated tag-based filtering for CLI configuration compliance.

## Overview

Hierarchical configuration compliance is a powerful extension to the standard CLI-based compliance checking that leverages the `hier_config` library to provide advanced configuration parsing and comparison capabilities. This feature allows you to define complex matching rules using tag-based filtering to focus compliance checks on specific configuration sections or patterns.

Unlike standard CLI compliance which matches configuration sections based on simple line-starting patterns, hierarchical compliance identifies and compares configuration elements based on their hierarchical relationships and specific attributes.

## When to Use Hierarchical Compliance

Hierarchical compliance is particularly useful when:

- You need to check compliance for complex nested configurations (e.g., BGP neighbors, interface configurations)
- Standard CLI compliance matching is too broad or doesn't capture the specific configuration elements you want to validate
- You need to apply compliance rules based on configuration hierarchy and relationships rather than simple line matching
- You want to leverage the advanced parsing capabilities of the `hier_config` library

## Requirements

### Platform Support

Hierarchical compliance requires:

1. **CLI Configuration Type**: Only `CLI` configuration types are supported for hierarchical compliance
2. **Platform Compatibility**: Your device platform must be supported by the `hier_config` library
3. **Network Driver Mapping**: The platform must have a valid `hier_config` mapping in its `network_driver_mappings`

### Repository Settings

The same repository settings required for standard compliance apply:

- Backup repository for storing device configurations
- Intended configuration repository
- Proper `backup_path_template` and `intended_path_template` configuration

## Configuring Hierarchical Compliance Rules

### Rule Identification

To create a hierarchical compliance rule, you must include a special comment marker in the **Config to Match** field of your compliance rule:

- For hier_config v2 syntax: `# hier_config_v2`
- For hier_config v3 syntax: `# hier_config_v3`

This marker must be the first line in your **Config to Match** field.

### Syntax Options

#### hier_config v2 Syntax

When using `# hier_config_v2`, define your matching rules using the v2 lineage format:

```yaml
# hier_config_v2
- lineage:
  - startswith: router bgp
  - startswith: neighbor
- lineage:
  - startswith: interface
  - contains: GigabitEthernet
```

#### hier_config v3 Syntax

When using `# hier_config_v3`, define your matching rules using the v3 tag rule format:

```yaml
# hier_config_v3
- match_rules:
  - startswith: router bgp
  - startswith: neighbor
- match_rules:
  - startswith: interface
  - contains: GigabitEthernet
```

### Example Configuration Rules

#### Example 1: BGP Neighbor Configuration

To check compliance for all BGP neighbor configurations:

**Feature**: BGP Neighbors  
**Config Type**: CLI  
**Config to Match**:
```yaml
# hier_config_v3
- match_rules:
  - startswith: router bgp
  - startswith: neighbor
```

This rule will match configurations like:
```
router bgp 65001
 neighbor 10.1.1.1
  remote-as 65002
  description PEER_ROUTER_A
 neighbor 10.1.1.2
  remote-as 65003
  description PEER_ROUTER_B
```

#### Example 2: Interface MTU Settings

To check compliance for MTU settings on all interfaces:

**Feature**: Interface MTU  
**Config Type**: CLI  
**Config to Match**:
```yaml
# hier_config_v3
- match_rules:
  - startswith: interface
  - contains: mtu
```

This rule will match configurations like:
```
interface GigabitEthernet0/1
 mtu 9000
interface GigabitEthernet0/2
 mtu 1500
```

#### Example 3: SNMP Configuration

To check compliance for SNMP server configurations:

**Feature**: SNMP Servers  
**Config Type**: CLI  
**Config to Match**:
```yaml
# hier_config_v2
- lineage:
  - startswith: snmp-server
```

This rule will match configurations like:
```
snmp-server community public RO
snmp-server community private RW
snmp-server host 192.168.1.100 version 2c public
```

#### Example 4: Access Control Lists

To check compliance for specific access control list entries:

**Feature**: Security ACLs  
**Config Type**: CLI  
**Config to Match**:
```yaml
# hier_config_v3
- match_rules:
  - startswith: ip access-list
  - contains: SECURITY
```

This rule will match configurations like:
```
ip access-list extended SECURITY_IN
 permit tcp any host 192.168.1.100 eq 443
 deny ip any any log
ip access-list extended SECURITY_OUT
 permit ip 192.168.1.0 0.0.0.255 any
 deny ip any any log
```

## How It Works

### Processing Flow

1. **Rule Detection**: The compliance engine detects hierarchical rules by scanning for `# hier_config` markers
2. **Configuration Parsing**: Both backup (actual) and intended configurations are parsed using the `hier_config` library
3. **Tag Application**: Matching rules are converted to tags and applied to configuration elements that match the criteria
4. **Filtering**: Only configuration elements with applied tags are included in the compliance comparison
5. **Comparison**: The filtered configurations are compared for compliance

### Tag-Based Filtering

The hierarchical compliance process:

1. Parses your YAML match configuration
2. Creates unique tags for each rule set
3. Applies tags to configuration elements that match the defined criteria
4. Filters both actual and intended configurations to include only tagged elements
5. Performs compliance comparison on the filtered results

### Configuration Processing

The system:

- Converts v2 syntax to v3 format internally for consistency
- Creates unique hash-based tag names for each rule
- Applies tags to matching configuration hierarchies
- Generates filtered configuration text for comparison

### Fallback Behavior for Empty Intended Configuration

In some cases, the intended configuration may not contain any elements that match the hierarchical rules, resulting in an empty intended configuration text. To handle this scenario, the system includes a fallback mechanism:

**Interface Fallback**: When the intended configuration text is empty, the system automatically looks for top-level interface configurations in the running configuration and uses them as the intended configuration baseline.

This fallback behavior:

1. **Triggers** when `intended_text` is empty after tag-based filtering
2. **Searches** the running configuration for top-level interface lines (indent level 0)
3. **Filters** for lines that start with "interface"
4. **Uses** these interface declarations as the intended configuration for comparison

**Example Scenario**:
- Your hierarchical rule targets specific VLAN configurations
- The intended configuration template doesn't include those VLANs
- The running configuration has interface declarations
- The system uses the interface lines from running config as the baseline

This ensures that remediation will not remove interfaces when intended configuration is empty for an interface.

## Troubleshooting

### Common Issues

#### Platform Not Supported
**Error**: `Unsupported platform for hier_config v3: <platform>`

**Solution**: Ensure your device platform has a valid `hier_config` mapping in its `network_driver_mappings`. Check the platform configuration in Nautobot.

#### Invalid YAML Syntax
**Error**: `Invalid YAML in match_config: <error details>`

**Solution**: Validate your YAML syntax in the **Config to Match** field. Ensure proper indentation and structure.

#### Wrong Configuration Type
**Error**: `Hier config compliance rules are only supported for CLI config types`

**Solution**: Change the **Config Type** to `CLI` for hierarchical compliance rules.

### Debug Tips

1. **Test YAML Syntax**: Validate your YAML configuration using an online YAML validator
2. **Check Platform Support**: Verify your platform's `network_driver_mappings` include `hier_config`
3. **Review hier_config Documentation**: Consult the [hier_config documentation](https://hier-config.readthedocs.io/en/latest/tags/) for advanced tagging examples
4. **Start Simple**: Begin with basic matching rules and gradually add complexity
5. **Empty Intended Configuration**: If you notice interface lines appearing in compliance results when not expected, check if your intended configuration contains the elements targeted by your hierarchical rules. The system automatically falls back to using running config interface declarations when intended configuration is empty

## Best Practices

### Rule Design

1. **Specific Matching**: Create focused rules that target specific configuration elements
2. **Logical Grouping**: Group related configuration elements in single rules when appropriate
3. **Clear Naming**: Use descriptive feature names that clearly indicate what the rule validates
4. **Complete Intended Configurations**: Ensure your intended configuration templates include all elements targeted by hierarchical rules to avoid unexpected fallback behavior where interface lines from running config are used as intended baseline

### Performance Considerations

1. **Scope Rules Appropriately**: Avoid overly broad rules that match large configuration sections
2. **Test Incrementally**: Test rules with small configuration sets before applying to large environments
3. **Monitor Processing Time**: Complex hierarchical rules may take longer to process than simple CLI rules

### Documentation

1. **Document Rule Purpose**: Clearly document what each hierarchical rule is intended to validate
2. **Maintain Examples**: Keep example configurations for testing and validation
3. **Version Control**: Track changes to hierarchical rules alongside configuration templates

## Advanced Usage

### Combining Multiple Rules

You can create multiple hierarchical compliance rules for the same platform to check different aspects of the configuration independently.

### Migration from Standard CLI

When migrating from standard CLI compliance to hierarchical compliance:

1. Analyze existing CLI rules to understand their scope
2. Design hierarchical rules that provide equivalent or improved coverage
3. Test hierarchical rules alongside existing CLI rules before migration
4. Update documentation and procedures

### Integration with Configuration Management

Hierarchical compliance works seamlessly with existing configuration management workflows:

- Backup processes remain unchanged
- Intended configuration generation follows the same patterns
- Compliance reporting provides the same interface with enhanced precision

## Related Documentation

- [Standard CLI Compliance](./app_feature_compliancecli.md)
- [Configuration Compliance Overview](./app_feature_compliance.md)
- [hier_config Documentation](https://hier-config.readthedocs.io/)
