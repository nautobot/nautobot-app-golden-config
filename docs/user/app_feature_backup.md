# Configuration Backup

The backup configuration process requires the Nautobot worker to connect via Nornir to the device, and run the `show run` or equivalent command, 
and save the configuration. The high-level process to run backups is:

* Download the latest version of each of the Git repositories configured with the `backup configs` capability within Nautobot.
* Run a Nornir play to obtain the cli configurations.
* Optionally perform some lightweight processing of the backup.
* Store each device's backup configuration file on the local filesystem.
* Commit all files added or changed in each repository.
* Push configuration files to the remote Git repositories.

## Configuration Backup Settings

Backup configurations often need some amount of parsing to stay sane. The two obvious use cases are firstly the ability to remove lines such as the "Last 
Configuration" changed date, as this will cause unnecessary changes and secondly stripping out secrets from the configuration. In an effort to support these use cases, the following settings are available and further documented below.

* Config Removals - provides the ability to remove a line based on a regex match.
* Config Replacements - provides the ability to swap out parts of a line based on a regex match.

### Backup Repositories

In the `Backup Repository` field of the Settings, configure the repository which you intend to use for backed-up device configurations as part of Golden Config.

Backup repositories must first be configured under **Extensibility -> Git Repositories**. When you configure a repository, look for the `Provides` field in the UI. To serve as a configuration backup store, the repository must be configured with the `backup configs` capability under the `Provides` field. For further details, refer to [Navigating Nautobot Git Settings](./app_use_cases.md#git-settings).


### Backup Path Template

The `backup_path_template` setting gives you a way to dynamically place each device's configuration file in the repository file structure. This setting uses the GraphQL query configured for the plugin. It works in a similar way to the Backup Repository Matching Rule above. Since the setting uses a GraphQL query, any valid Device model method is available. The plugin renders the values from the query, using Jinja2, to the relative path and file name in which to store a given device's configuration inside its backup repository. This may seem complicated, but the equivalent of `obj` by example would be:

```python
obj = Device.objects.get(name="nyc-rt01")
```

An example would be:
```python
backup_path_template = "{{obj.site.slug}}/{{obj.name}}.cfg"
```

With a Sydney, AU device `SYD001AURTR32`, in the site named `Sydney001` and the GraphQL query and `backup_path_template` configured above, our backed-up config would be placed in the repo in `/sydney001/SYD001AURTR32.cfg`.  The site value `sydney001` here is lower case because our template refers to the `slug` value, which by default will be lower case.

The backup process will automatically create folders as required based on the path definition. 

The `backup_path_template` can be set in the UI.  For navigation details [see](./app_use_cases.md#application-settings).

### Device Login Credentials

The credentials/secrets management is further described within the [nautbot-plugin-nornir](https://github.com/nautobot/nautobot-plugin-nornir)
repository. For the simplest use case you can set environment variables for `NAPALM_USERNAME`, `NAPALM_PASSWORD`, and `DEVICE_SECRET`. For more
complicated use cases, please refer to the plugin documentation linked above.

## Starting a Backup Job

To start a backup job manually:

1. Navigate to the Plugin Home (Golden Config->Home), with Home being in the `Golden Configuration` section
2. Select _Execute_ on the upper right buttons, then _Backup_
3. Fill in the data that you wish to have backed up
4. Select _Run Job_

## Config Removals

The line removals settings is a series of regex patterns to identify lines that should be removed. This is helpful as there are usually parts of the
configurations that will change each time. A match simply means to remove.

In order to specify line removals. Navigate to **Golden Config -> Config Removals**.  Click the **Add** button and fill out the details.

The remove setting is based on `Platform`.  An example is shown below.
![Config Removals View](../images/00-navigating-backup.png)

## Config Replacements

This is a replacement config with a regex pattern with a single capture groups to replace. This is helpful to strip out secrets.

The replace lines setting is based on `Platform`.  An example is shown below.

![Config Replacements View](../images/01-navigating-backup.png)

The line replace uses Python's `re.sub` method. As shown, a common pattern is to obtain the non-confidential data in a capture group e.g. `()`, and return the rest of the string returned in the backrefence, e.g. `\2`.

```python
re.sub(r"(username\s+\S+\spassword\s+5\s+)\S+(\s+role\s+\S+)", r"\1<redacted_config>\2", config, flags=re.MULTILINE))
```
