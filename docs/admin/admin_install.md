# Installing the App in Nautobot

## Prerequisites

- The plugin relies on [`nautobot_plugin_nornir`](https://pypi.org/project/nautobot-plugin-nornir/) to be installed and both plugins to be enabled in your configuration settings.
- The plugin is compatible with Nautobot 1.4.0 and higher.
- Databases supported: PostgreSQL, MySQL

!!! note
    Please check the [dedicated page](compatibility_matrix.md) for a full compatibility matrix and the deprecation policy.

## Install Guide

!!! note
    Plugins can be installed manually or using Python's `pip`. See the [nautobot documentation](https://nautobot.readthedocs.io/en/latest/plugins/#install-the-package) for more details. The pip package name for this plugin is [`nautobot-golden-config`](https://pypi.org/project/nautobot-golden-config/).

The plugin is available as a Python package via PyPI and can be installed with `pip`:

```shell
pip install nautobot-golden-config
```

To ensure Nautobot Golden Config is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the Nautobot root directory (alongside `requirements.txt`) and list the `nautobot-golden-config` package:

```shell
echo nautobot-golden-config >> local_requirements.txt
```

Once installed, the plugin needs to be enabled in your Nautobot configuration. The following block of code below shows the additional configuration required to be added to your `nautobot_config.py` file:

- Append `"nautobot_golden_config"` to the `PLUGINS` list, and `"nautobot_plugin_nornir"` if it was not already there (more info [here](https://github.com/nautobot/nautobot-plugin-nornir)).
- Append the `"nautobot_golden_config"` dictionary to the `PLUGINS_CONFIG` dictionary, and `"nautobot_plugin_nornir"` if it was not already there.

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
        "per_feature_bar_width": 0.15,
        "per_feature_width": 13,
        "per_feature_height": 4,
        "enable_backup": True,
        "enable_compliance": True,
        "enable_intended": True,
        "enable_sotagg": True,
        "sot_agg_transposer": None,
        "enable_postprocessing": False,
        "postprocessing_callables": [],
        "postprocessing_subscribed": [],
        "sync_config_context_repos": False,
        "platform_slug_map": None,
        # "get_custom_compliance": "my.custom_compliance.func"
    },
}
```

The following block of code below shows the additional configuration required to be added to your `nautobot_config.py` file:

- append `"nautobot_golden_config"` to the `PLUGINS` list, and `"nautobot_plugin_nornir"` if it was not already there (more info [here](https://github.com/nautobot/nautobot-plugin-nornir)).
- append the `"nautobot_golden_config"` dictionary to the `PLUGINS_CONFIG` dictionary, and `"nautobot_plugin_nornir"` if it was not already there.

Once the Nautobot configuration is updated, run the Post Upgrade command (`nautobot-server post_upgrade`) to run migrations and clear any cache.

```shell
nautobot-server post_upgrade
```

Then restart the Nautobot services which may include:

- Nautobot
- Nautobot Workers
- Nautobot Scheduler

```shell
sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
```

## App Configuration

The plugin behavior can be controlled with the following list of settings.

!!! note
    The `enable_backup`, `enable_compliance`, `enable_intended`, `enable_sotagg` and `enable_postprocessing` will toggle inclusion of the entire component.

| Key                       | Example                       | Default | Description                                                                                                                                                                |
| ------------------------- | ----------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| enable_backup             | True                          | True    | A boolean to represent whether or not to run backup configurations within the plugin.                                                                                      |
| enable_compliance         | True                          | True    | A boolean to represent whether or not to run the compliance process within the plugin.                                                                                     |
| enable_intended           | True                          | True    | A boolean to represent whether or not to generate intended configurations within the plugin.                                                                               |
| enable_sotagg             | True                          | True    | A boolean to represent whether or not to provide a GraphQL query per device to allow the intended configuration to provide data variables to the plugin.                   |
| enable_postprocessing     | True                          | False    | A boolean to represent whether or not to generate intended configurations to push, with extra processing such as secrets rendering.                                        |
| postprocessing_callables  | ['mypackage.myfunction']      | []      | A list of function paths, in dotted format, that are appended to the available methods for post-processing the intended configuration, for instance, the `render_secrets`. |
| postprocessing_subscribed | ['mypackage.myfunction']      | []      | A list of function paths, that should exist as postprocessing_callables, that defines the order of application of during the post-processing process.                      |
| platform_slug_map         | {"cisco_wlc": "cisco_aireos"} | None    | A dictionary in which the key is the platform slug and the value is what netutils uses in any "network_os" parameter.                                                      |
| sync_config_context_repos | False                         | False   | A boolean to represent whether to synchronize all configured Config Context git repositories during the intended generation.                                                                                               |
| sot_agg_transposer        | "mypkg.transposer"            | None    | A string representation of a function that can post-process the graphQL data.                                                                                              |
| per_feature_bar_width     | 0.15                          | 0.15    | The width of the table bar within the overview report                                                                                                                      |
| per_feature_width         | 13                            | 13      | The width in inches that the overview table can be.                                                                                                                        |
| per_feature_height        | 4                             | 4       | The height in inches that the overview table can be.                                                                                                                       |

!!! note
    Over time the compliance report will become more dynamic, but for now allow users to configure the `per_*` configs in a way that fits best for them.

!!! note
    Review [`nautobot_plugin_nornir`](https://pypi.org/project/nautobot-plugin-nornir/) for Nornir and dispatcher configuration options.
