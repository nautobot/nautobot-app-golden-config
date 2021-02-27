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
* Configuration Compliance - Is a Nornir process to run comparison of the actual (via backups) and intended (via Jinja file creation) cli configurations.

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

## Plugin Settings

There are three primary controls to determine the inclusion of a device within one of the four given components.

* The `allowed_os` will allow list the specific operating systems that can be included.
* The `enable_backup`, `enable_compliance`, `enable_intended`, and `enable_sotagg` will toggle inclusion of the entire component.
* There is the ability to manage on a per device element TODO: Needs to be updated after more correctly implemented.

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
