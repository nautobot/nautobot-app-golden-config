# Configuration Backup

The backup configuration process relies on the ability for the nautobot worker to connect via Nornir to the device, run the `show run` or equivalent command 
and save the configuration. The high-level process to run backups is:

* Download the latest Git repository, based on `backup config` type Git repo within Nautobot.
* Run a Nornir play to obtain the cli configurations.
* Optionally perform some lightweight processing of the backup.
* Store the backup configurations locally.
* Push configurations to the remote Git repository.

## Installation Instructions

## Configuration Backup Settings

Backup configurations often need some amount of parsing to stay sane. The two obvious use cases are the ability to remove lines such as the "Last 
Configuration" changed date, as this will cause unnecessary changes the second is to strip out secrets from the configuration. In an effort to support these 
uses cases, the following settings are available.

* Remove Lines - provides the ability to remove a line based on a regex match.
* Substitute Lines - provides the ability to swap out parts of a line based on a regex match.

TODO: Document when ideally it is in the UI and not in config context, for now, can reference [here](https://github.com/networktocode-llc/nautobot-gc-data/blob/be82d7f686a573ad33f85b2313e632d9bc2e7910/config_contexts/all.yml#L197-L214)

Backup configurations rely on a Git Repo, and the plugin registers an additional repository for Git source this access. Within the Nautobot Git repositories, there will be a `backup config` option, which there must be one and only one configured for the process to work.

TODO: insert screenshot

The `backup_path_template` provides the ability to dynamically state per device where the configurations should end up in the file structure. Every device 
there is a Django ORM object, tied to the model instance of a `Device` model, and that is represented as `obj`. That means that any valid Device model method is available. This is then compiled via Jinja. This may seem complicated, but the equivalent of `obj` by example would be:

```python
obj = Device.objects.get(name="nyc-rt01")
```

An example would be:
```python
backup_path_template = "{{obj.site.slug}}/{{obj.name}}.cfg"
```

The backup process will automatically create folders as required based on the path definition. 

## 
