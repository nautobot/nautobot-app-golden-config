# Installation

Plugins can be installed manually or use Python's `pip`. See the [nautobot documentation](https://nautobot.readthedocs.io/en/latest/plugins/#install-the-package) for more details. The pip package name for this plugin is [`nautobot-golden-config`](https://pypi.org/project/nautobot-golden-config/)

> The plugin is compatible with Nautobot 1.0.0 and higher

**Prerequisite:** The plugin relies on [`nautobot_plugin_nornir`](https://pypi.org/project/nautobot-plugin-nornir/) to be installed and both plugins to be enabled in your configuration settings.

**Required:** The following block of code below shows the additional configuration required to be added to your `nautobot_config.py` file:
- append `"nautobot_golden_config"` to the `PLUGINS` list, and `"nautobot_plugin_nornir"` if it was not already there (More info [here](https://github.com/nautobot/nautobot-plugin-nornir))
- append the `"nautobot_golden_config"` dictionary to the `PLUGINS_CONFIG` dictionary, and `"nautobot_plugin_nornir"` if it was not already there.

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
        "platform_slug_map": None,
        # "get_custom_compliance": "my.custom_compliance.func"
    },
}

```

## Plugin Configuration

The plugin behavior can be controlled with the following list of settings. 

* The `enable_backup`, `enable_compliance`, `enable_intended`, and `enable_sotagg` will toggle inclusion of the entire component.


| Key     | Example | Default | Description                          |
| ------- | ------ | -------- | ------------------------------------- |
| enable_backup | True | True | A boolean to represent whether or not to run backup configurations within the plugin. |
| enable_compliance | True | True | A boolean to represent whether or not to run the compliance process within the plugin. |
| enable_intended | True | True | A boolean to represent whether or not to generate intended configurations within the plugin. |
| enable_sotagg | True | True | A boolean to represent whether or not to provide a GraphQL query per device to allow the intended configuration to provide data variables to the plugin. |
| platform_slug_map | {"cisco_wlc": "cisco_aireos"} | None | A dictionary in which the key is the platform slug and the value is what netutils uses in any "network_os" parameter. |
| sot_agg_transposer | "mypkg.transposer" | None | A string representation of a function that can post-process the graphQL data. |
| per_feature_bar_width | 0.15 | 0.15 | The width of the table bar within the overview report |
| per_feature_width | 13 | 13 | The width in inches that the overview table can be. |
| per_feature_height | 4 | 4 | The height in inches that the overview table can be. |

> Note: Over time the compliance report will become more dynamic, but for now allow users to configure the `per_*` configs in a way that fits best for them.

> Note: Review [`nautobot_plugin_nornir`](https://pypi.org/project/nautobot-plugin-nornir/) for Nornir and dispatcher configuration options. 
