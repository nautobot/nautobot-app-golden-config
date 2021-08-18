# Quick Start Guides

- [Backup Configuration](#backup-configuration)
- [Intended Configuration](#intended-configuration)
- [Compliance](#compliance)

# Backup Configuration

Follow the steps below to get up and running for the configuration backup element of the plugin.

1. Enable the feature in the `PLUGIN_SETTINGS`.  The configuration should have `"enable_backup": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.

2. Add the git repository that will be used to house the backup configurations.

    1. In the UI `Extensibility -> Git Repositories`. Click Add.
    2. Populate the Git Repository data for the backup. [Git Settings](./navigating-golden.md#git-settings)
    3. Make sure to select the **provides** called `backup configs`.
    4. Click Create.

3. Next, make sure to update the Plugins **Settings** with the backup details.

    1. Navigate to `Plugins -> Settings` under the Golden Configuration Section.
    2. Fill out the Backup Repository. (The dropdown will show the repository that was just created.)
    3. Fill out Backup Path Template. Typically `{{obj.site.slug}}/{{obj.name}}.cfg`, see [Setting Details](./navigating-golden.md#application-settings)
    4. Select whether or not to do a connectivity check per device.
    5. Click Save.

4. Create Configuration Removals and Replacements.

    1. [Config Removals](./navigating-backup#config-removals)
    2. [Config Replacements](./navigating-backup#config-replacements)

5. Execute the Backup.

    1. Navigate to `Plugins -> Home`.
    2. Click on the `Execute` button and select `Backup`.
    3. Select what to run the backup on.
    4. Run the Job.

> For in-depth details see [Navigating Backup](./navigating-backup.md)

# Intended Configuration

Follow the steps below to get up and running for the intended configuration element of the plugin.

> Notice: Intended Configuration requires the `enable_intended` and `enabled_sotAgg` plugin features to be used.

1. Enable the feature in the `PLUGIN_SETTINGS`.  The configuration should have `"enable_intended": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.

2. Add the git repository that will be used to house the intended configurations.

    1. In the UI `Extensibility -> Git Repositories`. Click Add.
    2. Populate the Git Repository data for the intended. [Git Settings](./navigating-golden.md#git-settings)
    3. Make sure to select the **provides** called `intended configs`.
    4. Click Create.

3. Add the git repository that will be used to house the Jinja2 templates.

    1. In the UI `Extensibility -> Git Repositories`. Click Add.
    2. Populate the Git Repository data for the jinja2 templates. [Git Settings](./navigating-golden.md#git-settings)
    3. Make sure to select the **provides** called `jinja templates`.
    4. Click Create.

4. Next, make sure to update the Plugins **Settings** with the intended and jinja2 template details.

    1. Navigate to `Plugins -> Settings` under the Golden Configuration Section.
    2. Fill out the Intended Repository. (The dropdown will show the repository that was just created.)
    3. Fill out Intended Path Template. Typically `{{obj.site.slug}}/{{obj.name}}.cfg`, see [Setting Details](./navigating-golden.md#application-settings)
    4. Fill out Jinja Repository. (The dropdown will show the repository that was just created.)
    5. Fill out Jinja Path Template.  Typically `{{obj.platform.slug}}.j2`.

4. Determine what data(variables) the Jinja2 templates need from Nautobot.

    1. See [Source of Truth Agg Details](./navigating-sot-agg.md)
    2. Populate the SoTAgg field in the `Plugin -> Settings`.

5. Execute the Intended.

    1. Navigate to `Plugins -> Home`.
    2. Click on the `Execute` button and select `Intended`.
    3. Select what to run the intended generation on.
    4. Run the Job.

> For in-depth details see [Navigating Intended](./navigating-intended.md)

# Compliance

Compliance requires Backups and Intended Configurations in order to be executed.

1. Enable the feature in the `PLUGIN_SETTINGS`.  The configuration should have `"enable_compliance": True` set in the `PLUGINS_CONFIG` dictionary for `nautobot_golden_config`.
2. Follow the steps in [Backup Configuration](#backup-configuration).
3. Follow the steps in [Intended Configuration](#intended-configuration).
4. Create a Compliance Feature.

    1. Navigate to `Plugins -> Compliance Feature`.
    2. Click Add and give the feature a name.  Typically this is based on the configuration snippet or section. E.g. "aaa".

5. Create a Compliance Rule.

    1. Navigate to `Plugins -> Compliance Rules`.
    2. Click Add and populate the fields, make sure the rule is linked to the feature created previously. See [Configuration Compliance Settings](./navigating-compliance.md#configuration-compliance-settings) for details.

6. Execute Compliance Check.

    1. Navigate to `Plugins -> Configuration Compliance`.
    2. Click on the `Execute` button and select `Compliance`.
    3. Select what to run the compliance on.
    4. Run the Job.

> For in-depth details see [Navigating Compliance](./navigating-compliance.md)
