# Uninstall the App from Nautobot

Here you will find any steps necessary to cleanly remove the App from your Nautobot environment.

## Database Cleanup

Prior to removing the plugin from the `nautobot_config.py`, run the following command to roll back any migration specific to this plugin.

```shell
nautobot-server migrate nautobot_plugin_golden_config zero
```

## Remove App configuration

Remove the configuration you added in `nautobot_config.py` from `PLUGINS` & `PLUGINS_CONFIG`.
