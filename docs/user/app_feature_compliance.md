# Configuration Compliance

The following should be noted by what is meant by configuration compliance. Configurations are considered to be compliant if the generated configuration
(generally by merging data and Jinja2, will be referred to as the intended configuration from hence forth) matches "exactly" as the actual configuration is
on the backup. This may confusing to some, as for example to the average network engineer, there is no difference between `int g0/0` and
`interface GigabitEthernet0/0` but for the purpose of configuration compliance, it is not a match... full stop.

It's helpful to understand what are some common reasons a device is not compliant.

* There is missing configuration on the device.
* There is extra configuration on the device.
* The data used to generate the configuration is incorrect, and created a "false positive".
* The template used to generate the configuration is incorrect, and created a "false positive".
* The parser used to obtain the configuration from the feature is incorrect, and created a "false positive".

There is no magic to determine the state of configuration. You still must define what is good configuration and compare it. There are several reasons why
configuration may be as a network engineer wants it, but the tool correctly considers it non-compliant, since the tool is only comparing two configurations.
The tool makes no assumptions to determine what an engineer may want to do, but did not document via the configuration generation process.

## Compliance Configuration Settings

In order to generate the intended configurations, a minimum of two repositories are required.

1. At least one repository in which to save [intended configurations](./app_use_cases.md#git-settings) once generated.
2. At least one repository in which to store [Backups](./app_use_cases.md#git-settings) of devices' running configurations.
3. The [intended_path_template](./app_use_cases.md#application-settings) configuration parameter.
4. The [backup_path_template](./app_use_cases.md#application-settings) configuration parameter.

## Common Pitfalls

Understanding how Golden Config compliance works is straightforward once you grasp its mental model, but it often differs from what many users expect. Many compliance engines ask questions like "we should have NTP servers," focusing on the presence of certain configuration lines. In contrast, Golden Config compliance asks, "Does the intended NTP server configuration exactly match the actual configuration?" This approach is further distinguished by separating data from syntax using Jinja2 templates, rather than relying on regex matching or similar techniques.

Because of this shift in perspective, new users commonly encounter the following pitfalls.

### Data-Driven Templates vs Hardcoded Logic

A common pitfall when getting started with configuration compliance is to hardcode configuration per group directly in templates:

```jinja
{# Avoid this pattern — hardcoding config per region #}
{% if obj.location.parent.name == 'Americas' %}
ntp server 10.1.1.1
ntp server 10.1.1.2
{% elif obj.location.parent.name == 'Europe' %}
ntp server 10.2.1.1
ntp server 10.2.1.2
{% endif %}
```

This may work at first, but does not scale. Every new region, tenant, or role requires a template change. The recommended approach is to separate data from the cli syntax:

```jinja
{# Recommended — data-driven config generation #}
{% for ntp_server in config_context.ntp_servers %}
ntp server {{ ntp_server }}
{% endfor %}
```

Different scopes produce different data, and the same template generates the correct configuration for each device. This means:

- Adding a new region does not require a template change — just assign the correct config context data.
- The same template works for all devices on the platform regardless of tenant, role, or site.
- The compliance rule remains one rule per platform per feature. Different devices produce different intended configurations because the *data* is different, not the rule or the template logic.

This same principle applies to the question of per-tenant, per-role, per-tag or literally any data point compliance rules. Different tenants using TACACS+ vs RADIUS do not need separate `aaa` compliance rules. They need one `aaa` rule and templates that generate the correct AAA configuration based on the device's data.

### Compliance Rules Define Sections, Not Content

Another common pitfall is to put specific configuration lines into the compliance rule's "Config to Match" field:

```
ntp server 10.2.1.1
ntp server 10.2.1.2
```

This conflates the role of the compliance rule with the role of the intended configuration. The "Config to Match" field is a **section matcher** — it identifies which section of the running configuration to extract for comparison. For NTP, the correct match config is:

```
ntp server
```

This captures all lines beginning with `ntp server` from both the backup and the intended configuration. The compliance engine then compares the two sets. The *specific NTP servers* that should be present are defined in the intended configuration, which is generated from your templates and data — not from the compliance rule.

Putting full configuration lines in the rule creates several problems:

- The rule becomes device-specific and cannot be shared across the platform.
- Changing an NTP server requires updating the rule and the template instead of updating data.
- It signals that this is how configurations are generated when it is not the case.


## Empty Compliance Behavior

A common point of confusion is what happens when a compliance rule exists for a platform, but not every device on that platform needs every feature. For example:

- A BGP compliance rule applies to all Cisco IOS devices, but campus access switches will never have BGP configuration.
- Multiple teams share a platform, but Team B hasn't built intended configurations for a feature that Team A already manages.
- Core routers need `dot1x` compliance, but access switches on the same platform do not.

In all of these cases, the compliance engine compares the intended configuration against the actual configuration. **If you are generating the correct intended configuration, the answer is already handled.** A campus switch that should never have BGP should generate an empty intended BGP configuration — and an empty actual BGP section is a valid match. This is by design.

However, this can create confusion when reviewing compliance results:

- A device shows "Compliant" for BGP even though BGP was never relevant to it.
- A device shows "Non-Compliant" with "extra" configuration because Team B hasn't built the intended config yet, but the feature already exists on the device.

### When Empty Results Are Misleading

The real problem arises when a feature is not yet relevant or will never be relevant to a device, and the empty-vs-empty comparison produces a "Compliant" result that is misleading — or when a device has actual configuration but no intended configuration has been generated yet, producing a "Non-Compliant" result prematurely.

The **Empty Compliance Behavior** setting addresses this. Navigate to `Golden Config -> Settings`, select a settings entry, and choose one of the three options:

| Behavior | Use Case | Intended Empty + Actual Empty | Intended Empty + Actual Populated | Intended Populated |
|:--|:--|:--|:--|:--|
| **Validated** (default) | Standard compliance — empty configs are a valid match | Compliant | Normal compliance check | Normal compliance check |
| **Empty Both** | Features that will never apply to certain devices (e.g., BGP on campus switches) | N/A | Normal compliance check | Normal compliance check |
| **Empty Intended** | Gradual rollout — intended config is not yet generated for all devices | N/A | N/A | Normal compliance check |

**Empty Both** is best when a feature permanently does not apply to a device. Neither the intended nor the actual configuration will ever exist, so there is nothing meaningful to validate. This removes the noise of "Compliant" results for features that were never relevant.

**Empty Intended** is best when you are progressively rolling out intended configurations across teams or groups. Some devices may already have actual configuration on the device for a feature, but the intended configuration has not been built yet. Without this setting, those devices would show as "Non-Compliant" with extra configuration — even though no one has defined what the intended state should be. With **Empty Intended**, compliance is deferred until the intended configuration is generated.

When a compliance record is marked as N/A:

- The device tab shows a gray "N/A" badge instead of Compliant/Non-Compliant.
- The compliance overview table shows a dash for that feature.
- N/A records are excluded from compliance percentage calculations, compliant counts, and non-compliant counts.
- Remediation configuration is not generated for N/A records.

### Practical Usage: Controlling Empty Configurations via Templates

The Empty Compliance Behavior setting works in conjunction with your Jinja2 templates. By conditionally omitting configuration in your intended templates, you control which devices produce empty intended configs for a given feature — and the setting determines how those empty results are handled.

For example, if you are gradually rolling out NTP compliance and only certain tenants are ready:

```jinja
{# Only generate NTP configuration for tenants that have been onboarded #}
{% if obj.tenant and obj.tenant.name in ['Wayne Enterprise', 'Acme Corp'] %}
ntp server 10.1.1.1
ntp server 10.2.2.2
ntp source Loopback0
{% endif %}
```

Devices belonging to tenants not in the list will produce an empty intended configuration for this feature. With **Empty Intended** selected, those devices will show N/A instead of being flagged as non-compliant. As you onboard additional tenants, simply add them to the template condition — their compliance will begin to be evaluated automatically.

!!! note "Why not add filters to compliance rules?"
    Compliance rules are intentionally scoped to the platform level only. Adding tenant, role, site, tag or series of other filters directly to compliance rules would significantly increase the complexity of the solution, as rules would need to support multiple filter combinations, priority resolution, and overlapping scope. The Empty Compliance Behavior setting, combined with data-driven templates, provides the same outcome with far less complexity. The compliance rule stays simple (one rule per platform per feature), and the templates encode your business logic for which devices are in scope.

## Starting a Compliance Job

To start a compliance job manually:

1. Navigate to `Golden Config->Home`, with Home being in the `Golden Configuration` section
2. Select _Execute_ on the upper right buttons, then _Compliance_
3. Fill in the data that you wish to have a compliance report generated for
4. Select _Run Job_

## Configuration Compliance Settings

Configuration compliance requires the Git Repo settings for `config backups` and `intended configs`--which are covered in their respective sections--regardless if they are actually managed via the app or not. The same is true for the `Backup Path` and `Intended Path`.

The Configuration compliance rule map must be created per the operator/user. You can find these configurations via `Golden Config -> Compliance Rules`
links, which brings up the specific configurations.

![Configuration Rule](../images/ss1_navigate-compliance-rules_light.png#only-light){ .on-glb }
![Configuration Rule](../images/ss1_navigate-compliance-rules_dark.png#only-dark){ .on-glb }

Each configuration can be added and edits from this table. When editing/adding the configurations, the following should be noted.

![Configuration Rule Edit](../images/ss1_ss_compliance-rule_light.png#only-light){ .on-glb }
![Configuration Rule Edit](../images/ss1_ss_compliance-rule_dark.png#only-dark){ .on-glb }

The platform must refer to a platform with a valid network_driver supported by the configuration compliance engine. While there is no enforcement of this data from a database perspective, the job will never run successfully, rendering the additional configuration ineffective.

The Feature is a unique identifier, that should prefer shorter names, as this effects the width of the compliance overview and thus it's readability as a best practice.

The "Config to Match" section represents the configuration root elements. This would be the parent most key only. Additionally, the match is based on "Config Type", which could be JSON or CLI. For CLI based configs, the match is based on what a line starts with only. Meaning, there is an implicit greediness to the matching. All matches must start form the beginning of the line. For JSON based configs, the match is based on JSON's structure top level key name.

!!! note
    "Config to Match" is mandatory for CLI configurations. If config to match is not defined for JSON, the complete JSON configuration will be compared. If the config to match is defined, comparison will take place only for defined keys.

!!! note
    If the data is accidentally "corrupted" with a bad tested match, simply delete the devices an re-run the compliance process.

!!! note
    The mapping of "network_os" as defined by netutils is provided via the app settings in your nautobot_config.py, and documented on the primary Readme.

!!! note
    See [Compliance Rules Define Sections, Not Content](#compliance-rules-define-sections-not-content) for guidance on what belongs in Config to Match versus in your templates.

## Compliance View

The compliance overview will provide a per device and feature overview on the compliance of your network devices. From here you can navigate to the details view.

![Compliance Overview](../images/ss1_ss_compliance-overview_light.png#only-light){ .on-glb }
![Compliance Overview](../images/ss1_ss_compliance-overview_dark.png#only-dark){ .on-glb }

## Compliance Details View

Drilling into a specific device and feature, you can get an immediate detailed understanding of your device.

![Compliance Device](../images/ss1_device-compliance_light.png#only-light){ .on-glb }
![Compliance Device](../images/ss1_device-compliance_dark.png#only-dark){ .on-glb }

![Compliance Rule](../images/ss1_compliance-rule-detail_light.png#only-light){ .on-glb }
![Compliance Rule](../images/ss1_compliance-rule-detail_dark.png#only-dark){ .on-glb }

Please note the following about the compliance details page.

* The device Intended and Actual configuration will become a single cell configuration if there is an exact match.
* The device Intended and Actual configuration will both show if the configuration is matched, but not ordered the same.
* The icon next to the status will indicate whether or not the configuration is ordered.
* The icons on top of the page can be used to help navigate the page easier.

## Supported Platforms

Platforms support technically come from the options provided by [nornir-nautobot](https://github.com/nautobot/nornir-nautobot) for Nornir dispatcher tasks and
[netutils](https://github.com/networktocode/netutils) for configuration compliance and parsing. However, for reference, the valid network_driver's of the platforms are
provided in the [FAQ](./faq.md).

## Overview Report

There is a global overview or executive summary that provides a high level snapshot of the compliance. There are 3 points of data captured.

* Devices - This is only compliant if there is not a single non-compliant feature on the device. So if there is 10 features, and 1 feature is not compliant, the device is considered non-compliant.
* Features - This is the total number of features for all devices, and how many are compliant, and how many are non-compliant.
* Per Feature - This is a breakdown of that feature and how many within that feature are compliant of not.

## Detail Report

You can view the details from the `Compliance` details button within the `Configuration Compliance` table. From there you can filter the devices via the
form on the right side, limit the columns with the `Configure` button, or bulk delete with the `Delete` button. Additionally each device is click-able to view
the details of that individual device.

You can configure the columns to limit how much is showing on one screen.

## Device Details

You can get to the device details form either the Compliance details page, or there is a `content_template` on the device model page is Nautobot's core instance.

![Configuration Features](../images/ss1_device-compliance_light.png#only-light){ .on-glb }
![Configuration Features](../images/ss1_device-compliance_dark.png#only-dark){ .on-glb }
