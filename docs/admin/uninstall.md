# Uninstall the App from Nautobot

## Uninstall Guide

Remove the configuration you added in `nautobot_config.py` from `PLUGINS` & `PLUGINS_CONFIG`.

## Database Cleanup

Drop all tables from the plugin: `nautobot_plugin_goldenconfig*`.
