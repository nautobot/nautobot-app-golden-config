# Filtered Configuration Compliance

## Overview

Filtered configuration compliance is a powerful extension to the standard CLI-based compliance checking that leverages the `hier_config` library to provide advanced configuration parsing and comparison capabilities. This feature allows you to define complex matching rules to focus compliance checks on specific configuration sections or patterns. 

Unlike standard CLI compliance which matches configuration sections based on simple line-starting patterns, Filtered configuration compliance identifies and compares configuration elements based on their hierarchical relationships and specific attributes, which allows for filtering based on nested config lines.

## When to Use Filtered Configuraiton Compliance

This feature is particularly useful for:

- Configurations that are benign or non-consequential to the configurations. 
- When you are building out your compliance journey, and not prepared to include all configurations based on simple line matching.

!!! warning
    Should not be used to provide full line matches or matches that are better served as data, as an example you should not do this `- startswith: description USER PORT` but should do this `- startswith: description`. 

## Requirements

### Platform Support

Filtered configuration compliance requires:

1. **CLI Configuration Type**: Only `CLI` configuration types are supported for hierarchical compliance
2. **Platform Compatibility**: Your device platform must be supported by the `hier_config` library
3. **Network Driver Mapping**: The platform must have a valid `hier_config` mapping in its `network_driver_mappings`

### Repository Settings

The same repository settings required for standard compliance apply:

- Backup repository for storing device configurations
- Intended configuration repository
- Proper `backup_path_template` and `intended_path_template` configuration

## Configuring Filtered Compliance Rules

### Rule Identification

To create a filtered compliance rule, start the **Config to Match** field with the comment:

`# hier_config`

This comment must be the first line. The content that follows should be YAML consisting of one or more rule blocks. Each rule block uses the `match_rules` key containing an ordered list of predicates (e.g. `startswith`, `contains`, `re_search`, `endswith`).

### Syntax

Example with two rule blocks:

```yaml
# hier_config
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

```yaml
# hier_config
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

```yaml
# hier_config
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

```yaml
# hier_config
- match_rules:
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

```yaml
# hier_config
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

## Fallback Behavior for Empty Intended Configuration

In some cases, the intended configuration may not contain any elements that match the compliance rules, resulting in an empty intended configuration text. To handle this scenario, the system includes a fallback mechanism:

**Interface Fallback**: When the intended configuration text is empty, the system automatically looks for top-level interface configurations in the running configuration and uses them as the intended configuration baseline.

This fallback behavior:

1. **Triggers** when `intended_text` is empty after tag-based filtering
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

1. **Check Platform Support**: Verify your platform's `network_driver_mappings` include `hier_config`
2. **Review hier_config Documentation**: Consult the [hier_config documentation](https://hier-config.readthedocs.io/en/latest/tags/) for advanced tagging examples
3. **Start Simple**: Begin with basic matching rules and gradually add complexity
4. **Empty Intended Configuration**: If you notice interface lines appearing in compliance results when not expected, check if your intended configuration contains the elements targeted by your hierarchical rules. The system automatically falls back to using running config interface declarations when intended configuration is empty

## Best Practices

### Rule Design

1. **Specific Matching**: Create focused rules that target specific configuration elements
2. **Logical Grouping**: Group related configuration elements in single rules when appropriate
3. **Clear Naming**: Use descriptive feature names that clearly indicate what the rule validates
4. **Complete Intended Configurations**: Ensure your intended configuration templates include all elements targeted by filtered compliance rules to avoid unexpected fallback behavior where interface lines from running config are used as intended baseline

## Advanced Usage

### Combining Multiple Rules

You can create multiple hierarchical compliance rules for the same platform to check different aspects of the configuration independently.

### Integration with Configuration Management

Filtered configuration compliance works seamlessly with existing configuration management workflows:

- Backup processes remain unchanged
- Intended configuration generation follows the same patterns
- Compliance reporting provides the same interface with enhanced precision

## Related Documentation

- [Standard CLI Compliance](./app_feature_compliancecli.md)
- [Configuration Compliance Overview](./app_feature_compliance.md)
- [hier_config Documentation](https://hier-config.readthedocs.io/)
