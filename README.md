# Nautobot Golden Config

<p align="center">
  <img src="https://raw.githubusercontent.com/nautobot/nautobot-app-golden-config/develop/docs/images/icon-nautobot-golden-config.png" class="logo" height="200px">
  <br>
  <a href="https://github.com/nautobot/nautobot-app-golden-config/actions"><img src="https://github.com/nautobot/nautobot-app-golden-config/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://docs.nautobot.com/projects/golden-config/en/latest"><img src="https://readthedocs.org/projects/nautobot-app-golden-config/badge/"></a>
  <a href="https://pypi.org/project/nautobot-golden-config/"><img src="https://img.shields.io/pypi/v/nautobot-golden-config"></a>
  <a href="https://pypi.org/project/nautobot-golden-config/"><img src="https://img.shields.io/pypi/dm/nautobot-golden-config"></a>
  <br>
  An App for <a href="https://github.com/nautobot/nautobot">Nautobot</a>.
</p>

## Overview

The Golden Config App is a Nautobot App that provides a NetDevOps approach to golden configuration and configuration compliance.

!!! info
    Upgrading to Nautobot and Nautobot Golden Config 2.0, see our [migration guide](https://docs.nautobot.com/projects/golden-config/en/latest/admin/migrating_to_v2/)!

### Key Use Cases

> Developer Note: Place the files in the `docs/images/` folder and link them using only full URLs from GitHub, for example: `![Overview](https://raw.githubusercontent.com/nautobot/nautobot-app-golden-config/develop/docs/images/app-overview.png)`. This absolute static linking is required to ensure the README renders properly in GitHub, the docs site, and any other external sites like PyPI.

More screenshots can be found in the [Using the App](https://docs.nautobot.com/projects/golden-config/en/latest/user/app_use_cases/) page in the documentation. Here's a quick overview of some of the app's added functionality:

![](https://raw.githubusercontent.com/nautobot/nautobot-app-golden-config/develop/docs/images/placeholder.png)

## Try it out!

This App is installed in the Nautobot Community Sandbox found over at [demo.nautobot.com](https://demo.nautobot.com/)!

> For a full list of all the available always-on sandbox environments, head over to the main page on [networktocode.com](https://www.networktocode.com/nautobot/sandbox-environments/).

## Documentation

Full web-based HTML documentation for this app can be found over on the [Nautobot Docs](https://docs.nautobot.com/projects/golden-config/en/latest/) website:

- [User Guide](https://docs.nautobot.com/projects/golden-config/en/latest/user/app_overview/) - Overview, Using the App, Getting Started, Navigating compliance (cli, json, custom), backup, app usage, intended state creation.
- [Administrator Guide](https://docs.nautobot.com/projects/golden-config/en/latest/admin/install/) - How to Install, Configure, Upgrade, or Uninstall the App.
- [Developer Guide](https://docs.nautobot.com/projects/golden-config/en/latest/dev/contributing/) - Extending the App, Code Reference, Contribution Guide.
- [Release Notes / Changelog](https://docs.nautobot.com/projects/golden-config/en/latest/admin/release_notes/)
- [Frequently Asked Questions](https://docs.nautobot.com/projects/golden-config/en/latest/user/faq/)

### Contributing to the Docs

You can find all the Markdown source for the App documentation under the [`docs`](https://github.com/nautobot/nautobot-app-golden-config/tree/develop/docs) folder in this repository. For simple edits, a Markdown capable editor is sufficient: clone the repository and edit away.

If you need to view the fully generated documentation site, you can build it with [mkdocs](https://www.mkdocs.org/). A container hosting the docs will be started using the invoke commands (details in the [Development Environment Guide](https://docs.nautobot.com/projects/golden-config/en/latest/dev/dev_environment/#docker-development-environment)) on [http://localhost:8001](http://localhost:8001). As your changes are saved, the live docs will be automatically reloaded.

Any PRs with fixes or improvements are very welcome!

## Questions

For any questions or comments, please check the [FAQ](https://docs.nautobot.com/projects/golden-config/en/latest/user/faq/) first. Feel free to also swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#nautobot`), sign up [here](http://slack.networktocode.com/) if you don't have an account.
