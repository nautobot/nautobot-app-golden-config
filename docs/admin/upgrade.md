# Upgrading the App

Here you will find any steps necessary to upgrade the App in your Nautobot environment.

## Upgrade Guide

When a new release comes out it may be necessary to run a migration of the database to account for any changes in the data models used by this app. Execute the command `nautobot-server post-upgrade` within the runtime environment of your Nautobot installation after updating the `nautobot-golden-config` package via `pip`.

## Per-Setting Feature Flags

The `enable_backup`, `enable_compliance`, `enable_intended`, `enable_sotagg`, `enable_plan`, `enable_deploy`, and `enable_postprocessing` settings moved from `PLUGINS_CONFIG` in `nautobot_config.py` to fields of the same name on each Golden Config Setting.

- **Existing Golden Config Settings keep their behavior.** During `nautobot-server post-upgrade`, a migration copies the values currently in `PLUGINS_CONFIG` onto every existing Golden Config Setting. A setting that was not present in `PLUGINS_CONFIG` is copied as its previous default: `True` for all of them except `enable_postprocessing`, which was `False`.
- **Leave the settings in `PLUGINS_CONFIG` until the upgrade has run.** The migration reads them once; removing them first means the previous defaults are applied instead of your configured values.
- **Remove the settings from `PLUGINS_CONFIG` afterwards.** They are no longer read at runtime, and Nautobot logs a deprecation warning at startup for as long as any of them remain.
- **New Golden Config Settings keep the previous defaults.** Every flag defaults to `True` except `Enable Postprocessing`, which defaults to `False`. Uncheck the features a new Setting should not run.
- **Config plans for devices outside every Setting no longer deploy.** A plan whose device is not in scope of any Golden Config Setting is skipped with an `E3038` warning and stays in its current status, where it previously deployed. Bring the device back into a Setting's Dynamic Group to deploy it.
- **`Enable SoT Aggregation` requires a GraphQL Query.** A Setting cannot be saved with it checked and no `GraphQL Query` selected. Uncheck it on Settings that do not generate intended configurations, such as backup-only Settings.

Navigation, Git datasource contents, list-view columns, and device template content are no longer hidden when a feature is disabled; the per-Setting flag is applied when a job runs. See [Feature-Enable Resolution Across Multiple Settings](../user/app_use_cases.md#feature-enable-resolution-across-multiple-settings).

## v1.0.0

`v1.0.0` Provides a breaking change for the users running pre `1.0.0` code sourced from `develop` branch of the app. Only users of the `Backup Repository Matching Rule` and `Intended Repository Matching Rule` features are affected by following behavior: migration script will only migrate the first repository from the list into the new default settings.

Because of this specific behavior, please review your configuration and capture it before attempting to upgrade if using above features.

Users running the released packages are not affected by this behavior.
