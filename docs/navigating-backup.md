# Configuration Backup

The backup configuration process relies on the ability for the nautobot worker to connect via Nornir to the device, run the `show run` or equivalent command 
and save the configuration. The high-level process to run backups is:

* Download the latest Git repository, based on `backup config` type Git repo within Nautobot.
* Run a Nornir play to obtain the cli configurations.
* Optionally perform some lightweight processing of the backup.
* Store the backup configurations locally.
* Push configurations to the remote Git repository.

# Configuration Backup Settings

Backup configurations often need some amount of parsing to stay sane. The two obvious use cases are the ability to remove lines such as the "Last 
Configuration" changed date, as this will cause unnecessary changes the second is to strip out secrets from the configuration. In an effort to support these 
uses cases, the following settings are available.

* Remove Lines - provides the ability to remove a line based on a regex match.
* Substitute Lines - provides the ability to swap out parts of a line based on a regex match.

TODO: Document when ideally it is in the UI and not in config context, for now, can reference [here](https://github.com/networktocode-llc/nautobot-gc-data/blob/be82d7f686a573ad33f85b2313e632d9bc2e7910/config_contexts/all.yml#L197-L214)

Backup configurations rely on a Git Repo, and the plugin registers an additional repository for Git source this access. Within the Nautobot Git repositories, there will be a `backup config` option, which there must be one and only one configured for the process to work.

In order to setup this repository, go to Nautobot and navigate to the Data Sources Git integration. `Extensibility -> Git Repositories`.

![Backup Git Navigation](./img/git-step1.png)

From the Git Repositories page we an add the **Backup** repository.

Click on `[+ADD]`.

You will now be presented with a page to fill in the repository details.

Parameters:
|Field|Explanation|
|:--|:--|
|Name|User friendly name for the backup repo.|
|Slug|Auto-generated based on the `name` provided.|
|Remote URL|The URL pointing to the Git repo that stores the backup configuration files. Current git url usage is limited to `http` or `https`.|
|Branch|The branch in the Git repo to use. Defaults to `main`.|
|Token|The token is a personal access token for the `username` provided.  For more information on generating a personal access token. [Github Personal Access Token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
|Username|The Git username that corresponds with the personal access token above.|
|Provides|Valid providers for Git Repo.|
<br>

![Example Git Backups](./img/backup-git-step2.png)

Select `backup configs` and click on `[Create]`.

Once you click `[Create]` and the repository syncs, the main page will now show the repo along with its status.
![Git Backup Repo Status](./img/backup-git-step3.png)


The `backup_path_template` provides the ability to dynamically state per device where the configurations should end up in the file structure. Every device is a Django ORM object, tied to the model instance of a `Device` model, and that is represented as `obj`. That means that any valid Device model method is available. This is then compiled via Jinja. This may seem complicated, but the equivalent of `obj` by example would be:

```python
obj = Device.objects.get(name="nyc-rt01")
```

An example would be:
```python
backup_path_template = "{{obj.site.slug}}/{{obj.name}}.cfg"
```

The backup process will automatically create folders as required based on the path definition. 

The `backup_path_template` can be set in the UI.  For details [see](./golden-config-settings.md#Backup-Path)

# Remove Settings

The remove settings is a series of regex patterns to identify lines that should be removed. This is helpful as there are usually parts of the
configurations that will change each time. A match simply means to remove.

```re
^Building\s+configuration.*\n
^Current\s+configuration.*\n
^!\s+Last\s+configuration.*
```

# Substitute Lines

This is a replacement config with a regex pattern with a single capture group to replace. This is helpful to strip out secrets. The two are currently
split by 3 "pipes" `|||`. This is not an ideal configuration, but useful until a long term solution can be put in place.

```re
<redacted_config>|||username\s+\S+\spassword\s+5\s+(\S+)\s+role\s+\S+
```