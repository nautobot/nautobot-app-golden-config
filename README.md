# Nautobot Golden Config

<p align="center">
  <img src="https://raw.githubusercontent.com/nautobot/nautobot-plugin-golden-config/develop/docs/images/icon-NautobotGoldenConfig.png" class="logo" height="200px">
  <br>
  <a href="https://github.com/nautobot/nautobot-plugin-golden-config/actions"><img src="https://github.com/nautobot/nautobot-plugin-golden-config/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://docs.nautobot.com/projects/golden-config/en/latest/"><img src="https://readthedocs.org/projects/nautobot-plugin-golden-config/badge/"></a>
  <a href="https://pypi.org/project/nautobot-golden-config/"><img src="https://img.shields.io/pypi/v/nautobot-golden-config"></a>
  <a href="https://pypi.org/project/nautobot-golden-config/"><img src="https://img.shields.io/pypi/dm/nautobot-golden-config"></a>
  <br>
  An App for <a href="https://github.com/nautobot/nautobot">Nautobot</a>.
</p>

## Overview

The Golden Config plugin is a Nautobot plugin that provides a NetDevOps approach to golden configuration and configuration compliance.

### Key Use Cases

This plugin enable six (6) key use cases.

1. **Configuration Backups** - Is a Nornir process to connect to devices, optionally parse out lines/secrets, backup the configuration, and save to a Git repository.
2. **Intended Configuration** - Is a Nornir process to generate configuration based on a Git repo of Jinja files to combine with a GraphQL generated data and a Git repo to store the intended configuration.
3. **Source of Truth Aggregation** - Is a GraphQL query per device that creates a data structure used in the generation of configuration.
4. **Configuration Compliance** - Is a process to run comparison of the actual (via backups) and intended (via Jinja file creation) CLI configurations upon saving the actual and intended configuration. This is started by either a Nornir process for cli-like configurations or calling the API for json-like configurations
5. **Configuration Remediation** - Is a process of generating a partial device configuration that would get a configuration feature into a compliant state. 
6. **Configuration Deployment** - Is a process to generate a device configuration and push it to the network device. It supports compliance features, remediation engine and manual definitions.

> Notice: **Configuration Postprocessing** - (beta feature) This process renders a valid configuration artifact from an intended configuration, that can be pushed to devices. The current implementation renders this configuration; however, **it doesn't push it** to the target device.

> Notice: The operators of their own Nautobot instance are welcome to use any combination of these features. Though the appearance may seem like they are tightly coupled, this isn't actually the case. For example, one can obtain backup configurations from their current RANCID/Oxidized process and simply provide a Git Repo of the location of the backup configurations, and the compliance process would work the same way. Also, another user may only want to generate configurations, but not want to use other features, which is perfectly fine to do so.

## Screenshots

There are many features and capabilities the plugin provides into the Nautobot ecosystem. The following screenshots are intended to provide a quick visual overview of some of these features.

The golden configuration is driven by jobs that run a series of tasks and the result is captured in this overview.

![Overview](https://raw.githubusercontent.com/nautobot/nautobot-plugin-golden-config/develop/docs/images/ss_golden-overview.png)

The compliance report provides a high-level overview on the compliance of your network.
![Compliance Report](https://raw.githubusercontent.com/nautobot/nautobot-plugin-golden-config/develop/docs/images/ss_compliance-report.png)

The compliance overview will provide a per device and feature overview on the compliance of your network devices.
![Compliance Overview](https://raw.githubusercontent.com/nautobot/nautobot-plugin-golden-config/develop/docs/images/ss_compliance-overview.png)

Drilling into a specific device and feature, you can get an immediate detailed understanding of your device.
![Compliance Device](https://raw.githubusercontent.com/nautobot/nautobot-plugin-golden-config/develop/docs/images/ss_compliance-device.png)

![Compliance Rule](https://raw.githubusercontent.com/nautobot/nautobot-plugin-golden-config/develop/docs/images/ss_compliance-rule.png)

## Try it out!

This App is installed in the Nautobot Community Sandbox found over at [demo.nautobot.com](https://demo.nautobot.com/)!

> For a full list of all the available always-on sandbox environments, head over to the main page on [networktocode.com](https://www.networktocode.com/nautobot/sandbox-environments/).

## Documentation

Full web-based HTML documentation for this app can be found over on the [Nautobot Docs](https://docs.nautobot.com/projects/golden-config/en/latest/) website:

- [User Guide](https://docs.nautobot.com/projects/golden-config/en/latest/user/app_overview/) - Overview, Using the App, Getting Started, Navigating compliance (cli, json, custom), backup, app usage, intended state creation.
- [Administrator Guide](https://docs.nautobot.com/projects/golden-config/en/latest/admin/admin_install/) - How to Install, Configure, Upgrade, or Uninstall the App.
- [Developer Guide](https://docs.nautobot.com/projects/golden-config/en/latest/dev/dev_contributing/) - Extending the App, Code Reference, Contribution Guide.
- [Release Notes / Changelog](https://docs.nautobot.com/projects/golden-config/en/latest/admin/release_notes/)
- [Frequently Asked Questions](https://docs.nautobot.com/projects/golden-config/en/latest/user/app_faq/)

### Contributing to the Docs

You can find all the Markdown source for the App documentation under the [docs](https://github.com/nautobot/nautobot-plugin-golden-config/tree/develop/docs) folder in this repository. For simple edits, a Markdown capable editor is sufficient - clone the repository and edit away.

If you need to view the fully generated documentation site, you can build it with [mkdocs](https://www.mkdocs.org/). A container hosting the docs will be started using the invoke commands (details in the [Development Environment Guide](https://docs.nautobot.com/projects/golden-config/en/latest/dev/dev_environment/#docker-development-environment)) on [http://localhost:8001](http://localhost:8001). As your changes are saved, the live docs will be automatically reloaded.

Any PRs with fixes or improvements are very welcome!

## Questions

For any questions or comments, please check the [FAQ](https://docs.nautobot.com/projects/golden-config/en/latest/user/app_faq/) first. Feel free to also swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#nautobot`), sign up [here](http://slack.networktocode.com/) if you don't have an account.
