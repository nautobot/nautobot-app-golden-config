# Quick Start Guides

- [Quick Start Guides](#quick-start-guides)
- [Backup Configuration](#backup-configuration)
- [Intended Configuration](#intended-configuration)
- [Compliance](#compliance)
- [Load Properties from Git](#load-properties-from-git)

# Backup Configuration

Follow the steps below to get up and running for the configuration backup element of the plugin.

1. Enable the feature in the `PLUGIN_SETTINGS`. The configuration should have `"enable_backup": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.

2. Add any git repositories that will be used to house the backup configurations.

   1. In the UI `Extensibility -> Git Repositories`. Click Add.
   2. Populate the Git Repository data for the backup. [Git Settings](./navigating-golden.md#git-settings)
   3. Make sure to select the **Provides** called `backup configs`.
   4. Click Create.

3. Next, make sure to create new or update existing Plugins **Settings** with the backup details.

   1. Navigate to `Golden Config -> Settings` under the Golden Configuration Section.
   2. Create new or select one of the existing `Settings` objects
   3. Fill out the Backup Repository. (The dropdown will show the repository that was just created.)
   4. Fill out Backup Path Template. Typically `{{obj.site.slug}}/{{obj.name}}.cfg`, see [Setting Details](./navigating-golden.md#application-settings)
   5. Select whether or not to do a connectivity check per device.
   6. Click Save.

4. Create Configuration Removals and Replacements.

   1. [Config Removals](./navigating-backup.md#config-removals)
   2. [Config Replacements](./navigating-backup.md#config-replacements)

5. Execute the Backup.

   1. Navigate to `Golden Config -> Home` under the Golden Configuration Section.
   2. Click on the `Execute` button and select `Backup`.
   3. Select what to run the backup on.
   4. Run the Job by clicking "Run Job" button.

> For in-depth details see [Navigating Backup](./navigating-backup.md)

# Intended Configuration

Follow the steps below to get up and running for the intended configuration element of the plugin.

> Notice: Intended Configuration requires the `enable_intended` and `enabled_sotAgg` plugin features to be used.

1. Enable the feature in the `PLUGIN_SETTINGS`. The configuration should have `"enable_intended": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.

> Notice: If Secret Group is used for the Repositories the secrets type HTTP(S) is required for this plugin.

2. Add any git repositories that will be used to house the intended configurations.

   1. In the UI `Extensibility -> Git Repositories`. Click Add.
   2. Populate the Git Repository data for the intended. [Git Settings](./navigating-golden.md#git-settings)
   3. Make sure to select the **Provides** called `intended configs`.
   4. Click Create.

3. Add the git repository that will be used to house the Jinja2 templates.

   1. In the UI `Extensibility -> Git Repositories`. Click Add.
   2. Populate the Git Repository data for the jinja2 templates. [Git Settings](./navigating-golden.md#git-settings)
   3. Make sure to select the **Provides** called `jinja templates`.
   4. Click Create.

4. Next, make sure to create new or update existing Plugins **Settings** with the intended and jinja2 template details.

   1. Navigate to `Golden Config -> Settings` under the Golden Configuration Section.
   2. Create new or select one of the existing `Settings` objects
   3. Fill out the Intended Repository. (The dropdown will show the repository that was just created.)
   4. Fill out Intended Path Template. Typically `{{obj.site.slug}}/{{obj.name}}.cfg`, see [Setting Details](./navigating-golden.md#application-settings)
   5. Fill out Jinja Repository. (The dropdown will show the repository that was just created.)
   6. Fill out Jinja Path Template.  Typically `{{obj.platform.slug}}.j2`.

5. Determine what data(variables) the Jinja2 templates need from Nautobot.

   1. See [Source of Truth Agg Details](./navigating-sot-agg.md)
   2. In the UI `Extensibility -> GraphQL Queries`. Click Add.
   3. Populate the GraphQL data.
   4. Make sure to follow the format specified in the **GraphQL** section in [Source of Truth Agg Details](./navigating-sot-agg.md)
   5. Click Create.
   6. Navigate to `Golden Config -> Settings` under the Golden Configuration Section.
   7. Select a SoTAgg Saved Query. (The dropdown will show the GraphQL query that was just created.)

6. Execute the Intended.

   1. Navigate to `Golden Config -> Home`.
   2. Click on the `Execute` button and select `Intended`.
   3. Select what to run the intended generation on.
   4. Run the Job.

> For in-depth details see [Navigating Intended](./navigating-intended.md)

# Compliance

Compliance requires Backups and Intended Configurations in order to be executed.

1. Enable the feature in the `PLUGIN_SETTINGS`. The configuration should have `"enable_compliance": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.
2. Follow the steps in [Backup Configuration](#backup-configuration).
3. Follow the steps in [Intended Configuration](#intended-configuration).
4. Create a Compliance Feature.

   1. Navigate to `Golden Config -> Compliance Feature`.
   2. Click Add and give the feature a name. Typically this is based on the configuration snippet or section. E.g. "aaa".

5. Create a Compliance Rule.

   1. Navigate to `Golden Config -> Compliance Rules`.
   2. Click Add and populate the fields, make sure the rule is linked to the feature created previously. See [Configuration Compliance Settings](./navigating-compliance.md#configuration-compliance-settings) for details.

6. Execute Compliance Check.

   1. Navigate to `Golden Config -> Configuration Compliance`.
   2. Click on the `Execute` button and select `Compliance`.
   3. Select what to run the compliance on.
   4. Run the Job.

> For in-depth details see [Navigating Compliance](./navigating-compliance.md)

# Load Properties from Git

Golden Config properties include: Compliance Features, Compliance Rules, Config Removals, and Config Replacements. They can be created via the UI, API, or alternatively you can load these properties from a Git repository, defined in YAML files following the this directory structure (you can skip any of them if not apply):

```
├── golden_config
│   ├── compliance_features
│   ├── compliance_rules
│   ├── config_removes
│   ├── config_replaces
```

The files within these folders can follow any naming pattern or nested folder structure, all of them will be recursively taken into account. So it's up to you to decide how to you prefer to organize these files (within the previously stated directory structure):

````
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
``

The `YAML` files will contain all the attributes necessary to identify an object (for instance, a `ComplianceRule` is identified by the `feature_slug` and the `platform_slug` together) and the other attributes (the ones that are not used to identify the object). For example:

`compliance_features` example:

```yaml
---
- name: "aaa"
  slug: "aaa"
  description: "aaa feature"
````

`compliance_rules` example:

```yaml
---
- feature_slug: "aaa"
  platform_slug: "cisco_ios"
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
- platform_slug: "cisco_ios"
  name: "Build config"
  regex: '^Building\s+configuration.*\n'
```

`config_replaces` example:

```yaml
---
- name: "username"
  platform_slug: "cisco_ios"
  description: "username"
  regex: '(username\s+\S+\spassword\s+5\s+)\S+(\s+role\s+\S+)'
  replace: '\1<redacted_config>\2'
```

> For Foreign Key references to `ComplianceFeature` and `Platform` we use the keywords `feature_slug` and `platform_slug` respectively.

1. Add the Git repository that will be used to sync Git properties.

   1. In the UI `Extensibility -> Git Repositories`. Click Add.
   2. Populate the Git Repository data for the GC properties. [Git Settings](./navigating-golden.md#git-settings)
   3. Make sure to select the **Provides** called `Golden Config properties`.
   4. Click Create (This step runs an automatic sync).

2. Run `sync` and all the properties will be created/updated in a declarative way and following the right order to respect the dependencies between objects. The import task will raise a `warning` if the dependencies are not available yet (for instance, a referenced `Platform` is not created), so the `sync` process will continue, and you could then fix these warnings by reviewing the mismatch (maybe creating the required object) and run the `sync` process again.

```

```
