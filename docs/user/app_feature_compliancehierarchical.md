# Hierarchical Configuration Compliance

!!! note
    This document provides instructions for using the Hierarchical Configuration Compliance feature, which is an advanced option for CLI-based configuration compliance.

## Introduction to Hierarchical Configuration Compliance

The Hierarchical Configuration Compliance feature extends the basic CLI-based compliance by using the [hier_config](https://github.com/netdevops/hier_config) library to provide more powerful and flexible configuration comparison capabilities. Instead of using simpler section-based parsing, hierarchical compliance allows you to define specific matching rules to target particular configuration elements across the configuration hierarchy.

This approach is especially useful for:

1. Focusing compliance checks on specific configuration areas while ignoring others
2. Creating complex matching patterns that span different configuration sections
3. Handling nested configuration structures with greater precision

## Setting Up Hierarchical Configuration Rules

To use the hierarchical configuration compliance feature:

1. Navigate to `Golden Config -> Compliance Rules`
2. Click "Add" to create a new rule
3. Select a platform that has a valid `hier_config` mapping
4. Select "CLI" as the Config Type
5. For the Match Config, start with the special comment marker `# hier_config` followed by YAML-formatted hierarchical rules

### Example Hierarchical Rule Definition

```yaml
# hier_config
- lineage:
    - startswith: interface
    - startswith: description

- lineage:
    - startswith: router bgp
    - contains: "neighbor"
```

This example creates compliance rules that will:
1. Match all interface description configurations 
2. Match all BGP neighbor configurations

### Key Concepts in Hierarchical Rules

Each rule in the hierarchical configuration consists of:

- **lineage**: Defines the path through the configuration hierarchy to match
- **filter options**: Various matching methods like `startswith`, `endswith`, `contains`, etc.

## How Hierarchical Compliance Works

When using hierarchical configuration compliance:

1. The system loads both the running (backup) and intended configurations
2. It creates a hierarchical representation of both configurations
3. It applies the matching rules defined in your compliance rule
4. Unique tags are assigned to matched configuration elements
5. Both configurations are filtered based on these tags
6. The filtered configurations are compared for compliance checking

## Advanced Matching Options

Hierarchical configuration rules support several matching methods:

| Method | Description | Example |
|--------|-------------|---------|
| `startswith` | Match lines starting with the pattern | `startswith: interface` |
| `endswith` | Match lines ending with the pattern | `endswith: "255.255.255.0"` |
| `contains` | Match lines containing the pattern | `contains: "permit ip any any"` |
| `re_search` | Use regular expression patterns | `lines_match: "ip address \d+\.\d+\.\d+\.\d+"` |

You can combine these in a single lineage to create complex matching patterns.


```yaml
# hier_config
- lineage:
  - startswith: interface
  - startswith: description
- lineage:
  - startswith: router bgp
  - startswith: address-family ipv4
  - endswith: activate
```

## Troubleshooting Hierarchical Rules

If you encounter issues with hierarchical compliance rules:

1. **Syntax errors**: Ensure your YAML syntax is correct
2. **Structure errors**: Each entry in the rule must be a dictionary with proper keys like `lineage`
3. **Empty results**: Check that your matching patterns aren't too restrictive
4. **Incomplete matching**: Verify that your lineage correctly traverses the configuration hierarchy

## More Information

For more detailed information about hierarchical configuration tagging, refer to the [hier_config documentation](https://hier-config.readthedocs.io/en/2.3-lts/advanced-topics/#working-with-tags).
