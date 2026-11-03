# Partial Configuration Compliance

## Overview

Partial Configuration Compliance is an extension to the standard CLI-based compliance checking that leverages the `hier_config` library to provide advanced configuration parsing and comparison capabilities. This feature allows you to define matching rules that focus compliance checks on specific lines, including lines nested under a parent, instead of complete configuration sections.

Unlike standard CLI compliance which matches configuration sections based on simple line-starting patterns, Partial Configuration Compliance identifies and compares configuration elements based on their hierarchical relationships and specific attributes, which allows for filtering based on nested config lines.

## When to Use Partial Configuration Compliance

This feature is particularly useful for:

- Configurations that are benign or non-consequential to overall device operation.
- When you are building out your compliance journey, and not prepared to include all configurations based on simple line matching.

!!! warning
    Should not be used to provide full line matches or matches that are better served as data, as an example you should not do this `- startswith: description USER PORT` but should do this `- startswith: description`.

## Requirements

### Platform Support

Partial configuration compliance requires:

1. **Platform Compatibility**: Your device platform must be supported by the `hier_config` library
2. **Network Driver Mapping**: The platform must have a valid `hier_config` mapping in its `network_driver_mappings`

## Configuring Partial Compliance Rules

### Rule Identification

To create a partial compliance rule, set the **Config Type** of the compliance rule to `Partial CLI`.

The **Config to Match** field is mandatory and must be YAML consisting of one or more rule blocks. Each rule block uses the `match_rules` key containing an ordered list of predicates (e.g. `startswith`, `contains`, `re_search`, `endswith`), one for each level of the configuration hierarchy.

### Syntax

Example with two rule blocks:

```yaml
- match_rules:
  - startswith: router bgp
  - startswith: neighbor
- match_rules:
  - startswith: interface
  - contains: GigabitEthernet
```

### Validation

The **Config to Match** field is validated when the compliance rule is saved, in the UI and the API. The rule is rejected if the field is:

- Not valid YAML.
- Not a non-empty list of rule blocks.
- Contains a rule block that is not a mapping with a `match_rules` key.
- Contains match rules that `hier_config` rejects.

The same checks run during the compliance job, so an invalid rule fails the job with a clear error.

### Example Configuration Rules

#### Example 1: BGP Neighbor Configuration

To check compliance for all BGP neighbor configurations:

```yaml
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

## Viewing Partial Compliance Results

The actual and intended configurations stored for a partial compliance rule only contain the matched lines and their parent lines. Compliance, missing, extra and remediation are all based on these lines.

To see the matched lines in context, the configuration panels of a partial compliance rule have a **Matched | Full** toggle. It is available on the Config Compliance detail page and on each partial rule of a device's Config Compliance tab.

- **Matched** (default) shows the stored actual and intended configurations.
- **Full** shows the complete top-level sections that contain a matched line in either configuration, for example the whole `interface` section instead of only its `ip flow monitor` line.

On the detail page, the selected view is remembered for the user.

!!! note
    The **Full** view is built from the latest backup and intended configurations stored for the device, which can be newer than the last compliance run.

## Known Limitation: Remediation of Sections Without Matches

When none of the matched lines under a parent are present in the intended configuration, the parent is not part of the intended configuration either. Config remediation then treats the whole section as extra and can propose removing it.

For example, with a rule matching `ip flow monitor` lines under interfaces:

```yaml
- match_rules:
  - startswith: interface
  - startswith: ip flow monitor
```

If the running configuration has `ip flow monitor` on `GigabitEthernet0/1` and the intended configuration does not, the proposed remediation is `no interface GigabitEthernet0/1` instead of `no ip flow monitor ...` under the interface.

Always review the remediation of these rules before deploying it.

## Troubleshooting

### Common Issues

#### Platform Not Supported
**Error**: `Unsupported platform for hier_config v3: <platform>`

**Solution**: Ensure your device platform has a valid `hier_config` mapping in its `network_driver_mappings`. Check the platform configuration in Nautobot.

#### Invalid Config to Match
**Error**: `Invalid YAML in match_config: <error details>`, `Invalid hier_config match rules in match_config: <error details>` or a similar message on the **Config to Match** field.

**Solution**: Fix the **Config to Match** field so it is a YAML list of rule blocks, each with a `match_rules` key. Ensure proper indentation and structure.

### Debug Tips

1. **Check Platform Support**: Verify your platform's `network_driver_mappings` include `hier_config`
2. **Review hier_config Documentation**: Consult the [hier_config documentation](https://hier-config.readthedocs.io/en/latest/tags/) for advanced tagging examples
3. **Start Simple**: Begin with basic matching rules and gradually add complexity
4. **Use the Full View**: Switch to **Full** to check which sections the rule matched

## Best Practices

### Rule Design

1. **Specific Matching**: Create focused rules that target specific configuration elements
2. **Logical Grouping**: Group related configuration elements in single rules when appropriate
3. **Clear Naming**: Use descriptive feature names that clearly indicate what the rule validates

## Advanced Usage

### Combining Multiple Rules

You can create multiple partial compliance rules for the same platform to check different aspects of the configuration independently.

### Integration with Configuration Management

Partial configuration compliance works seamlessly with existing configuration management workflows:

- Backup processes remain unchanged
- Intended configuration generation follows the same patterns
- Compliance reporting provides the same interface with enhanced precision

## Related Documentation

- [Standard CLI Compliance](./app_feature_compliancecli.md)
- [Configuration Compliance Overview](./app_feature_compliance.md)
- [hier_config Documentation](https://hier-config.readthedocs.io/)
