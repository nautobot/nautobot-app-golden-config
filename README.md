# nautobot-golden-config

A plugin for [Nautobot](https://github.com/nautobot/nautobot) that intends to provide context around golden configuration.

In addition to this overview, documentation can be found for:

- [Navigating Overview](./docs/navigating-golden.md)
- [Navigating Backup](./docs/navigating-backup.md)
- [Navigating Compliance](./docs/navigating-compliance.md)
- [Navigating Intended](./docs/navigating-intended.md)
- [Navigating SoTAgg](./docs/navigating-sotagg.md)
- [FAQ](./docs/FAQ.md)

# Overview

The golden configuration plugin performs four primary actions, each of which can be toggled on with a respective `enable_*` setting, covered in detail 
later in the readme. 

* Configuration Backup - Is a Nornir process to connect to devices, optionally parse out lines/secrets, backup the configuration, and save to a Git repository.
* Configuration Intended - Is a Nornir process to generate configuration based on a Git repo of Jinja files and a Git repo to store the intended configuration.
* Source of Truth Aggregation - Is a GraphQL query per device with that creates a data structure used in the generation of configuration.
* Configuration Compliance - This is a comparison of the actual (via backups) and intended (via Jinja file creation) cli configurations.

The operator's of their own Nautobot instance are welcome to use any combination of these features. Though the appearance may seem like they are tightly 
coupled, they are not actually. As an example, once can obtain backup configurations from their current RANCID/Oxidized process and simply provide a Git Repo
of the location of the backup configurations and the compliance process would work the same way. Another user may only want to generate configurations.

## Screenshots

There are many features and capabilities the plugin provides, the following is intended to provide a quick visual overview of some of those features.

The golden configuration is driven by jobs that run a series of tasks and the result is captured in this overview.

![Compliance Feature](./docs/img/golden-overview.png)

The compliance report provides a high-level overview on the compliance of your network.
![Compliance Report](./docs/img/compliance-report.png)

The compliance overview will provide a per device and feature overview on the compliance of your network devices.
![Compliance Overview](./docs/img/compliance-overview.png)

Drilling into a specfic device and feature, you can get an immediate detailed understanding of your device.
![Compliance Device](./docs/img/compliance-device.png)

![Compliance Feature](./docs/img/compliance-feature.png)

## Settings

There are three primary controls to determine the inclusion of a device within one of the four given components.

* The `allowed_os` will allow list the specific operating systems that can be included.
* The `enable_backup`, `enable_compliance`, `enable_intended`, and `enable_sotagg` will toggle inclusion of the entire component.
* There is the ability to manage on a per device element TODO: Needs to be updated after more correctly implemented.

## Configuration Backup

The backup configuration process relies on the ability for the nautobot worker to connect via Nornir to the device, run the `show run` or equivalent command 
and save the configuration. The high-level process to run backups is:

* Download the latest Git repository, based on `backup config` type Git repo within Nautobot.
* Run a Nornir play to obtain the cli configurations.
* Optionally perform some lightweight processing of the backup.
* Store the backup configurations locally.
* Push configurations to the remote Git repository.

### Configuration Backup Settings

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

## Configuration Compliance 

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

### Configuration Compliance Parsing Engine

Configuration compliance is different then a simple unix diff. While the UI provides both, the compliance metrics are not influenced by the unix diff 
capabilities. One of the challenges of getting a device into compliance is the ramp up it takes to model and generate configurations for an entire 
configuration. The compliance engine has several features to better build out this process.

1. The ability to parse into smaller sections, given a list of root configuration elements.
2. The ability to consider ordered and non-ordered configurations.
3. The ability to dynamically understand parent/child relationships within the configurations.

In regards to `1`, consider the following example of how to obtain service configurations:
```
service
no service
```
Specific configurations that start with either of these commands can be grouped together.

In regards to `2`, consider the configurations of SNMP on a nexus switch. 
```
snmp-server community secure group network-admin
snmp-server community networktocode group network-operator
```

The above configurations are rendered based on the order in which they were entered, not based on the a deterministic way. The comparison process takes this into consideration. 

In regards to `3`, consider the following example of BGP configuration. 
```
router bgp
prefix-list
```
All configurations that are a parent and child relationships would be considered within the parsing engine. Additionally, if one configuration line was 
wrong, only that line and the parents would be shown, not all lines or only the missing configuration without context of the parents, e.g. Given:

Actual
```
router bgp 65250
  router-id 10.0.10.5
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map PERMIT_CONN_ROUTES
  neighbor 10.10.10.5
    remote-as 65250
    address-family ipv4 unicast
```

Intended
```
router bgp 65250
  router-id 10.0.10.6
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map PERMIT_CONN_ROUTES
  neighbor 10.10.10.5
    remote-as 65250
    address-family ipv4 unicast
```
Would result in the identfying the missing configurations as:

```
router bgp 65250
  router-id 10.0.10.6
```

### Configuration Compliance Settings

Configuration compliance requires the Git Repo settings for `config backups` and `intended configs`--which are covered in their respective sections--regardless if they are actually managed via the plugin or not.

The Configuration compliance feature map must be created per the operator. 

TODO: Once move the UI, document for now an example can be found [here](https://github.com/networktocode-llc/nautobot-gc-data/blob/be82d7f686a573ad33f85b2313e632d9bc2e7910/config_contexts/all.yml#L7-L196)

## Intended Configuration Generation

The Golden Config plugin provides the ability to generate configurations. The process is a Nornir play that points to a single Jinja template per 
device that generates the configurations. Data is provided via the Source of Truth aggregation and is currently a hard requirement to be turned on if 
generating configuration via the Golden Config plugin. Whatever data is returned by the Source of Truth Aggregation is available to the Jinja template.

As previous stated, there can only be a single template per device. It is often advantageous to break configurations into smaller snippets. A common pattern 
to overcome is:

```jinja
!
{% include os ~ '/services.j2' %}
!
{% include os ~ '/hostname.j2' %}
!
{% include os ~ '/ntp.j2' %}
!
```
or 

```jinja
!
{% set features = ['services', 'hostname', 'ntp'] %}
{% for feature in features %}
{% include os ~ '/' ~ feature ~ '.j2' %}
!
{% endfor %}
```

### Intended Configuration Settings

The configuration generation requires three components in addition to what was covered in the overall settings.

1. The creation of a Git Repo for "Intended Config".
2. The creation of a Git Repo for "Jinja Templates".
3. The `intended_path_template` configuration parameter.
4. The `jinja_path_template` configuration parameter.

The Git Repo's and path templates follow the same philosophy as those reviewed in the backup configuration. Please refer to that section for further details.

# Installation

> The plugin is compatible with Nautobot 1.0.0 and higher

Once installed, the plugin needs to be enabled in your `configuration.py` for both plugins

```python
PLUGINS = ["nautobot_plugin_nornir", "nautobot_golden_config"]

PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "nornir_settings": {
            "credentials": "nautobot_plugin_nornir.plugins.credentials.env_vars.CredentialsEnvVars",
            "runner": {
                "plugin": "threaded",
                "options": {
                    "num_workers": 20,
                },
            },
        },
    },
    "nautobot_golden_config": {
        "allowed_os": os.environ.get("ALLOWED_OS", "all").split(","),
        "per_feature_bar_width": float(os.environ.get("PER_FEATURE_BAR_WIDTH", 0.15)),
        "per_feature_width": int(os.environ.get("PER_FEATURE_WIDTH", 13)),
        "per_feature_height": int(os.environ.get("PER_FEATURE_HEIGHT", 4)),
        "enable_backup": is_truthy(os.environ.get("ENABLE_BACKUP", True)),
        "enable_compliance": is_truthy(os.environ.get("ENABLE_COMPLIANCE", True)),
        "enable_intended": is_truthy(os.environ.get("ENABLE_INTENDED", True)),
        "enable_sotagg": is_truthy(os.environ.get("ENABLE_SOTAGG", True)),
        "sot_agg_transposer": os.environ.get("SOT_AGG_TRANSPOSER"),
    },
}

```

The plugin behavior can be controlled with the following list of settings. 

| Key     | Example | Default | Description                          |
| ------- | ------ | -------- | ------------------------------------- |
| allowed_os | [cisco_ios, arista_eos] | [all] | A list of platforms supported, identified by the `platform_slug`, with special consideration for `all`. |
| enable_backup | True | True | A boolean to represent whether or not to run backup configurations within the plugin. |
| enable_compliance | True | True | A boolean to represent whether or not to run the compliance process within the plugin. |
| enable_intended | True | True | A boolean to represent whether or not to generate intended configurations within the plugin. |
| enable_sotagg | True | True | A boolean to represent whether or not to provide a GraphQL query per device to allow the intended configuration to provide data variables to the plugin. |
| per_feature_bar_width | 0.15 | 0.15 | The width of the table bar within the overview report | 
| per_feature_width | 13 | 13 | The width in inches that the overview table can be. | 
| per_feature_height | 4 | 4 | The height in inches that the overview table can be. | 
| sot_agg_transposer | mypkg.transposer | - | A string representation of a function that can post-process the graphQL data. |

> Note: Over time the intention is to make the compliance report more dynamic, but for now allow users to configure in a way that fits best for them.


## API

There is no way to currently run the script via an API, this would be helpful to use in the configuration compliance workflow, and will be a future feature.

# Contributing

Pull requests are welcomed and automatically built and tested against multiple version of Python and multiple version of Nautobot through TravisCI.

The project is packaged with a light development environment based on `docker-compose` to help with the local development of the project and to run the tests within TravisCI.

The project is following Network to Code software development guideline and is leveraging:
- Black, Pylint, Bandit, flake8, and pydocstyle for Python linting and formatting.
- Django unit test to ensure the plugin is working properly.

## CLI Helper Commands

The project is coming with a CLI helper based on [invoke](http://www.pyinvoke.org/) to help setup the development environment. The commands are listed below in 3 categories `dev environment`, `utility` and `testing`. 

Each command can be executed with `invoke <command>`. All commands support the arguments `--nautobot-ver` and `--python-ver` if you want to manually define the version of Python and Nautobot to use. Each command also has its own help `invoke <command> --help`

### Local dev environment

```
  build            Build all docker images.
  debug            Start Nautobot and its dependencies in debug mode.
  destroy          Destroy all containers and volumes.
  restart          Restart Nautobot and its dependencies in detached mode.
  start            Start Nautobot and its dependencies in detached mode.
  stop             Stop Nautobot and its dependencies.
```

### Utility 

```
  cli              Launch a bash shell inside the running Nautobot container.
  create-user      Create a new user in django (default: admin), will prompt for password.
  makemigrations   Run Make Migration in Django.
  nbshell          Launch a nbshell session.
```

### Testing 

```
  bandit           Run bandit to validate basic static code security analysis.
  black            Run black to check that Python files adhere to its style standards.
  flake8           Run flake8 to check that Python files adhere to its style standards.
  pylint           Run pylint code analysis.
  pydocstyle       Run pydocstyle to validate docstring formatting adheres to NTC defined standards.
  tests            Run all tests for this plugin.
  unittest         Run Django unit tests for the plugin.
```
