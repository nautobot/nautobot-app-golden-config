# Upgrading the App

Here you will find any steps necessary to upgrade the App in your Nautobot environment.

## Upgrade Guide

When a new release comes out it may be necessary to run a migration of the database to account for any changes in the data models used by this plugin. Execute the command `nautobot-server post-upgrade` within the runtime environment of your Nautobot installation after updating the `nautobot-golden-config` package via `pip`.

## v1.0.0

`v1.0.0` Provides a breaking change for the users running pre `1.0.0` code sourced from `develop` branch of the plugin. Only users of the `Backup Repository Matching Rule` and `Intended Repository Matching Rule` features are affected by following behavior: migration script will only migrate the first repository from the list into the new default settings.

Because of this specific behavior, please review your configuration and capture it before attempting to upgrade if using above features.

Users running the released packages are not affected by this behavior.
