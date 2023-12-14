# Getting Started with the App

This document provides a step-by-step tutorial on how to get the App going and how to use it.

## Install the App

To install the App, please follow the instructions detailed in the [Installation Guide](../admin/install.md).

## First steps with the App

### Backup Configuration

Follow the steps below to get up and running for the configuration backup element of the plugin.

1. Enable the feature in the `PLUGIN_SETTINGS`. The configuration should have `"enable_backup": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.

2. Add any git repositories that will be used to house the backup configurations.

    1. In the UI `Extensibility -> Git Repositories`. Click Add.
    2. Populate the Git Repository data for the backup. [Git Settings](./app_use_cases.md#git-settings)
    3. Make sure to select the **Provides** called `backup configs`.
    4. Click Create.

3. Next, make sure to create new or update existing Plugins **Settings** with the backup details.
    1. Navigate to `Golden Config -> Settings` under the Golden Configuration Section.
    2. Create new or select one of the existing `Settings` objects
    3. Fill out the Backup Repository. (The dropdown will show the repository that was just created.)
    4. Fill out Backup Path Template. Typically `{{obj.location.name|slugify}}/{{obj.name}}.cfg`, see [Setting Details](./app_use_cases.md#application-settings)
    5. Select whether or not to do a connectivity check per device.
    6. Click Save.

4. Create Configuration Removals and Replacements.

    1. [Config Removals](./app_feature_backup.md#config-removals)
    2. [Config Replacements](./app_feature_backup.md#config-replacements)

5. Execute the Backup.

    1. Navigate to `Golden Config -> Home` under the Golden Configuration Section.
    2. Click on the `Execute` button and select `Backup`.
    3. Select what to run the backup on.
    4. Run the Job by clicking "Run Job" button.

> For in-depth details see [Navigating Backup](./app_feature_backup.md)

### Intended Configuration

Follow the steps below to get up and running for the intended configuration element of the plugin.

!!! note
    Intended Configuration requires the `enable_intended` and `enabled_sotAgg` plugin features to be used.

!!! note
    If Secret Group is used for the Repositories the secrets type HTTP(S) is required for this plugin.

1. Enable the feature in the `PLUGIN_SETTINGS`. The configuration should have `"enable_intended": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.


2. Add any git repositories that will be used to house the intended configurations.

    1. In the UI `Extensibility -> Git Repositories`. Click Add.
    2. Populate the Git Repository data for the intended. [Git Settings](./app_feature_backup.md#git-settings)
    3. Make sure to select the **Provides** called `intended configs`.
    4. Click Create.

3. Add the git repository that will be used to house the Jinja2 templates.

    1. In the UI `Extensibility -> Git Repositories`. Click Add.
    2. Populate the Git Repository data for the jinja2 templates. [Git Settings](./app_feature_backup.md#git-settings)
    3. Make sure to select the **Provides** called `jinja templates`.
    4. Click Create.

4. Next, make sure to create new or update existing Plugins **Settings** with the intended and jinja2 template details.

    1. Navigate to `Golden Config -> Settings` under the Golden Configuration Section.
    2. Create new or select one of the existing `Settings` objects
    3. Fill out the Intended Repository. (The dropdown will show the repository that was just created.)
    4. Fill out Intended Path Template. Typically `{{obj.location.name|slugify}}/{{obj.name}}.cfg`, see [Setting Details](./app_feature_backup.md#application-settings)
    5. Fill out Jinja Repository. (The dropdown will show the repository that was just created.)
    6. Fill out Jinja Path Template.  Typically `{{obj.platform.network_driver}}.j2`.

5. Determine what data(variables) the Jinja2 templates need from Nautobot.

    1. See [Source of Truth Agg Details](./app_feature_sotagg.md)
    2. In the UI `Extensibility -> GraphQL Queries`. Click Add.
    3. Populate the GraphQL data.
    4. Make sure to follow the format specified in the **GraphQL** section in [Source of Truth Agg Details](./app_feature_sotagg.md)
    5. Click Create.
    6. Navigate to `Golden Config -> Settings` under the Golden Configuration Section.
    7. Select a SoTAgg Saved Query. (The dropdown will show the GraphQL query that was just created.)

6. Execute the Intended.

    1. Navigate to `Golden Config -> Home`.
    2. Click on the `Execute` button and select `Intended`.
    3. Select what to run the intended generation on.
    4. Run the Job.

> For in-depth details see [Navigating Intended](./app_feature_intended.md)

### Compliance

Compliance requires Backups and Intended Configurations in order to be executed.

1. Enable the feature in the `PLUGIN_SETTINGS`. The configuration should have `"enable_compliance": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.
2. Follow the steps in [Backup Configuration](#backup-configuration).
3. Follow the steps in [Intended Configuration](#intended-configuration).
4. Create a Compliance Feature.

    1. Navigate to `Golden Config -> Compliance Feature`.
    2. Click Add and give the feature a name. Typically this is based on the configuration snippet or section. E.g. "aaa".

5. Create a Compliance Rule.

    1. Navigate to `Golden Config -> Compliance Rules`.
    2. Click Add and populate the fields, make sure the rule is linked to the feature created previously. See [Configuration Compliance Settings](./app_feature_compliance.md#configuration-compliance-settings) for details.

6. Execute Compliance Check.

    1. Navigate to `Golden Config -> Configuration Compliance`.
    2. Click on the `Execute` button and select `Compliance`.
    3. Select what to run the compliance on.
    4. Run the Job.

> For in-depth details see [Navigating Compliance](./app_feature_compliance.md)

### Config Remediation

Follow the steps below to get up and running for the configuration remediation element of the plugin.

1. Navigate to `Golden Config -> Compliance Rules`.
2. Select the rules in which you'd like to enable remediation on.
3. Edit the `Compliance Rule` and turn on the `Remediation` toggle button.
4. Run the `Compliance` job again which will generate the initial remediation plan for the feature.
5. Navigate to `Golden Config -> Config Compliance`, select the device and notice a remediation section is not present for the compliance details for the feature.

> For in-depth details see [Navigating Config Plans](./app_feature_remediation.md)

### Config Plans

Follow the steps below to get up and running for the configuration plans element of the plugin.

1. Enable the feature in the `PLUGIN_SETTINGS`. The configuration should have `"enable_plan": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.
2. Follow the steps in [Compliance](#compliance).
    - Compliance is necessary if ConfigPlans will be generated utilizing any of the attributes provided by a Compliance object.
    - This step may be skipped if only `manual` ConfigPlans are going to be generated.
3. Create a ConfigPlan

    1. Navigate to `Golden Config -> Config Plans`
    2. Click on `ADD` button.
    3. Fill out the plan details and plan filters.
        - The options dynamically change in the form based on the `plan type` selected.
        - If the `plan type` is Intended, Remediation, Missing.
            - Select the Compliance Features to use to generate the plan.  If none are selected all features will be in scope.
        - If the `plan type` is Manual.
            - Create a manual plan to accomplish the goal. Note: Access to `obj` is available to dynamically populate fields via Jinja2 syntax.
    4. Click `Generate`

> For in-depth details see [Navigating Config Plans](./app_feature_config_plans.md)

### Config Deploy

Follow the steps below to get up and running for the configuration deployment element of the plugin.

1. Enable the feature in the `PLUGIN_SETTINGS`. The configuration should have `"enable_deploy": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.
2. Follow the steps in [Config Plans](#config-plans).
3. Navigate to the specific ConfigPlan to deploy, or multi-select them from the ConfigPlan list view.
    - If deploying from a specific ConfigPlan object. Click `Deploy` button and accept the warnings.
    - If deploying from the ConfigPlan list view. Click `Deploy Selected` button and accept the warnings.
4. Interpret the results from the popup modal and navigate to the job result as needed for more details.

> Config Deployments utilize the dispatchers from nornir-nautobot just like the other functionality of Golden Config. See [Troubleshooting Dispatchers](./troubleshooting/troubleshoot_dispatchers.md) for more details.

### Load Properties from Git

Golden Config properties include: Compliance Features, Compliance Rules, Config Removals, and Config Replacements. They can be created via the UI, API, or alternatively you can load these properties from a Git repository, defined in YAML files following the this directory structure (you can skip any of them if not apply):

```shell
├── golden_config
│   ├── compliance_features
│   ├── compliance_rules
│   ├── config_removes
│   ├── config_replaces
```

The files within these folders can follow any naming pattern or nested folder structure, all of them will be recursively taken into account. So it's up to you to decide how to you prefer to organize these files (within the previously stated directory structure):

```shell
├── golden_config
│   ├── compliance_features
│   │   └── all.yml
│   ├── compliance_rules
│   │   ├── my_rule_for_cisco_ios
│   │   │   ├── some_rules.yml
│   │   │   └── some_other_rules.yml
│   │   └── juniper_junos.yml
│   ├── config_removes
│   │   ├── cisco_ios.yml
│   │   └── juniper_junos.yml
│   ├── config_replaces
│   │   ├── cisco_ios.yml
│   │   └── juniper_junos.yml
```

The `YAML` files will contain all the attributes necessary to identify an object (for instance, a `ComplianceRule` is identified by the `feature_slug` and the `platform_network_driver` together) and the other attributes (the ones that are not used to identify the object). For example:

`compliance_features` example:

```yaml
---
- name: "aaa"
  slug: "aaa"
  description: "aaa feature"
```

`compliance_rules` example:

```yaml
---
- feature_slug: "aaa"
  platform_network_driver: "Cisco IOS"
  config_ordered: true
  match_config: |
    aaa
    line
    username
    role
    tacacs
  config_type: "cli"
```

`config_removes` example:

```yaml
---
- platform_network_driver: "Cisco IOS"
  name: "Build config"
  regex: '^Building\s+configuration.*\n'
```

`config_replaces` example:

```yaml
---
- name: "username"
  platform_network_driver: "Cisco IOS"
  description: "username"
  regex: '(username\s+\S+\spassword\s+5\s+)\S+(\s+role\s+\S+)'
  replace: '\1<redacted_config>\2'
```

CustomField data can be added using the `_custom_field_data` attribute, that takes a dictionary mapping custom_field names to their values:

```yaml
---
- name: "aaa"
  slug: "aaa"
  description: "aaa feature"
  _custom_field_data:
    custom_field_a: "abc"
    custom_field_b: 123
```

!!! note
    For Foreign Key references to `ComplianceFeature` and `Platform` we use the keywords `feature_slug` and `platform_network_driver` respectively.

1. Add the Git repository that will be used to sync Git properties.

    1. In the UI `Extensibility -> Git Repositories`. Click Add.
    2. Populate the Git Repository data for the GC properties. [Git Settings](./app_use_cases.md#git-settings)
    3. Make sure to select the **Provides** called `Golden Config properties`.
    4. Click Create (This step runs an automatic sync).

2. Run `sync` and all the properties will be created/updated in a declarative way and following the right order to respect the dependencies between objects. The import task will raise a `warning` if the dependencies are not available yet (for instance, a referenced `Platform` is not created), so the `sync` process will continue, and you could then fix these warnings by reviewing the mismatch (maybe creating the required object) and run the `sync` process again.

### Constance Settings

Golden config uses the `dispatch_params()` function in conjunction with the constance settings DEFAULT_FRAMEWORK, GET_CONFIG_FRAMEWORK, MERGE_CONFIG_FRAMEWORK, and REPLACE_CONFIG_FRAMEWORK. This allows you to define in this order of precedence:

- For a specific method, such as get_config, which framework do I want to use, netmiko or napalm **for a specific network_driver** such as `cisco_ios`?
- For a specific method, such as get_config, which framework do I want to use, netmiko or napalm  **for all** network_drivers?
- By default, which framework do I want to use, netmiko or napalm **for a specific network_driver** such as `cisco_ios`?
- By default, which framework do I want to use, netmiko or napalm **for all** network_drivers?

!!! info
    These settings are not considered when using a custom_dispatcher as described below.

Each of the constance settings allow for the usage of either a key named **exactly** as the `network_driver` or the key of `all`, anything else will not result in anything valid. The value, should only be napalm or netmiko at this point, but subject to change in the future.

Let's take a few examples to bring this to life a bit more.

```json
# DEFAULT_FRAMEWORK
{
  "all": "napalm"
}
```

Using the previous example, everything will use the napalm dispatcher, this is in fact the default settings

```json
# DEFAULT_FRAMEWORK
{
  "all": "napalm",
  "fortinet": "netmiko"
}
```

Using the previous example, everything will use the napalm dispatcher **except** forinet, which would use netmiko.

```json
# DEFAULT_FRAMEWORK
{
  "all": "napalm",
  "fortinet": "netmiko"
}
# GET_CONFIG_FRAMEWORK
{
  "arista_eos": "netmiko",
  "cisco_nxos": "netmiko"
}
```

Using the previous example, everything will use the napalm dispatcher **except** forinet **and** when using the `get_config` method for `arista_eos` and `cisco_nxos`, use netmiko.

As you can see, you now have the flexibility to control which network_driver will use which framework for every method, as each constance setting is sanely named to match the method name (e.g. `GET_CONFIG_FRAMEWORK` maps the `get_config` method). Additionally, if the current `network_driver` and associated `network_driver_mappings` is not sufficient as is, you can extend the [NETWORK DRIVER](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/configuration/optional-settings/#network_drivers) settings as well.

Golden Config leverages the [config framework](https://docs.nautobot.com/projects/core/en/stable/development/apps/api/database-backend-config/) from [constance](https://django-constance.readthedocs.io/en/latest/), please refer to that documentation for how to use. You can access your configurations from your name in the top right of the UI, followed by `Admin -> Configuration -> Config` and locate your setting.

## What are the next steps?

You can check out the [Use Cases](app_use_cases.md) section for more examples.
