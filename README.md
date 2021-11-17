# nautobot-golden-config

A plugin for [Nautobot](https://github.com/nautobot/nautobot) that intends to provide context around golden configuration.

# Introduction

## What is the Golden Configuration Plugin?

The golden configuration plugin is a Nautobot plugin that aims to solve common configuration management challenges.

## Key Use Cases

This plugin enable four (4) key use cases.


1. **Configuration Backups** - Is a Nornir process to connect to devices, optionally parse out lines/secrets, backup the configuration, and save to a Git repository.
2. **Intended Configuration** - Is a Nornir process to generate configuration based on a Git repo of Jinja files to combine with a GraphQL generated data and a Git repo to store the intended configuration.
3. **Source of Truth Aggregation** - Is a GraphQL query per device that creates a data structure used in the generation of configuration.
4. **Configuration Compliance** - Is a process to run comparison of the actual (via backups) and intended (via Jinja file creation) CLI configurations upon saving the actual and intended configuration. This is started by either a Nornir process for cli-like configurations or calling the API for json-like configurations

>Notice: The operator's of their own Nautobot instance are welcome to use any combination of these features. Though the appearance may seem like they are tightly 
coupled, this isn't actually the case. For example, one can obtain backup configurations from their current RANCID/Oxidized process and simply provide a Git Repo
of the location of the backup configurations, and the compliance process would work the same way. Also, another user may only want to generate configurations,
but not want to use other features, which is perfectly fine to do so.

## Documentation
- [Installation](./docs/installation.md)
- [Quick Start Guide](./docs/quick-start.md)
- [Navigating Overview](./docs/navigating-golden.md)
- [Navigating Backup](./docs/navigating-backup.md)
- [Navigating Intended](./docs/navigating-intended.md)
- [Navigating SoTAgg](./docs/navigating-sot-agg.md)
- [Navigating Compliance](./docs/navigating-compliance.md)
- [Navigating JSON Compliance](./docs/navigating-compliance-json.md)
- [Navigating Custom Compliance](./docs/navigating-compliance-custom.md)
- [FAQ](./docs/FAQ.md)

## Screenshots

There are many features and capabilities the plugin provides into the Nautobot ecosystem. The following screenshots are intended to provide a quick visual overview of some of these features.

The golden configuration is driven by jobs that run a series of tasks and the result is captured in this overview.

![Overview](./docs/img/golden-overview.png)

The compliance report provides a high-level overview on the compliance of your network.
![Compliance Report](./docs/img/compliance-report.png)

The compliance overview will provide a per device and feature overview on the compliance of your network devices.
![Compliance Overview](./docs/img/compliance-overview.png)

Drilling into a specific device and feature, you can get an immediate detailed understanding of your device.
![Compliance Device](./docs/img/compliance-device.png)

![Compliance Rule](./docs/img/compliance-rule.png)

# Contributing

Pull requests are welcomed and automatically built and tested against multiple versions of Python and Nautobot through TravisCI.

The project is packaged with a light development environment based on `docker-compose` to help with the local development of the project and to run tests within TravisCI.

The project is following Network to Code software development guidelines and are leveraging the following:
- Black, Pylint, Bandit, flake8, and pydocstyle for Python linting and formatting.
- Django unit test to ensure the plugin is working properly.

## Branching Policy

The branching policy includes the following tenets:

- The develop branch is the branch of the next major or minor version planned.
- The `stable-<major>.<minor>` branch is the branch of the latest version within that major/minor version
- PRs intended to add new features should be sourced from the develop branch
- PRs intended to address bug fixes and security patches should be sourced from `stable-<major>.<minor>`

Nautobot Golden Config will observe semantic versioning, as of 1.0. This may result in an quick turn around in minor versions to keep
pace with an ever growing feature set.

## Release Policy

Nautobot Golden Config has currently no intended scheduled release schedule, and will release new feature in minor versions.

## Deprecation Policy

Support of upstream Nautobot will be announced 1 minor or major version ahead. Deprecation policy will be announced within the
CHANGELOG.md file, and updated in the table below. There will be a `stable-<major>.<minor>` branch that will be minimally maintained.
Any security enhancements or major bugs will be supported for a limited time. 

| Golden Config Version | Nautobot First Support Version | Nautobot Last Support Version |
| --------------------- | ------------------------------ | ----------------------------- |
| 0.9.X                 | 1.0                            | 1.2 [Official]                |
| 1.0.X                 | 1.2                            | 1.2 [Tentative]               |

## CLI Helper Commands

The project features a CLI helper based on [invoke](http://www.pyinvoke.org/) to help setup the development environment. The commands are listed below in 3 categories:
- `dev environment`
- `utility`
- `testing`. 

Each command can be executed with `invoke <command>`. All commands support the arguments `--nautobot-ver` and `--python-ver` if you want to manually define the version of Python and Nautobot to use. Each command also has its own help `invoke <command> --help`

> Note: to run the mysql (mariadb) development environment, set the environment variable as such `export NAUTOBOT_USE_MYSQL=1`.

### Local Development Environment

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
  pydocstyle       Run pydocstyle to validate docstring formatting adheres to NTC defined standards.
  pylint           Run pylint code analysis.
  tests            Run all tests for this plugin.
  unittest         Run Django unit tests for the plugin.
```
