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

The `backup_path_template` setting gives you a way to dynamically place each device's configuration file in the repository file structure. This setting uses the GraphQL query configured for the app. It works in a similar way to the Backup Repository Matching Rule above. Since the setting uses a GraphQL query, any valid Device model method is available. The app renders the values from the query, using Jinja2, to the relative path and file name in which to store a given device's configuration inside its backup repository. This may seem complicated, but the equivalent of `obj` by example would be:

```python
obj = Device.objects.get(name="nyc-rt01")
```

An example would be:
```python
backup_path_template = "{{obj.location.name|slugify}}/{{obj.name}}.cfg"
```

With a Sydney, AU device `SYD001AURTR32`, in the location named `Sydney001` and the GraphQL query and `backup_path_template` configured above, our backed-up config would be placed in the repo in `/sydney001/SYD001AURTR32.cfg`.

The backup process will automatically create folders as required based on the path definition. 

The `backup_path_template` can be set in the UI.  For navigation details [see](./app_use_cases.md#application-settings).

### Device Login Credentials

The credentials/secrets management occurs within the [nautobot-plugin-nornir](https://github.com/nautobot/nautobot-plugin-nornir) library and is described in the [Navigating Credentials](https://docs.nautobot.com/projects/plugin-nornir/en/latest/user/app_feature_credentials/) documentation. For the simplest use case you can set environment variables for `NAPALM_USERNAME`, `NAPALM_PASSWORD`, and `DEVICE_SECRET` in conjunction with the `credentials` string shown below in your configuration for `nautobot-plugin-nornir`.

```python
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "nornir_settings": {
           "credentials": "nautobot_plugin_nornir.plugins.credentials.env_vars.CredentialsEnvVars"
        },
    }
}
```

## Starting a Backup Job

To start a backup job manually:

1. Navigate to the App Home (Golden Config->Home), with Home being in the `Golden Configuration` section
2. Select _Execute_ on the upper right buttons, then _Backup_
3. Fill in the data that you wish to have backed up
4. Select _Run Job_

## Config Removals

The line removals settings is a series of regex patterns to identify lines that should be removed. This is helpful as there are usually parts of the
configurations that will change each time. A match simply means to remove.

In order to specify line removals. Navigate to **Golden Config -> Config Removals**.  Click the **Add** button and fill out the details.

The remove setting is based on `Platform`.  An example is shown below.

![Config Removals View](../images/ss1_00-navigating-backup_light.png#only-light){ .on-glb }
![Config Removals View](../images/ss1_00-navigating-backup_dark.png#only-dark){ .on-glb }

## Config Replacements

This is a replacement config with a regex pattern with a single capture groups to replace. This is helpful to strip out secrets.

The replace lines setting is based on `Platform`.  An example is shown below.

![Config Replacements View](../images/ss1_01-navigating-backup_light.png#only-light){ .on-glb }
![Config Replacements View](../images/ss1_01-navigating-backup_dark.png#only-dark){ .on-glb }

The line replace uses Python's `re.sub` method. As shown, a common pattern is to obtain the non-confidential data in a capture group e.g. `()`, and return the rest of the string returned in the backreference, e.g. `\2`.

```python
re.sub(r"(username\s+\S+\spassword\s+5\s+)\S+(\s+role\s+\S+)", r"\1<redacted_config>\2", config, flags=re.MULTILINE))
```

### Hashing Secrets Instead of Removing Them

+++ 3.1.0

Replacing a secret with a static placeholder such as `<redacted_config>` discards the value entirely, so every device with a secret on that line ends up identical and the line can no longer be meaningfully compliance-checked. As an alternative, the **Replaced Text** field is Jinja-aware: instead of a static replacement you can supply a Jinja template that transforms the matched data, for example by hashing it with the [`hash_data`](https://netutils.readthedocs.io/en/latest/dev/code_reference/hash/) filter. Because the same hash filter is available when rendering your intended configuration, you can hash the same cleartext value on both sides and the backup will still be compliant, all without storing the cleartext secret in the backup.

!!! note
    Jinja rendering of the Replaced Text relies on the optional `jinja2` dependency of `netutils`. It is already installed as part of Golden Config's dependencies, so no extra action is required.

#### How the Template Works

When the **Replaced Text** contains a Jinja expression (`{{ ... }}`), Golden Config renders the *entire* replacement as a Jinja template once per matched line, rather than performing a plain `re.sub` string substitution. The regex capture groups are made available to the template, so you write the full output line and drop each captured value into place:

- Reference a named capture group (`(?P<name>...)`) by name inside a `{{ ... }}` expression, e.g. `{{ secret }}`. Named groups are recommended for readability. Positional groups are also available via the familiar `re.sub` backreference syntax (`\1`, `\2`, ...).
- Static text is written literally, exactly as it should appear in the backup.
- Pipe a capture group through any [netutils Jinja filter](https://netutils.readthedocs.io/en/latest/user/lib_use_cases_jinja_filters/), most usefully `hash_data('<algorithm>')` where `<algorithm>` is any algorithm supported by Python's `hashlib` (e.g. `md5`, `sha256`, `sha512`).

!!! warning
    The regex must capture *exactly* the secret you intend to transform. Anything you do not re-emit in the template (literally or via a backreference) is dropped from the line.

#### Examples

![Config Replacements with Hashing](../images/config-replacement-hashing_light.png#only-light){ .on-glb }
![Config Replacements with Hashing](../images/config-replacement-hashing_dark.png#only-dark){ .on-glb }

Hash the username and the secret on an IOS local-user line, using named capture groups for readability.

Regex Pattern to Substitute:

```text
username (?P<user>\S+) privilege 15 secret 9 (?P<secret>\S+)
```

Replaced Text:

```text
username {{ user | hash_data('md5') }} privilege 15 secret 9 {{ secret | hash_data('md5') }}
```

Given the line `username foo privilege 15 secret 9 bar`, the backup stores:

```text
username acbd18db4cc2f85cedef654fccc4a4d8 privilege 15 secret 9 37b51d194a7513e45b56f6524f2d51f2
```

The same substitution can be written with positional backreferences (`\1`, `\2`, ...) instead of named groups, which is handy for quick one-off patterns.

Regex Pattern to Substitute:

```text
username (\S+) privilege 15 secret 9 (\S+)
```

Replaced Text:

```text
username {{ \1 | hash_data('md5') }} privilege 15 secret 9 {{ \2 | hash_data('md5') }}
```

#### Keeping Templates Within the Field Limit

For longer lines, rather than re-typing every static word, capture the unchanging middle of the line into its own group and re-emit it unchanged. Named and positional groups can be mixed freely in the same template: name the values you care about and use a positional backreference for the bulk carry-over.

Regex Pattern to Substitute:

```text
username (?P<user>\S+) (.+) secret 9 (?P<secret>\S+)
```

Replaced Text:

```text
username {{ user | hash_data('md5') }} {{ \2 }} secret 9 {{ secret | hash_data('md5') }}
```

Here the `user` and `secret` named groups are hashed, while the positional `\2` captures everything between the username and `secret 9` and is reproduced verbatim.

!!! note
    The positional number is based on the order the capture groups appear in the regex, reading left to right: `\1` is the first `(...)` group, `\2` is the second, and so on. Named groups are also counted in this order, so a named group still has a positional number you can reference if you prefer.
